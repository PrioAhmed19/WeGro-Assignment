from fastapi import HTTPException, status


ACCEPTED_VALUES = {
    "region": {"Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Rangpur", "Barisal", "Mymensingh"},
    "farm_type": {"Small", "Medium", "Large", "Commercial"},
    "crop_category": {"Cereal", "Vegetable", "Fruit", "Pulse", "Oilseed", "Cash Crop", "Spice"},
    "season": {"Spring", "Summer", "Autumn", "Winter"},
    "growing_season": {"Rabi", "Kharif", "Zaid", "Year-Round"},
    "market_type": {"Local", "Wholesale", "Export", "Retail", "Government Procurement"},
    "price_tier": {"Low", "Medium", "High", "Premium"},
    "quality_grade": {"A", "B", "C", "D"},
    "pesticide_residue": {"None", "Trace", "Low", "High"},
    "water_requirement": {"Low", "Medium", "High"},
    "year": {2022, 2023, 2024},
    "quarter": {1, 2, 3, 4},
    "metric": {"profit", "revenue", "yield"},
}


def validate_choice(name: str, value):
    if value is None:
        return
    if value not in ACCEPTED_VALUES[name]:
        accepted = sorted(ACCEPTED_VALUES[name])
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {name}: {value}. Accepted values: {accepted}",
        )


def validate_positive_limit(limit: int):
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid limit: must be a positive integer.",
        )
