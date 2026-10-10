"""Broad-class guidance layer: every model class resolves to honest guidance.

The trained classifier outputs the 8 broad classes in ml/classes.json. These
tests guarantee the backend can render guidance for every one of them, that
the guidance never overclaims a specific subtype, that lookup prefers the
specific demo pool, and that a missing CLASS_INDEX_MAP fails safe (unknown),
never silently guessing an order.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_KEYS = {
    "material_id", "name", "category", "disposal_bin", "bin_label",
    "recovery_potential", "next_life", "recovery_channel",
    "contamination_notes", "action", "do", "do_not",
}
VALID_BINS = {"wet", "dry", "hazardous", "e_waste", "rejected"}
VALID_RECOVERY = {"high", "medium", "low", "none"}


def _canonical_classes():
    raw = json.loads((REPO_ROOT / "ml" / "classes.json").read_text(encoding="utf-8"))
    return [raw[str(i)] for i in range(len(raw))]


def test_every_model_class_has_guidance_in_order():
    from app.services.inference.broad_classes import broad_class_ids
    assert broad_class_ids() == _canonical_classes()


def test_guidance_entries_are_complete():
    from app.services.inference.broad_classes import BROAD_MATERIAL_GUIDANCE
    assert BROAD_MATERIAL_GUIDANCE
    for entry in BROAD_MATERIAL_GUIDANCE:
        missing = REQUIRED_KEYS - set(entry)
        assert not missing, f"{entry.get('material_id')} missing keys: {missing}"
        assert entry["category"]
        assert entry["bin_label"]
        assert entry["material_id"] not in ("", "unknown")
        assert entry["disposal_bin"] in VALID_BINS, entry["material_id"]
        assert entry["recovery_potential"] in VALID_RECOVERY, entry["material_id"]
        assert isinstance(entry["do"], list) and entry["do"]
        assert isinstance(entry["do_not"], list) and entry["do_not"]


def test_broad_entries_do_not_claim_specific_subtypes():
    from app.services.inference.broad_classes import BROAD_MATERIAL_GUIDANCE
    banned = ["pet", "hdpe", "ldpe", "polyethylene", "aa", "aaa", "lithium",
              "aluminium", "aluminum", "tetra", "charger", "wine", "beer"]
    for entry in BROAD_MATERIAL_GUIDANCE:
        name = entry["name"].lower()
        for word in banned:
            assert word not in name, (
                f"broad class '{entry['material_id']}' name overclaims '{word}': {entry['name']}"
            )


def test_broad_ids_do_not_collide_with_demo_pool():
    from app.services.inference.broad_classes import broad_class_ids
    from app.services.inference.mock import MOCK_MATERIAL_POOL
    pool_ids = {e["material_id"] for e in MOCK_MATERIAL_POOL}
    assert pool_ids.isdisjoint(set(broad_class_ids()))


def test_get_broad_entry_lookup():
    from app.services.inference.broad_classes import get_broad_entry
    assert get_broad_entry("plastic")["category"] == "plastic"
    assert get_broad_entry("unknown") is None
    assert get_broad_entry(None) is None
    assert get_broad_entry("") is None


def test_lookup_prefers_specific_pool_then_broad():
    from app.services.inference.onnx_classifier import ONNXClassifier
    clf = object.__new__(ONNXClassifier)
    assert clf._lookup_entry("plastic_pet_bottle")["material_id"] == "plastic_pet_bottle"
    assert clf._lookup_entry("textile")["material_id"] == "textile"
    assert clf._lookup_entry("no_such_material") is None
    assert clf._lookup_entry(None) is None
    assert clf._lookup_entry("") is None


def test_class_map_fallback_fails_safe():
    from app.services.inference.onnx_classifier import ONNXClassifier
    clf = object.__new__(ONNXClassifier)
    assert clf._load_class_map(None) == {}
    assert clf._load_class_map("/no/such/class-index-map.json") == {}
