"""Geo-aware seasonal pest, disease, and weed calendar.

Provides proactive alerts based on region, month, grass type, and weather conditions.
"""

from typing import Optional

SEASONAL_ALERTS = [
    # ── JAPANESE BEETLES ──────────────────────────────────
    {
        "id": "japanese-beetle",
        "name": "Japanese Beetle Season",
        "type": "pest",
        "regions": ["northeast", "midwest"],
        "months": [6, 7, 8],
        "grass_types": None,
        "severity": "moderate",
        "icon": "🐞",
        "title": "Japanese Beetle Adults Active",
        "description": "Adult Japanese beetles are feeding and laying eggs in lawns. Grub larvae will hatch mid-summer and damage roots through fall.",
        "risk_conditions": "Peak activity on warm (>80°F), sunny days. Heaviest feeding in June-July.",
        "preventive_action": "Apply GrubEx NOW — best before egg hatch (early June). One application lasts the season.",
        "curative_action": "For existing grub damage Aug-Sep: apply BioAdvanced 24hr Grub Killer Plus. Water thoroughly after.",
        "products": [
            {"name": "Scotts GrubEx Season-Long Grub Killer", "timing": "May-July, water in immediately", "type": "preventive"},
            {"name": "BioAdvanced 24Hr Grub Killer Plus", "timing": "August-September for active grubs", "type": "curative"},
        ],
        "watch_for": "Spongy patches that roll up like a rug, birds digging, brown patches that won't green up with water.",
    },
    # ── SPRING GRUB REEMERGENCE ───────────────────────────
    {
        "id": "grub-spring",
        "name": "Spring Grub Activity",
        "type": "pest",
        "regions": ["northeast", "midwest", "southeast"],
        "months": [3, 4, 5],
        "grass_types": None,
        "severity": "moderate",
        "icon": "🪱",
        "title": "Spring Grub Feeding",
        "description": "Overwintered grubs return to the root zone to feed before pupating. May cause irregular dead patches in early spring.",
        "risk_conditions": "Cool springs following heavy grub infestations the prior summer.",
        "preventive_action": "If grubs were a problem last year, apply GrubEx in late spring/early summer.",
        "curative_action": "For active spring grubs: apply Dylox (trichlorfon) for fast knockdown.",
        "products": [
            {"name": "Scotts GrubEx", "timing": "May-June as preventive", "type": "preventive"},
        ],
        "watch_for": "Patches that pull up easily like loose carpet. Skunks or raccoons digging at night.",
    },
    # ── BROWN PATCH ───────────────────────────────────────
    {
        "id": "brown-patch",
        "name": "Brown Patch Fungus Risk",
        "type": "disease",
        "regions": ["northeast", "southeast", "midwest"],
        "months": [6, 7, 8],
        "grass_types": ["tall_fescue", "kentucky_bluegrass", "perennial_ryegrass", "cool_mix", "st_augustine"],
        "severity": "high",
        "icon": "🍂",
        "title": "Brown Patch Disease Alert",
        "description": "Brown patch thrives when temperatures stay above 70°F at night with high humidity. Can devastate cool-season lawns in 24 hours.",
        "risk_conditions": "Night temps >70°F, humidity >90%, lawn watered in evenings.",
        "preventive_action": "Switch all watering to early morning (5-9am). Avoid over-fertilizing with nitrogen in summer.",
        "curative_action": "Apply Scotts DiseaseEx or BioAdvanced Fungus Control. Repeat every 14-28 days while conditions persist.",
        "products": [
            {"name": "Scotts DiseaseEx Lawn Fungicide", "timing": "At first symptoms, repeat every 14 days", "type": "curative"},
            {"name": "BioAdvanced Fungus Control for Lawns", "timing": "Preventive in high-risk periods", "type": "preventive"},
        ],
        "watch_for": "Circular brown patches 6in to several feet wide. Smoke ring (dark border) in early morning. Rapid spread.",
    },
    # ── DOLLAR SPOT ───────────────────────────────────────
    {
        "id": "dollar-spot",
        "name": "Dollar Spot Conditions",
        "type": "disease",
        "regions": ["northeast", "midwest", "southeast"],
        "months": [5, 6, 7, 8, 9],
        "grass_types": None,
        "severity": "moderate",
        "icon": "💰",
        "title": "Dollar Spot Risk",
        "description": "Dollar spot causes small, bleached spots in lawns with low nitrogen and drought stress, especially with heavy morning dew.",
        "risk_conditions": "Low soil nitrogen, drought stress, heavy morning dew, temps 60-80°F.",
        "preventive_action": "Maintain adequate nitrogen fertility. Water deeply but infrequently.",
        "curative_action": "Apply Spectracide Immunox fungicide and follow with a light nitrogen feeding.",
        "products": [
            {"name": "Spectracide Immunox Multi-Purpose Fungicide", "timing": "At first symptoms", "type": "curative"},
        ],
        "watch_for": "Small (1-3 inch) bleached/tan circular spots. White cobweb mycelium visible in early morning dew.",
    },
    # ── CRABGRASS PRE-EMERGENT WINDOW ─────────────────────
    {
        "id": "crabgrass-preemergent",
        "name": "Crabgrass Pre-Emergent Window",
        "type": "weed",
        "regions": ["northeast", "midwest", "southeast", "southwest", "transition"],
        "months": [3, 4, 5],
        "grass_types": None,
        "severity": "high",
        "icon": "🌿",
        "title": "Apply Crabgrass Pre-Emergent Now",
        "description": "Crabgrass germinates when soil temps reach 55°F. A 2-week window to apply pre-emergent before germination begins.",
        "risk_conditions": "Soil temp approaching 55°F — typically when forsythia blooms drop.",
        "preventive_action": "Apply crabgrass pre-emergent NOW. Do not aerate or dethatch after applying.",
        "curative_action": "If crabgrass is already visible: apply Ortho WeedBGon Crabgrass Killer on young plants.",
        "products": [
            {"name": "Scotts Halts Crabgrass Preventer", "timing": "Before soil temps reach 55°F", "type": "preventive"},
            {"name": "Ortho WeedBGon Crabgrass Killer", "timing": "Young plants (1-3 tillers)", "type": "curative"},
        ],
        "watch_for": "Light-green, wide-bladed grass clumping in hot/dry spots. Germinating in thin areas and bare spots.",
    },
    # ── CRABGRASS POST-EMERGENT WINDOW ────────────────────
    {
        "id": "crabgrass-curative",
        "name": "Crabgrass Post-Emergent Last Chance",
        "type": "weed",
        "regions": ["northeast", "midwest", "southeast", "transition"],
        "months": [6, 7],
        "grass_types": None,
        "severity": "moderate",
        "icon": "🌿",
        "title": "Last Window: Crabgrass Post-Emergent",
        "description": "Post-emergent crabgrass control is most effective on young plants. Once mature, crabgrass will die with first frost anyway.",
        "risk_conditions": "Thin areas from disease, drought, or a missed pre-emergent application.",
        "preventive_action": "Apply pre-emergent next spring. Overseed thin areas this fall.",
        "curative_action": "Apply Drive XLR8 (quinclorac) or Ortho WeedBGon Crabgrass Killer for young plants.",
        "products": [
            {"name": "Ortho WeedBGon Crabgrass Killer", "timing": "When plants are small (1-3 tillers)", "type": "curative"},
        ],
        "watch_for": "Light-green clumping grass growing faster than surrounding turf. Spreading from edges and thin spots.",
    },
    # ── FIRE ANTS ─────────────────────────────────────────
    {
        "id": "fire-ants",
        "name": "Fire Ant Activity",
        "type": "pest",
        "regions": ["southeast", "southwest"],
        "months": [3, 4, 5, 9, 10],
        "grass_types": None,
        "severity": "high",
        "icon": "🐜",
        "title": "Fire Ant Season",
        "description": "Fire ants are most active when temps are 70-90°F. Mounds can appear overnight and pose a serious sting risk.",
        "risk_conditions": "Warm soil, spring rains causing surface mound activity.",
        "preventive_action": "Apply broadcast granules (two-step method) across entire lawn — most effective approach.",
        "curative_action": "For individual mounds: use Ortho Orthene Fire Ant Killer (acephate) powder directly into mound.",
        "products": [
            {"name": "Ortho Fire Ant Killer Broadcast Granules", "timing": "Spring and fall, broadcast across lawn", "type": "preventive"},
            {"name": "Ortho Orthene Fire Ant Killer", "timing": "Individual mound treatment", "type": "curative"},
        ],
        "watch_for": "Dome-shaped mounds (no hole in center) 6-24 inches wide. Aggressive ants swarming when disturbed.",
    },
    # ── CHINCH BUGS ───────────────────────────────────────
    {
        "id": "chinch-bugs",
        "name": "Chinch Bug Risk",
        "type": "pest",
        "regions": ["southeast", "northeast"],
        "months": [6, 7, 8, 9],
        "grass_types": ["st_augustine", "zoysia", "bermuda", "kentucky_bluegrass"],
        "severity": "moderate",
        "icon": "🐛",
        "title": "Chinch Bug Alert",
        "description": "Chinch bugs suck sap from grass stems, causing yellow then brown patches that spread in hot, dry weather — often mistaken for drought stress.",
        "risk_conditions": "Hot, dry summers. Heavy thatch. Sunny, south-facing areas.",
        "preventive_action": "Maintain proper moisture to reduce stress. Dethatch to remove habitat.",
        "curative_action": "Apply bifenthrin-based insecticide and water in thoroughly.",
        "products": [
            {"name": "BioAdvanced Complete Insect Killer for Soil & Turf", "timing": "When active, water in well", "type": "curative"},
        ],
        "watch_for": "Yellow/brown patches in hot spots that don't green up with water. Tiny black/red insects at the turf line.",
    },
    # ── ARMYWORMS ─────────────────────────────────────────
    {
        "id": "armyworms",
        "name": "Fall Armyworm Alert",
        "type": "pest",
        "regions": ["southeast", "midwest", "northeast"],
        "months": [8, 9, 10],
        "grass_types": None,
        "severity": "high",
        "icon": "🐛",
        "title": "Fall Armyworm Migration",
        "description": "Fall armyworms can devastate a lawn in 24-48 hours. They travel in large groups and move lawn to lawn. Act immediately.",
        "risk_conditions": "Late summer/fall. Often arrives after nearby crop harvest.",
        "preventive_action": "Inspect lawn regularly in fall. Do soapy water drench test (1oz soap/gallon) to check.",
        "curative_action": "Apply bifenthrin or spinosad-based product immediately. Speed is critical.",
        "products": [
            {"name": "Ortho Bug B Gon Insect Killer for Lawns", "timing": "Immediately at first detection", "type": "curative"},
            {"name": "Spectracide Triazicide Insect Killer", "timing": "Immediate application, water lightly", "type": "curative"},
        ],
        "watch_for": "Rapid browning of entire lawn. Starlings or birds clustered and feeding intensely. Small caterpillars visible at dusk.",
    },
    # ── MOSS ──────────────────────────────────────────────
    {
        "id": "moss-season",
        "name": "Moss Growth Conditions",
        "type": "weed",
        "regions": ["northwest", "northeast"],
        "months": [3, 4, 9, 10, 11],
        "grass_types": None,
        "severity": "moderate",
        "icon": "🟢",
        "title": "Moss Growth Season",
        "description": "Moss thrives in cool, wet, shaded conditions with low pH and compacted soil. It's a symptom of poor growing conditions, not just a weed to kill.",
        "risk_conditions": "pH <6.0, shaded areas, poor drainage, compaction, low fertility.",
        "preventive_action": "Test soil pH — apply lime if below 6.0. Aerate compacted areas. Improve drainage.",
        "curative_action": "Apply Scotts MossEx or iron sulfate. Follow up by addressing root causes or moss returns.",
        "products": [
            {"name": "Scotts MossEx 3-in-1", "timing": "Spring or fall", "type": "curative"},
            {"name": "Jonathan Green MAG-I-CAL Plus", "timing": "After moss removal to correct pH", "type": "soil_amendment"},
        ],
        "watch_for": "Low-lying green/black mats in shaded or wet areas. Moss replacing thinning grass.",
    },
    # ── CLOVER ────────────────────────────────────────────
    {
        "id": "clover-pressure",
        "name": "Clover Pressure Season",
        "type": "weed",
        "regions": ["northeast", "midwest", "southeast", "transition"],
        "months": [4, 5, 6, 9, 10],
        "grass_types": None,
        "severity": "low",
        "icon": "☘️",
        "title": "Clover — Nitrogen Deficiency Signal",
        "description": "Clover thrives in low-nitrogen soils. Heavy clover invasion is a signal that your lawn needs nitrogen fertilization.",
        "risk_conditions": "Low soil nitrogen, thin grass stand, pH 6.0-7.0.",
        "preventive_action": "Increase nitrogen with a slow-release fertilizer. Dense grass shades out clover naturally.",
        "curative_action": "Apply a three-way herbicide with 2,4-D + MCPP + Dicamba. Do not mow 3 days before or after.",
        "products": [
            {"name": "Ortho WeedBGon Lawn Weed Killer", "timing": "Spring or fall when temps 60-85°F", "type": "curative"},
        ],
        "watch_for": "White flowers attracting bees. Trifoliate low-growing mats spreading from thin areas.",
    },
    # ── NUTSEDGE ──────────────────────────────────────────
    {
        "id": "nutsedge",
        "name": "Nutsedge (Nutgrass) Season",
        "type": "weed",
        "regions": ["northeast", "midwest", "southeast", "transition", "southwest"],
        "months": [6, 7, 8],
        "grass_types": None,
        "severity": "high",
        "icon": "🌾",
        "title": "Nutsedge Active",
        "description": "Nutsedge is a sedge, not grass — most herbicides don't work. It thrives in wet, poorly drained areas and spreads via underground tubers.",
        "risk_conditions": "Overwatered lawns, poor drainage, summer heat.",
        "preventive_action": "Improve drainage. Avoid overwatering. Do not leave tubers in soil when pulling by hand.",
        "curative_action": "Use SedgeHammer (halosulfuron) or Ortho Nutsedge Killer. May need 2+ applications.",
        "products": [
            {"name": "Ortho Nutsedge Killer for Lawns", "timing": "Summer when actively growing", "type": "curative"},
        ],
        "watch_for": "Fast-growing light-green plants taller than surrounding grass after mowing. Triangular stem cross-section.",
    },
    # ── SNOW MOLD ─────────────────────────────────────────
    {
        "id": "snow-mold",
        "name": "Snow Mold Emergence",
        "type": "disease",
        "regions": ["northeast", "midwest", "northwest"],
        "months": [2, 3, 4],
        "grass_types": ["kentucky_bluegrass", "tall_fescue", "perennial_ryegrass", "cool_mix"],
        "severity": "moderate",
        "icon": "❄️",
        "title": "Snow Mold — Inspect After Snowmelt",
        "description": "Pink and gray snow mold appear after snow melts. Pink snow mold is more serious and can kill grass crowns.",
        "risk_conditions": "Long snow cover, dense matted grass, high nitrogen applied late fall.",
        "preventive_action": "Final fall mow at lower height. Apply last fertilizer 6+ weeks before freeze.",
        "curative_action": "Rake matted areas to improve air circulation. Overseed severely affected spots in spring.",
        "products": [
            {"name": "Scotts DiseaseEx", "timing": "Late fall as preventive in snow-prone areas", "type": "preventive"},
        ],
        "watch_for": "Circular straw-colored patches 3-12 inches wide when snow melts. Pink or gray cottony growth on leaf blades.",
    },
    # ── CRANE FLY ─────────────────────────────────────────
    {
        "id": "crane-fly",
        "name": "Crane Fly Larvae (Pacific NW)",
        "type": "pest",
        "regions": ["northwest"],
        "months": [9, 10, 2, 3, 4],
        "grass_types": None,
        "severity": "moderate",
        "icon": "🦟",
        "title": "Crane Fly Larvae Activity",
        "description": "European crane fly larvae feed on grass roots and crowns. Adults fly in September, larvae feed through fall and spring.",
        "risk_conditions": "Wet Pacific Northwest winters. Peak damage February-April.",
        "preventive_action": "Apply imidacloprid in late September when eggs are newly hatched.",
        "curative_action": "Apply BioAdvanced Lawn Insect Killer when larvae are active (Feb-April). Water in well.",
        "products": [
            {"name": "BioAdvanced Lawn Insect Killer Granules", "timing": "September or Feb-April", "type": "curative"},
        ],
        "watch_for": "Thin, bare patches in spring. Small gray-brown legless larvae at soil surface. Birds pecking heavily.",
    },
    # ── RED THREAD ────────────────────────────────────────
    {
        "id": "red-thread",
        "name": "Red Thread Disease",
        "type": "disease",
        "regions": ["northwest", "northeast"],
        "months": [4, 5, 6, 9, 10],
        "grass_types": ["perennial_ryegrass", "tall_fescue", "kentucky_bluegrass", "fine_fescue", "cool_mix"],
        "severity": "low",
        "icon": "🔴",
        "title": "Red Thread Conditions",
        "description": "Red thread causes pink/red patches in cool, wet weather on nitrogen-deficient lawns. Rarely fatal but very unsightly.",
        "risk_conditions": "Cool (65-75°F), wet weather. Low nitrogen. Common in Pacific NW spring and fall.",
        "preventive_action": "Apply a nitrogen-rich fertilizer — almost always indicates nitrogen deficiency.",
        "curative_action": "A quick nitrogen application usually resolves red thread. Fungicide rarely needed.",
        "products": [
            {"name": "Any balanced fertilizer with nitrogen", "timing": "Spring, when disease appears", "type": "curative"},
        ],
        "watch_for": "Irregular pink-red patches 4-8 inches. Red needle-like structures on grass tips.",
    },
    # ── LARGE PATCH ───────────────────────────────────────
    {
        "id": "large-patch",
        "name": "Large Patch Disease (Warm-Season)",
        "type": "disease",
        "regions": ["southeast", "transition"],
        "months": [3, 4, 5, 10, 11],
        "grass_types": ["zoysia", "st_augustine", "centipede", "bermuda", "warm_mix"],
        "severity": "high",
        "icon": "🍂",
        "title": "Large Patch Disease Alert",
        "description": "Large patch attacks warm-season grasses during spring green-up and fall pre-dormancy. Can cause large circular dead areas.",
        "risk_conditions": "Temps 60-80°F with extended leaf wetness. High nitrogen applied too early in spring or late fall.",
        "preventive_action": "Hold nitrogen until warm-season grass is 50%+ green. Avoid late fall nitrogen.",
        "curative_action": "Apply azoxystrobin or thiophanate-methyl fungicide.",
        "products": [
            {"name": "Scotts DiseaseEx Lawn Fungicide", "timing": "Fall preventive, spring at first symptoms", "type": "curative"},
        ],
        "watch_for": "Large (3-20+ foot) circular orange/brown patches. Orange ring at the expanding edge.",
    },
    # ── MOLE CRICKETS ─────────────────────────────────────
    {
        "id": "mole-crickets",
        "name": "Mole Cricket Season",
        "type": "pest",
        "regions": ["southeast"],
        "months": [3, 4, 5, 6, 8, 9],
        "grass_types": ["bermuda", "bahia", "st_augustine"],
        "severity": "high",
        "icon": "🦗",
        "title": "Mole Cricket Activity",
        "description": "Mole crickets tunnel through soil and sever grass roots. Adults are flying and laying eggs now.",
        "risk_conditions": "Sandy soils, warm nights in spring (flying adults), summer heat (young nymphs feeding).",
        "preventive_action": "Apply preventive insecticide in June-July when nymphs are young and most susceptible.",
        "curative_action": "Mole cricket baits work best in the evening after irrigation.",
        "products": [
            {"name": "Spectracide Mole Cricket Bait", "timing": "Evening after irrigation, May-July", "type": "curative"},
        ],
        "watch_for": "Spongy, tunneled soil surface. Dying strips of grass. Do soapy water flush test.",
    },
    # ── OVERSEEDING WINDOW ────────────────────────────────
    {
        "id": "overseeding-fall",
        "name": "Prime Overseeding Window",
        "type": "cultural",
        "regions": ["northeast", "midwest", "transition"],
        "months": [8, 9, 10],
        "grass_types": ["kentucky_bluegrass", "tall_fescue", "perennial_ryegrass", "fine_fescue", "cool_mix"],
        "severity": "info",
        "icon": "🌱",
        "title": "Best Time to Overseed",
        "description": "The late summer/early fall 6-week window is the best time to overseed cool-season lawns. Warm soil + cool air = perfect germination.",
        "risk_conditions": "Any thin areas, bare spots, or disease damage should be reseeded now.",
        "preventive_action": "Do NOT use a pre-emergent if overseeding. Aerate first. Keep seed moist for 2-3 weeks.",
        "curative_action": "Overseed bare patches with species-matching seed. Apply starter fertilizer (high phosphorus).",
        "products": [
            {"name": "Jonathan Green Black Beauty Grass Seed", "timing": "Late August through September", "type": "seed"},
            {"name": "Scotts Starter Fertilizer for New Grass", "timing": "At time of seeding", "type": "fertilizer"},
        ],
        "watch_for": "Thin areas from summer stress, disease, or grub feeding. Target coverage below 70% of ideal stand.",
    },
    # ── FALL FERTILIZER ───────────────────────────────────
    {
        "id": "fall-fertilizer",
        "name": "Fall Fertilizer — Most Important Application",
        "type": "cultural",
        "regions": ["northeast", "midwest"],
        "months": [9, 10, 11],
        "grass_types": ["kentucky_bluegrass", "tall_fescue", "perennial_ryegrass", "fine_fescue", "cool_mix"],
        "severity": "info",
        "icon": "🍂",
        "title": "Apply Fall Winterizer Now",
        "description": "Fall fertilization is the single most impactful thing you can do for a cool-season lawn. Roots store nutrients for next spring's green-up.",
        "risk_conditions": "Best when soil temps drop below 60°F but before hard freeze.",
        "preventive_action": "Apply high-nitrogen winterizer between Labor Day and mid-October. Do not skip this step.",
        "curative_action": "Even if lawn is thin or damaged, fall fertilizer helps root development through winter.",
        "products": [
            {"name": "Scotts Turf Builder WinterGuard Fall Lawn Food", "timing": "September-October", "type": "fertilizer"},
            {"name": "Jonathan Green Winter Survival Fall Lawn Fertilizer", "timing": "September-October", "type": "fertilizer"},
        ],
        "watch_for": "Thin lawns and yellow/stressed areas heading into fall — give them one last feeding.",
    },
    # ── SPRING DEAD SPOT ──────────────────────────────────
    {
        "id": "spring-dead-spot",
        "name": "Spring Dead Spot (Bermuda)",
        "type": "disease",
        "regions": ["transition", "southeast", "southwest"],
        "months": [3, 4, 5],
        "grass_types": ["bermuda"],
        "severity": "high",
        "icon": "⚪",
        "title": "Spring Dead Spot on Bermuda",
        "description": "Circular dead patches in bermudagrass that fail to green up in spring. Caused by soilborne fungi active during winter dormancy.",
        "risk_conditions": "Stressed bermuda, excessive thatch, acidic soil, cold winter.",
        "preventive_action": "Apply preventive fungicide in FALL before dormancy. Manage thatch. Maintain pH 6.0-6.5.",
        "curative_action": "Existing patches won't respond to spring fungicide. Renovate damaged patches by plugging or sodding.",
        "products": [
            {"name": "Scotts DiseaseEx", "timing": "Fall (September-October) as preventive", "type": "preventive"},
        ],
        "watch_for": "Circular bleached/dead patches 1-3 feet wide that don't green up when surrounding bermuda does.",
    },
]


def get_region_for_coords(lat: float, lon: float) -> list[str]:
    """Determine climate region(s) from lat/lon — simplified geographic approximation."""
    regions = []

    if 42 <= lat <= 49 and -124 <= lon <= -116:
        regions.append("northwest")
    elif 25 <= lat <= 42 and lon <= -96:
        regions.append("southwest")
    elif lat <= 36 and lon >= -97:
        regions.append("southeast")
    elif 35 <= lat <= 40 and lon >= -97:
        regions.append("transition")
        if lon >= -85:
            regions.append("northeast")
    elif lat >= 37 and -104 <= lon <= -82:
        regions.append("midwest")
    elif lat >= 36 and lon >= -82:
        regions.append("northeast")

    return regions or ["northeast", "midwest"]


def get_active_alerts(
    month: int,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    grass_type: Optional[str] = None,
    regions: Optional[list[str]] = None,
) -> list[dict]:
    """Return alerts active for the given month, location, and grass type."""
    if regions is None:
        regions = get_region_for_coords(lat, lon) if (lat and lon) else ["northeast", "midwest"]

    active = []
    for alert in SEASONAL_ALERTS:
        if month not in alert["months"]:
            continue
        alert_regions = alert.get("regions") or []
        if alert_regions and not any(r in alert_regions for r in regions):
            continue
        alert_grass = alert.get("grass_types")
        if alert_grass and grass_type and grass_type not in alert_grass:
            continue
        active.append(alert)

    # Sort: high > moderate > low > info
    order = {"high": 0, "moderate": 1, "low": 2, "info": 3}
    active.sort(key=lambda a: order.get(a.get("severity", "info"), 3))
    return active
