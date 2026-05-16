from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
from fastapi import HTTPException, status

from app.db.database import get_engine


class AgricultureReportService:
    """Loads agriculture data and produces pandas-backed report payloads."""

    VIEW_NAME = "vw_harvest_full"

    COLUMN_ALIASES = {
        "farm_id": ["farm_id"],
        "farm_name": ["farm_name", "name"],
        "owner": ["owner", "owner_name", "farm_owner"],
        "region": ["region"],
        "farm_type": ["farm_type", "size_category"],
        "crop_id": ["crop_id"],
        "crop_name": ["crop_name"],
        "crop_category": ["crop_category", "category"],
        "season": ["season"],
        "growing_season": ["growing_season"],
        "year": ["year", "harvest_year", "date_year"],
        "quarter": ["quarter"],
        "market_name": ["market_name"],
        "market_type": ["market_type"],
        "district": ["district", "market_district"],
        "price_tier": ["price_tier"],
        "quality_grade": ["quality_grade"],
        "pesticide_residue": ["pesticide_residue"],
        "water_requirement": ["water_requirement"],
        "quantity_sold_ton": ["quantity_sold_ton", "sold_quantity_ton", "total_quantity_sold_ton"],
        "harvested_ton": ["harvested_ton", "quantity_harvested_ton", "harvest_quantity_ton", "total_harvested_ton"],
        "lost_ton": ["lost_ton", "quantity_lost_ton", "loss_quantity_ton", "post_harvest_loss_ton", "total_lost_ton"],
        "loss_pct": ["loss_pct", "loss_percentage", "post_harvest_loss_pct", "avg_loss_pct"],
        "revenue_bdt": ["revenue_bdt", "total_revenue_bdt"],
        "cost_bdt": ["cost_bdt", "total_cost_bdt", "production_cost_bdt", "input_cost_bdt"],
        "net_profit_bdt": ["net_profit_bdt", "profit_bdt"],
        "area_planted_ha": ["area_planted_ha", "planted_area_ha", "total_area_planted_ha"],
        "yield_benchmark_ton_per_ha": [
            "yield_benchmark_ton_per_ha",
            "avg_yield_benchmark_ton_per_ha",
            "national_avg_yield_ton_per_ha",
            "national_benchmark_yield_ton_per_ha",
        ],
        "price_per_ton_bdt": ["price_per_ton_bdt", "avg_price_per_ton_bdt", "selling_price_per_ton_bdt"],
    }

    def __init__(self):
        self.engine = get_engine()

    def _load_harvest_data(self) -> pd.DataFrame:
        query = """
            SELECT
                h.harvest_id,
                h.farm_id,
                h.crop_id,
                f.farm_name,
                f.owner_name,
                f.region,
                f.district AS farm_district,
                f.farm_type,
                f.total_area_ha,
                c.crop_name,
                c.crop_category,
                c.growing_season,
                c.avg_yield_ton_per_ha AS yield_benchmark_ton_per_ha,
                c.water_requirement,
                d.full_date,
                d.month_name,
                d.quarter,
                d.year,
                d.season,
                s.supply_name,
                s.supply_type,
                s.is_organic,
                m.market_name,
                m.market_type,
                m.price_tier,
                m.district,
                m.location AS market_location,
                h.area_planted_ha,
                h.quantity_harvested_ton,
                h.quantity_sold_ton,
                h.quantity_lost_ton,
                h.price_per_ton_bdt,
                h.revenue_bdt,
                h.input_cost_bdt,
                h.net_profit_bdt,
                h.quality_grade,
                h.moisture_pct,
                h.pesticide_residue,
                (h.quantity_lost_ton / NULLIF(h.quantity_harvested_ton, 0)) * 100 AS loss_pct
            FROM fact_harvest_sales h
            JOIN dim_farm f ON h.farm_id = f.farm_id
            JOIN dim_crop c ON h.crop_id = c.crop_id
            JOIN dim_date d ON h.date_id = d.date_id
            JOIN dim_input_supply s ON h.supply_id = s.supply_id
            JOIN dim_market m ON h.market_id = m.market_id
        """
        return pd.read_sql(query, self.engine)

    def _column(self, df: pd.DataFrame, canonical: str, required: bool = True) -> Optional[str]:
        for candidate in self.COLUMN_ALIASES.get(canonical, [canonical]):
            if candidate in df.columns:
                return candidate
        if required:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Required database column for '{canonical}' was not found in {self.VIEW_NAME}.",
            )
        return None

    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        filtered = df.copy()
        for canonical, value in filters.items():
            if value is None:
                continue
            column = self._column(filtered, canonical, required=False)
            if column is None:
                continue
            filtered = filtered[filtered[column] == value]
        return filtered

    def _filters_applied(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in filters.items() if value is not None}

    def _records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        normalized = df.where(pd.notnull(df), None)
        return normalized.to_dict(orient="records")

    def _round(self, value: Any, digits: int = 2) -> float:
        if pd.isna(value):
            return 0.0
        return round(float(value), digits)

    def farm_summary(
        self,
        region: Optional[str] = None,
        farm_type: Optional[str] = None,
        year: Optional[int] = None,
        season: Optional[str] = None,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        filters = {"region": region, "farm_type": farm_type, "year": year, "season": season}
        df = self._apply_filters(df, filters)

        farm_name = self._column(df, "farm_name")
        region_col = self._column(df, "region")
        farm_type_col = self._column(df, "farm_type")
        revenue = self._column(df, "revenue_bdt")
        cost = self._column(df, "cost_bdt")
        profit = self._column(df, "net_profit_bdt")
        loss_pct = self._column(df, "loss_pct")

        grouped = (
            df.groupby([farm_name, region_col, farm_type_col], dropna=False)
            .agg(
                total_revenue_bdt=(revenue, "sum"),
                total_cost_bdt=(cost, "sum"),
                net_profit_bdt=(profit, "sum"),
                avg_loss_pct=(loss_pct, "mean"),
            )
            .reset_index()
            .rename(columns={farm_name: "farm_name", region_col: "region", farm_type_col: "farm_type"})
        )
        grouped["avg_loss_pct"] = grouped["avg_loss_pct"].round(2)

        return {
            "total_farms": int(grouped["farm_name"].nunique()),
            "filters_applied": self._filters_applied(filters),
            "data": self._records(grouped),
        }

    def farm_performance(
        self,
        farm_id: int,
        year: Optional[int] = None,
        crop_category: Optional[str] = None,
        market_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        farm_id_col = self._column(df, "farm_id")
        df = df[df[farm_id_col] == farm_id]
        if df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Farm id {farm_id} was not found.")

        filters = {"year": year, "crop_category": crop_category, "market_type": market_type}
        filtered = self._apply_filters(df, filters)

        crop_name = self._column(filtered, "crop_name")
        year_col = self._column(filtered, "year")
        market_type_col = self._column(filtered, "market_type")
        quantity = self._column(filtered, "quantity_sold_ton")
        revenue = self._column(filtered, "revenue_bdt")
        profit = self._column(filtered, "net_profit_bdt")
        quality = self._column(filtered, "quality_grade")

        grouped = (
            filtered.groupby([crop_name, year_col, market_type_col, quality], dropna=False)
            .agg(quantity_sold_ton=(quantity, "sum"), revenue_bdt=(revenue, "sum"), net_profit_bdt=(profit, "sum"))
            .reset_index()
            .rename(
                columns={
                    crop_name: "crop_name",
                    year_col: "year",
                    market_type_col: "market_type",
                    quality: "quality_grade",
                }
            )
        )

        first = df.iloc[0]
        return {
            "farm_id": farm_id,
            "farm_name": first.get(self._column(df, "farm_name")),
            "owner": first.get(self._column(df, "owner")),
            "region": first.get(self._column(df, "region")),
            "filters_applied": self._filters_applied(filters),
            "performance": self._records(grouped),
        }

    def top_farms(
        self,
        metric: str = "profit",
        region: Optional[str] = None,
        farm_type: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        filters = {"region": region, "farm_type": farm_type, "year": year}
        df = self._apply_filters(df, filters)

        farm_name = self._column(df, "farm_name")
        region_col = self._column(df, "region")
        farm_type_col = self._column(df, "farm_type")
        revenue = self._column(df, "revenue_bdt")
        profit = self._column(df, "net_profit_bdt")
        quantity = self._column(df, "harvested_ton")
        area = self._column(df, "area_planted_ha")

        grouped = (
            df.groupby([farm_name, region_col, farm_type_col], dropna=False)
            .agg(
                net_profit_bdt=(profit, "sum"),
                total_revenue_bdt=(revenue, "sum"),
                total_harvested_ton=(quantity, "sum"),
                total_area_planted_ha=(area, "sum"),
            )
            .reset_index()
            .rename(columns={farm_name: "farm_name", region_col: "region", farm_type_col: "farm_type"})
        )
        grouped["yield_efficiency"] = grouped.apply(
            lambda row: self._round(row["total_harvested_ton"] / row["total_area_planted_ha"])
            if row["total_area_planted_ha"]
            else 0,
            axis=1,
        )

        sort_column = {"profit": "net_profit_bdt", "revenue": "total_revenue_bdt", "yield": "yield_efficiency"}[metric]
        grouped = grouped.sort_values(sort_column, ascending=False).head(limit).reset_index(drop=True)
        grouped.insert(0, "rank", grouped.index + 1)

        applied = self._filters_applied(filters)
        applied["limit"] = limit
        return {"metric": metric, "filters_applied": applied, "rankings": self._records(grouped)}

    def loss_analysis(
        self,
        region: Optional[str] = None,
        year: Optional[int] = None,
        season: Optional[str] = None,
        quality_grade: Optional[str] = None,
        crop_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        filters = {
            "region": region,
            "year": year,
            "season": season,
            "quality_grade": quality_grade,
            "crop_category": crop_category,
        }
        df = self._apply_filters(df, filters)

        harvested = self._column(df, "harvested_ton")
        lost = self._column(df, "lost_ton")
        region_col = self._column(df, "region")
        crop_category_col = self._column(df, "crop_category")
        quality = self._column(df, "quality_grade")
        pesticide = self._column(df, "pesticide_residue")

        grouped = (
            df.groupby([region_col, crop_category_col, quality, pesticide], dropna=False)
            .agg(total_harvested_ton=(harvested, "sum"), total_lost_ton=(lost, "sum"))
            .reset_index()
            .rename(
                columns={
                    region_col: "region",
                    crop_category_col: "crop_category",
                    quality: "quality_grade",
                    pesticide: "pesticide_residue",
                }
            )
        )
        grouped["loss_pct"] = grouped.apply(
            lambda row: self._round((row["total_lost_ton"] / row["total_harvested_ton"]) * 100)
            if row["total_harvested_ton"]
            else 0,
            axis=1,
        )
        grouped = grouped[["region", "crop_category", "quality_grade", "total_lost_ton", "loss_pct", "pesticide_residue"]]

        total_harvested = df[harvested].sum()
        total_lost = df[lost].sum()
        return {
            "filters_applied": self._filters_applied(filters),
            "summary": {
                "total_harvested_ton": self._round(total_harvested),
                "total_lost_ton": self._round(total_lost),
                "overall_loss_pct": self._round((total_lost / total_harvested) * 100) if total_harvested else 0,
            },
            "breakdown": self._records(grouped),
        }

    def crop_yield_efficiency(
        self,
        crop_category: Optional[str] = None,
        season: Optional[str] = None,
        year: Optional[int] = None,
        region: Optional[str] = None,
        water_requirement: Optional[str] = None,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        filters = {
            "crop_category": crop_category,
            "season": season,
            "year": year,
            "region": region,
            "water_requirement": water_requirement,
        }
        df = self._apply_filters(df, filters)

        crop_name = self._column(df, "crop_name")
        crop_category_col = self._column(df, "crop_category")
        benchmark = self._column(df, "yield_benchmark_ton_per_ha")
        quantity = self._column(df, "harvested_ton")
        area = self._column(df, "area_planted_ha")
        season_col = self._column(df, "growing_season", required=False) or self._column(df, "season")

        grouped = (
            df.groupby([crop_name, crop_category_col, season_col], dropna=False)
            .agg(
                avg_yield_benchmark_ton_per_ha=(benchmark, "mean"),
                total_harvested_ton=(quantity, "sum"),
                total_area_planted_ha=(area, "sum"),
            )
            .reset_index()
            .rename(columns={crop_name: "crop_name", crop_category_col: "crop_category", season_col: "season"})
        )
        grouped["actual_avg_yield_ton_per_ha"] = grouped.apply(
            lambda row: self._round(row["total_harvested_ton"] / row["total_area_planted_ha"])
            if row["total_area_planted_ha"]
            else 0,
            axis=1,
        )
        grouped["efficiency_pct"] = grouped.apply(
            lambda row: self._round(
                (row["actual_avg_yield_ton_per_ha"] / row["avg_yield_benchmark_ton_per_ha"]) * 100
            )
            if row["avg_yield_benchmark_ton_per_ha"]
            else 0,
            axis=1,
        )
        grouped["avg_yield_benchmark_ton_per_ha"] = grouped["avg_yield_benchmark_ton_per_ha"].round(2)
        grouped = grouped[
            [
                "crop_name",
                "crop_category",
                "avg_yield_benchmark_ton_per_ha",
                "actual_avg_yield_ton_per_ha",
                "efficiency_pct",
                "total_area_planted_ha",
                "season",
            ]
        ]
        return {"filters_applied": self._filters_applied(filters), "data": self._records(grouped)}

    def seasonal_revenue_trend(
        self,
        crop_name: Optional[str] = None,
        crop_category: Optional[str] = None,
        year: Optional[int] = None,
        quarter: Optional[int] = None,
        market_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        filters = {
            "crop_name": crop_name,
            "crop_category": crop_category,
            "year": year,
            "quarter": quarter,
            "market_type": market_type,
        }
        df = self._apply_filters(df, filters)

        crop_name_col = self._column(df, "crop_name")
        year_col = self._column(df, "year")
        quarter_col = self._column(df, "quarter")
        season_col = self._column(df, "season")
        quantity = self._column(df, "quantity_sold_ton")
        revenue = self._column(df, "revenue_bdt")

        grouped = (
            df.groupby([crop_name_col, year_col, quarter_col, season_col], dropna=False)
            .agg(
                total_quantity_sold_ton=(quantity, "sum"),
                total_revenue_bdt=(revenue, "sum"),
                num_harvests=(revenue, "count"),
            )
            .reset_index()
            .rename(
                columns={
                    crop_name_col: "crop_name",
                    year_col: "year",
                    quarter_col: "quarter",
                    season_col: "season",
                }
            )
        )
        grouped["avg_price_per_ton_bdt"] = grouped.apply(
            lambda row: self._round(row["total_revenue_bdt"] / row["total_quantity_sold_ton"])
            if row["total_quantity_sold_ton"]
            else 0,
            axis=1,
        )
        grouped = grouped.sort_values(["year", "quarter", "crop_name"])
        return {"filters_applied": self._filters_applied(filters), "trend": self._records(grouped)}

    def market_price_comparison(
        self,
        market_type: Optional[str] = None,
        crop_category: Optional[str] = None,
        year: Optional[int] = None,
        season: Optional[str] = None,
        price_tier: Optional[str] = None,
        district: Optional[str] = None,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        filters = {
            "market_type": market_type,
            "crop_category": crop_category,
            "year": year,
            "season": season,
            "price_tier": price_tier,
            "district": district,
        }
        df = self._apply_filters(df, filters)

        market_name = self._column(df, "market_name")
        market_type_col = self._column(df, "market_type")
        price_tier_col = self._column(df, "price_tier")
        district_col = self._column(df, "district")
        crop_name = self._column(df, "crop_name")
        quantity = self._column(df, "quantity_sold_ton")
        revenue = self._column(df, "revenue_bdt")

        grouped = (
            df.groupby([market_name, market_type_col, price_tier_col, district_col, crop_name], dropna=False)
            .agg(total_quantity_sold_ton=(quantity, "sum"), total_revenue_bdt=(revenue, "sum"))
            .reset_index()
            .rename(
                columns={
                    market_name: "market_name",
                    market_type_col: "market_type",
                    price_tier_col: "price_tier",
                    district_col: "district",
                    crop_name: "crop_name",
                }
            )
        )
        grouped["avg_price_per_ton_bdt"] = grouped.apply(
            lambda row: self._round(row["total_revenue_bdt"] / row["total_quantity_sold_ton"])
            if row["total_quantity_sold_ton"]
            else 0,
            axis=1,
        )
        grouped = grouped[
            [
                "market_name",
                "market_type",
                "price_tier",
                "district",
                "crop_name",
                "avg_price_per_ton_bdt",
                "total_quantity_sold_ton",
                "total_revenue_bdt",
            ]
        ]
        return {"filters_applied": self._filters_applied(filters), "comparison": self._records(grouped)}

    def quality_breakdown(
        self,
        crop_id: Optional[int] = None,
        crop_category: Optional[str] = None,
        year: Optional[int] = None,
        region: Optional[str] = None,
        market_type: Optional[str] = None,
        pesticide_residue: Optional[str] = None,
    ) -> Dict[str, Any]:
        df = self._load_harvest_data()
        filters = {
            "crop_id": crop_id,
            "crop_category": crop_category,
            "year": year,
            "region": region,
            "market_type": market_type,
            "pesticide_residue": pesticide_residue,
        }
        df = self._apply_filters(df, filters)

        total_records = int(len(df))
        quality = self._column(df, "quality_grade")
        pesticide = self._column(df, "pesticide_residue")
        revenue = self._column(df, "revenue_bdt")

        grade_distribution = {}
        for grade in ["A", "B", "C", "D"]:
            subset = df[df[quality] == grade]
            count = int(len(subset))
            grade_distribution[grade] = {
                "count": count,
                "pct": self._round((count / total_records) * 100) if total_records else 0,
                "avg_revenue_bdt": self._round(subset[revenue].mean()) if count else 0,
            }

        pesticide_breakdown = {}
        for residue in ["None", "Trace", "Low", "High"]:
            subset = df[df[pesticide] == residue]
            count = int(len(subset))
            pesticide_breakdown[residue] = {
                "count": count,
                "pct": self._round((count / total_records) * 100) if total_records else 0,
            }

        return {
            "filters_applied": self._filters_applied(filters),
            "total_records": total_records,
            "grade_distribution": grade_distribution,
            "pesticide_residue_breakdown": pesticide_breakdown,
        }


agriculture_report_service = AgricultureReportService()
