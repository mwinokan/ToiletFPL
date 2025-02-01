import re
from plotly.offline import plot
import plotly.graph_objects as go


def manager_rank_waterfall(api, man):

    gws = man._active_gws

    or_delta = [man._overall_rank[0]] + [
        r - man._overall_rank[i] for i, r in enumerate(man._overall_rank[1:])
    ]

    # print(gws)
    # print(man._overall_rank)
    # print(or_delta)

    # for gw, r in zip(gws,or_delta):
    # 	print(gw,r)

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=gws,
            name="Rank",
            x=gws,
            text=[
                f"GW{i}: {api.big_number_format(r)}"
                for i, r in zip(man._active_gws, man._event_rank)
            ],
            y=or_delta,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={
                "marker": {
                    "color": "green",
                }
            },
            increasing={"marker": {"color": "red"}},
        )
    )

    fig.update_layout(
        # title = f"{man.name}'s Overall Rank",
        showlegend=False
    )

    fig.update_yaxes(title_text=f"Overall Rank", autorange="reversed", type="log")

    # Get HTML representation of plotly.js and this figure
    plot_div = plot(fig, output_type="div", include_plotlyjs=False)

    # Get id of html div element that looks like
    # <div id="301d22ab-bfba-4621-8f5d-dc4fd855bb33" ... >
    res = re.search('<div id="([^"]*)"', plot_div)
    div_id = res.groups()[0]

    # Build JavaScript callback for handling clicks
    # and opening the URL in the trace's customdata
    js_callback = """
	<script>
	var plot_element = document.getElementById("{div_id}");
	plot_element.on('plotly_click', function(data){{
	    console.log(data);
	    var point = data.points[0];
	    if (point) {{
	        console.log(point.customdata);
	        window.open(point.customdata);
	    }}
	}})
	</script>
	""".format(
        div_id=div_id
    )

    # Build HTML string
    html_str = """{plot_div}
	{js_callback}
	""".format(
        plot_div=plot_div, js_callback=js_callback
    )

    return html_str
