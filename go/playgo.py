import api as fpl_api
from player import Player
import plotly.graph_objects as go
from plotly.offline import plot
import re
import mout
import math


def create_player_figure(api, player, show=False):
    """

    Figure:
            gw_points: Bar Chart
            form: line?
            expected: scatter?
            ct_index: scatter?

    """

    html_str = ""

    gw = api._current_gw

    active_gws = [i for i in range(1, gw + 1)]

    event_points = []
    event_summaries = []
    event_form = []
    event_expected = []
    event_performed_xpts = []

    style = player.team_obj.style

    for i in active_gws:
        score, summary = player.get_event_score(
            gw=i, not_playing_is_none=False, summary=True, html_highlight=False
        )
        event_points.append(score)
        event_summaries.append(summary)
        past_3 = [event_points[j - 1] for j in range(max(1, i - 3), i + 1)]
        event_form.append(sum(past_3) / len(past_3))
        xpts = player.get_performed_xpts(gw=i)
        if xpts is not None:
            xpts = round(xpts, 1)
        event_performed_xpts.append(xpts)

    all_gws = []
    for i in range(38):
        j = i + 1
        all_gws.append(j)
        event_expected.append(round(player.expected_points(gw=j), 1))

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Points",
            x=active_gws,
            y=event_points,
            hovertext=event_summaries,
            marker=dict(color=style["color"]),
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Form",
            x=active_gws,
            y=event_form,
            mode="lines",
            line_width=4,
            marker=dict(color=style["accent"]),
        )
    )
    fig.add_trace(
        go.Scatter(
            name="xPoints",
            x=all_gws,
            y=event_expected,
            mode="markers",
            marker_size=12,
            marker=dict(color=style["accent"]),
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Performed xPoints",
            x=active_gws,
            y=event_performed_xpts,
            mode="lines",
            marker=dict(color=style["accent"]),
            line={"dash": "dash"},
        )
    )

    fig.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor=style["background-color"],
    )
    fig.update_xaxes(title_text="GW")
    fig.update_yaxes(title_text="Points")

    def largest_value(lists):
        all_vals = sum(lists, [])
        all_vals = [v for v in all_vals if v is not None]
        return max(all_vals)

    max_yval = largest_value(
        [event_points, event_expected, event_form, event_performed_xpts]
    )

    fig.update_yaxes(range=[0, math.ceil((max_yval + 0.5) / 5) * 5])

    # Get HTML representation of plotly.js and this figure
    plot_div = plot(fig, output_type="div", include_plotlyjs=False)

    # Get id of html div element that looks like
    # <div id="301d22ab-bfba-4621-8f5d-dc4fd855bb33" ... >
    res = re.search('<div id="([^"]*)"', plot_div)
    div_id = res.groups()[0]

    # Build HTML string
    html_str = """{plot_div}
	""".format(
        plot_div=plot_div
    )

    return html_str
