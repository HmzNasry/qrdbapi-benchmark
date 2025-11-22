import json
import plotly.graph_objects as go
from pathlib import Path

def generate_chart(json_path: str):
    """
    Generates an interactive HTML horizontal bar chart using Plotly.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    scenarios = list(data.keys())
    
    systems = set()
    for scen in data.values():
        for sys_name in scen.keys():
            systems.add(sys_name)
    systems = sorted(list(systems))

    fig = go.Figure()

    for sys in systems:
        means = []
        hover_texts = []
        bar_texts = []
        
        for scen in scenarios:
            result = data[scen].get(sys)
            
            if isinstance(result, dict) and "mean" in result:
                means.append(result["mean"])
                
                marker = " 👑" if result.get("is_winner") else ""
                bar_texts.append(marker)
                
                text = (
                    f"<b>{sys.upper()}{marker}</b><br>"
                    f"Mean: {result['mean']:.4f}s<br>"
                    f"P99:  {result['p99']:.4f}s<br>"
                    f"Min:  {result['min']:.4f}s<br>"
                    f"Max:  {result['max']:.4f}s"
                )
                hover_texts.append(text)
            else:
                means.append(0)
                bar_texts.append("")
                status = result if isinstance(result, str) else "N/A"
                hover_texts.append(f"<b>{sys.upper()}</b><br>Status: {status}")

        fig.add_trace(go.Bar(
            y=scenarios,
            x=means,
            name=sys.upper(),
            orientation='h',
            hoverinfo="text",
            hovertext=hover_texts,
            text=bar_texts,
            textposition='outside',
        ))

    dynamic_height = max(800, len(scenarios) * 30)

    fig.update_layout(
        title=f"API Benchmark Results ({Path(json_path).stem})",
        xaxis_title="Mean Latency (Seconds)",
        yaxis_title="Scenario",
        barmode='group',
        height=dynamic_height,
        margin=dict(l=10, r=10, t=40, b=20),
        legend=dict(x=1, y=1),
        yaxis=dict(autorange="reversed") 
    )

    output_path = Path(json_path).with_suffix(".html")
    fig.write_html(str(output_path))

    return str(output_path)
