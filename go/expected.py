#!/usr/bin/env python3

import api as fpl_api
from player import Player
import plotly.graph_objects as go
import mout
from scipy import stats
import numpy as np


def main():

    api = fpl_api.FPL_API()

    budget = 15
    position = None
    minutes = 90

    xdata = []
    ydata = []
    tdata = []

    gw = api._current_gw

    player_ids = api._elements["id"]
    for i, pid in enumerate(player_ids):
        if i % 50 == 0:
            print(i)

        if position is not None and position != api._elements["element_type"][i]:
            continue

        if budget is not None and api._elements["now_cost"][i] > 10 * budget:
            continue

        if api._elements["minutes"][i] < minutes:
            continue

        index = api.get_player_index(pid)
        p = Player(None, api, index=index)

        tdata.append(f"{p.name}, {p.team_obj.shortname}")

        expected, actual = p.expected_total_points(
            return_actual=True, use_official=False
        )

        xdata.append(expected)
        ydata.append(actual)

    fig = go.FigureWidget()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xdata, y=ydata, text=tdata, textposition="middle right", mode="markers"
        )
    )

    x_min = 0
    x_max = max(xdata)
    x = np.linspace(x_min, x_max, 20)

    # forwards
    # res = stats.linregress(xdata, ydata)
    mout.headerOut("Forwards")
    # mout.varOut("R-squared",f"{res.rvalue**2:.6f}")
    # mout.varOut("slope",f"{res.slope:.6f}")
    # mout.varOut("intercept",f"{res.intercept:.6f}")
    # y = res.intercept + res.slope*x
    y = x
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines"))

    fig.update_traces(
        marker=dict(size=12, line=dict(width=2, color="DarkSlateGrey")),
        selector=dict(mode="markers"),
    )

    fig.update_layout(legend_title_text="Expected")
    fig.update_xaxes(title_text="Expected Total Points")
    fig.update_yaxes(title_text="Actual Total Points")
    fig.show()


if __name__ == "__main__":
    main()
