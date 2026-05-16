from typing import Optional

from fastapi import APIRouter, Query

from app.services.agriculture_report_service import agriculture_report_service
from app.utils.filter_validation import validate_choice, validate_positive_limit

router = APIRouter(tags=["Agriculture Reports"])


@router.get("/farms/summary", summary="Farm Summary")
async def farm_summary(
    region: Optional[str] = Query(None, description="Farm region"),
    farm_type: Optional[str] = Query(None, description="Small, Medium, Large, or Commercial"),
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    season: Optional[str] = Query(None, description="Spring, Summer, Autumn, or Winter"),
):
    validate_choice("region", region)
    validate_choice("farm_type", farm_type)
    validate_choice("year", year)
    validate_choice("season", season)
    return agriculture_report_service.farm_summary(region, farm_type, year, season)

@router.get("/farms/{farm_id}/performance", summary="Single Farm Performance")
async def farm_performance(
    farm_id: int,
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    crop_category: Optional[str] = Query(None, description="Crop category"),
    market_type: Optional[str] = Query(None, description="Market type"),
):
    validate_choice("year", year)
    validate_choice("crop_category", crop_category)
    validate_choice("market_type", market_type)
    return agriculture_report_service.farm_performance(farm_id, year, crop_category, market_type)


@router.get("/farms/top", summary="Top Farms Ranking")
async def top_farms(
    metric: str = Query("profit", description="profit, revenue, or yield"),
    region: Optional[str] = Query(None, description="Farm region"),
    farm_type: Optional[str] = Query(None, description="Small, Medium, Large, or Commercial"),
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    limit: int = Query(10, description="Positive integer result limit"),
):
    validate_choice("metric", metric)
    validate_choice("region", region)
    validate_choice("farm_type", farm_type)
    validate_choice("year", year)
    validate_positive_limit(limit)
    return agriculture_report_service.top_farms(metric, region, farm_type, year, limit)


@router.get("/farms/loss-analysis", summary="Loss Analysis")
async def loss_analysis(
    region: Optional[str] = Query(None, description="Farm region"),
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    season: Optional[str] = Query(None, description="Spring, Summer, Autumn, or Winter"),
    quality_grade: Optional[str] = Query(None, description="A, B, C, or D"),
    crop_category: Optional[str] = Query(None, description="Crop category"),
):
    validate_choice("region", region)
    validate_choice("year", year)
    validate_choice("season", season)
    validate_choice("quality_grade", quality_grade)
    validate_choice("crop_category", crop_category)
    return agriculture_report_service.loss_analysis(region, year, season, quality_grade, crop_category)




@router.get("/crops/yield-efficiency", summary="Crop Yield Efficiency")
async def crop_yield_efficiency(
    crop_category: Optional[str] = Query(None, description="Crop category"),
    season: Optional[str] = Query(None, description="Spring, Summer, Autumn, or Winter"),
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    region: Optional[str] = Query(None, description="Farm region"),
    water_requirement: Optional[str] = Query(None, description="Low, Medium, or High"),
):
    validate_choice("crop_category", crop_category)
    validate_choice("season", season)
    validate_choice("year", year)
    validate_choice("region", region)
    validate_choice("water_requirement", water_requirement)
    return agriculture_report_service.crop_yield_efficiency(crop_category, season, year, region, water_requirement)


@router.get("/crops/seasonal-trend", summary="Seasonal Revenue Trend")
async def seasonal_revenue_trend(
    crop_name: Optional[str] = Query(None, description="Crop name"),
    crop_category: Optional[str] = Query(None, description="Crop category"),
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    quarter: Optional[int] = Query(None, description="1, 2, 3, or 4"),
    market_type: Optional[str] = Query(None, description="Market type"),
):
    validate_choice("crop_category", crop_category)
    validate_choice("year", year)
    validate_choice("quarter", quarter)
    validate_choice("market_type", market_type)
    return agriculture_report_service.seasonal_revenue_trend(crop_name, crop_category, year, quarter, market_type)


@router.get("/markets/price-comparison", summary="Market Price Comparison")
async def market_price_comparison(
    market_type: Optional[str] = Query(None, description="Market type"),
    crop_category: Optional[str] = Query(None, description="Crop category"),
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    season: Optional[str] = Query(None, description="Spring, Summer, Autumn, or Winter"),
    price_tier: Optional[str] = Query(None, description="Low, Medium, High, or Premium"),
    district: Optional[str] = Query(None, description="Market district"),
):
    validate_choice("market_type", market_type)
    validate_choice("crop_category", crop_category)
    validate_choice("year", year)
    validate_choice("season", season)
    validate_choice("price_tier", price_tier)
    return agriculture_report_service.market_price_comparison(market_type, crop_category, year, season, price_tier, district)


@router.get("/crops/quality-breakdown", summary="Quality Grade Breakdown")
async def quality_breakdown(
    crop_id: Optional[int] = Query(None, description="Crop id"),
    crop_category: Optional[str] = Query(None, description="Crop category"),
    year: Optional[int] = Query(None, description="2022, 2023, or 2024"),
    region: Optional[str] = Query(None, description="Farm region"),
    market_type: Optional[str] = Query(None, description="Market type"),
    pesticide_residue: Optional[str] = Query(None, description="None, Trace, Low, or High"),
):
    validate_choice("crop_category", crop_category)
    validate_choice("year", year)
    validate_choice("region", region)
    validate_choice("market_type", market_type)
    validate_choice("pesticide_residue", pesticide_residue)
    return agriculture_report_service.quality_breakdown(crop_id, crop_category, year, region, market_type, pesticide_residue)
