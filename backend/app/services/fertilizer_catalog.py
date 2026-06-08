"""Built-in fertilizer program catalog.

Contains curated program data from Scotts and Jonathan Green.
Programs are seeded into the database on first startup and can be
refreshed via the API to pick up catalog updates from new container builds.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CATALOG_YEAR = 2026

PROGRAMS = [
    # ── Scotts 4-Step (Cool-Season) ─────────────────────────
    {
        "name": "Scotts 4-Step Program",
        "slug": "scotts-4-step",
        "brand": "Scotts",
        "description": "The classic Scotts Turf Builder 4-Step annual lawn program for cool-season grasses. Prevents crabgrass, controls weeds, strengthens against heat, and prepares for winter.",
        "grass_season": "cool",
        "soil_type": "any",
        "source_url": "https://www.scotts.com/en-us/programs",
        "steps": [
            {
                "step_number": 1,
                "product_name": "Scotts Turf Builder Halts Crabgrass Preventer with Lawn Food",
                "product_description": "Pre-emergent crabgrass prevention + early season feeding",
                "season": "early_spring",
                "month_start": 2, "month_end": 4,
                "application_rate_per_1k": "2.87 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "13.35 lbs",
                "purpose": "Prevents crabgrass before it germinates and gives the lawn its first feeding to help recover from winter.",
                "tips": "Apply before soil temps reach 55°F consistently. Best applied before Easter in most regions. Do not aerate or dethatch after applying.",
                "icon_emoji": "🛡️",
            },
            {
                "step_number": 2,
                "product_name": "Scotts Turf Builder Weed & Feed",
                "product_description": "Broadleaf weed killer + lawn fertilizer",
                "season": "late_spring",
                "month_start": 4, "month_end": 6,
                "application_rate_per_1k": "3.23 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "14.29 lbs",
                "purpose": "Kills dandelions, clover, and other broadleaf weeds while continuing to feed the lawn.",
                "tips": "Apply 4-6 weeks after Step 1, ideally near Memorial Day. Apply to a damp lawn on a calm day. Do NOT water for 24 hours after application.",
                "icon_emoji": "🧹",
            },
            {
                "step_number": 3,
                "product_name": "Scotts Turf Builder Lawn Food with 2% Iron",
                "product_description": "Summer feeding with iron for deep green color",
                "season": "summer",
                "month_start": 6, "month_end": 8,
                "application_rate_per_1k": "2.87 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "12.6 lbs",
                "purpose": "Strengthens lawn against heat and drought stress. Iron provides deep green color without excessive growth.",
                "tips": "Apply near Independence Day. Water the lawn after application if rain is not expected within 48 hours.",
                "icon_emoji": "💪",
            },
            {
                "step_number": 4,
                "product_name": "Scotts Turf Builder WinterGuard Fall Lawn Food",
                "product_description": "Fall fertilizer for winter root strength",
                "season": "fall",
                "month_start": 9, "month_end": 11,
                "application_rate_per_1k": "2.87 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "12.5 lbs",
                "purpose": "Builds strong, deep roots for winter survival. Most important feeding of the year — ensures a greener lawn next spring.",
                "tips": "Apply between Labor Day and mid-October. This is the MOST important application of the year for cool-season lawns.",
                "icon_emoji": "🍂",
            },
        ],
    },

    # ── Scotts Southern (Warm-Season) ───────────────────────
    {
        "name": "Scotts Southern Lawn Program",
        "slug": "scotts-southern",
        "brand": "Scotts",
        "description": "Scotts program designed for warm-season Southern lawns (St. Augustine, Centipede, Zoysia, Bermuda). Handles Southern weeds and heat stress.",
        "grass_season": "warm",
        "soil_type": "any",
        "source_url": "https://www.scotts.com/en-us/programs",
        "steps": [
            {
                "step_number": 1,
                "product_name": "Scotts Turf Builder Bonus S Southern Weed & Feed",
                "product_description": "Kills dollarweed, clover & feeds Southern lawns",
                "season": "early_spring",
                "month_start": 3, "month_end": 5,
                "application_rate_per_1k": "3.27 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "17.24 lbs",
                "purpose": "Kills existing Southern weeds (dollarweed, clover, henbit) and feeds the lawn as it greens up from winter dormancy.",
                "tips": "Apply when grass is actively growing and temps are consistently above 60°F. Apply to a dry lawn. For Bermuda, use WinterGuard Weed & Feed instead for fall.",
                "icon_emoji": "🌴",
            },
            {
                "step_number": 2,
                "product_name": "Scotts Turf Builder Southern Lawn Food",
                "product_description": "Feeds for thick, green turf and heat protection",
                "season": "late_spring",
                "month_start": 5, "month_end": 6,
                "application_rate_per_1k": "2.63 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "14.06 lbs",
                "purpose": "Builds thick, green turf and provides nutrients to protect against upcoming summer heat and drought.",
                "tips": "Apply 6-8 weeks after Step 1. Water in well after application.",
                "icon_emoji": "☀️",
            },
            {
                "step_number": 3,
                "product_name": "Scotts Turf Builder SummerGuard Lawn Food with Insect Control",
                "product_description": "Summer feeding + fire ant, grub, and insect control",
                "season": "summer",
                "month_start": 6, "month_end": 8,
                "application_rate_per_1k": "3.23 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "13.35 lbs",
                "purpose": "Feeds the lawn during peak summer while controlling fire ants, grubs, ticks, and other insects for up to 3 months.",
                "tips": "Apply during the hottest months. Water immediately after application for best insect control results.",
                "icon_emoji": "🐛",
            },
            {
                "step_number": 4,
                "product_name": "Scotts Turf Builder Bonus S Southern Weed & Feed",
                "product_description": "Fall weed control + feeding before dormancy",
                "season": "fall",
                "month_start": 9, "month_end": 10,
                "application_rate_per_1k": "3.27 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "17.24 lbs",
                "purpose": "Kills weeds that emerged during summer/fall and strengthens roots before winter dormancy.",
                "tips": "Apply while grass is still actively growing, before first frost. For Bermuda grass, use Scotts WinterGuard Weed & Feed instead.",
                "icon_emoji": "🍂",
            },
        ],
    },

    # ── Jonathan Green Standard (Acidic Soil) ───────────────
    {
        "name": "Jonathan Green Annual Program (Acidic Soil)",
        "slug": "jg-acidic",
        "brand": "Jonathan Green",
        "description": "Jonathan Green's 4-step program for cool-season lawns in acidic soil regions (Eastern & Midwestern US). Feeds the lawn AND the soil.",
        "grass_season": "cool",
        "soil_type": "acidic",
        "source_url": "https://www.jonathangreen.com/annual-lawn-care-program",
        "steps": [
            {
                "step_number": 1,
                "product_name": "Veri-Green Crabgrass Preventer Plus Lawn Fertilizer",
                "product_description": "Pre-emergent crabgrass prevention + spring feeding",
                "season": "early_spring",
                "month_start": 3, "month_end": 4,
                "application_rate_per_1k": "3.5 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "16 lbs",
                "purpose": "Prevents crabgrass and other annual grassy weeds before they germinate. Provides early-season nutrition for spring green-up.",
                "tips": "Apply before forsythia blooms drop (a natural indicator of soil temp reaching crabgrass germination threshold). Do NOT use within 60 days of seeding.",
                "icon_emoji": "🛡️",
            },
            {
                "step_number": 2,
                "product_name": "Veri-Green Weed & Feed Lawn Fertilizer",
                "product_description": "Broadleaf weed control + feeding",
                "season": "late_spring",
                "month_start": 5, "month_end": 6,
                "application_rate_per_1k": "3.5 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "16 lbs",
                "purpose": "Controls dandelions, clover, chickweed, and other broadleaf weeds while providing sustained feeding.",
                "tips": "Wet the lawn before application so the product adheres to weed leaves. Do NOT mow for 2 days after application.",
                "icon_emoji": "🧹",
            },
            {
                "step_number": 3,
                "product_name": "MAG-I-CAL Plus for Acidic & Hard Soil",
                "product_description": "Soil conditioner — raises pH & loosens compacted soil",
                "season": "summer",
                "month_start": 7, "month_end": 8,
                "application_rate_per_1k": "18 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "54 lbs",
                "purpose": "Raises soil pH toward the ideal 6.2-6.9 range, loosens compacted soil, and activates beneficial soil microbes. Critical for nutrient absorption.",
                "tips": "Ideal soil pH is 6.2-6.9. Test your soil pH first. Can be applied any time during the growing season. Not a fertilizer — it's a soil amendment.",
                "icon_emoji": "🧫",
            },
            {
                "step_number": 4,
                "product_name": "Winter Survival Fall Lawn Fertilizer",
                "product_description": "Fall fertilizer for winter hardiness",
                "season": "fall",
                "month_start": 9, "month_end": 10,
                "application_rate_per_1k": "3.5 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "16 lbs",
                "purpose": "Provides essential nutrients to build deep roots and disease resistance for winter. Safe to apply on the same day as overseeding.",
                "tips": "Best applied in early fall (September). Can be combined with fall overseeding. This is the most important feeding for cool-season lawns.",
                "icon_emoji": "❄️",
            },
        ],
    },

    # ── Jonathan Green Standard (Alkaline Soil) ─────────────
    {
        "name": "Jonathan Green Annual Program (Alkaline Soil)",
        "slug": "jg-alkaline",
        "brand": "Jonathan Green",
        "description": "Jonathan Green's 4-step program for cool-season lawns in alkaline soil regions (Western US). Uses specialized MAG-I-CAL Plus for alkaline conditions.",
        "grass_season": "cool",
        "soil_type": "alkaline",
        "source_url": "https://www.jonathangreen.com/annual-lawn-care-program",
        "steps": [
            {
                "step_number": 1,
                "product_name": "Crabgrass Preventer Plus Green-Up Lawn Fertilizer",
                "product_description": "Pre-emergent crabgrass prevention + green-up feeding",
                "season": "early_spring",
                "month_start": 3, "month_end": 4,
                "application_rate_per_1k": "3.5 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "16 lbs",
                "purpose": "Prevents crabgrass while providing early spring green-up nutrients. Formulated for alkaline soil conditions.",
                "tips": "Apply before soil temperature consistently reaches 55°F. Do NOT use within 60 days of seeding.",
                "icon_emoji": "🛡️",
            },
            {
                "step_number": 2,
                "product_name": "Weed & Feed Lawn Fertilizer",
                "product_description": "Broadleaf weed control + balanced feeding",
                "season": "late_spring",
                "month_start": 5, "month_end": 6,
                "application_rate_per_1k": "3.5 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "16 lbs",
                "purpose": "Controls broadleaf weeds and feeds the lawn through late spring.",
                "tips": "Apply to a wet lawn so granules stick to weed leaves. Avoid mowing for 2 days after application.",
                "icon_emoji": "🧹",
            },
            {
                "step_number": 3,
                "product_name": "MAG-I-CAL Plus for Alkaline & Hard Soil",
                "product_description": "Soil conditioner — lowers pH & loosens compacted soil",
                "season": "summer",
                "month_start": 7, "month_end": 8,
                "application_rate_per_1k": "18 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "54 lbs",
                "purpose": "Lowers soil pH toward the ideal 6.2-6.9 range for alkaline soils. Loosens hard soil and activates soil biology.",
                "tips": "Test your soil pH first. This product is specifically formulated for soils with pH above 7.0. Can be applied any time during growing season.",
                "icon_emoji": "🧫",
            },
            {
                "step_number": 4,
                "product_name": "Winter Survival Fall Lawn Fertilizer",
                "product_description": "Fall fertilizer for winter hardiness",
                "season": "fall",
                "month_start": 9, "month_end": 10,
                "application_rate_per_1k": "3.5 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "16 lbs",
                "purpose": "Builds deep root systems and disease resistance for winter. Compatible with fall overseeding.",
                "tips": "Apply in early fall, can be the same day as overseeding. Most critical feeding of the year.",
                "icon_emoji": "❄️",
            },
        ],
    },

    # ── Jonathan Green Natural/Organic ──────────────────────
    {
        "name": "Jonathan Green Natural Organic Program",
        "slug": "jg-organic",
        "brand": "Jonathan Green",
        "description": "100% organic/natural 4-step program. Safe for children and pets. Feeds both the lawn and soil using organic ingredients including corn gluten for natural weed prevention.",
        "grass_season": "cool",
        "soil_type": "any",
        "source_url": "https://www.jonathangreen.com/natural-annual-lawn-care-program",
        "steps": [
            {
                "step_number": 1,
                "product_name": "Corn Gluten Weed Preventer Plus Lawn Food",
                "product_description": "Organic pre-emergent + natural fertilizer",
                "season": "early_spring",
                "month_start": 3, "month_end": 4,
                "application_rate_per_1k": "20 lbs",
                "coverage_sqft_per_bag": 1250,
                "bag_weight": "25 lbs",
                "purpose": "Natural pre-emergent that prevents crabgrass, dandelions, and other weeds from germinating. Also provides organic nutrition.",
                "tips": "Corn gluten is a PRE-EMERGENT only — it won't kill existing weeds. Do NOT seed within 60-90 days of application. If already seeded, wait 45 days.",
                "icon_emoji": "🌽",
            },
            {
                "step_number": 2,
                "product_name": "Organic Lawn Food",
                "product_description": "Slow-release organic fertilizer",
                "season": "late_spring",
                "month_start": 5, "month_end": 6,
                "application_rate_per_1k": "6.25 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "25 lbs",
                "purpose": "Provides steady, slow-release organic nutrition. Safe for children and pets immediately after application.",
                "tips": "Can be applied to a dry lawn. Organic granules break down naturally — no burn risk.",
                "icon_emoji": "🌱",
            },
            {
                "step_number": 3,
                "product_name": "MAG-I-CAL Plus for Acidic & Hard Soil",
                "product_description": "Natural soil conditioner for pH balance",
                "season": "summer",
                "month_start": 7, "month_end": 8,
                "application_rate_per_1k": "18 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "54 lbs",
                "purpose": "Balances soil pH and loosens compacted soil naturally. Activates beneficial microbial life in the soil.",
                "tips": "Choose the Acidic or Alkaline formula based on your soil pH test results. Essential for organic soil health.",
                "icon_emoji": "🧫",
            },
            {
                "step_number": 4,
                "product_name": "Organic Lawn Food",
                "product_description": "Fall organic feeding for winter prep",
                "season": "fall",
                "month_start": 9, "month_end": 10,
                "application_rate_per_1k": "6.25 lbs",
                "coverage_sqft_per_bag": 5000,
                "bag_weight": "25 lbs",
                "purpose": "Final organic feeding to nourish the lawn and soil before winter. Safe to apply same day as overseeding.",
                "tips": "Great combined with fall overseeding. Organic nutrients continue feeding through late fall.",
                "icon_emoji": "🍂",
            },
        ],
    },
]


SEASON_LABELS = {
    "early_spring": "Early Spring",
    "late_spring": "Late Spring",
    "summer": "Summer",
    "fall": "Fall",
}

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


async def seed_builtin_programs(db):
    """Seed or refresh built-in fertilizer programs from the catalog.

    Only updates/inserts built-in programs (is_builtin=True).
    Custom programs are never touched.
    """
    from app.models.fertilizer import FertilizerProgram, FertilizerStep
    from sqlalchemy import select, delete

    count = 0
    for prog_data in PROGRAMS:
        slug = prog_data["slug"]

        # Check if program exists
        result = await db.execute(
            select(FertilizerProgram).where(FertilizerProgram.slug == slug)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing program
            existing.name = prog_data["name"]
            existing.brand = prog_data["brand"]
            existing.description = prog_data["description"]
            existing.grass_season = prog_data["grass_season"]
            existing.soil_type = prog_data["soil_type"]
            existing.source_url = prog_data.get("source_url")
            existing.year = CATALOG_YEAR
            existing.step_count = len(prog_data["steps"])
            existing.updated_at = datetime.now()

            # Delete old steps and re-create
            await db.execute(
                delete(FertilizerStep).where(FertilizerStep.program_id == existing.id)
            )
            for step_data in prog_data["steps"]:
                step = FertilizerStep(program_id=existing.id, **step_data)
                db.add(step)
        else:
            # Create new program
            program = FertilizerProgram(
                name=prog_data["name"],
                slug=slug,
                brand=prog_data["brand"],
                description=prog_data["description"],
                grass_season=prog_data["grass_season"],
                soil_type=prog_data["soil_type"],
                is_builtin=True,
                is_custom=False,
                source_url=prog_data.get("source_url"),
                year=CATALOG_YEAR,
                step_count=len(prog_data["steps"]),
            )
            db.add(program)
            await db.flush()

            for step_data in prog_data["steps"]:
                step = FertilizerStep(program_id=program.id, **step_data)
                db.add(step)

        count += 1

    await db.commit()
    logger.info(f"Seeded/refreshed {count} built-in fertilizer programs")
    return count
