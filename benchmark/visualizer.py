import json
import plotly.graph_objects as go
from pathlib import Path


def generate_chart(json_path: str):
    """
    Generates an interactive HTML horizontal bar chart using Plotly.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    # 1. Extract Data Structure
    scenarios = list(data.keys())
    
    # Get all unique systems present in the file
    systems = set()
    for scen in data.values():
        for sys_name in scen.keys():
            systems.add(sys_name)
    systems = sorted(list(systems))

    fig = go.Figure()

    # 2. Build Traces (One group of bars per System)
    for sys in systems:
        means = []
        hover_texts = []
        
        for scen in scenarios:
            result = data[scen].get(sys)
            
            if isinstance(result, dict) and "mean" in result:
                means.append(result["mean"])
                # Rich tooltip data
                text = (
                    f"<b>{sys.upper()}</b><br>"
                    f"Mean: {result['mean']:.4f}s<br>"
                    f"P99:  {result['p99']:.4f}s<br>"
                    f"Min:  {result['min']:.4f}s<br>"
                    f"Max:  {result['max']:.4f}s"
                )
                hover_texts.append(text)
            else:
                means.append(0)
                status = result if isinstance(result, str) else "N/A"
                hover_texts.append(f"<b>{sys.upper()}</b><br>Status: {status}")

        fig.add_trace(go.Bar(
            y=scenarios,
            x=means,
            name=sys.upper(),
            orientation='h',
            hoverinfo="text",
            hovertext=hover_texts,
        ))

    # 3. Layout Configuration
    # Calculate height: at least 800px, or more if there are many scenarios
    dynamic_height = max(800, len(scenarios) * 30)

    fig.update_layout(
        title=f"API Benchmark Results ({Path(json_path).stem})",
        xaxis_title="Mean Latency (Seconds)",
        yaxis_title="Scenario",
        barmode='group',
        height=dynamic_height,
        margin=dict(l=10, r=10, t=40, b=20),
        legend=dict(x=1, y=1),
        # Invert Y axis so top scenarios are at the top of the chart
        yaxis=dict(autorange="reversed") 
    )

    # 4. Save to HTML
    output_path = Path(json_path).with_suffix(".html")
    fig.write_html(str(output_path))

    return str(output_path)
