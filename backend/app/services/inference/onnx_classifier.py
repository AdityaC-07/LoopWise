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
from app.services.inference.mock import MockClassifier, UNKNOWN_MATERIAL, get_material_entry
from app.services.inference.broad_classes import get_broad_entry
from app.core.errors import InferenceFailedError

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.35


class ONNXClassifier(BaseClassifier):
    """ONNX Runtime Waste Classifier for production mode."""

    def __init__(self, model_path: str, class_index_map: Optional[str] = None):
        self._model_path = model_path
        self._class_index_map = class_index_map
        self._index_to_class: Dict[int, str] = self._load_class_map(class_index_map)
        try:
            from app.core.config import get_settings as _get_settings
            self._model_version = _get_settings().MODEL_VERSION or "yolo26-v1"
        except Exception:
            self._model_version = "yolo26-v1"

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

    def _lookup_entry(self, material_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Resolve a predicted class to guidance: specific demo pool first,
        then the honest broad-class entries (ml/classes.json taxonomy)."""
        if not material_id:
            return None
        return get_material_entry(material_id) or get_broad_entry(material_id)

    @property
    def model_version(self) -> str:
        return getattr(self, "_model_version", "yolo26-v1")

    @property
    def is_demo(self) -> bool:
        return False

    async def classify(
        self,
        image_bytes: Optional[bytes] = None,
        description: Optional[str] = None
    ) -> ClassificationResult:
        if not image_bytes:
            # ONNX model handles images only. Text-only input honestly falls
            # back to the transparent demo simulator (is_demo=True).
            logger.warning("ONNXClassifier received text-only input; using demo simulator for text match.")
            mock = MockClassifier()
            return await mock.classify(image_bytes=None, description=description)

        try:
            # Perform preprocessing and inference within 5-second timeout
            return await asyncio.wait_for(
                self._run_inference(image_bytes, description),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("ONNX inference timed out after 5.0 seconds.")
            raise InferenceFailedError("Inference timed out. Please try again.")
        except Exception as e:
            logger.error(f"ONNX classification failed: {e}")
            raise InferenceFailedError("Could not process image with production model.")

    async def _run_inference(self, image_bytes: bytes, description: Optional[str]) -> ClassificationResult:
        """Run GENUINE ONNX inference. Never substitutes mock output as genuine."""
        try:
            import numpy as np  # type: ignore
        except ImportError:
            raise InferenceFailedError("Production model dependencies are unavailable on this server.")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        target_h, target_w = self._target_hw()
        image = image.resize((target_w, target_h))
        arr = np.asarray(image).astype(np.float32) / 255.0
        arr = np.transpose(arr, (2, 0, 1))[np.newaxis, ...]  # NCHW

        def _infer() -> Any:
            if not self._input_name:
                raise InferenceFailedError("Production model has no usable input.")
            outputs = self._session.run(None, {self._input_name: arr})
            return outputs[0] if outputs else None

        loop = asyncio.get_running_loop()
        logits = await loop.run_in_executor(None, _infer)
        if logits is None:
            raise InferenceFailedError("Production model returned no output.")

        class_ids, confidences = self._parse_logits(logits)
        if not class_ids:
            raise InferenceFailedError("Could not interpret production model output.")

        best_conf = confidences[0]
        if best_conf < LOW_CONFIDENCE_THRESHOLD:
            return self._unknown_genuine_result(best_conf, class_ids, confidences)

        material_id = self._index_to_class.get(class_ids[0])
        entry = self._lookup_entry(material_id)
        if entry is None:
            logger.warning(f"ONNX predicted unmapped class index {class_ids[0]}; returning unknown.")
            return self._unknown_genuine_result(best_conf, class_ids, confidences)

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
            is_demo=False,
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

    def _parse_logits(self, logits: Any) -> tuple:
        """Return (class_ids, softmax confidences) sorted desc. Supports 2D
        classification logits [1, C] and YOLO-style detection [1, C+4, N].
        Pure-Python (no numpy required) so the module imports without ML deps."""
        data = logits.tolist() if hasattr(logits, "tolist") else logits
        try:
            class_scores: List[float] = []
            if isinstance(data, list) and data and isinstance(data[0], list):
                if data[0] and isinstance(data[0][0], list):
                    # 3D [1, rows, cols]: YOLO detection, first 4 rows are boxes.
                    rows = data[0]
                    if len(rows) > 4:
                        class_rows = rows[4:]
                        n_boxes = len(rows[0])
                        best_box, best_val = 0, float("-inf")
                        for b in range(n_boxes):
                            col_best = max(float(r[b]) for r in class_rows)
                            if col_best > best_val:
                                best_val, best_box = col_best, b
                        class_scores = [float(r[best_box]) for r in class_rows]
                    else:
                        class_scores = [max(float(v) for v in row) for row in rows]
                else:
                    # 2D [1, C]
                    row = data[0] if isinstance(data[0], list) else data
                    class_scores = [float(v) for v in row]
            elif isinstance(data, list):
                class_scores = [float(v) for v in data]
            else:
                return ([], [])
            if not class_scores:
                return ([], [])
            m = max(class_scores)
            exps = [math.exp(s - m) for s in class_scores]
            total = sum(exps)
            probs = [e / total for e in exps]
            order = sorted(range(len(probs)), key=lambda i: -probs[i])
            return ([int(i) for i in order], [float(probs[i]) for i in order])
        except Exception:
            return ([], [])

    def _unknown_genuine_result(self, best_conf: float, class_ids: List[int], confidences: List[float]) -> ClassificationResult:
        """Honest low-confidence result from the GENUINE model (is_demo=False)."""
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
            next_life="The trained model could not confidently identify this item. Please check your local waste rules or select the material manually.",
            recovery_channel="manual_check",
            contamination_notes="Genuine model output with low confidence — not verified. When in doubt, keep the item separate and check local waste rules.",
        )
        disp_guidance = DisposalGuidance(
            bin_label=UNKNOWN_MATERIAL["bin_label"],
            action="The model was not confident about this photo. Please describe the item in words or pick the closest material below.",
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
            is_demo=False,
        )
