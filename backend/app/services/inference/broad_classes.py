"""Guidance entries for the model's 8 BROAD material classes.

The trained classifier (see ml/classes.json) predicts broad material
categories only — it cannot identify subtypes such as plastic resin codes,
battery chemistry, glass colour, or specific electronic components. These
entries therefore give honest, category-level disposal guidance and NEVER
claim a specific subtype. Detailed per-material guidance for the demo mode
lives in app.services.inference.mock.

Entries are ordered to match ml/classes.json (alphabetical broad classes),
which is also the class-index order used by the exported ONNX class map.

Lookup order in ONNXClassifier: MOCK_MATERIAL_POOL first (specific demo
material_ids), then BROAD_MATERIAL_GUIDANCE here. Anything missing from both
is reported as "unknown" with safe check-local-rules guidance.
"""

from typing import Any, Dict, List, Optional

BROAD_MATERIAL_GUIDANCE: List[Dict[str, Any]] = [
    {
        "material_id": "battery_hazardous",
        "name": "Battery or household hazardous item",
        "category": "hazardous",
        "disposal_bin": "hazardous",
        "bin_label": "Red Hazardous Waste Bin",
        "recovery_potential": "medium",
        "next_life": "Collected separately so heavy metals and electrolyte are treated safely at a licensed facility.",
        "recovery_channel": "hazardous_facility",
        "contamination_notes": "Never place batteries in the regular wet or dry bins — they can leak chemicals or cause fires in collection vehicles.",
        "action": "Tape the terminals and drop the item at a battery or hazardous-waste collection point.",
        "do": ["Tape the terminals with electrical tape", "Keep in a dry container until disposal", "Use an authorised collection point"],
        "do_not": ["Do not throw in wet or dry bin", "Do not puncture, crush or incinerate"],
    },
    {
        "material_id": "glass",
        "name": "Glass containers (colour and type not identified)",
        "category": "glass",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Crushed cullet is melted down and formed into new glass containers.",
        "recovery_channel": "municipality_dry",
        "contamination_notes": "Empty and rinse. Handle broken glass carefully and wrap sharp pieces before disposal.",
        "action": "Rinse out contents and place carefully in the dry waste bin.",
        "do": ["Rinse liquid residue", "Keep the container intact", "Wrap broken pieces before disposal"],
        "do_not": ["Do not shatter glass directly into the bin", "Do not mix broken glass with wet waste"],
    },
    {
        "material_id": "metal",
        "name": "Metal packaging (type not identified)",
        "category": "metal",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Metals are shredded, melted and recast — aluminium and steel both recycle repeatedly without quality loss.",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Empty and rinse liquid residue. The photo does not identify the alloy — mixed metals are still accepted in dry waste.",
        "action": "Rinse, crush if possible, and place in the dry waste bin.",
        "do": ["Rinse out contents", "Crush cans to save space"],
        "do_not": ["Do not include liquids", "Do not put pressurised or sealed cans in the oven/microwave"],
    },
    {
        "material_id": "organic",
        "name": "Food & garden waste",
        "category": "organic",
        "disposal_bin": "wet",
        "bin_label": "Green Wet Waste Bin",
        "recovery_potential": "high",
        "next_life": "Composted into soil enricher or processed into biogas.",
        "recovery_channel": "composting",
        "contamination_notes": "Drain excess moisture and keep plastic bags, wrappers and packaging out of the wet bin.",
        "action": "Place directly into the green wet waste bin.",
        "do": ["Drain liquid before disposal", "Remove any plastic wrapping or sticker"],
        "do_not": ["Do not mix with plastic wrappers", "Do not include packaging or synthetic material"],
    },
    {
        "material_id": "other_residue",
        "name": "Other or mixed waste (not identified)",
        "category": "other",
        "disposal_bin": "rejected",
        "bin_label": "Check local waste rules",
        "recovery_potential": "none",
        "next_life": "This item did not match any recognised material category, so no recovery route can be confirmed from the photo.",
        "recovery_channel": "manual_check",
        "contamination_notes": "Sort out anything recyclable (paper, plastic, metal, glass) before discarding the rest, and follow your local waste rules.",
        "action": "Check your local waste rules or pick the closest material from the list.",
        "do": ["Sort recyclables out first", "Check local rules when unsure", "Describe the item in words for a better match"],
        "do_not": ["Do not assume it is recyclable", "Do not place batteries or electronics in general waste"],
    },
    {
        "material_id": "paper_cardboard",
        "name": "Paper & cardboard (grade not identified)",
        "category": "paper",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Repulped into recycled paper, kraft board and packaging sheets.",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Remove plastic packing tape and keep sheets dry — wet or grease-soaked paper cannot be recycled.",
        "action": "Flatten boxes, remove plastic tape, and place in the dry waste bin.",
        "do": ["Flatten cardboard", "Remove plastic tape and stickers where easy", "Keep paper dry"],
        "do_not": ["Do not include grease-soaked or food-soiled paper", "Do not mix with wet waste"],
    },
    {
        "material_id": "plastic",
        "name": "Plastic packaging (specific type not identified)",
        "category": "plastic",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Sorted plastics are washed, shredded and reprocessed into new plastic products, fibres or rags.",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Rinse out food and liquid first. The photo does not reveal the resin type — check the recycling code or local rules when the exact plastic matters.",
        "action": "Rinse and place in the dry waste bin.",
        "do": ["Rinse out food or liquid", "Keep the item dry", "Check local recycling rules for the resin code when in doubt"],
        "do_not": ["Do not put food-soiled plastic in the recycling", "Do not burn plastic waste"],
    },
    {
        "material_id": "textile",
        "name": "Textiles — clothes, shoes or fabric",
        "category": "textile",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "medium",
        "next_life": "Reusable items are donated or resold; worn-out textiles are downcycled into rags, stuffing or insulation fibre.",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Keep textiles clean and dry. Wet or soiled fabric contaminates the dry recycling stream.",
        "action": "Bag clothes and shoes separately and hand them to a kabadiwala, donation drive or textile recycler.",
        "do": ["Keep items dry", "Pair shoes together", "Donate items that are still wearable"],
        "do_not": ["Do not include wet or heavily soiled textiles", "Do not include single soiled items with regular dry waste"],
    },
]


def get_broad_entry(material_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the broad guidance entry for a model class, else None."""
    if not material_id:
        return None
    for entry in BROAD_MATERIAL_GUIDANCE:
        if entry["material_id"] == material_id:
            return entry
    return None


def broad_class_ids() -> List[str]:
    return [entry["material_id"] for entry in BROAD_MATERIAL_GUIDANCE]
