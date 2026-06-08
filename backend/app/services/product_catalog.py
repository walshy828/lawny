"""Built-in product catalog — common lawn care products from major retailers."""

import logging

logger = logging.getLogger(__name__)

PRODUCTS = [
    # ── FERTILIZERS ──────────────────────────────────────
    {
        "name": "Scotts Turf Builder All-Purpose Lawn Food",
        "brand": "Scotts",
        "category": "fertilizer",
        "npk_ratio": "32-0-10",
        "application_rate_per_1k": "2.87 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "12.5 lbs",
        "application_timing": "Spring or fall. Do not apply to stressed or dormant lawn.",
        "notes": "General-purpose quick-green fertilizer. Water in after application.",
    },
    {
        "name": "Scotts Turf Builder WinterGuard Fall Lawn Food",
        "brand": "Scotts",
        "category": "fertilizer",
        "npk_ratio": "32-0-10",
        "application_rate_per_1k": "2.87 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "12.5 lbs",
        "application_timing": "September through November, before hard freeze.",
        "notes": "Most important fertilizer application for cool-season lawns. Builds root reserves.",
    },
    {
        "name": "Scotts Turf Builder Lawn Food with 2% Iron",
        "brand": "Scotts",
        "category": "fertilizer",
        "npk_ratio": "29-0-3",
        "application_rate_per_1k": "2.87 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "12.6 lbs",
        "application_timing": "Summer (June-August). Iron deepens green color without excess growth.",
        "notes": "Summer feeding. Iron helps maintain color during heat stress.",
    },
    {
        "name": "Jonathan Green Green-Up Lawn Fertilizer",
        "brand": "Jonathan Green",
        "category": "fertilizer",
        "npk_ratio": "29-0-3",
        "application_rate_per_1k": "3.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "15 lbs",
        "application_timing": "Spring green-up and fall.",
        "notes": "Ideal companion with MAG-I-CAL to feed lawn and correct soil simultaneously.",
    },
    {
        "name": "GreenView Fairway Formula Spring Fertilizer with Crabgrass Preventer",
        "brand": "GreenView",
        "category": "fertilizer",
        "npk_ratio": "24-0-6",
        "application_rate_per_1k": "3.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "18 lbs",
        "application_timing": "Early spring before soil reaches 55°F.",
        "notes": "High-quality alternative to Scotts Step 1. Combines spring feeding + crabgrass prevention.",
        "safe_grass_types": ["kentucky_bluegrass", "tall_fescue", "fine_fescue", "perennial_ryegrass", "cool_mix"],
    },
    {
        "name": "GreenView Fairway Formula Fall Fertilizer",
        "brand": "GreenView",
        "category": "fertilizer",
        "npk_ratio": "22-0-14",
        "application_rate_per_1k": "3.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "18 lbs",
        "application_timing": "September-October for cool-season grasses.",
        "notes": "Premium fall fertilizer with high potassium for root development and winter hardiness.",
    },
    {
        "name": "Pennington UltraGreen Lawn Fertilizer",
        "brand": "Pennington",
        "category": "fertilizer",
        "npk_ratio": "30-0-4",
        "application_rate_per_1k": "2.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "14 lbs",
        "application_timing": "Spring through fall during active growth.",
        "notes": "Polymer-coated slow-release nitrogen. Feeds for up to 3 months.",
    },
    {
        "name": "Milorganite Organic Nitrogen Fertilizer",
        "brand": "Milorganite",
        "category": "fertilizer",
        "npk_ratio": "6-4-0",
        "application_rate_per_1k": "6 lbs",
        "coverage_sqft_per_bag": 2500,
        "bag_size": "36 lbs",
        "application_timing": "Any time during growing season. Safe for use in summer heat.",
        "notes": "Slow-release organic fertilizer with iron. No burn risk. Safe for children and pets when dry. Great for summer feeding when synthetic N can burn.",
    },
    {
        "name": "Espoma Organic Lawn Food",
        "brand": "Espoma",
        "category": "fertilizer",
        "npk_ratio": "8-0-1",
        "application_rate_per_1k": "6.25 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "30 lbs",
        "application_timing": "Spring, summer, and fall.",
        "notes": "100% organic, pet-safe. Biozome beneficial microbes improve soil health. Slow-release, no burn.",
    },
    {
        "name": "Scotts Starter Fertilizer for New Grass",
        "brand": "Scotts",
        "category": "fertilizer",
        "npk_ratio": "24-25-4",
        "application_rate_per_1k": "2.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "14 lbs",
        "application_timing": "At time of seeding or sodding.",
        "notes": "High phosphorus starter fertilizer for new lawn establishment. Do not use on established lawns repeatedly.",
    },

    # ── PRE-EMERGENTS ─────────────────────────────────────
    {
        "name": "Scotts Halts Crabgrass Preventer with Lawn Food",
        "brand": "Scotts",
        "category": "pre_emergent",
        "npk_ratio": "28-0-3",
        "active_ingredient": "Pendimethalin 1.71%",
        "application_rate_per_1k": "2.87 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "14 lbs",
        "application_timing": "Early spring before soil temps reach 55°F. Do not use within 4 months of seeding.",
        "notes": "Combined crabgrass preventer + fertilizer. Apply before forsythia blooms drop.",
    },
    {
        "name": "Jonathan Green Veri-Green Crabgrass Preventer Plus Lawn Fertilizer",
        "brand": "Jonathan Green",
        "category": "pre_emergent",
        "npk_ratio": "20-0-3",
        "active_ingredient": "Pendimethalin",
        "application_rate_per_1k": "3.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "16 lbs",
        "application_timing": "Early spring, when forsythia blooms drop (soil approaching 55°F).",
        "notes": "Do NOT use within 60 days of seeding.",
    },
    {
        "name": "GreenView Crabgrass Control Plus Lawn Fertilizer",
        "brand": "GreenView",
        "category": "pre_emergent",
        "active_ingredient": "Prodiamine",
        "application_rate_per_1k": "3.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "application_timing": "Early spring, split application possible for season-long control.",
        "notes": "Prodiamine provides longer residual activity than pendimethalin — good for extended season control.",
    },
    {
        "name": "Corn Gluten Weed Preventer Plus Lawn Food (Organic)",
        "brand": "Jonathan Green",
        "category": "pre_emergent",
        "npk_ratio": "9-0-0",
        "application_rate_per_1k": "20 lbs",
        "coverage_sqft_per_bag": 1250,
        "bag_size": "25 lbs",
        "application_timing": "Early spring and fall.",
        "notes": "Organic pre-emergent. PRE-EMERGENT ONLY — won't kill existing weeds. Wait 45+ days to seed after application.",
    },

    # ── HERBICIDES / WEED CONTROL ─────────────────────────
    {
        "name": "Scotts Turf Builder Weed & Feed",
        "brand": "Scotts",
        "category": "post_emergent",
        "active_ingredient": "2,4-D + MCPP + Dicamba",
        "application_rate_per_1k": "3.23 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "14.29 lbs",
        "application_timing": "Late spring when weeds are actively growing. Apply to damp lawn. Do NOT water for 24 hours.",
        "notes": "Kills dandelions, clover, and broadleaf weeds while feeding. Do not apply in heat over 85°F.",
    },
    {
        "name": "Ortho WeedBGon Lawn Weed Killer Concentrate",
        "brand": "Ortho",
        "category": "post_emergent",
        "active_ingredient": "2,4-D + MCPP + Dicamba",
        "application_timing": "Spring or fall when temps 60-85°F. Do not mow 3 days before or after.",
        "notes": "Liquid concentrate for spot or broadcast application. Fast-acting broadleaf weed killer. Clover, dandelion, chickweed, ground ivy.",
    },
    {
        "name": "Ortho WeedBGon Crabgrass Killer",
        "brand": "Ortho",
        "category": "post_emergent",
        "active_ingredient": "Quinclorac",
        "application_timing": "When crabgrass is young (1-3 tillers). June-July.",
        "notes": "Also controls foxtail, barnyard grass. Most effective on young plants. Requires multiple applications.",
    },
    {
        "name": "Ortho Nutsedge Killer for Lawns",
        "brand": "Ortho",
        "category": "herbicide",
        "active_ingredient": "Halosulfuron-methyl",
        "application_timing": "Summer when nutsedge is actively growing. May need 2 applications, 30 days apart.",
        "notes": "Specifically targets sedges — does not harm most grasses. Repeat application often needed for heavy infestations.",
    },
    {
        "name": "Jonathan Green Veri-Green Weed & Feed",
        "brand": "Jonathan Green",
        "category": "post_emergent",
        "active_ingredient": "2,4-D + MCPP + Dicamba",
        "application_rate_per_1k": "3.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "16 lbs",
        "application_timing": "Late spring. Wet lawn before application so granules stick to weed leaves.",
        "notes": "Do not mow for 2 days after application.",
    },
    {
        "name": "Spectracide Weed Stop For Lawns",
        "brand": "Spectracide",
        "category": "post_emergent",
        "active_ingredient": "2,4-D + MCPP + Dicamba",
        "application_timing": "Spring or fall during active weed growth.",
        "notes": "Ready-to-spray hose-end formulation. Kills 250+ weeds including clover, dandelion, ground ivy.",
    },
    {
        "name": "Scotts MossEx 3-in-1 Ready-Spray",
        "brand": "Scotts",
        "category": "herbicide",
        "active_ingredient": "Iron HEDTA",
        "application_timing": "Spring or fall when moss is actively growing.",
        "notes": "Kills moss fast (blackens within hours). Follow with pH correction (lime) and overseeding to prevent return.",
    },

    # ── FUNGICIDES ────────────────────────────────────────
    {
        "name": "Scotts DiseaseEx Lawn Fungicide",
        "brand": "Scotts",
        "category": "fungicide",
        "active_ingredient": "Azoxystrobin 0.31%",
        "application_rate_per_1k": "2.87 lbs",
        "coverage_sqft_per_bag": 5000,
        "application_timing": "At first symptoms or preventively in high-risk periods. Repeat every 14-28 days.",
        "notes": "Broad-spectrum systemic fungicide. Controls brown patch, dollar spot, red thread, snow mold, leaf spot.",
    },
    {
        "name": "BioAdvanced Fungus Control for Lawns Ready-to-Spray",
        "brand": "BioAdvanced",
        "category": "fungicide",
        "active_ingredient": "Propiconazole",
        "application_timing": "At first disease symptoms. Repeat every 14-28 days as needed.",
        "notes": "Liquid spray for even coverage. Systemic action. Controls brown patch, dollar spot, rust, and more.",
    },
    {
        "name": "Spectracide Immunox Multi-Purpose Fungicide",
        "brand": "Spectracide",
        "category": "fungicide",
        "active_ingredient": "Myclobutanil",
        "application_timing": "At first symptoms of disease. Repeat every 14 days.",
        "notes": "Controls dollar spot, brown patch, leaf spot. Also works on ornamental plants.",
    },

    # ── INSECTICIDES ─────────────────────────────────────
    {
        "name": "Scotts GrubEx Season-Long Grub Killer",
        "brand": "Scotts",
        "category": "insecticide",
        "active_ingredient": "Chlorantranilipole 0.08%",
        "application_rate_per_1k": "2.87 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "14.35 lbs",
        "application_timing": "May through July. MUST be watered in within 24 hours of application.",
        "notes": "Season-long preventive. Best applied before egg hatch (June). Will not cure active grub infestations.",
    },
    {
        "name": "BioAdvanced 24Hr Grub Killer Plus",
        "brand": "BioAdvanced",
        "category": "insecticide",
        "active_ingredient": "Trichlorfon 9.3%",
        "application_rate_per_1k": "3.0 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "10 lbs",
        "application_timing": "August-September when grub damage is visible. Water in immediately.",
        "notes": "Curative for active grub infestations. Fast-acting. Do not use near water. Most effective on young grubs.",
    },
    {
        "name": "Ortho Bug B Gon Insect Killer for Lawns",
        "brand": "Ortho",
        "category": "insecticide",
        "active_ingredient": "Bifenthrin 0.115%",
        "application_rate_per_1k": "2.0 lbs",
        "coverage_sqft_per_bag": 5000,
        "application_timing": "When insects are active. Water lightly after application.",
        "notes": "Broad-spectrum contact insecticide. Controls armyworms, chinch bugs, billbugs, ants. Fast knockdown.",
    },
    {
        "name": "Spectracide Triazicide Insect Killer for Lawns",
        "brand": "Spectracide",
        "category": "insecticide",
        "active_ingredient": "Gamma-cyhalothrin",
        "application_timing": "When insect pests are active. Acts on contact.",
        "notes": "Broad-spectrum. Good for armyworm emergencies — fast-acting contact killer.",
    },
    {
        "name": "BioAdvanced Complete Insect Killer for Soil & Turf",
        "brand": "BioAdvanced",
        "category": "insecticide",
        "active_ingredient": "Imidacloprid + Beta-cyfluthrin",
        "application_timing": "When surface and soil insects are present. Water in after application.",
        "notes": "Dual action: kills surface insects on contact and soil insects (grubs, chinch bugs) systemically.",
    },
    {
        "name": "Ortho Fire Ant Killer Broadcast Granules",
        "brand": "Ortho",
        "category": "insecticide",
        "active_ingredient": "Bifenthrin",
        "application_timing": "Spring and fall broadcast across entire lawn. Water in after.",
        "safe_grass_types": None,
        "notes": "Most effective approach for fire ant control — broadcast method vs. mound-by-mound. Prevents new mound establishment.",
    },
    {
        "name": "Ortho Orthene Fire Ant Killer",
        "brand": "Ortho",
        "category": "insecticide",
        "active_ingredient": "Acephate 50%",
        "application_timing": "Individual mound treatment. Do not water for 24 hours.",
        "notes": "Apply powder directly into mound opening without disturbing fire ants. Fast colony kill.",
    },

    # ── SOIL AMENDMENTS ──────────────────────────────────
    {
        "name": "Jonathan Green MAG-I-CAL Plus for Acidic & Hard Soil",
        "brand": "Jonathan Green",
        "category": "soil_amendment",
        "application_rate_per_1k": "18 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "54 lbs",
        "application_timing": "Any time during growing season. Ideal in summer (Step 3 of JG program).",
        "notes": "Raises soil pH, loosens compacted soil, activates beneficial soil microbes. Use for acidic soils (pH below 6.0).",
    },
    {
        "name": "Jonathan Green MAG-I-CAL Plus for Alkaline & Hard Soil",
        "brand": "Jonathan Green",
        "category": "soil_amendment",
        "application_rate_per_1k": "18 lbs",
        "coverage_sqft_per_bag": 5000,
        "bag_size": "54 lbs",
        "application_timing": "Any time during growing season.",
        "notes": "Lowers soil pH for alkaline soils (pH above 7.0). Contains sulfur + calcium. Also loosens hard soil.",
    },
    {
        "name": "Espoma Organic Garden Lime",
        "brand": "Espoma",
        "category": "soil_amendment",
        "active_ingredient": "Calcium carbonate (calcite)",
        "application_rate_per_1k": "25-50 lbs depending on pH gap",
        "coverage_sqft_per_bag": 500,
        "bag_size": "25 lbs",
        "application_timing": "Fall is ideal; spring works too. Takes 3-6 months to affect pH.",
        "notes": "Finely ground lime for faster pH correction. Mix into soil when possible or apply to surface.",
    },
    {
        "name": "Encap Fast-Acting Lime with AST",
        "brand": "Encap",
        "category": "soil_amendment",
        "active_ingredient": "Calcium carbonate",
        "application_rate_per_1k": "10-20 lbs",
        "coverage_sqft_per_bag": 5000,
        "application_timing": "Spring or fall. Faster-acting than traditional pelletized lime.",
        "notes": "AST technology makes lime work faster — pH correction in weeks vs. months for traditional lime.",
    },
    {
        "name": "Pennington Ironite Mineral Supplement",
        "brand": "Pennington",
        "category": "soil_amendment",
        "active_ingredient": "Iron (5%), Nitrogen (1%)",
        "application_rate_per_1k": "2.5 lbs",
        "coverage_sqft_per_bag": 5000,
        "application_timing": "Spring through fall to deepen green color. Safe to apply every 4 weeks.",
        "notes": "Adds iron for deep green color without promoting excessive growth. Good for lawns with iron chlorosis.",
    },

    # ── SEEDS ─────────────────────────────────────────────
    {
        "name": "Jonathan Green Black Beauty Ultra Grass Seed",
        "brand": "Jonathan Green",
        "category": "seed",
        "application_timing": "Late August through September (ideal). Spring is second choice.",
        "notes": "Premium tall fescue/bluegrass blend with endophyte enhancement for pest resistance. Germinates in 7-14 days.",
        "safe_grass_types": ["tall_fescue", "kentucky_bluegrass", "cool_mix"],
    },
    {
        "name": "Scotts Turf Builder Grass Seed Sun & Shade Mix",
        "brand": "Scotts",
        "category": "seed",
        "application_timing": "Fall (ideal) or spring. Soil temp 50-65°F for cool-season.",
        "notes": "Good for mixed sun/shade conditions. Contains fine fescue for shade tolerance. Fertilizer coating speeds germination.",
    },
    {
        "name": "Pennington Smart Seed Sun & Shade Grass Seed",
        "brand": "Pennington",
        "category": "seed",
        "application_timing": "Fall (Aug-Oct) or spring (Mar-May) in cool-season regions.",
        "notes": "Penko coating technology reduces watering needs by 30%. Good drought tolerance once established.",
    },
    {
        "name": "Scotts EZ Seed Patch & Repair",
        "brand": "Scotts",
        "category": "seed",
        "application_timing": "Spring or fall for patching bare areas.",
        "notes": "All-in-one seed + starter fertilizer + mulch. Excellent for small patches. Keeps seed moist for better germination.",
    },
]


async def seed_product_catalog(db):
    """Seed or refresh built-in product catalog.

    Only updates/inserts products that don't already exist (matched by name+brand).
    """
    from app.models.product import ProductCatalog
    from sqlalchemy import select

    count = 0
    for prod_data in PRODUCTS:
        result = await db.execute(
            select(ProductCatalog).where(
                ProductCatalog.name == prod_data["name"],
                ProductCatalog.is_builtin.is_(True),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Update existing
            for key, value in prod_data.items():
                setattr(existing, key, value)
        else:
            product = ProductCatalog(is_builtin=True, is_custom=False, **prod_data)
            db.add(product)
        count += 1

    await db.commit()
    logger.info(f"Seeded/refreshed {count} built-in products")
    return count
