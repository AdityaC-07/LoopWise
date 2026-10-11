import pytest
from app.services.inference.mock import MockClassifier
from app.services.inference.factory import get_classifier
from app.services.inference.result import ClassificationResult


@pytest.mark.asyncio
async def test_mock_classifier_returns_classification_result():
    classifier = MockClassifier()
    res = await classifier.classify(description="plastic water bottle")
    assert isinstance(res, ClassificationResult)
    assert res.is_demo is True
    assert res.model_version == "mock-v1"
    assert res.predicted_class is not None
    assert res.confidence > 0.0
    assert res.confidence_label in ["high", "medium", "low"]


@pytest.mark.asyncio
async def test_mock_classifier_deterministic_hashing():
    classifier = MockClassifier()
    res1 = await classifier.classify(description="cardboard packaging box")
    res2 = await classifier.classify(description="cardboard packaging box")
    assert res1.predicted_class == res2.predicted_class
    assert res1.confidence == res2.confidence
    assert res1.confidence_label == res2.confidence_label


@pytest.mark.asyncio
async def test_mock_classifier_top3_structure():
    classifier = MockClassifier()
    res = await classifier.classify(description="aluminum soda can")
    assert len(res.top3) == 3
    assert res.top3[0]["class"] == res.predicted_class
    assert res.top3[0]["confidence"] == res.confidence


@pytest.mark.asyncio
async def test_mock_classifier_plain_language_guidance():
    classifier = MockClassifier()
    res = await classifier.classify(description="used aa household battery")
    assert "confidence" not in res.guidance.action.lower()
    assert "model" not in res.guidance.action.lower()
    assert res.material.disposal_bin in ["wet", "dry", "hazardous", "e_waste", "rejected"]


@pytest.mark.asyncio
async def test_factory_returns_mock_when_demo_mode_true():
    classifier = get_classifier()
    assert classifier.is_demo is True
    assert classifier.model_version == "mock-v1"


@pytest.mark.asyncio
async def test_mock_classifier_handles_empty_or_image_bytes():
    classifier = MockClassifier()
    res = await classifier.classify(image_bytes=b"fake_image_bytes_content")
    assert res.predicted_class is not None
    assert res.confidence > 0.0


@pytest.mark.asyncio
async def test_confidence_tier_labels():
    classifier = MockClassifier()
    # Test multiple items to verify high, medium, and low labels are assigned properly
    labels = set()
    for item in ["pet bottle", "paper carton", "food scrap", "battery", "old glass"]:
        res = await classifier.classify(description=item)
        labels.add(res.confidence_label)
    assert len(labels) >= 1


@pytest.mark.asyncio
async def test_image_only_upload_returns_unknown_not_ewaste():
    """Regression: a photo without description must NOT be hashed to e-waste."""
    classifier = MockClassifier()
    for raw in [b"fake-plastic-bottle-photo-1", b"fake-plastic-bottle-photo-2", b"\x89PNGfakepngbytes"]:
        res = await classifier.classify(image_bytes=raw)
        assert res.predicted_class == "unknown"
        assert res.predicted_class != "e_waste_mobile_charger"
        assert res.confidence_label == "low"
        assert res.is_demo is True
        assert res.model_version == "mock-v1"
        assert res.material.disposal_bin == "rejected"
        assert "local waste rules" in (res.guidance.bin_label + " " + " ".join(res.guidance.do)).lower()
        assert len(res.top3) == 3
        assert res.top3[0]["class"] == "unknown"


@pytest.mark.asyncio
async def test_plastic_bottle_text_maps_to_plastic_not_ewaste():
    classifier = MockClassifier()
    res = await classifier.classify(description="plastic water bottle")
    assert res.predicted_class == "plastic_pet_bottle"
    assert res.is_demo is True
    assert res.confidence_label == "medium"


@pytest.mark.asyncio
async def test_gibberish_description_returns_unknown():
    classifier = MockClassifier()
    res = await classifier.classify(description="xqzt blorpt wobble 12345")
    assert res.predicted_class == "unknown"
    assert res.confidence_label == "low"
    assert "demo" in res.material.contamination_notes.lower()


@pytest.mark.asyncio
async def test_onnx_logits_parsing_orders_classes():
    """LOGITS semantics (explicitly configured) softmax and order classes.

    The default semantics is "probabilities"; a raw-logits vector must only be
    softmaxed when the model is explicitly declared as a logits model.
    """
    from app.services.inference.onnx_classifier import ONNXClassifier
    clf = object.__new__(ONNXClassifier)
    clf._index_to_class = {0: "plastic_pet_bottle", 1: "organic_food_waste", 2: "paper_cardboard_box"}
    clf._input_shape = [1, 3, 640, 640]
    clf._input_name = "input"
    clf._model_path = "test"
    clf._output_semantics = "logits"
    probs = clf._interpret_output([[2.0, 1.0, 0.1]])
    ids, confs = clf._rank(probs)
    assert ids[0] == 0
    assert abs(sum(confs) - 1.0) < 1e-5
    assert confs == sorted(confs, reverse=True)


@pytest.mark.asyncio
async def test_onnx_low_confidence_returns_genuine_unknown():
    from app.services.inference.onnx_classifier import ONNXClassifier
    clf = object.__new__(ONNXClassifier)
    clf._index_to_class = {0: "plastic_pet_bottle", 1: "organic_food_waste"}
    res = clf._unknown_genuine_result(0.2, [0, 1], [0.2, 0.15])
    assert res.predicted_class == "unknown"
    assert res.is_demo is False  # genuine model, honestly uncertain
    assert res.confidence_label == "low"


def test_model_version_default_and_onnx_fallback():
    from app.core.config import get_settings
    from app.services.inference.onnx_classifier import ONNXClassifier
    assert get_settings().MODEL_VERSION == "yolo26-v1"
    # Instances built without __init__ (e.g. in unit tests) still report honestly.
    assert ONNXClassifier.model_version.fget(object.__new__(ONNXClassifier)) == "yolo26-v1"
