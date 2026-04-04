import asyncio
import os
import sys
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.markdown import Markdown

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.intelligence.mirofish_agent import MarketReportAgent
from src.intelligence.swarm import run_swarm_simulation

console = Console()

async def run_dashboard():
    """
    GodMode-inspired Live Dashboard for SatTrade Swarm Intelligence.
    Visualizes multi-persona consensus and GTFI in real-time.
    """
    console.print("[bold blue]Initialising SatTrade MiroFish Intelligence Swarm...[/bold blue]")
    
    agent = MarketReportAgent()
    
    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            # 1. Fetch consensus
            consensus = await agent.generate_swarm_consensus(
                requirement="Simulate systemic impact of Suez/Panama canal chokepoint friction."
            )
            
            # 2. Build Layout (GodMode Multi-Pane Style)
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="footer", size=3)
            )
            
            layout["main"].split_row(
                Layout(name="consensus", ratio=2),
                Layout(name="stats", ratio=1)
            )
            
            # Header: GTFI & Status
            gtfi = consensus["gtfi"]
            status_color = "green" if gtfi > 0.9 else "yellow" if gtfi > 0.7 else "red"
            layout["header"].update(Panel(
                f"[bold]GTFI (Global Trade Flow Index): [ {status_color} ] {gtfi} [/] | Consensus: SYSTEMIC_ALPHA_DETECTED",
                title="SatTrade MiroFish Core v2.0"
            ))
            
            # Main Consensus: Markdown report
            layout["consensus"].update(Panel(
                Markdown(consensus["consensus_report"]),
                title="[bold yellow]Multi-Persona Consensus (God-View)[/]"
            ))
            
            # Stats: Persona divergence
            stats_table = Table(title="Persona Divergence Stats")
            stats_table.add_column("Persona", style="cyan")
            stats_table.add_column("Agents", justify="right")
            stats_table.add_column("Vibe", justify="center")
            
            # Mocking some vibes based on persona names
            vibes = {
                "Cautious": "🛡️ RISK_OFF",
                "Aggressive": "🚀 YOLD_ALPHA",
                "Standard": "⚖️ BALANCED",
                "Weather-Sensitive": "🌊 ENVIRO_RES",
                "Economic-Sensitive": "📊 MACRO_NAV"
            }
            
            # We would normally fetch this from swarm_result
            # For the demo, we show the personas list
            for p in consensus["individual_reports"].keys():
                stats_table.add_row(p, "400", vibes.get(p, "???"))
                
            layout["stats"].update(Panel(stats_table, title="[bold cyan]Swarm Metrics[/]"))
            
            layout["footer"].update(Panel(
                f"Seed Ingestion Active | NASA FIRMS | USGS | Open-Meteo | FRED | NOAA | [bold green]Open Topo (NEW)[/]",
                style="italic"
            ))
            
            live.update(layout)
            await asyncio.sleep(60) # Update every minute

if __name__ == "__main__":
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        console.print("\n[bold red]Dashboard offline.[/bold red]")
