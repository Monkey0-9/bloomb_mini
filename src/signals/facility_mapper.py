from dataclasses import dataclass
from typing import Literal


@dataclass
class FacilityMapping:
    facility_id: str
    facility_name: str
    facility_type: Literal["PORT", "RETAIL", "INDUSTRIAL"]
    bbox_wgs84: list[float]
    primary_ticker: str
    primary_exchange: str
    revenue_attribution: float
    attribution_source: str
    supply_chain_depth: int
    confidence_weight: float
    causal_hypothesis: str
    lag_days_expected: int
    validation_status: Literal["VALIDATED", "PROVISIONAL", "SPECULATIVE"]


class FacilityMapper:
    INITIAL_MAPPINGS: list[FacilityMapping] = [
        FacilityMapping(
            facility_id="PORT-ROTTERDAM-001",
            facility_name="Port of Rotterdam Maasvlakte 2",
            facility_type="PORT",
            bbox_wgs84=[3.9, 51.85, 4.6, 52.05],
            primary_ticker="AMKBY",
            primary_exchange="OTC",
            revenue_attribution=0.23,
            attribution_source="AP Moller-Maersk Annual Report 2023 Terminal Division",
            supply_chain_depth=1,
            confidence_weight=0.90,
            causal_hypothesis=(
                "Rotterdam Maasvlakte 2 is operated by APM Terminals, a wholly owned "
                "subsidiary of AP Møller-Maersk. Elevated vessel throughput at berth "
                "indicates higher cargo volumes on North Europe trade lanes. This "
                "contributes to terminal revenue, which appears in the Ocean segment "
                "of Maersk quarterly earnings 6-8 weeks after the satellite observation "
                "date due to the cargo voyage + reporting lag."
            ),
            lag_days_expected=49,
            validation_status="PROVISIONAL",
        ),
        FacilityMapping(
            facility_id="PORT-SINGAPORE-001",
            facility_name="Singapore PSA Tanjong Pagar",
            facility_type="PORT",
            bbox_wgs84=[103.6, 1.2, 104.1, 1.5],
            primary_ticker="ZIM",
            primary_exchange="NYSE",
            revenue_attribution=0.08,
            attribution_source="ZIM Integrated Shipping 20-F 2023 Volume Breakdown",
            supply_chain_depth=2,
            confidence_weight=0.75,
            causal_hypothesis=(
                "Singapore is a major transshipment hub. ZIM calls at Singapore on "
                "its ZX1 and ZX7 services. Elevated throughput indicates healthy "
                "Trans-Pacific and Intra-Asia demand, which drives ZIM's rate per TEU "
                "and volume metrics. Revenue impact appears in next quarterly report."
            ),
            lag_days_expected=42,
            validation_status="PROVISIONAL",
        ),
        FacilityMapping(
            facility_id="PORT-SHANGHAI-001",
            facility_name="Shanghai Yangshan Deep Water Port",
            facility_type="PORT",
            bbox_wgs84=[121.8, 30.5, 122.1, 30.75],
            primary_ticker="1919.HK",
            primary_exchange="HKEX",
            revenue_attribution=0.31,
            attribution_source="COSCO Shipping Holdings Annual Report 2023 Port Operations Segment",
            supply_chain_depth=1,
            confidence_weight=0.90,
            causal_hypothesis=(
                "Yangshan is operated by Shanghai International Port Group in which "
                "COSCO Shipping Ports holds a significant stake. Throughput at Yangshan "
                "is a direct leading indicator of COSCO's container terminal revenue "
                "and reflects Trans-Pacific export demand from China."
            ),
            lag_days_expected=35,
            validation_status="PROVISIONAL",
        ),
        FacilityMapping(
            facility_id="RETAIL-WALMART-TX-001",
            facility_name="Walmart Supercenter Texas Cluster",
            facility_type="RETAIL",
            bbox_wgs84=[-100.0, 25.8, -93.5, 36.5],
            primary_ticker="WMT",
            primary_exchange="NYSE",
            revenue_attribution=0.04,
            attribution_source="Walmart FY2024 10-K US Comparable Store Sales Methodology",
            supply_chain_depth=1,
            confidence_weight=0.90,
            causal_hypothesis=(
                "Parking lot density at Walmart Supercenters is a direct proxy for "
                "foot traffic, which is the primary driver of same-store sales (SSS). "
                "Elevated parking density relative to same-period prior year indicates "
                "above-consensus SSS for that quarter."
            ),
            lag_days_expected=28,
            validation_status="PROVISIONAL",
        ),
        FacilityMapping(
            facility_id="INDUSTRIAL-ARCELOR-DUNKIRK-001",
            facility_name="ArcelorMittal Dunkirk Steel Plant",
            facility_type="INDUSTRIAL",
            bbox_wgs84=[2.3, 50.9, 2.5, 51.1],
            primary_ticker="MT",
            primary_exchange="NYSE",
            revenue_attribution=0.07,
            attribution_source="ArcelorMittal Annual Report 2023 Europe Segment Production Volumes",
            supply_chain_depth=1,
            confidence_weight=0.90,
            causal_hypothesis=(
                "Dunkirk is ArcelorMittal's largest French integrated steel plant. "
                "Thermal anomaly index correlates with blast furnace operating rate. "
                "Elevated thermal signature indicates near-capacity production."
            ),
            lag_days_expected=56,
            validation_status="PROVISIONAL",
        ),
    ]

    def get_by_facility_id(self, facility_id: str) -> FacilityMapping | None:
        for m in self.INITIAL_MAPPINGS:
            if m.facility_id == facility_id:
                return m
        return None

    def get_by_ticker(self, ticker: str) -> list[FacilityMapping]:
        return [m for m in self.INITIAL_MAPPINGS if m.primary_ticker == ticker]

    def get_all_by_type(self, ftype: str) -> list[FacilityMapping]:
        return [m for m in self.INITIAL_MAPPINGS if m.facility_type == ftype]
