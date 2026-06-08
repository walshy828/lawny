"""Soil test interpretation and amendment calculator.

Interprets nutrient levels and calculates lime/sulfur quantities
needed to correct pH based on lawn area and soil type.
"""

from typing import Optional

# Ideal ranges for turfgrass
IDEAL_PH = (6.0, 7.0)
IDEAL_ORGANIC_MATTER = (3.0, 5.0)

NUTRIENT_RANGES = {
    "phosphorus_ppm": {
        "very_low": (0, 15),
        "low": (15, 25),
        "medium": (25, 50),
        "high": (50, 100),
        "very_high": (100, 9999),
        "ideal": (25, 50),
        "unit": "ppm",
        "label": "Phosphorus (P)",
    },
    "potassium_ppm": {
        "very_low": (0, 75),
        "low": (75, 150),
        "medium": (150, 250),
        "high": (250, 400),
        "very_high": (400, 9999),
        "ideal": (150, 250),
        "unit": "ppm",
        "label": "Potassium (K)",
    },
    "calcium_ppm": {
        "low": (0, 500),
        "medium": (500, 1000),
        "high": (1000, 2000),
        "very_high": (2000, 9999),
        "ideal": (500, 1500),
        "unit": "ppm",
        "label": "Calcium (Ca)",
    },
    "magnesium_ppm": {
        "low": (0, 50),
        "medium": (50, 125),
        "high": (125, 250),
        "very_high": (250, 9999),
        "ideal": (50, 150),
        "unit": "ppm",
        "label": "Magnesium (Mg)",
    },
    "organic_matter_pct": {
        "very_low": (0, 1.5),
        "low": (1.5, 3.0),
        "medium": (3.0, 5.0),
        "high": (5.0, 8.0),
        "very_high": (8.0, 100),
        "ideal": (3.0, 5.0),
        "unit": "%",
        "label": "Organic Matter",
    },
}

STATUS_COLORS = {
    "very_low": "danger",
    "low": "warning",
    "medium": "success",
    "high": "info",
    "very_high": "warning",
    "ideal": "success",
}


def classify_ph(ph: float) -> dict:
    """Return status and recommendation for a given soil pH."""
    if ph < 5.0:
        return {"status": "very_low", "label": "Very Acidic", "color": "danger",
                "action": f"Soil is extremely acidic (pH {ph:.1f}). Heavy lime application needed."}
    if ph < 6.0:
        return {"status": "low", "label": "Acidic", "color": "warning",
                "action": f"Soil is acidic (pH {ph:.1f}). Lime application recommended to raise pH toward 6.5."}
    if ph <= 7.0:
        return {"status": "ideal", "label": "Ideal", "color": "success",
                "action": f"Soil pH is in the ideal range ({ph:.1f}). No adjustment needed."}
    if ph <= 7.5:
        return {"status": "high", "label": "Slightly Alkaline", "color": "info",
                "action": f"Soil is slightly alkaline (pH {ph:.1f}). Sulfur application may help if grass shows symptoms."}
    return {"status": "very_high", "label": "Very Alkaline", "color": "danger",
            "action": f"Soil is very alkaline (pH {ph:.1f}). Elemental sulfur application needed."}


def classify_nutrient(field: str, value: float) -> dict:
    """Return classification for a nutrient value."""
    meta = NUTRIENT_RANGES.get(field)
    if not meta:
        return {"status": "unknown", "label": "Unknown", "color": "secondary"}

    for status, (low, high) in meta.items():
        if status in ("ideal", "unit", "label"):
            continue
        if low <= value < high:
            color = STATUS_COLORS.get(status, "secondary")
            labels = {"very_low": "Very Low", "low": "Low", "medium": "Medium",
                      "high": "High", "very_high": "Very High"}
            return {"status": status, "label": labels.get(status, status), "color": color,
                    "value": value, "unit": meta["unit"], "field_label": meta["label"]}

    return {"status": "unknown", "label": "Unknown", "color": "secondary"}


def calculate_lime_needed(
    current_ph: float,
    target_ph: float,
    area_sqft: float,
    soil_type: str = "loam",
    buffer_ph: Optional[float] = None,
) -> dict:
    """Calculate lime needed to raise soil pH.

    Uses buffer pH (Penn State method) if available, otherwise uses rule-of-thumb.
    Returns amounts for both pelletized lime and ag lime.
    """
    if current_ph >= target_ph:
        return {"needed": False, "reason": f"pH is already {current_ph:.1f}, at or above target {target_ph:.1f}. No lime needed."}

    # Penn State buffer pH method — most accurate
    if buffer_ph and buffer_ph < 7.5:
        # ENP (Effective Neutralizing Power) method — approximate
        # lbs/1000 sqft = (target buffer pH - buffer pH) * soil_factor
        soil_factors = {"sandy": 10.0, "loam": 16.0, "clay": 22.0}
        factor = soil_factors.get(soil_type, 16.0)
        lbs_per_1k = (target_ph - buffer_ph) * factor
        method = "Penn State buffer pH method"
    else:
        # Rule of thumb: lbs pelletized lime to raise pH 1 unit per 1000 sqft
        # Accounts for different soil types
        lbs_per_unit_ph = {"sandy": 40, "loam": 65, "clay": 90}
        base = lbs_per_unit_ph.get(soil_type, 65)
        ph_gap = target_ph - current_ph
        lbs_per_1k = base * ph_gap
        method = "Rule-of-thumb estimate (for precision, use buffer pH method)"

    # Cap at 50 lbs/1000 sqft per application — never apply more than this at once
    lbs_per_1k = min(lbs_per_1k, 50.0)
    total_area_1k = area_sqft / 1000.0
    total_lbs = lbs_per_1k * total_area_1k

    # Pelletized lime is ~100% effective, ag lime ~50% — adjust for pelletized
    bags_50lb = total_lbs / 50.0

    note = None
    if total_lbs > (50 * total_area_1k):
        note = "Split into 2 applications, 30-60 days apart. Never apply more than 50 lbs/1000 sqft at once."

    return {
        "needed": True,
        "lbs_per_1k_sqft": round(lbs_per_1k, 1),
        "total_lbs": round(total_lbs, 0),
        "bags_50lb": round(bags_50lb, 1),
        "method": method,
        "product_recommendation": "Pelletized lime (fast-acting) or Jonathan Green MAG-I-CAL Plus for acidic soil",
        "application_note": note or "Apply evenly with a spreader. Water in after application. Takes 3-6 months to fully affect pH.",
        "current_ph": current_ph,
        "target_ph": target_ph,
    }


def calculate_sulfur_needed(
    current_ph: float,
    target_ph: float,
    area_sqft: float,
    soil_type: str = "loam",
) -> dict:
    """Calculate elemental sulfur needed to lower soil pH."""
    if current_ph <= target_ph:
        return {"needed": False, "reason": f"pH is already {current_ph:.1f}, at or below target {target_ph:.1f}. No sulfur needed."}

    # lbs elemental sulfur per 1000 sqft to lower pH 1 unit
    lbs_per_unit_ph = {"sandy": 10, "loam": 15, "clay": 20}
    base = lbs_per_unit_ph.get(soil_type, 15)
    ph_gap = current_ph - target_ph
    lbs_per_1k = base * ph_gap
    lbs_per_1k = min(lbs_per_1k, 10.0)  # never more than 10 lbs/1000 sqft at once

    total_area_1k = area_sqft / 1000.0
    total_lbs = lbs_per_1k * total_area_1k

    note = None
    if ph_gap > 0.5:
        note = "Large pH adjustment — split into 2-3 applications over 1-2 years. Large single applications can harm grass."

    return {
        "needed": True,
        "lbs_per_1k_sqft": round(lbs_per_1k, 1),
        "total_lbs": round(total_lbs, 0),
        "method": "Rule-of-thumb estimate",
        "product_recommendation": "Elemental sulfur (slow-acting, 6-12 months) or Jonathan Green MAG-I-CAL Plus for alkaline soil",
        "application_note": note or "Work into soil if possible. Best applied in fall or spring. Results take 6-12 months.",
        "current_ph": current_ph,
        "target_ph": target_ph,
    }


def interpret_soil_test(test: dict, area_sqft: float = 5000, soil_type: str = "loam") -> dict:
    """Full interpretation of a soil test with recommendations.

    Args:
        test: dict of soil test values (ph, phosphorus_ppm, etc.)
        area_sqft: total lawn area for amendment calculations
        soil_type: sandy, loam, or clay
    """
    result = {
        "ph_status": None,
        "nutrients": {},
        "amendments": [],
        "overall_score": None,
        "summary": [],
    }

    # pH interpretation
    if test.get("ph"):
        ph = test["ph"]
        result["ph_status"] = classify_ph(ph)

        if ph < 6.0:
            lime = calculate_lime_needed(ph, 6.5, area_sqft, soil_type, test.get("buffer_ph"))
            if lime["needed"]:
                result["amendments"].append({"type": "lime", "details": lime})
        elif ph > 7.2:
            sulfur = calculate_sulfur_needed(ph, 6.8, area_sqft, soil_type)
            if sulfur["needed"]:
                result["amendments"].append({"type": "sulfur", "details": sulfur})

    # Nutrient interpretation
    for field in ["phosphorus_ppm", "potassium_ppm", "calcium_ppm", "magnesium_ppm", "organic_matter_pct"]:
        val = test.get(field)
        if val is not None:
            classification = classify_nutrient(field, val)
            result["nutrients"][field] = classification

    # Build overall score (simple — based on how many are in ideal range)
    ideal_count = sum(
        1 for v in result["nutrients"].values()
        if v.get("status") in ("medium", "ideal")
    )
    total_nutrients = len(result["nutrients"])
    ph_ok = result["ph_status"] and result["ph_status"].get("status") == "ideal"

    if total_nutrients > 0 or result["ph_status"]:
        score_parts = [(1 if ph_ok else 0)] + [
            1 if v.get("status") in ("medium", "ideal") else 0
            for v in result["nutrients"].values()
        ]
        total = len(score_parts)
        result["overall_score"] = round((sum(score_parts) / total) * 10, 1) if total else None

    # Summary messages
    if result["ph_status"] and result["ph_status"]["status"] != "ideal":
        result["summary"].append(result["ph_status"]["action"])

    for field, nut in result["nutrients"].items():
        meta = NUTRIENT_RANGES.get(field, {})
        ideal_low, ideal_high = meta.get("ideal", (0, 9999))
        val = test.get(field, 0)
        label = meta.get("label", field)
        if nut["status"] in ("very_low", "low"):
            result["summary"].append(f"{label} is low ({val} {meta.get('unit', '')}) — deficiency may limit grass growth.")
        elif nut["status"] == "very_high":
            result["summary"].append(f"{label} is very high ({val} {meta.get('unit', '')}) — avoid adding more.")

    return result
