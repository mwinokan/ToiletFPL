#!/usr/bin/env python3

import api as fpl_api
from player import Player
import plotly.graph_objects as go


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

        xdata.append(p.selected_by)

        next5_sum = 0
        for i in range(gw, gw + 6):
            next5_sum += p.expected_points(gw=i, use_official=False)

        ydata.append(next5_sum)

        tdata.append(f"{p.name}, {p.team_obj.shortname}")

    fig = go.FigureWidget()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xdata, y=ydata, text=tdata, textposition="middle right", mode="markers"
        )
    )

    fig.update_traces(
        marker=dict(size=12, line=dict(width=2, color="DarkSlateGrey")),
        selector=dict(mode="markers"),
    )

    fig.update_layout(legend_title_text="Differentials")
    fig.update_xaxes(title_text="Selected %")
    fig.update_yaxes(title_text="Next5 xPts")
    fig.show()


if __name__ == "__main__":
    main()
