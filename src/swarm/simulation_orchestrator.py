"""
Simulation Orchestrator - Complete MiroFish-style simulation engine.

Ties together all components:
- Signal detection from satellite data
- Agent swarm consensus
- GraphRAG knowledge reasoning
- Collective memory lookup
- Report generation
- Interactive chat

Provides a unified interface for running end-to-end satellite signal simulations.
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SimulationStage(Enum):
    """Stages of the signal simulation pipeline."""
    IDLE = "idle"
    SIGNAL_DETECTION = "signal_detection"
    SWARM_CONSENSUS = "swarm_consensus"
    GRAPH_REASONING = "graph_reasoning"
    MEMORY_LOOKUP = "memory_lookup"
    REPORT_GENERATION = "report_generation"
    COMPLETE = "complete"


@dataclass
class SimulationState:
    """Current state of a running simulation."""
    simulation_id: str
    ticker: str
    facility_name: str
    stage: SimulationStage
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    """Complete result from a signal simulation."""
    simulation_id: str
    signal_data: Dict[str, Any]
    swarm_consensus: Dict[str, Any]
    graph_analysis: Dict[str, Any]
    historical_context: Dict[str, Any]
    report: Dict[str, Any]
    chat_session_id: Optional[str]
    execution_time_ms: int
    timestamp: datetime


class SignalSimulationOrchestrator:
    """
    End-to-end orchestrator for satellite signal simulations.
    
    MiroFish-style workflow:
    1. Signal Detection → Detect thermal anomalies
    2. Swarm Consensus → Multi-agent debate
    3. GraphRAG → Knowledge graph impact analysis
    4. Memory → Historical pattern matching
    5. Report → Generate comprehensive report
    6. Chat → Enable interactive exploration
    
    Usage:
        orchestrator = SignalSimulationOrchestrator()
        result = await orchestrator.run_simulation("MT", thermal_signal_data)
    """
    
    def __init__(self):
        self.active_simulations: Dict[str, SimulationState] = {}
        self.completed_simulations: Dict[str, SimulationResult] = {}
        self._progress_callbacks: List[Callable[[str, float, SimulationStage], None]] = []
        
    def register_progress_callback(self, callback: Callable[[str, float, SimulationStage], None]) -> None:
        """Register a callback for simulation progress updates."""
        self._progress_callbacks.append(callback)
    
    def _notify_progress(self, sim_id: str, progress: float, stage: SimulationStage) -> None:
        """Notify all registered callbacks of progress."""
        for callback in self._progress_callbacks:
            try:
                callback(sim_id, progress, stage)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    async def run_simulation(self,
                            ticker: str,
                            signal_data: Dict[str, Any],
                            facility_name: Optional[str] = None) -> SimulationResult:
        """
        Run complete signal simulation pipeline.
        
        Args:
            ticker: Stock ticker symbol
            signal_data: Raw satellite signal data
            facility_name: Optional facility name override
            
        Returns:
            Complete SimulationResult with all analysis
        """
        sim_id = f"sim_{ticker}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        facility = facility_name or signal_data.get('facility_name', 'Unknown')
        
        state = SimulationState(
            simulation_id=sim_id,
            ticker=ticker,
            facility_name=facility,
            stage=SimulationStage.IDLE,
            started_at=datetime.now(timezone.utc)
        )
        self.active_simulations[sim_id] = state
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Stage 1: Signal Detection/Validation (10%)
            await self._run_stage(state, SimulationStage.SIGNAL_DETECTION, 0.10)
            validated_signal = self._validate_signal(signal_data)
            state.results['signal'] = validated_signal
            
            # Stage 2: Swarm Consensus (30%)
            await self._run_stage(state, SimulationStage.SWARM_CONSENSUS, 0.30)
            swarm_result = self._run_swarm_consensus(validated_signal)
            state.results['swarm'] = swarm_result
            
            # Stage 3: GraphRAG Analysis (50%)
            await self._run_stage(state, SimulationStage.GRAPH_REASONING, 0.50)
            graph_result = self._run_graph_analysis(facility, ticker)
            state.results['graph'] = graph_result
            
            # Stage 4: Memory Lookup (70%)
            await self._run_stage(state, SimulationStage.MEMORY_LOOKUP, 0.70)
            memory_result = self._run_memory_lookup(ticker, validated_signal)
            state.results['memory'] = memory_result
            
            # Stage 5: Report Generation (90%)
            await self._run_stage(state, SimulationStage.REPORT_GENERATION, 0.90)
            report_result = self._generate_report(
                validated_signal, swarm_result, graph_result, memory_result
            )
            state.results['report'] = report_result
            
            # Stage 6: Create Chat Session (100%)
            await self._run_stage(state, SimulationStage.COMPLETE, 1.0)
            chat_session = self._create_chat_session(ticker, sim_id, validated_signal)
            
            # Calculate execution time
            end_time = datetime.now(timezone.utc)
            execution_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Build final result
            result = SimulationResult(
                simulation_id=sim_id,
                signal_data=validated_signal,
                swarm_consensus=swarm_result,
                graph_analysis=graph_result,
                historical_context=memory_result,
                report=report_result,
                chat_session_id=chat_session,
                execution_time_ms=execution_ms,
                timestamp=end_time
            )
            
            self.completed_simulations[sim_id] = result
            del self.active_simulations[sim_id]
            
            logger.info(f"Simulation {sim_id} completed in {execution_ms}ms")
            return result
            
        except Exception as e:
            logger.error(f"Simulation {sim_id} failed: {e}")
            state.errors.append(str(e))
            raise
    
    async def _run_stage(self, state: SimulationState, stage: SimulationStage, progress: float) -> None:
        """Update simulation stage and notify progress."""
        state.stage = stage
        state.progress = progress
        self._notify_progress(state.simulation_id, progress, stage)
        
        # Small delay for visual feedback
        await asyncio.sleep(0.1)
    
    def _validate_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich raw signal data."""
        # Ensure required fields
        required = ['ticker', 'anomaly_sigma', 'frp_mw']
        for field in required:
            if field not in signal_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Add metadata
        signal_data['validated_at'] = datetime.now(timezone.utc).isoformat()
        signal_data['validation_version'] = '1.0'
        
        # Calculate signal strength category
        sigma = signal_data.get('anomaly_sigma', 0)
        if sigma > 3.0:
            signal_data['strength_category'] = 'EXTREME'
        elif sigma > 2.0:
            signal_data['strength_category'] = 'STRONG'
        elif sigma > 1.0:
            signal_data['strength_category'] = 'MODERATE'
        else:
            signal_data['strength_category'] = 'WEAK'
        
        return signal_data
    
    def _run_swarm_consensus(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent swarm consensus."""
        try:
            from src.swarm.signal_swarm import get_signal_swarm
            
            swarm = get_signal_swarm()
            consensus = swarm.debate_signal(signal_data)
            
            return {
                'consensus_stance': consensus.consensus_stance.name,
                'consensus_score': consensus.consensus_score,
                'confidence': consensus.confidence,
                'bull_votes': consensus.bull_votes,
                'bear_votes': consensus.bear_votes,
                'neutral_votes': consensus.neutral_votes,
                'reasoning_summary': consensus.reasoning_summary,
                'dissenting_opinion': consensus.dissenting_opinion,
                'votes': [
                    {
                        'agent_name': v.agent.name,
                        'agent_type': v.agent.type,
                        'stance': v.stance.name,
                        'conviction': v.conviction,
                        'reasoning': v.reasoning
                    }
                    for v in consensus.votes
                ]
            }
        except Exception as e:
            logger.error(f"Swarm consensus failed: {e}")
            return {'error': str(e)}
    
    def _run_graph_analysis(self, facility_name: str, ticker: str) -> Dict[str, Any]:
        """Execute GraphRAG knowledge analysis."""
        try:
            from src.swarm.graphrag_engine import get_graphrag_engine
            
            engine = get_graphrag_engine()
            
            # Find facility ID from name
            facility_id = None
            for node_id, node in engine.graph.nodes.items():
                if node.name == facility_name or facility_name in node.name:
                    facility_id = node_id
                    break
            
            if not facility_id:
                # Use generic facility lookup
                facility_id = f"facility_{facility_name.lower().replace(' ', '_')}"
            
            analysis = engine.analyze_facility_event(
                facility_id=facility_id,
                event_type='production_surge',
                severity=0.8
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Graph analysis failed: {e}")
            return {'error': str(e)}
    
    def _run_memory_lookup(self, ticker: str, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collective memory lookup."""
        try:
            from src.swarm.collective_memory import get_collective_memory
            from src.swarm.collective_memory import SignalMemory
            
            memory = get_collective_memory()
            
            # Get insight report
            report = memory.get_insight_report(ticker)
            
            # Find similar historical signals
            similar = memory.find_similar_signals(
                ticker=ticker,
                signal_type='thermal',
                anomaly_sigma=signal_data.get('anomaly_sigma', 0),
                n_results=5
            )
            
            # Get expected return
            expected_return, confidence = memory.get_expected_return(
                ticker=ticker,
                signal_type='thermal',
                anomaly_sigma=signal_data.get('anomaly_sigma', 0),
                horizon_days=5
            )
            
            return {
                'ticker': ticker,
                'overall_win_rate': report.get('overall_win_rate', 0.5),
                'total_signals': report.get('total_signals', 0),
                'recommendation': report.get('recommendation', ''),
                'learned_patterns': report.get('learned_patterns', []),
                'expected_return_5d': expected_return,
                'return_confidence': confidence,
                'similar_historical_signals': [
                    {
                        'signal_id': s.signal_id,
                        'sigma': s.anomaly_sigma,
                        'return_5d': s.forward_return_5d,
                        'correct': s.prediction_correct,
                        'date': s.timestamp.isoformat() if s.timestamp else None
                    }
                    for s in similar
                ]
            }
            
        except Exception as e:
            logger.error(f"Memory lookup failed: {e}")
            return {'error': str(e)}
    
    def _generate_report(self,
                        signal_data: Dict[str, Any],
                        swarm_result: Dict[str, Any],
                        graph_result: Dict[str, Any],
                        memory_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report."""
        try:
            from src.swarm.report_agent import get_report_agent
            
            agent = get_report_agent()
            
            report = agent.generate_report(
                signal_data=signal_data,
                swarm_consensus=swarm_result,
                graph_analysis=graph_result,
                historical_data=memory_result
            )
            
            return {
                'report_id': report.report_id,
                'executive_summary': report.executive_summary,
                'recommendation': report.recommendation,
                'confidence_metrics': report.confidence_metrics,
                'risk_factors': report.risk_factors,
                'markdown': agent.to_markdown(report)
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {'error': str(e)}
    
    def _create_chat_session(self, ticker: str, sim_id: str, signal_data: Dict[str, Any]) -> str:
        """Create interactive chat session."""
        try:
            from src.swarm.agent_chat import get_chat_system
            
            chat = get_chat_system()
            session = chat.create_session(
                agent_name=None,  # Swarm chat
                ticker=ticker,
                signal_id=signal_data.get('signal_id')
            )
            
            return session.session_id
            
        except Exception as e:
            logger.error(f"Chat session creation failed: {e}")
            return ""
    
    def get_simulation_status(self, sim_id: str) -> Optional[SimulationState]:
        """Get status of an active simulation."""
        return self.active_simulations.get(sim_id)
    
    def get_simulation_result(self, sim_id: str) -> Optional[SimulationResult]:
        """Get completed simulation result."""
        return self.completed_simulations.get(sim_id)
    
    def list_active_simulations(self) -> List[Dict[str, Any]]:
        """List all active simulations."""
        return [
            {
                'simulation_id': s.simulation_id,
                'ticker': s.ticker,
                'stage': s.stage.value,
                'progress': s.progress,
                'started_at': s.started_at.isoformat()
            }
            for s in self.active_simulations.values()
        ]
    
    def list_completed_simulations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List most recent completed simulations."""
        sorted_simulations = sorted(
            self.completed_simulations.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        return [
            {
                'simulation_id': s.simulation_id,
                'ticker': s.signal_data.get('ticker'),
                'facility': s.signal_data.get('facility_name'),
                'consensus': s.swarm_consensus.get('consensus_stance'),
                'confidence': s.swarm_consensus.get('confidence'),
                'execution_time_ms': s.execution_time_ms,
                'completed_at': s.timestamp.isoformat()
            }
            for s in sorted_simulations[:limit]
        ]


# Singleton
_orchestrator: Optional[SignalSimulationOrchestrator] = None

def get_orchestrator() -> SignalSimulationOrchestrator:
    """Get or create orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SignalSimulationOrchestrator()
    return _orchestrator


# Convenience function for quick simulations
async def quick_simulate(ticker: str, anomaly_sigma: float, facility_name: str) -> SimulationResult:
    """
    Quick simulation with minimal parameters.
    
    Usage:
        result = await quick_simulate("MT", 2.3, "ArcelorMittal Dunkirk")
    """
    orchestrator = get_orchestrator()
    
    signal_data = {
        'signal_id': f'quick_{ticker}_{datetime.now(timezone.utc).strftime("%H%M%S")}',
        'ticker': ticker,
        'facility_name': facility_name,
        'anomaly_sigma': anomaly_sigma,
        'frp_mw': 100.0 + (anomaly_sigma * 20),
        'brightness_k': 350.0,
        'cluster_size': int(3 + anomaly_sigma),
        'lat': 51.0,
        'lon': 2.0,
        'type': 'INDUSTRIAL_THERMAL',
        'detected_at': datetime.now(timezone.utc).isoformat(),
        'data_sources': ['NASA FIRMS']
    }
    
    return await orchestrator.run_simulation(ticker, signal_data, facility_name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test_orchestrator():
        print("=" * 70)
        print("Testing Signal Simulation Orchestrator")
        print("=" * 70)
        
        # Progress callback
        def on_progress(sim_id: str, progress: float, stage: SimulationStage):
            print(f"  [{sim_id[:20]}...] {stage.value}: {progress:.0%}")
        
        orchestrator = get_orchestrator()
        orchestrator.register_progress_callback(on_progress)
        
        # Run test simulation
        print("\nRunning test simulation for MT (ArcelorMittal)...")
        print("-" * 70)
        
        result = await quick_simulate("MT", 2.3, "ArcelorMittal Dunkirk")
        
        print("\n" + "=" * 70)
        print("Simulation Complete!
        print("=" * 70)
        
        print(f"\nSimulation ID: {result.simulation_id}")
        print(f"Execution Time: {result.execution_time_ms}ms")
        print(f"Timestamp: {result.timestamp.isoformat()}")
        
        print(f"\nSignal Data:")
        print(f"  Ticker: {result.signal_data.get('ticker')}")
        print(f"  Facility: {result.signal_data.get('facility_name')}")
        print(f"  Anomaly: {result.signal_data.get('anomaly_sigma'):.1f}σ")
        print(f"  Strength: {result.signal_data.get('strength_category')}")
        
        print(f"\nSwarm Consensus:")
        print(f"  Stance: {result.swarm_consensus.get('consensus_stance')}")
        print(f"  Score: {result.swarm_consensus.get('consensus_score')}")
        print(f"  Confidence: {result.swarm_consensus.get('confidence'):.0%}")
        print(f"  Votes: {result.swarm_consensus.get('bull_votes')} bull, "
              f"{result.swarm_consensus.get('bear_votes')} bear, "
              f"{result.swarm_consensus.get('neutral_votes')} neutral")
        
        print(f"\nHistorical Context:")
        print(f"  Win Rate: {result.historical_context.get('overall_win_rate', 0):.0%}")
        print(f"  Expected Return (5d): {result.historical_context.get('expected_return_5d', 0):.2%}")
        print(f"  Return Confidence: {result.historical_context.get('return_confidence', 0):.0%}")
        
        print(f"\nRecommendation:")
        rec = result.report.get('recommendation', {})
        print(f"  Action: {rec.get('action')}")
        print(f"  Position Size: {rec.get('position_size')}")
        print(f"  Urgency: {rec.get('urgency')}")
        print(f"  Target: {rec.get('target')}")
        
        print(f"\nConfidence Metrics:")
        conf = result.report.get('confidence_metrics', {})
        print(f"  Composite: {conf.get('composite_confidence', 0):.0%}")
        print(f"  Grade: {conf.get('reliability_grade', 'N/A')}")
        
        print(f"\nChat Session: {result.chat_session_id}")
        
        # List completed simulations
        print(f"\nCompleted Simulations: {len(orchestrator.list_completed_simulations())}")
    
    # Run test
    asyncio.run(test_orchestrator())
