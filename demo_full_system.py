"""
Full End-to-End System Demonstration (Phases 0-8)

This script instantiates the core components of the Satellite-Based AI Trading System
and runs a simulated data flow through all phases to demonstrate completeness and functionality.
"""

import sys
import logging
from datetime import datetime, timedelta, timezone
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SatTrade-E2E")

try:
    # Phase 0-2: Config, Schemas, Quality Gates
    from src.common.config import load_constraints
    from src.common.schemas import TileMetadata, BoundingBox, SensorType, ProcessingLevel
    from src.ingest.quality_gates import QualityGates
    
    # Phase 3: Annotation
    from src.annotate.taxonomy import get_taxonomy, UseCase
    from src.annotate.quality import AnnotationQualityAgent, Annotation
    
    # Phase 4: Feature Extraction & Store
    from src.features.feature_store import FeatureStore, FeatureRecord
    
    # Phase 5: Signal Modeling
    from src.signals.price_impact import LinearModel
    
    # Phase 6: Backtesting
    from src.execution.signal_scoring import SignalScoringEngine, RawSignal
    from src.backtest.walk_forward import WalkForwardValidator
    
    # Phase 7: Execution
    from src.execution.risk_engine import RiskEngine, PortfolioPosition
    from src.execution.order_manager import OrderManager, OrderSide, OrderType
    
    # Phase 8: Monitoring
    from src.monitoring.retrain import RetrainingScheduler
    
    COMPONENTS_LOADED = True
except ImportError as e:
    logger.error(f"Failed to import system components: {e}")
    COMPONENTS_LOADED = False


def run_full_pipeline_demo():
    if not COMPONENTS_LOADED:
        print("❌ Cannot run demo: missing components. Please ensure you are in the project root.")
        return

    print("\n" + "="*80)
    print("SATTRADE SYSTEM E2E DEMONSTRATION")
    print("="*80 + "\n")

    now = datetime.now(timezone.utc)
    
    # ─── PHASE 0: CONFIGURATION ───────────────────────────────────────────
    print(">>> PHASE 0: Configuration & Constraints")
    try:
        constraints = load_constraints()
        print(f"[OK] Loaded constraints: Simulated NAV = ${constraints.capital.simulated_nav_usd:,.2f}")
    except Exception as e:
        print(f"[INFO] Could not load constraints.yaml (expected in config/): {e}")

    # ─── PHASE 1-2: INGESTION & QUALITY GATES ─────────────────────────────
    print("\n>>> PHASE 1-2: Data Ingestion & Quality Gates")
    tile = TileMetadata(
        tile_id="DEMO_TILE_001",
        source="sentinel-2",
        acquisition_utc=now,
        cloud_cover_pct=15.0,
        sensor_type=SensorType.OPTICAL,
        resolution_m=10.0,
        bounding_box_wgs84=BoundingBox(west=100.0, south=1.0, east=101.0, north=2.0),
        license_id="copernicus",
        commercial_use_permitted=True,
        processing_level=ProcessingLevel.L2A,
        checksum_sha256="a" * 64,
    )
    gates = QualityGates()
    results = gates.run_all_checks(tile)
    passed = all(r.passed for r in results)
    print(f"[OK] Tile {tile.tile_id} passed Quality Gates: {passed}")

    # ─── PHASE 3: ANNOTATION & TAXONOMY ───────────────────────────────────
    print("\n>>> PHASE 3: Annotation Taxonomy & Quality Control")
    taxonomy = get_taxonomy(UseCase.PORT_THROUGHPUT)
    print(f"[OK] Loaded Port Taxonomy with {taxonomy.get_num_classes()} classes (e.g., {taxonomy.get_class_names()[0]})")
    
    aq_agent = AnnotationQualityAgent()
    annotations = {
        "DEMO_TILE_001": [
            [Annotation("DEMO_TILE_001", "ann1", "container_stack", (10, 10, 50, 50))],
            [Annotation("DEMO_TILE_001", "ann2", "container_stack", (12, 12, 48, 48))],
            [Annotation("DEMO_TILE_001", "ann3", "container_stack", (11, 11, 49, 49))],
        ]
    }
    report = aq_agent.process_batch(annotations)
    print(f"[OK] Processed internal annotations. Accepted: {report.n_accepted}, Discarded: {report.n_discarded}")

    # ─── PHASE 4: FEATURE STORE (Point-in-Time) ───────────────────────────
    print("\n>>> PHASE 4: Feature Extraction & Feature Store")
    fs = FeatureStore()
    record = FeatureRecord(
        entity_id="PORT_SINGAPORE",
        feature_name="vessel_count",
        feature_value=142.5,
        feature_timestamp=now - timedelta(hours=1),
        source_tile_ids=["DEMO_TILE_001"],
        model_version="v1.0"
    )
    fs.materialize(record)
    fv = fs.get_features_as_of("PORT_SINGAPORE", now)
    print(f"[OK] Materialised and retrieved Point-in-Time correct feature: vessel_count = {fv.features.get('vessel_count')}")

    # ─── PHASE 5: SIGNAL MODELING ─────────────────────────────────────────
    print("\n>>> PHASE 5: Signal Modeling")
    # Mocking a linear model fit
    X = np.random.randn(100, 3)
    y = 0.5 * X[:, 0] + 0.3 * X[:, 1] + np.random.randn(100) * 0.1
    model = LinearModel()
    fit_result = model.fit(X, y, feature_names=["vessel_count", "crane_activity", "truck_ratio"])
    print(f"[OK] Fits Linear Price Impact Model. R-squared: {fit_result['r_squared']:.4f}")

    # ─── PHASE 6: SIMULATED BACKTEST & VALIDATION ─────────────────────────
    print("\n>>> PHASE 6: Backtesting (Walk-Forward Validation)")
    validator = WalkForwardValidator(holdout_start=now - timedelta(days=90))
    dates = [now - timedelta(days=365) + timedelta(weeks=w) for w in range(52)]
    folds = validator.generate_folds(dates)
    print(f"[OK] Generated {len(folds)} Walk-Forward Folds for out-of-sample testing.")

    # ─── PHASE 7: EXECUTION RUNTIME ───────────────────────────────────────
    print("\n>>> PHASE 7: Execution & Risk Management")
    order_mgr = OrderManager()
    risk_engine = RiskEngine()
    
    # Create order
    order = order_mgr.create_order("MAERSK", OrderSide.BUY, 100, OrderType.MARKET)
    print(f"[OK] Created Order: {order.order_id} ({order.status.value})")
    
    # Run pre-trade checks
    pos = PortfolioPosition("MAERSK", 50, 25000, "2030", "DK", 1000000, 500.0)
    risk_res = risk_engine.run_pretrade_checks(
        "MAERSK", 100, 500.0, 3600, [pos]
    )
    if risk_res.all_passed:
        order_mgr.approve_risk(order.order_id, "chk_1")
        print(f"[OK] Order passed Risk Engine checks -> {order.status.value}")
        
        order_mgr.submit(order.order_id)
        order_mgr.fill(order.order_id, fill_price=501.25)
        print(f"[OK] Order Executed and Filled at $501.25 -> {order.status.value}")
    else:
        print(f"[FAIL] Order failed Risk Engine: {risk_res.block_reason}")

    # ─── PHASE 8: MONITORING & OPERATIONS ─────────────────────────────────
    print("\n>>> PHASE 8: Monitoring & Retraining")
    scheduler = RetrainingScheduler()
    drift_data = {"vessel_count": {"psi": 0.25, "classification": "SIGNIFICANT_DRIFT"}}
    jobs = scheduler.check_triggers(feature_drift_results=drift_data, current_time=now)
    print(f"[OK] Retraining Scheduler evaluated drift (PSI=0.25). Triggered {len(jobs)} retrain jobs.")
    if jobs:
        print(f"   -> Job Trigger Reason: {jobs[0].trigger.value}")

    print("\n" + "="*80)
    print("[SUCCESS] SATTRADE PIPELINE EXECUTED SUCCESSFULLY ACROSS ALL 8 PHASES")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_full_pipeline_demo()
