import asyncio
import logging
from sqlalchemy import select
from app.models.database import AsyncSessionLocal, check_db_connection
from app.models.materials import Material
from app.models.events import MaterialCategoryEnum, DisposalBinEnum, RecoveryPotentialEnum

logger = logging.getLogger(__name__)

SEED_MATERIALS = [
    # Plastic Category (5)
    {
        "material_id": "plastic_pet_bottle",
        "name": "PET Plastic Bottle",
        "category": MaterialCategoryEnum.plastic,
        "subcategory": "PET Type 1",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Recycled into polyester fibre or new PET bottles",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Rinse out residue. Remove cap.",
        "icon_slug": "pet_bottle",
        "demo_seed": True
    },
    {
        "material_id": "plastic_hdpe_container",
        "name": "HDPE Milk / Detergent Container",
        "category": MaterialCategoryEnum.plastic,
        "subcategory": "HDPE Type 2",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Recycled into heavy-duty plastic pipes, crates, and furniture",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Rinse thoroughly and drain before binning.",
        "icon_slug": "hdpe_jug",
        "demo_seed": True
    },
    {
        "material_id": "plastic_ldpe_bag",
        "name": "Single-Use Carry Bag / Wrap",
        "category": MaterialCategoryEnum.plastic,
        "subcategory": "LDPE Type 4",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.medium,
        "next_life": "Pelletised for composite lumber or low-grade plastic products",
        "recovery_channel": "municipality_dry",
        "contamination_notes": "Ensure clean and dry. Avoid food grease.",
        "icon_slug": "plastic_bag",
        "demo_seed": True
    },
    {
        "material_id": "plastic_pp_container",
        "name": "PP Food Takeout Box",
        "category": MaterialCategoryEnum.plastic,
        "subcategory": "PP Type 5",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.medium,
        "next_life": "Recycled into automotive parts, battery cases, and storage bins",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Wipe or rinse off oil and curry residues completely.",
        "icon_slug": "pp_box",
        "demo_seed": True
    },
    {
        "material_id": "plastic_ps_cutlery",
        "name": "Polystyrene (Thermocol) Cup / Cutlery",
        "category": MaterialCategoryEnum.plastic,
        "subcategory": "PS Type 6",
        "disposal_bin": DisposalBinEnum.rejected,
        "recovery_potential": RecoveryPotentialEnum.low,
        "next_life": "Extremely difficult to recycle; processed into refuse-derived fuel (RDF)",
        "recovery_channel": "municipality_dry",
        "contamination_notes": "Avoid single-use foam cutlery where possible.",
        "icon_slug": "foam_cup",
        "demo_seed": True
    },

    # Paper Category (4)
    {
        "material_id": "paper_cardboard_box",
        "name": "Corrugated Cardboard Box",
        "category": MaterialCategoryEnum.paper,
        "subcategory": "Corrugated Board",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Repulped into new cardboard sheets and paper packaging",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Flatten flat and strip plastic adhesive tape.",
        "icon_slug": "cardboard_box",
        "demo_seed": True
    },
    {
        "material_id": "paper_newspaper",
        "name": "Old Newspaper & Magazine",
        "category": MaterialCategoryEnum.paper,
        "subcategory": "Newsprint",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Recycled into newsprint, tissue, and paper bags",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Keep dry. Do not mix with wet food waste.",
        "icon_slug": "newspaper",
        "demo_seed": True
    },
    {
        "material_id": "paper_office_sheet",
        "name": "White Printing & Office Paper",
        "category": MaterialCategoryEnum.paper,
        "subcategory": "High-grade Paper",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Recycled into high-quality stationery and paper towels",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Remove metal staples and plastic covers.",
        "icon_slug": "office_paper",
        "demo_seed": True
    },
    {
        "material_id": "paper_soiled_napkin",
        "name": "Food-Soiled Tissue / Napkin",
        "category": MaterialCategoryEnum.paper,
        "subcategory": "Tissue",
        "disposal_bin": DisposalBinEnum.wet,
        "recovery_potential": RecoveryPotentialEnum.none,
        "next_life": "Composts with organic waste in municipal composting units",
        "recovery_channel": "composting",
        "contamination_notes": "Place in wet bin; cannot be recycled as dry paper.",
        "icon_slug": "tissue_paper",
        "demo_seed": True
    },

    # Organic Category (4)
    {
        "material_id": "organic_food_waste",
        "name": "Cooked Food Residue & Scraps",
        "category": MaterialCategoryEnum.organic,
        "subcategory": "Food Scraps",
        "disposal_bin": DisposalBinEnum.wet,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Converted to nutrient-rich organic compost or biogas",
        "recovery_channel": "composting",
        "contamination_notes": "Drain liquids prior to binning. Keep free of plastics.",
        "icon_slug": "food_scraps",
        "demo_seed": True
    },
    {
        "material_id": "organic_fruit_peel",
        "name": "Raw Fruit & Vegetable Peels",
        "category": MaterialCategoryEnum.organic,
        "subcategory": "Green Waste",
        "disposal_bin": DisposalBinEnum.wet,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Processed into agricultural compost or bio-fertilizer",
        "recovery_channel": "composting",
        "contamination_notes": "Ideal input for home or society composting pits.",
        "icon_slug": "veggie_peel",
        "demo_seed": True
    },
    {
        "material_id": "organic_coconut_shell",
        "name": "Coconut Shell & Husk",
        "category": MaterialCategoryEnum.organic,
        "subcategory": "Fibrous Organic",
        "disposal_bin": DisposalBinEnum.wet,
        "recovery_potential": RecoveryPotentialEnum.medium,
        "next_life": "Processed into coir pith, activated carbon, or mulch",
        "recovery_channel": "composting",
        "contamination_notes": "Slow to decompose; crush shell if composting locally.",
        "icon_slug": "coconut_shell",
        "demo_seed": True
    },
    {
        "material_id": "organic_garden_trimmings",
        "name": "Garden Leaves & Plant Trimmings",
        "category": MaterialCategoryEnum.organic,
        "subcategory": "Yard Waste",
        "disposal_bin": DisposalBinEnum.wet,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Shredded for soil mulching or community aerobic composting",
        "recovery_channel": "composting",
        "contamination_notes": "Keep free of stones, plastic pots, and wire.",
        "icon_slug": "leaf_trimmings",
        "demo_seed": True
    },

    # Glass Category (3)
    {
        "material_id": "glass_bottle_beverage",
        "name": "Glass Beverage & Sauce Bottle",
        "category": MaterialCategoryEnum.glass,
        "subcategory": "Container Glass",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Melted down indefinitely into new glass bottles and jars",
        "recovery_channel": "municipality_dry",
        "contamination_notes": "Rinse residue. Remove metal caps.",
        "icon_slug": "glass_bottle",
        "demo_seed": True
    },
    {
        "material_id": "glass_jar_food",
        "name": "Glass Jam / Pickle Jar",
        "category": MaterialCategoryEnum.glass,
        "subcategory": "Container Glass",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Reused directly or remelted for new container glass",
        "recovery_channel": "municipality_dry",
        "contamination_notes": "Wash out food oils completely.",
        "icon_slug": "glass_jar",
        "demo_seed": True
    },
    {
        "material_id": "glass_mirror_broken",
        "name": "Broken Mirror / Window Glass",
        "category": MaterialCategoryEnum.glass,
        "subcategory": "Flat Glass",
        "disposal_bin": DisposalBinEnum.rejected,
        "recovery_potential": RecoveryPotentialEnum.low,
        "next_life": "Specialist reprocessing or inclusion in fiberglass insulation",
        "recovery_channel": "specialized",
        "contamination_notes": "Wrap sharp edges securely in paper before disposal for safety.",
        "icon_slug": "broken_glass",
        "demo_seed": True
    },

    # Metal Category (3)
    {
        "material_id": "metal_can_aluminum",
        "name": "Aluminum Beverage Can",
        "category": MaterialCategoryEnum.metal,
        "subcategory": "Aluminum",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Recycled infinitely into new aluminum cans and industrial parts",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Rinse out drink residue and crush.",
        "icon_slug": "soda_can",
        "demo_seed": True
    },
    {
        "material_id": "metal_tin_container",
        "name": "Tin / Steel Food Can",
        "category": MaterialCategoryEnum.metal,
        "subcategory": "Steel / Tinplate",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Smelted into recycled steel beams, rebar, and machine components",
        "recovery_channel": "informal_sector",
        "contamination_notes": "Rinse clean of food sauce before binning.",
        "icon_slug": "tin_can",
        "demo_seed": True
    },
    {
        "material_id": "metal_foil_wrapper",
        "name": "Aluminum Kitchen Foil",
        "category": MaterialCategoryEnum.metal,
        "subcategory": "Foil",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.medium,
        "next_life": "Recycled if clean; re-smelted into secondary aluminum alloys",
        "recovery_channel": "municipality_dry",
        "contamination_notes": "Wipe clean of food residue and roll into a tight ball.",
        "icon_slug": "aluminum_foil",
        "demo_seed": True
    },

    # E-Waste Category (2)
    {
        "material_id": "e_waste_mobile_charger",
        "name": "Mobile Charger & USB Cable",
        "category": MaterialCategoryEnum.e_waste,
        "subcategory": "Cable & Adapter",
        "disposal_bin": DisposalBinEnum.e_waste,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Copper wire and plastics stripped for electronics manufacturing",
        "recovery_channel": "specialized",
        "contamination_notes": "Drop in e-waste bin; do not mix with wet/dry household bin.",
        "icon_slug": "usb_charger",
        "demo_seed": True
    },
    {
        "material_id": "e_waste_circuit_board",
        "name": "Old Circuit Board / PCB",
        "category": MaterialCategoryEnum.e_waste,
        "subcategory": "Printed Circuit Board",
        "disposal_bin": DisposalBinEnum.e_waste,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Precious metals (gold, silver, copper) extracted at hydrometallurgical plant",
        "recovery_channel": "specialized",
        "contamination_notes": "Handle with care; deliver to registered e-waste collector.",
        "icon_slug": "circuit_board",
        "demo_seed": True
    },

    # Hazardous Category (2)
    {
        "material_id": "hazardous_battery_aa",
        "name": "Used Household Battery (AA / AAA)",
        "category": MaterialCategoryEnum.hazardous,
        "subcategory": "Dry Cell Battery",
        "disposal_bin": DisposalBinEnum.hazardous,
        "recovery_potential": RecoveryPotentialEnum.medium,
        "next_life": "Zinc, manganese, and steel recovered in controlled hazard facility",
        "recovery_channel": "hazardous_facility",
        "contamination_notes": "Do not throw in general dry bin to prevent chemical leakage.",
        "icon_slug": "aa_battery",
        "demo_seed": True
    },
    {
        "material_id": "hazardous_paint_tin",
        "name": "Chemical / Solvent Container",
        "category": MaterialCategoryEnum.hazardous,
        "subcategory": "Chemical Packaging",
        "disposal_bin": DisposalBinEnum.hazardous,
        "recovery_potential": RecoveryPotentialEnum.low,
        "next_life": "Neutralised and safely incinerated in toxic waste management facility",
        "recovery_channel": "hazardous_facility",
        "contamination_notes": "Keep lid tightly closed. Deposit at hazardous waste station.",
        "icon_slug": "paint_can",
        "demo_seed": True
    },

    # Composite Category (1)
    {
        "material_id": "composite_tetrapack",
        "name": "Tetra Pack Carton",
        "category": MaterialCategoryEnum.composite,
        "subcategory": "Multilayer Packaging",
        "disposal_bin": DisposalBinEnum.dry,
        "recovery_potential": RecoveryPotentialEnum.high,
        "next_life": "Pulp separated into paper products; poly-aluminum pressed into roofing sheets",
        "recovery_channel": "specialized",
        "contamination_notes": "Flatten carton completely after drinking.",
        "icon_slug": "tetrapack",
        "demo_seed": True
    },

    # Other Category (1)
    {
        "material_id": "other_sanitary_waste",
        "name": "Sanitary & Hygiene Product",
        "category": MaterialCategoryEnum.other,
        "subcategory": "Sanitary Waste",
        "disposal_bin": DisposalBinEnum.rejected,
        "recovery_potential": RecoveryPotentialEnum.none,
        "next_life": "Incinerated at high temperatures in biomedical incinerator",
        "recovery_channel": "specialized",
        "contamination_notes": "Wrap securely in newspaper and mark with a red cross.",
        "icon_slug": "sanitary_pad",
        "demo_seed": True
    }
]


async def seed_materials_database():
    """Seeds 25 representative Indian waste stream materials into DB."""
    if not await check_db_connection():
        logger.warning("Database not connected. Skipping DB seed insertion; serving the in-memory material catalog instead.")
        return

    async with AsyncSessionLocal() as session:
        try:
            inserted_count = 0
            for mat_data in SEED_MATERIALS:
                stmt = select(Material).where(Material.material_id == mat_data["material_id"])
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()
                if not existing:
                    mat = Material(**mat_data)
                    session.add(mat)
                    inserted_count += 1
            await session.commit()
            logger.info(f"Successfully seeded {inserted_count} new materials into DB.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error seeding materials: {e}")


def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_materials_database())


if __name__ == "__main__":
    main()
