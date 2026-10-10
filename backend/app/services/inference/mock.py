import uuid
from typing import Optional, List, Dict, Any
from app.services.inference.base import BaseClassifier
from app.services.inference.result import ClassificationResult, MaterialGuidance, DisposalGuidance

MOCK_MATERIAL_POOL: List[Dict[str, Any]] = [
    {
        "material_id": "plastic_pet_bottle",
        "name": "PET Plastic Bottle",
        "category": "plastic",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Recycled into polyester fibre or new PET bottles",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Rinse out liquids and crush bottle before placing in bin.",
        "action": "Rinse, crush, and place in the dry waste bin.",
        "do": ["Rinse out residue", "Remove the plastic cap", "Crush to save space"],
        "do_not": ["Do not include if contaminated with food", "Do not mix with wet waste"],
        "top3_pairs": [
            {"class": "plastic_pet_bottle", "confidence_high": 0.87, "confidence_med": 0.72, "confidence_low": 0.48},
            {"class": "plastic_hdpe_container", "confidence_high": 0.09, "confidence_med": 0.18, "confidence_low": 0.32},
            {"class": "composite_tetrapack", "confidence_high": 0.04, "confidence_med": 0.10, "confidence_low": 0.20}
        ]
    },
    {
        "material_id": "composite_tetrapack",
        "name": "Tetra Pack Carton",
        "category": "composite",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Separated into paper pulp and aluminum-polymer composite boards",
        "recovery_channel": "specialized",
        "contamination_notes": "Flatten completely and ensure no liquid remains.",
        "action": "Flatten carton and place in the dry waste bin.",
        "do": ["Flatten carton completely", "Rinse residual liquid"],
        "do_not": ["Do not leave liquid inside", "Do not mix with organic waste"],
        "top3_pairs": [
            {"class": "composite_tetrapack", "confidence_high": 0.84, "confidence_med": 0.68, "confidence_low": 0.45},
            {"class": "paper_cardboard_box", "confidence_high": 0.11, "confidence_med": 0.20, "confidence_low": 0.33},
            {"class": "plastic_pet_bottle", "confidence_high": 0.05, "confidence_med": 0.12, "confidence_low": 0.22}
        ]
    },
    {
        "material_id": "organic_food_waste",
        "name": "Food Residue & Vegetable Scraps",
        "category": "organic",
        "disposal_bin": "wet",
        "bin_label": "Green Wet Waste Bin",
        "recovery_potential": "high",
        "next_life": "Converted into organic compost or biogas energy",
        "recovery_channel": "composting",
        "contamination_notes": "Drain excess moisture before binning.",
        "action": "Place directly into the green wet waste bin.",
        "do": ["Drain liquid before disposal", "Keep in compostable lining"],
        "do_not": ["Do not mix with plastic wrappers", "Do not include sanitary waste"],
        "top3_pairs": [
            {"class": "organic_food_waste", "confidence_high": 0.92, "confidence_med": 0.76, "confidence_low": 0.51},
            {"class": "organic_garden_waste", "confidence_high": 0.06, "confidence_med": 0.16, "confidence_low": 0.29},
            {"class": "paper_newspaper", "confidence_high": 0.02, "confidence_med": 0.08, "confidence_low": 0.20}
        ]
    },
    {
        "material_id": "paper_cardboard_box",
        "name": "Cardboard Packaging Box",
        "category": "paper",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Repulped into recycled kraft paper and packaging sheets",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Remove plastic adhesive tape and flatten.",
        "action": "Flatten box and drop in the dry waste bin.",
        "do": ["Flatten box flat", "Remove plastic packing tape"],
        "do_not": ["Do not include if soaked in grease or food", "Do not wet with water"],
        "top3_pairs": [
            {"class": "paper_cardboard_box", "confidence_high": 0.89, "confidence_med": 0.74, "confidence_low": 0.49},
            {"class": "composite_tetrapack", "confidence_high": 0.08, "confidence_med": 0.17, "confidence_low": 0.31},
            {"class": "paper_newspaper", "confidence_high": 0.03, "confidence_med": 0.09, "confidence_low": 0.20}
        ]
    },
    {
        "material_id": "hazardous_battery_aa",
        "name": "Used AA Household Battery",
        "category": "hazardous",
        "disposal_bin": "hazardous",
        "bin_label": "Red Hazardous Waste Bin",
        "recovery_potential": "medium",
        "next_life": "Heavy metals extracted safely at specialized treatment facility",
        "recovery_channel": "hazardous_facility",
        "contamination_notes": "Do not mix with general dry waste to avoid chemical leakage.",
        "action": "Deposit in designated red hazardous waste bin or collection drop.",
        "do": ["Tape battery terminals", "Keep in dry container until disposal"],
        "do_not": ["Do not throw in wet or dry bin", "Do not puncture or incinerate"],
        "top3_pairs": [
            {"class": "hazardous_battery_aa", "confidence_high": 0.82, "confidence_med": 0.65, "confidence_low": 0.44},
            {"class": "e_waste_circuit_board", "confidence_high": 0.12, "confidence_med": 0.22, "confidence_low": 0.34},
            {"class": "metal_can_aluminum", "confidence_high": 0.06, "confidence_med": 0.13, "confidence_low": 0.22}
        ]
    },
    {
        "material_id": "glass_bottle_beverage",
        "name": "Glass Beverage Bottle",
        "category": "glass",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Melted into cullet for new glass container manufacturing",
        "recovery_channel": "municipality_dry",
        "contamination_notes": "Handle with care to prevent breakage.",
        "action": "Rinse out and place carefully in dry waste bin.",
        "do": ["Rinse liquid residue", "Keep bottle intact"],
        "do_not": ["Do not shatter into bin", "Do not mix broken glass with wet waste"],
        "top3_pairs": [
            {"class": "glass_bottle_beverage", "confidence_high": 0.88, "confidence_med": 0.71, "confidence_low": 0.47},
            {"class": "plastic_pet_bottle", "confidence_high": 0.09, "confidence_med": 0.19, "confidence_low": 0.32},
            {"class": "other_sanitary_waste", "confidence_high": 0.03, "confidence_med": 0.10, "confidence_low": 0.21}
        ]
    },
    {
        "material_id": "metal_can_aluminum",
        "name": "Aluminum Beverage Can",
        "category": "metal",
        "disposal_bin": "dry",
        "bin_label": "Blue Dry Waste Bin",
        "recovery_potential": "high",
        "next_life": "Infinitely recycled into new aluminum cans and sheet metal",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Rinse out drink residue.",
        "action": "Rinse, crush, and place in dry waste bin.",
        "do": ["Rinse clean", "Crush can"],
        "do_not": ["Do not include liquids", "Do not throw in wet bin"],
        "top3_pairs": [
            {"class": "metal_can_aluminum", "confidence_high": 0.91, "confidence_med": 0.75, "confidence_low": 0.50},
            {"class": "plastic_pet_bottle", "confidence_high": 0.06, "confidence_med": 0.16, "confidence_low": 0.30},
            {"class": "hazardous_battery_aa", "confidence_high": 0.03, "confidence_med": 0.09, "confidence_low": 0.20}
        ]
    },
    {
        "material_id": "e_waste_mobile_charger",
        "name": "Unused Electronic Cable / Charger",
        "category": "e_waste",
        "disposal_bin": "e_waste",
        "bin_label": "Violet E-Waste Bin",
        "recovery_potential": "high",
        "next_life": "Copper wiring and plastic casing recovered for industrial reuse",
        "recovery_channel": "specialized",
        "contamination_notes": "Drop at authorized e-waste collection center or designated bin.",
        "action": "Place in the specialized e-waste collection bin.",
        "do": ["Bundle cable neatly", "Dispose at e-waste center"],
        "do_not": ["Do not mix with general dry waste", "Do not cut wires"],
        "top3_pairs": [
            {"class": "e_waste_mobile_charger", "confidence_high": 0.85, "confidence_med": 0.69, "confidence_low": 0.46},
            {"class": "hazardous_battery_aa", "confidence_high": 0.10, "confidence_med": 0.20, "confidence_low": 0.33},
            {"class": "plastic_hdpe_container", "confidence_high": 0.05, "confidence_med": 0.11, "confidence_low": 0.21}
        ]
    }
]


# Keyword rules for TRANSPARENT text-based demo matching.
# The mock NEVER performs visual recognition: image bytes are ignored for
# material selection (they only signal that a photo was uploaded). Order
# matters — more specific phrases are checked first.
KEYWORD_RULES: List[Dict[str, Any]] = [
    {"material_id": "plastic_pet_bottle", "keywords": ["pet bottle", "plastic bottle", "water bottle", "soda bottle", "pet "]},
    {"material_id": "plastic_pet_bottle", "keywords": ["plastic", "bottle", "pet"]},
    {"material_id": "composite_tetrapack", "keywords": ["tetra", "tetrapack", "tetra pack"]},
    {"material_id": "paper_cardboard_box", "keywords": ["cardboard", "corrugated", "pizza box", "packaging box", "carton box"]},
    {"material_id": "paper_cardboard_box", "keywords": ["newspaper", "magazine", "office paper", "cardboard", "carton"]},
    {"material_id": "organic_food_waste", "keywords": ["food", "vegetable", "peel", "banana", "organic", "compost", "leftover", "scrap", "residue", "garden"]},
    {"material_id": "hazardous_battery_aa", "keywords": ["battery", "batteries", "aa ", "aaa", "dry cell"]},
    {"material_id": "glass_bottle_beverage", "keywords": ["glass"]},
    {"material_id": "metal_can_aluminum", "keywords": ["aluminium", "aluminum", "soda can", "tin ", "steel can", "foil"]},
    {"material_id": "metal_can_aluminum", "keywords": ["can "]},
    {"material_id": "e_waste_mobile_charger", "keywords": ["cable", "charger", "usb", "e-waste", "ewaste", "e waste", "circuit", "electronic", "phone", "wire", "laptop", "charger"]},
]

UNKNOWN_MATERIAL: Dict[str, Any] = {
    "material_id": "unknown",
    "name": "Unknown item — needs manual check",
    "category": "other",
    "disposal_bin": "rejected",
    "bin_label": "Check local waste rules",
    "recovery_potential": "none",
    "next_life": "This demo simulation could not identify the item. Please check your local waste rules or select the material manually.",
    "recovery_channel": "manual_check",
    "contamination_notes": "Demo simulation only — not a verified image recognition result. When in doubt, keep the item separate and check local waste rules.",
    "action": "We could not identify this item from the photo in demo mode. Please describe it in words or pick the closest material below.",
    "do": ["Describe the item in words (e.g. plastic bottle, newspaper, food scraps)", "Pick the closest material from the list", "Check your local waste rules when unsure"],
    "do_not": ["Do not treat this demo result as a verified recognition", "Do not put hazardous or e-waste items in the regular bins"],
}


def find_material_by_keywords(description: str) -> Optional[Dict[str, Any]]:
    """Return the MOCK_MATERIAL_POOL entry matching text keywords, else None."""
    text = (description or "").lower()
    if not text.strip():
        return None
    for rule in KEYWORD_RULES:
        for kw in rule["keywords"]:
            if kw in text:
                for entry in MOCK_MATERIAL_POOL:
                    if entry["material_id"] == rule["material_id"]:
                        return entry
    return None


def get_material_entry(material_id: str) -> Optional[Dict[str, Any]]:
    for entry in MOCK_MATERIAL_POOL:
        if entry["material_id"] == material_id:
            return entry
    return None


class MockClassifier(BaseClassifier):
    """Deterministic DEMO simulator (NOT a computer-vision model).

    Transparent demo strategy:
    - Text descriptions are matched with visible keyword rules above.
    - Uploaded image bytes are NEVER visually analysed; a photo without a
      recognisable description returns an explicit ``unknown`` result with
      ``confidence_label="low"`` and safe "check local rules" guidance.
    - Every result carries ``is_demo=True`` / ``model_version="mock-v1"`` so
      callers can label it as a demo simulation.
    """

    @property
    def model_version(self) -> str:
        return "mock-v1"

    @property
    def is_demo(self) -> bool:
        return True

    async def classify(
        self,
        image_bytes: Optional[bytes] = None,
        description: Optional[str] = None
    ) -> ClassificationResult:
        # Transparent demo: text keywords drive the match. Image bytes are
        # deliberately NOT analysed — a photo alone yields "unknown".
        matched = find_material_by_keywords(description or "")

        if matched is not None:
            # Deterministic medium-confidence demo match (never "high": this
            # is a keyword simulation, not a verified recognition).
            pair_key = "confidence_med"
            confidence_label = "medium"
            material_info = matched
            top3 = []
            for pair in material_info["top3_pairs"]:
                top3.append({
                    "class": pair["class"],
                    "confidence": round(pair[pair_key], 2)
                })
            main_confidence = top3[0]["confidence"]

            mat_guidance = MaterialGuidance(
                name=material_info["name"],
                category=material_info["category"],
                disposal_bin=material_info["disposal_bin"],
                recovery_potential=material_info["recovery_potential"],
                next_life=material_info["next_life"],
                recovery_channel=material_info["recovery_channel"],
                contamination_notes=material_info["contamination_notes"]
            )

            disp_guidance = DisposalGuidance(
                bin_label=material_info["bin_label"],
                action=material_info["action"],
                do=material_info["do"],
                do_not=material_info["do_not"]
            )

            return ClassificationResult(
                event_id=str(uuid.uuid4()),
                predicted_class=material_info["material_id"],
                confidence=main_confidence,
                confidence_label=confidence_label,
                top3=top3,
                material=mat_guidance,
                guidance=disp_guidance,
                model_version=self.model_version,
                is_demo=self.is_demo
            )

        # No recognisable description (photo-only upload, gibberish text, or
        # empty input): explicit uncertain result with safe instructions.
        # A plastic-bottle photo without a description MUST land here — never
        # on an arbitrary pool entry such as e-waste.
        top3 = [
            {"class": "unknown", "confidence": 0.18},
            {"class": "plastic_pet_bottle", "confidence": 0.12},
            {"class": "organic_food_waste", "confidence": 0.10},
        ]

        mat_guidance = MaterialGuidance(
            name=UNKNOWN_MATERIAL["name"],
            category=UNKNOWN_MATERIAL["category"],
            disposal_bin=UNKNOWN_MATERIAL["disposal_bin"],
            recovery_potential=UNKNOWN_MATERIAL["recovery_potential"],
            next_life=UNKNOWN_MATERIAL["next_life"],
            recovery_channel=UNKNOWN_MATERIAL["recovery_channel"],
            contamination_notes=UNKNOWN_MATERIAL["contamination_notes"]
        )

        disp_guidance = DisposalGuidance(
            bin_label=UNKNOWN_MATERIAL["bin_label"],
            action=UNKNOWN_MATERIAL["action"],
            do=UNKNOWN_MATERIAL["do"],
            do_not=UNKNOWN_MATERIAL["do_not"]
        )

        return ClassificationResult(
            event_id=str(uuid.uuid4()),
            predicted_class=UNKNOWN_MATERIAL["material_id"],
            confidence=top3[0]["confidence"],
            confidence_label="low",
            top3=top3,
            material=mat_guidance,
            guidance=disp_guidance,
            model_version=self.model_version,
            is_demo=self.is_demo
        )
