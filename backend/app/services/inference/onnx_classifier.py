import asyncio
import io
import json
import logging
import math
import os
import uuid
from typing import Optional, List, Dict, Any
from PIL import Image
from app.services.inference.base import BaseClassifier
from app.services.inference.result import ClassificationResult, MaterialGuidance, DisposalGuidance
from app.services.inference.broad_classes import UNKNOWN_MATERIAL, get_broad_entry
from app.services.inference.preprocess import preprocess_image, DEFAULT_INPUT_SIZE, NUM_CHANNELS
from app.core.errors import InferenceFailedError, InvalidInputError, UnsupportedFormatError

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.35

# --- ONNX output contract -------------------------------------------------
# The deployed model (yolo26n-cls-v1, exported by ml/export_onnx.py) has a
# Softmax classification head: its [1, C] output is ALREADY a probability
# distribution (verified against the artefact: finite, within [0, 1], sums to
# 1.0). Applying softmax again on such an output caps the maximum confidence at
# e / (e + C - 1) ≈ 0.28 for C = 8, silently breaking thresholding. The default
# semantics is therefore "probabilities". A genuinely different model that
# returns raw logits must opt in explicitly via MODEL_OUTPUT="logits"; the
# classifier never guesses (and never softmaxes twice).
DEFAULT_OUTPUT_SEMANTICS = "probabilities"
VALID_OUTPUT_SEMANTICS = ("probabilities", "logits")

# Documented tolerance for the "sums to one" validation of probability output.
# A genuine softmax head sums to 1 within fp32 rounding (~1e-6); 2% absorbs
# platform/quantisation drift while still rejecting malformed vectors.
OUTPUT_SUM_TOLERANCE = 0.02
# Probabilities must be non-negative; a tiny epsilon absorbs fp32 rounding.
PROB_NEG_EPSILON = 1e-6


class ModelOutputError(ValueError):
    """Raised when an ONNX output violates the configured output contract."""


class ONNXClassifier(BaseClassifier):
    """ONNX Runtime Waste Classifier — the application's only classification path."""

    def __init__(self, model_path: str, class_index_map: Optional[str] = None,
                 output_semantics: Optional[str] = None):
        self._model_path = model_path
        self._class_index_map = class_index_map
        self._index_to_class: Dict[int, str] = self._load_class_map(class_index_map)
        self._output_semantics = self._resolve_output_semantics(output_semantics)
        try:
            from app.core.config import get_settings as _get_settings
            self._model_version = _get_settings().MODEL_VERSION or "yolo26n-cls-v1"
        except Exception:
            self._model_version = "yolo26n-cls-v1"

        try:
            import onnxruntime as ort
            self._session = ort.InferenceSession(model_path)
            inputs = self._session.get_inputs()
            self._input_name = inputs[0].name if inputs else None
            self._input_shape = list(inputs[0].shape) if inputs else [1, 3, 640, 640]
        except Exception as e:
            logger.error(f"Failed to load ONNX model at {model_path}: {e}")
            raise FileNotFoundError(f"ONNX model file at '{model_path}' could not be loaded: {e}")

    def _load_class_map(self, class_index_map: Optional[str]) -> Dict[int, str]:
        """Load index->material_id mapping from JSON file.

        Fail-safe: if the map is missing or unparseable the mapping is EMPTY,
        which makes every prediction resolve to the honest "unknown" result —
        silently guessing an order (e.g. pool order) would mislabel every
        prediction under the broad-class taxonomy.
        """
        if class_index_map and os.path.exists(class_index_map):
            try:
                with open(class_index_map, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                mapping: Dict[int, str] = {}
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        mapping[int(k)] = str(v)
                elif isinstance(raw, list):
                    for i, v in enumerate(raw):
                        mapping[i] = str(v)
                if mapping:
                    logger.info(f"Loaded {len(mapping)} class mappings from {class_index_map}.")
                    return mapping
            except Exception as e:
                logger.warning(f"Could not parse CLASS_INDEX_MAP '{class_index_map}': {e}.")
        logger.error(
            "CLASS_INDEX_MAP missing or unusable — predictions will be reported as "
            "'unknown' (fail-safe, no guessing)."
        )
        return {}

    def _resolve_output_semantics(self, output_semantics: Optional[str]) -> str:
        """Resolve the configured ONNX output semantics.

        Precedence: explicit argument > MODEL_OUTPUT setting > default
        ("probabilities"). Unknown values fall back to the safe default with a
        loud error log rather than guessing a semantics.
        """
        value = output_semantics
        if value is None:
            try:
                from app.core.config import get_settings
                value = getattr(get_settings(), "MODEL_OUTPUT", None)
            except Exception:
                value = None
        value = (value or DEFAULT_OUTPUT_SEMANTICS).strip().lower()
        if value not in VALID_OUTPUT_SEMANTICS:
            logger.error(
                "Unknown MODEL_OUTPUT semantics '%s'; using '%s'.",
                value, DEFAULT_OUTPUT_SEMANTICS,
            )
            return DEFAULT_OUTPUT_SEMANTICS
        return value

    def _lookup_entry(self, material_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Resolve a predicted class to its honest broad-class guidance entry."""
        if not material_id:
            return None
        return get_broad_entry(material_id)

    @property
    def model_version(self) -> str:
        return getattr(self, "_model_version", "yolo26n-cls-v1")

    async def classify(
        self,
        image_bytes: Optional[bytes] = None,
        description: Optional[str] = None
    ) -> ClassificationResult:
        if not image_bytes:
            # Image-only inference: there is no text fallback path. A text-only
            # request is rejected outright rather than answered from a guess.
            logger.warning("ONNXClassifier received a request without image bytes.")
            raise InvalidInputError(
                "Please add a photo of the item. The description is optional, but the model needs an image to classify."
            )

        try:
            # Perform preprocessing and inference within 5-second timeout
            return await asyncio.wait_for(
                self._run_inference(image_bytes, description),
                timeout=5.0
            )
        except (InferenceFailedError, InvalidInputError, UnsupportedFormatError):
            raise
        except asyncio.TimeoutError:
            logger.error("ONNX inference timed out after 5.0 seconds.")
            raise InferenceFailedError("Image classification is temporarily unavailable. Please check the server and try again.")
        except Exception as e:
            logger.error(f"ONNX classification failed: {e}")
            raise InferenceFailedError("Image classification is temporarily unavailable. Please check the server and try again.")

    async def _run_inference(self, image_bytes: bytes, description: Optional[str]) -> ClassificationResult:
        """Run genuine ONNX inference. Never substitutes a fabricated result."""
        try:
            arr = self._preprocess(image_bytes)
        except (InferenceFailedError, UnsupportedFormatError):
            raise
        except Exception as e:
            # The upload already passed magic-byte validation, so a decode
            # failure here means the file itself is broken — a user problem,
            # reported as such rather than as a server outage.
            logger.error(f"Could not decode/preprocess image: {e}")
            raise UnsupportedFormatError("We couldn't read that photo. Please try a different JPEG or PNG photo.")

        def _infer() -> Any:
            if not self._input_name:
                raise InferenceFailedError("Image classification is temporarily unavailable. Please check the server and try again.")
            outputs = self._session.run(None, {self._input_name: arr})
            return outputs[0] if outputs else None

        loop = asyncio.get_running_loop()
        output = await loop.run_in_executor(None, _infer)
        if output is None:
            raise InferenceFailedError("Image classification is temporarily unavailable. Please check the server and try again.")

        try:
            probs = self._interpret_output(output)
        except ModelOutputError as e:
            logger.error(f"Rejected ONNX model output: {e}")
            raise InferenceFailedError("Image classification is temporarily unavailable. Please check the server and try again.")
        if not probs:
            raise InferenceFailedError("Image classification is temporarily unavailable. Please check the server and try again.")

        class_ids, confidences = self._rank(probs)
        best_conf = confidences[0]
        if best_conf < LOW_CONFIDENCE_THRESHOLD:
            return self._unknown_result(best_conf, class_ids, confidences)

        material_id = self._index_to_class.get(class_ids[0])
        entry = self._lookup_entry(material_id)
        if entry is None:
            logger.warning(f"ONNX predicted unmapped class index {class_ids[0]}; returning unknown.")
            return self._unknown_result(best_conf, class_ids, confidences)

        top3 = []
        for cid, conf in zip(class_ids[:3], confidences[:3]):
            mid = self._index_to_class.get(cid, "unknown")
            top3.append({"class": mid, "confidence": round(float(conf), 2)})
        main_confidence = top3[0]["confidence"]
        confidence_label = "high" if main_confidence >= 0.8 else ("medium" if main_confidence >= 0.55 else "low")

        mat_guidance = MaterialGuidance(
            name=entry["name"],
            category=entry["category"],
            disposal_bin=entry["disposal_bin"],
            recovery_potential=entry["recovery_potential"],
            next_life=entry["next_life"],
            recovery_channel=entry["recovery_channel"],
            contamination_notes=entry["contamination_notes"],
        )
        disp_guidance = DisposalGuidance(
            bin_label=entry["bin_label"],
            action=entry["action"],
            do=list(entry["do"]),
            do_not=list(entry["do_not"]),
        )
        return ClassificationResult(
            event_id=str(uuid.uuid4()),
            predicted_class=entry["material_id"],
            confidence=main_confidence,
            confidence_label=confidence_label,
            top3=top3,
            material=mat_guidance,
            guidance=disp_guidance,
            model_version=self.model_version,
        )

    def _target_hw(self) -> tuple:
        try:
            shape = list(self._input_shape)
            # Expect NCHW; fall back to 640x640 on dynamic dims.
            h = shape[2] if len(shape) > 2 and isinstance(shape[2], int) else 640
            w = shape[3] if len(shape) > 3 and isinstance(shape[3], int) else 640
            return (int(h), int(w))
        except Exception:
            return (640, 640)

    def _input_size(self) -> int:
        """Square input edge length from the model, or DEFAULT_INPUT_SIZE."""
        h, w = self._target_hw()
        if h == w:
            return h if h > 0 else DEFAULT_INPUT_SIZE
        # The reference classification transform is square; a non-square input
        # is not something this model contract supports. Use the shorter edge
        # and let the runtime surface a shape mismatch rather than guessing.
        logger.warning("Non-square model input %dx%d; using %d for preprocessing.", w, h, min(h, w))
        return min(h, w)

    def _preprocess(self, image_bytes: bytes) -> Any:
        """Decode + transform an uploaded image to the NCHW model input.

        Uses the shared reference-matching transform (shortest-edge BILINEAR
        resize -> centre crop -> /255, no ImageNet mean/std). See
        app.services.inference.preprocess and ml/evaluate.py --preprocess backend.
        """
        image = Image.open(io.BytesIO(image_bytes))
        size = self._input_size()
        arr = preprocess_image(image, size)
        expected_shape = (1, NUM_CHANNELS, size, size)
        if tuple(arr.shape) != expected_shape:
            raise InferenceFailedError(
                f"Preprocessing produced shape {tuple(arr.shape)}, expected {expected_shape}."
            )
        return arr

    def _flatten_class_scores(self, output: Any) -> List[float]:
        """Return a 1-D list of class scores, or [] for unsupported shapes.

        Accepts [C] and [1, C]. Anything else (e.g. detection tensors such as
        [1, C+4, N]) is rejected rather than guessed: this model contract is a
        single-image classification output.
        """
        data = output.tolist() if hasattr(output, "tolist") else output
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
            data = data[0]  # unwrap the leading batch dimension
        if not isinstance(data, list) or any(isinstance(v, list) for v in data):
            return []
        try:
            return [float(v) for v in data]
        except (TypeError, ValueError):
            return []

    @staticmethod
    def _softmax(scores: List[float]) -> List[float]:
        """Numerically stable softmax. Only used for LOGITS models."""
        m = max(scores)
        exps = [math.exp(s - m) for s in scores]
        total = sum(exps)
        if total <= 0.0 or not math.isfinite(total):
            raise ModelOutputError("softmax produced a non-finite normalisation")
        return [e / total for e in exps]

    def _interpret_output(self, output: Any) -> List[float]:
        """Validate and return the probability vector in class-index order.

        Behaviour is driven by the configured semantics:
          * "probabilities" (default): the output must already be a valid
            distribution (finite, non-negative, summing to ~1 within
            ``OUTPUT_SUM_TOLERANCE``). It is validated and used DIRECTLY — never
            re-normalised, never softmaxed again.
          * "logits": finite scores receive a numerically stable softmax.

        Raises ``ModelOutputError`` on any malformed/inconsistent output so the
        caller returns an honest failure instead of a fabricated prediction.
        """
        scores = self._flatten_class_scores(output)
        if not scores:
            raise ModelOutputError("output is not a 1-D score vector")

        expected = len(self._index_to_class)
        if expected and len(scores) != expected:
            raise ModelOutputError(
                f"expected {expected} class scores, got {len(scores)}"
            )

        if not all(math.isfinite(s) for s in scores):
            raise ModelOutputError("output contains NaN or infinite values")

        semantics = getattr(self, "_output_semantics", DEFAULT_OUTPUT_SEMANTICS)
        if semantics == "logits":
            return self._softmax(scores)

        # semantics == "probabilities"
        if any(s < -PROB_NEG_EPSILON for s in scores):
            raise ModelOutputError("probability output contains negative values")
        total = sum(scores)
        if abs(total - 1.0) > OUTPUT_SUM_TOLERANCE:
            raise ModelOutputError(
                f"probability output sums to {total:.6f}, "
                f"outside tolerance {OUTPUT_SUM_TOLERANCE}"
            )
        return [float(s) for s in scores]

    @staticmethod
    def _rank(probs: List[float]) -> tuple:
        """Return (class_ids, confidences) sorted by descending confidence."""
        order = sorted(range(len(probs)), key=lambda i: -probs[i])
        return ([int(i) for i in order], [float(probs[i]) for i in order])

    def _unknown_result(self, best_conf: float, class_ids: List[int], confidences: List[float]) -> ClassificationResult:
        """Honest low-confidence result: a real model answer the user must verify.

        This is a genuine (if uncertain) classification, NOT a service error.
        A backend failure raises InferenceFailedError instead and never reaches
        here, so an "unknown" answer is never used to mask an outage.
        """
        top3 = [{"class": "unknown", "confidence": round(float(best_conf), 2)}]
        for cid, conf in zip(class_ids[:2], confidences[:2]):
            mid = self._index_to_class.get(cid)
            if mid:
                top3.append({"class": mid, "confidence": round(float(conf), 2)})
        while len(top3) < 3:
            top3.append({"class": "unknown", "confidence": round(float(best_conf), 2)})
        mat_guidance = MaterialGuidance(
            name=UNKNOWN_MATERIAL["name"],
            category=UNKNOWN_MATERIAL["category"],
            disposal_bin=UNKNOWN_MATERIAL["disposal_bin"],
            recovery_potential=UNKNOWN_MATERIAL["recovery_potential"],
            next_life=UNKNOWN_MATERIAL["next_life"],
            recovery_channel=UNKNOWN_MATERIAL["recovery_channel"],
            contamination_notes=UNKNOWN_MATERIAL["contamination_notes"],
        )
        disp_guidance = DisposalGuidance(
            bin_label=UNKNOWN_MATERIAL["bin_label"],
            action=UNKNOWN_MATERIAL["action"],
            do=list(UNKNOWN_MATERIAL["do"]),
            do_not=list(UNKNOWN_MATERIAL["do_not"]),
        )
        return ClassificationResult(
            event_id=str(uuid.uuid4()),
            predicted_class="unknown",
            confidence=top3[0]["confidence"],
            confidence_label="low",
            top3=top3[:3],
            material=mat_guidance,
            guidance=disp_guidance,
            model_version=self.model_version,
        )
