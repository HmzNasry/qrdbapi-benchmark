import typer
from pathlib import Path
from benchmark.core import BenchmarkRunner
from benchmark.visualizer import generate_chart
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def start(
    config: str = "inputs/benchmarks.json",
    system: str = typer.Option(None, help="Specific system to test (e.g., 'fastapi')"),
):
    """
    Run the API Benchmark based on the configuration file.
    """
    runner = BenchmarkRunner(config)
    runner.run(target_system=system)


@app.command()
def visualize(
    file: str = typer.Argument(..., help="Path to the results JSON file")
):
    """
    Generate an interactive HTML chart from a results JSON file.
    """
    if not Path(file).exists():
        console.print(f"[bold red]File not found: {file}[/bold red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Generating interactive chart for {file}...[/cyan]")
    html_path = generate_chart(file)
    console.print(f"[bold green]Interactive chart saved to: {html_path}[/bold green]")
    console.print(f"[dim]Open this file in your browser to view results.[/dim]")


if __name__ == "__main__":
    app()
