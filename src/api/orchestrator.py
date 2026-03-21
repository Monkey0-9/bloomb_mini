import asyncio
from typing import List, Dict, Any
import structlog
from src.api.agents.base import BaseAgent

log = structlog.get_logger()

class Orchestrator:
    """Coordinates multiple agents to fulfill complex queries."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.log = log.bind(component="orchestrator")

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.name] = agent
        self.log.info("agent_registered", agent=agent.name)

    async def execute_dag(self, dag: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a directed acyclic graph of agent tasks.
        Format: {
            "tasks": [
                {"id": "t1", "agent": "thermal", "params": {...}},
                {"id": "t2", "agent": "news", "params": {...}, "depends_on": ["t1"]},
            ]
        }
        """
        results = {}
        tasks = dag.get("tasks", [])
        
        # Simple BFS/topological sort execution for now
        # In a real system, we'd use a proper DAG runner
        pending = list(tasks)
        while pending:
            current_batch = [t for t in pending if all(d in results for d in t.get("depends_on", []))]
            if not current_batch:
                if pending:
                    self.log.error("dag_cycle_detected", pending=[t["id"] for t in pending])
                    break
                break
                
            async_tasks = []
            for t in current_batch:
                agent = self.agents.get(t["agent"])
                if not agent:
                    results[t["id"]] = {"error": f"Agent {t['agent']} not found"}
                    continue
                
                # Merge dependency results into params
                params = t.get("params", {})
                for dep_id in t.get("depends_on", []):
                    params[f"input_{dep_id}"] = results[dep_id]
                
                # In DAG execution, we assume a default task type or use 'agent_specific_task'
                # If the task dict has a 'type', use it, otherwise use 'default'
                task_type = t.get("type", "execute")
                async_tasks.append((t["id"], agent.process_task(task_type, params)))
            
            ids, futures = zip(*async_tasks) if async_tasks else ([], [])
            batch_results = await asyncio.gather(*futures)
            
            for tid, res in zip(ids, batch_results):
                results[tid] = res
                
            for t in current_batch:
                pending.remove(t)
                
    async def dispatch_task(self, agent_name: str, task_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method for one-off agent tasks used by routers."""
        agent = self.agents.get(agent_name)
        if not agent:
             # Fallback: check case-insensitive or common aliases
             for name, a in self.agents.items():
                 if name.lower() == agent_name.lower():
                     agent = a
                     break
        
        if not agent:
            return {"status": "error", "message": f"Agent {agent_name} not found"}
        
        try:
            # Most agents have a process_task or process method
            return await agent.process_task(task_type, params)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_unified_state(self) -> Dict[str, Any]:
        """Aggregates state from all registered agents."""
        state = {}
        for name, agent in self.agents.items():
            if hasattr(agent, "get_state"):
                state[name] = await agent.get_state()
        return state

# Alias for router compatibility
SignalOrchestrator = Orchestrator
