import pandas as pd

# from IPython.core.display import HTML
from web import get_style_from_event_score

DEPLOY_ROOT = "mwinokan.github.io/ToiletFPL"


def compare_squads(m1, m2, interactive=False):

    if m1 is None or m2 is None:
        return "BYE!"

    s1 = m1.get_current_squad()
    s2 = m2.get_current_squad()

    gw = m1._api._current_gw

    m1_dict = {}
    for p in s1.sorted_players:
        if p.multiplier:
            m1_dict[p.id] = p

    m2_dict = {}
    for p in s2.sorted_players:
        if p.multiplier:
            m2_dict[p.id] = p

    data = {
        "m1": [],
        "m2": [],
        "common": [],
    }

    for p_id in m1_dict.keys() | m2_dict.keys():

        mult1 = m1_dict[p_id].multiplier if p_id in m1_dict else 0
        mult2 = m2_dict[p_id].multiplier if p_id in m2_dict else 0

        if p_id in m1_dict:
            p = m1_dict[p_id]
        else:
            p = m2_dict[p_id]

        if mult1 == mult2:
            data["common"].append(p)

        points = p.get_event_score() or None

        if mult1 > mult2:
            data["m1"].append(dict(player=p, m_diff=mult1 - mult2))
        elif mult1 < mult2:
            data["m2"].append(dict(player=p, m_diff=mult2 - mult1))

    html_buffer = ""

    from wiki import floating_subtitle

    html_buffer += floating_subtitle(f"{m1} vs {m2}", pad=1)

    html_buffer += '<table class="w3-table w3-hoverable w3-white">\n'

    html_buffer += "<tr>\n"
    html_buffer += '<th class="w3-center"></th>\n'
    html_buffer += f'<th class="w3-center">You</th>\n'
    html_buffer += f'<th class="w3-center">Oppenent</th>\n'
    html_buffer += "</tr>\n"

    html_buffer += "<tr>\n"
    html_buffer += '<td class="w3-center">Live</td>\n'

    if m1.livescore > m2.livescore:
        html_buffer += f'<th class="w3-center w3-green">{m1.livescore}</th>\n'
        html_buffer += f'<th class="w3-center">{m2.livescore}</th>\n'

    elif m1.livescore < m2.livescore:
        html_buffer += f'<th class="w3-center">{m1.livescore}</th>\n'
        html_buffer += f'<th class="w3-center w3-green">{m2.livescore}</th>\n'

    else:
        html_buffer += f'<th class="w3-center">{m1.livescore}</th>\n'
        html_buffer += f'<th class="w3-center">{m2.livescore}</th>\n'

    html_buffer += "</tr>\n"

    m1_projected = m1.squad.projected_points
    m2_projected = m2.squad.projected_points

    html_buffer += "<tr>\n"
    html_buffer += '<td class="w3-center">Projected</td>\n'

    if m1_projected > m2_projected:
        html_buffer += f'<th class="w3-center w3-green">{m1_projected:.1f}</th>\n'
        html_buffer += f'<th class="w3-center">{m2_projected:.1f}</th>\n'

    elif m1_projected < m2_projected:
        html_buffer += f'<th class="w3-center">{m1_projected:.1f}</th>\n'
        html_buffer += f'<th class="w3-center w3-green">{m2_projected:.1f}</th>\n'

    else:
        html_buffer += f'<th class="w3-center">{m1_projected:.1f}</th>\n'
        html_buffer += f'<th class="w3-center">{m2_projected:.1f}</th>\n'

    html_buffer += "</tr>\n"

    html_buffer += "</table>\n"

    html_buffer += "<br>\n"
    html_buffer += '<table class="w3-table w3-hoverable w3-white">\n'

    if data["common"]:
        html_buffer += f'<tr><th class="w3-center">You both have</th><th class="w3-center">Points</th><th class="w3-center">Projected</th><th class="w3-center">Remaining</th></tr>\n'
        for p in data["common"]:
            html_buffer += player_row(gw, p)
        if len(data["common"]) > 1:
            html_buffer += "<tr>\n"
            html_buffer += '<td class="w3-center">Total:</td>\n'
            html_buffer += f'<td class="w3-center">{sum([p.get_event_score(gw=gw, not_playing_is_none=False) for p in data["common"]])}</td>\n'
            html_buffer += f'<td class="w3-center">{sum([p.projected_points for p in data["common"]]):.1f}</td>\n'
            html_buffer += '<td class="w3-center"></td>\n'
            html_buffer += "</tr>\n"

        html_buffer += "</table>\n"
        html_buffer += "<br>\n"

    if data["m1"]:
        html_buffer += '<table class="w3-table w3-hoverable w3-white">\n'
        html_buffer += f'<tr><th class="w3-center">Only you have</th><th class="w3-center">Points</th><th class="w3-center">Projected</th><th class="w3-center">Remaining</th></tr>\n'
        for d in data["m1"]:
            p = d["player"]
            html_buffer += player_row(gw, p, d["m_diff"])
        if len(data["m1"]) > 1:
            html_buffer += "<tr>\n"
            html_buffer += '<td class="w3-center">Total:</td>\n'
            html_buffer += f'<td class="w3-center">{sum([d["player"].get_event_score(gw=gw, not_playing_is_none=False) * d["m_diff"] for d in data["m1"]])}</td>\n'
            html_buffer += f'<td class="w3-center">{sum([d["player"].projected_points * d["m_diff"] for d in data["m1"]]):.1f}</td>\n'
            html_buffer += '<td class="w3-center"></td>\n'
            html_buffer += "</tr>\n"

    if data["m2"]:
        html_buffer += '<table class="w3-table w3-hoverable w3-white">\n'
        html_buffer += f'<tr><th class="w3-center">Only opponent has</th><th class="w3-center">Points</th><th class="w3-center">Projected</th><th class="w3-center">Remaining</th></tr>\n'
        for d in data["m2"]:
            p = d["player"]
            html_buffer += player_row(gw, p, d["m_diff"])
        if len(data["m2"]) > 1:
            html_buffer += "<tr>\n"
            html_buffer += '<td class="w3-center">Total:</td>\n'
            html_buffer += f'<td class="w3-center">{sum([d["player"].get_event_score(gw=gw, not_playing_is_none=False) * d["m_diff"] for d in data["m2"]])}</td>\n'
            html_buffer += f'<td class="w3-center">{sum([d["player"].projected_points * d["m_diff"] for d in data["m2"]]):.1f}</td>\n'
            html_buffer += '<td class="w3-center"></td>\n'
            html_buffer += "</tr>\n"

    html_buffer += "</table>\n"
    html_buffer += "<br>\n"

    return html_buffer


def player_row(gw, p, m_diff=1, not_started_only=False):
    html_buffer = ""
    html_buffer += "<tr>\n"
    if m_diff != 1:
        prepend = f"{m_diff} x "
    else:
        prepend = None
    html_buffer += player_name_cell(p, prepend=prepend)

    score = p.get_event_score()

    if score is None:
        html_buffer += f'<td class="w3-center">-</td>\n'
        score = 0
    else:
        style_str = (
            get_style_from_event_score(score).rstrip('"') + ';vertical-align:middle;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>{score:.0f}</td>\n'

    # exp = p.expected_points(gw=gw, not_started_only=not_started_only) # + score
    exp = p.projected_points

    # print(p, exp, score)

    style_str = get_style_from_event_score(exp).rstrip('"') + ';vertical-align:middle;"'

    html_buffer += f'<td class="w3-center" style={style_str}>{exp:.1f}</td>\n'

    html_buffer += '<td class="w3-center">\n'
    # html_buffer += f'{p.get_event_summary(gw=gw, pts_line=False)}\n'
    html_buffer += f"{p.get_fixture_str(gw=gw, short=True)}\n"
    html_buffer += "</td>\n"
    html_buffer += "</tr>\n"
    return html_buffer


def player_name_cell(p, prepend=None):
    # name
    html_buffer = ""
    bg_color = p.team_obj.get_style()["background-color"]
    text_color = p.team_obj.get_style()["color"]
    style_str = (
        f'"background-color:{bg_color};color:{text_color};vertical-align:middle;"'
    )
    html_buffer += f"<td style={style_str}>\n"
    if prepend:
        html_buffer += prepend
    html_buffer += f'<img class="w3-image" src="{p.team_obj._badge_url}" alt="{p.team_obj.shortname}" width="20" height="20">\n'
    html_buffer += (
        f'<a href="{p._gui_url}"><b> {p.name}</a>\n'
    )
    if p.is_yellow_flagged:
        html_buffer += f" ⚠️"
    elif p.is_red_flagged:
        html_buffer += f" ⛔️"
    html_buffer += f"</b></td>\n"
    return html_buffer
