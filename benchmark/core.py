import json
import os
import statistics
import httpx
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)

from benchmark.requester import fetch_url
from benchmark.analyzer import calculate_stats

console = Console()


class BenchmarkRunner:
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.data = json.load(f)
        
        self.config = self.data["config"]
        self.systems = self.data["systems"]
        self.scenarios = self.data["scenarios"]

    def run(self, target_system: str | None = None):
        results = {}
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        active_systems = {
            k: v for k, v in self.systems.items() 
            if target_system is None or k == target_system
        }
        
        summary_data = {
            sys: {"means": [], "failures": []} 
            for sys in active_systems
        }

        console.print(f"[bold green]Starting Benchmark ({self.config['iterations']} iter/req)[/bold green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            
            for scenario in self.scenarios:
                scen_name = scenario["name"]
                results[scen_name] = {}
                
                progress.console.print(f"[bold cyan]\nScenario: {scen_name}[/bold cyan]")

                for sys_name, base_url in active_systems.items():
                    endpoint = scenario["endpoints"].get(sys_name)

                    if not endpoint:
                        progress.console.print(f"  ⏭️  [dim]{sys_name}: SKIPPED (No endpoint)[/dim]")
                        results[scen_name][sys_name] = "SKIPPED"
                        continue

                    full_url = f"{base_url}{endpoint}"
                    task_id = progress.add_task(f"[magenta]{sys_name}[/magenta]", total=self.config["iterations"])
                    
                    times = []
                    errors = []

                    with httpx.Client(timeout=self.config["timeout_seconds"]) as client:
                        for _ in range(self.config["iterations"]):
                            duration, error = fetch_url(client, full_url)
                            if duration is not None:
                                times.append(duration)
                            if error:
                                errors.append(error)
                            progress.advance(task_id)

                    progress.remove_task(task_id)

                    stats = calculate_stats(times, self.config["remove_outliers"])
                    
                    if stats:
                        progress.console.print(
                            f"  ✅ [green]{sys_name:<10}[/green] "
                            f"Avg: [bold]{stats['mean']:.4f}s[/bold] | "
                            f"P99: {stats['p99']:.4f}s | "
                            f"Min: {stats['min']:.4f}s"
                        )
                        results[scen_name][sys_name] = stats
                        summary_data[sys_name]["means"].append(stats["mean"])
                    else:
                        primary_error = max(set(errors), key=errors.count) if errors else "Unknown Error"
                        progress.console.print(f"  ❌ [red]{sys_name:<10}[/red] FAILED: {primary_error}")
                        results[scen_name][sys_name] = {"error": primary_error}
                        
                        summary_data[sys_name]["failures"].append({
                            "scenario": scen_name,
                            "error": primary_error
                        })

        self._save_results(results, timestamp)
        self._print_summary(summary_data)

    def _save_results(self, results: dict, timestamp: str):
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        path = f"{output_dir}/results_{timestamp}.json"
        
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
            
        console.print(f"\n[dim]Full raw data saved to: {path}[/dim]")

    def _print_summary(self, summary_data: dict):
        has_any_failures = any(len(d["failures"]) > 0 for d in summary_data.values())

        table = Table(title="\n🏆 Final Benchmark Conclusion", show_lines=True)
        table.add_column("System", style="cyan", no_wrap=True)
        table.add_column("Scenarios Run", justify="right")
        table.add_column("Global Avg Latency", justify="right", style="green")
        
        if has_any_failures:
            table.add_column("Endpoints Failed", justify="right", style="red")
            
        table.add_column("Status", justify="center")

        best_time = float("inf")
        winner = None

        for sys_name, data in summary_data.items():
            means = data["means"]
            failures = data["failures"]
            total_runs = len(means) + len(failures)
            
            if total_runs == 0:
                row = [sys_name, "0", "N/A"]
                if has_any_failures: row.append("-")
                row.append("Skipped")
                table.add_row(*row)
                continue
            
            avg_of_avgs = statistics.mean(means) if means else 0.0
            
            if means and avg_of_avgs < best_time:
                best_time = avg_of_avgs
                winner = sys_name
            
            latency_text = f"{avg_of_avgs:.4f}s" if means else "N/A"
            status_icon = "✅" if not failures else "⚠️"
            
            row = [sys_name, str(total_runs), latency_text]
            if has_any_failures:
                row.append(str(len(failures)) if failures else "-")
            row.append(status_icon)
            
            table.add_row(*row)

        console.print(table)
        
        if winner:
            console.print(f"\n🚀 Fastest System: [bold green]{winner.upper()}[/bold green]")

        if has_any_failures:
            console.print("\n[bold red]🛑 Failure Details:[/bold red]")
            for sys_name, data in summary_data.items():
                if data["failures"]:
                    console.print(f"[bold]{sys_name}[/bold]:")
                    for fail in data["failures"]:
                        console.print(f"  - {fail['scenario']}: [red]{fail['error']}[/red]")
