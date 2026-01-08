#!/usr/bin/env python3

import markdown
import mout

player_modals = {}
player_history_tables = {}


def md2html(md):
    html = markdown.markdown(md, extensions=["extra"])
    html = fix_image_links(html)
    html = fix_table_classes(html)
    html = fix_column_divs(html)
    return html


def fix_column_divs(html):
    # html = html.replace("<h1>_tag_div_class_row</h1>",'<div class="row">')
    # html = html.replace("<h1>_tag_div_class_column</h1>",'<div class="column">')
    # html = html.replace("<h1>_tag_enddiv</h1>",'</div>')

    html = html.replace("<h1>_tag_div_class_column</h1>", '<div class="w3-col s12 m6">')
    html = html.replace("<h1>_tag_enddiv</h1>", "</div>")
    return html


def fix_image_links(html):
    """
    [[https://github.com/mwinokan/FPL_GUI/blob/main/kits/Newcastle.png]]

                                    |
                                    V

    <img class="w3-image" src="/w3images/jane.jpg" alt="Fashion Blog" width="1600" height="1060">
    """
    html = html.replace("[[https://", '<img class="w3-image" src="https://')
    html = html.replace(
        ".png]]", '.png?raw=true" alt="Kit Icon" width="22" height="29">'
    )
    return html

    # https://github.com/mwinokan/FPL_GUI/blob/main/kits/Newcastle.png?raw=true


def fix_table_classes(html):
    # https://www.w3schools.com/w3css/w3css_tables.asp

    """
    <table>    --> 		<table class="w3-table-all w3-hoverable">
    """

    html = html.replace(
        "<table>",
        '<div class="w3-responsive">\n<table class="w3-table w3-hoverable responsive-text">',
    )
    html = html.replace("</table>", "</table>\n</div>")
    return html


# @mout.debug_time
def html_page(
    target,
    mdfile=None,
    title="FPL_GUI",
    sidebar_content=None,
    gw=None,
    html=None,
    showtitle=True,
    bar_html=None,
    extra_style=None,
    colour="white",
    nonw3_colour=False,
    plotly=False,
    text_colour="black",
    timestamp=False,
    live=None,
):
    mout.debugOut(f"html_page({target})")

    if mdfile is None:
        html_content = html
    else:
        with open(mdfile, "rt") as fin:
            html_content = md2html(fin.read())

    sidebar_html = ""
    if sidebar_content is not None:
        sidebar_html = md2html(sidebar_content)

    fout_buffer = []

    fout_buffer.append("<!DOCTYPE html>\n")
    fout_buffer.append("<html>\n")
    fout_buffer.append("<head>\n")
    fout_buffer.append(f"<title>{title}</title>\n")
    fout_buffer.append('<meta charset="UTF-8">\n')
    fout_buffer.append(
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    )
    fout_buffer.append(
        '<link rel="stylesheet" href="https://www.w3schools.com/w3css/5/w3.css">\n'
    )
    fout_buffer.append(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Oswald">\n'
    )
    fout_buffer.append(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Open Sans">\n'
    )
    fout_buffer.append(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">\n'
    )
    if plotly:
        fout_buffer.append(
            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n'
        )
    fout_buffer.append("<style>\n")
    fout_buffer.append('h1,h2,h3,h4,h5,h6 {font-family: "Oswald"}')
    fout_buffer.append('body {font-family: "Open Sans"}\n')
    fout_buffer.append("h5.double {line-height: 2}\n")
    fout_buffer.append("/*drop shadow*/\n")
    fout_buffer.append(
        ".shadow10 {box-shadow: rgba(0, 0, 0, 0.25) 0px 54px 55px, rgba(0, 0, 0, 0.12) 0px -12px 30px, rgba(0, 0, 0, 0.12) 0px 4px 6px, rgba(0, 0, 0, 0.17) 0px 12px 13px, rgba(0, 0, 0, 0.09) 0px -3px 5px;}\n"
    )
    fout_buffer.append("/*drop shadow*/\n")
    fout_buffer.append(".shadow20 {box-shadow: rgb(38, 57, 77) 0px 20px 30px -10px;}\n")
    fout_buffer.append("/*inner shadow*/\n")
    fout_buffer.append(
        ".shadow25 {box-shadow: rgba(50, 50, 93, 0.25) 0px 30px 60px -12px inset, rgba(0, 0, 0, 0.3) 0px 18px 36px -18px inset;}\n"
    )
    fout_buffer.append("/*pink effect*/\n")
    fout_buffer.append(
        ".shadow50 {box-shadow: rgba(240, 46, 170, 0.4) 5px 5px, rgba(240, 46, 170, 0.3) 10px 10px, rgba(240, 46, 170, 0.2) 15px 15px, rgba(240, 46, 170, 0.1) 20px 20px, rgba(240, 46, 170, 0.05) 25px 25px;}\n"
    )
    fout_buffer.append("/*soft inner and outer*/\n")
    fout_buffer.append(
        ".shadow87 {box-shadow: rgba(0, 0, 0, 0.17) 0px -23px 25px 0px inset, rgba(0, 0, 0, 0.15) 0px -36px 30px 0px inset, rgba(0, 0, 0, 0.1) 0px -79px 40px 0px inset, rgba(0, 0, 0, 0.06) 0px 2px 1px, rgba(0, 0, 0, 0.09) 0px 4px 2px, rgba(0, 0, 0, 0.09) 0px 8px 4px, rgba(0, 0, 0, 0.09) 0px 16px 8px, rgba(0, 0, 0, 0.09) 0px 32px 16px;}\n"
    )
    fout_buffer.append("/*button shadow*/\n")
    fout_buffer.append(
        ".shadow89 {box-shadow: rgba(0, 0, 0, 0.4) 0px 2px 4px, rgba(0, 0, 0, 0.3) 0px 7px 13px -3px, rgba(0, 0, 0, 0.2) 0px -3px 0px inset;}\n"
    )
    fout_buffer.append(
        "@media screen and (min-width: 601px) { .responsive-text { font-size: 16px;  } }"
    )
    fout_buffer.append(
        "@media screen and (max-width: 600px) { .responsive-text { font-size: 12px;  } }"
    )
    fout_buffer.append(
        "@media screen and (max-width: 600px) { .hide-if-narrow { display: none !important; } }"
    )

    if extra_style is not None:
        fout_buffer.append(extra_style)
    fout_buffer.append("</style>\n")
    fout_buffer.append("</head>\n")

    # BAR
    if bar_html is not None:
        fout_buffer.append(bar_html)

    # BODY
    if nonw3_colour:
        fout_buffer.append(
            f'<body class="shadow25" style="background-color:{colour};color:{text_colour}">\n'
        )
    else:
        fout_buffer.append(f'<body class="w3-{colour} shadow25">\n')

    # CONTENT
    fout_buffer.append(
        '<div class="w3-content" style="max-width:1400px;min-height:1200px;">\n'
    )

    # TITLE
    if showtitle:
        fout_buffer.append('<div class="w3-center w3-padding-large">\n')
        if colour == "white":
            fout_buffer.append(
                f'\t<h1><span class="w3-tag w3-black shadow50">{title}</span></h1>\n'
            )
        else:
            fout_buffer.append(
                f'\t<h1><span class="w3-tag w3-white shadow50">{title}</span></h1>\n'
            )
        fout_buffer.append("</div>\n")

    # HTML
    fout_buffer.append(
        '<div class="w3-row-padding" style="padding-left:0px;padding-right:0px">\n'
    )
    fout_buffer.append(html_content)
    fout_buffer.append("</div>\n")

    # END CONTENT
    fout_buffer.append("</div>\n")
    # END BODY
    # fout_buffer.append('</body>\n')

    fout_buffer.append('<div class="w3-center" style="padding:32px">\n')
    # fout_buffer.append('<footer class="w3-container w3-black w3-center" style="padding:32px">\n')
    if timestamp:
        from datetime import datetime

        timestamp = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        if live:
            live = " live"
        else:
            live = ""
        fout_buffer.append(f"<p>Accurate as of {timestamp}, (GW{gw}{live})</p>\n")
    fout_buffer.append(
        '<p>Max Winokan <span class="w3-tag w3-black">mwinokan@me.com</span></a></p>\n'
    )
    # fout_buffer.append('</footer>\n')
    fout_buffer.append("</div>\n")
    fout_buffer.append("</body>\n")
    fout_buffer.append("</html>\n")

    with open(target, "wt") as fout:
        fout.writelines("".join(fout_buffer))


def player_summary_cell_modal(player, gw):

    global player_modals

    if player.id not in player_modals.keys():
        player_modals[player.id] = {}

    if gw not in player_modals[player.id].keys():

        score, summary = player.get_event_score(
            gw, summary=True, md_bold=False, return_str=True
        )

        summary = summary.replace("\n", "</p>\n<p>")
        summary = "<p>" + summary + "</p>"

        html_buffer = ""

        status = None
        if score in ["Did not play", "Bench", "Yet to play"]:
            status = score
            score = None

        if score is not None:
            style_str = (
                get_style_from_event_score(score).rstrip('"')
                + ';vertical-align:middle;"'
            )
        if gw == player._api.current_gw and player.multiplier == 0:
            stag = "<s>"
            etag = "</s>"
        else:
            stag = ""
            etag = ""

        id = f"id{player.id}_{gw}"

        html_buffer += """<td onclick="document.getElementById('"""
        html_buffer += f"{id}"
        html_buffer += """').style.display='block'" class="w3-center" """

        if score is None:
            if status == "Did not play":
                html_buffer += f' style="vertical-align:middle;">x'
            elif status == "Bench":
                html_buffer += f' style="vertical-align:middle;">🪑'
            elif status == "Yet to play":
                html_buffer += f' style="vertical-align:middle;">-'
            else:
                html_buffer += f' style="vertical-align:middle;">o'
        else:
            html_buffer += f" style={style_str}>"
            html_buffer += f"{stag}{score}{etag}"

        html_buffer += f"</td>"
        html_buffer += f'<div id="{id}" class="w3-modal">'
        html_buffer += f'<div class="w3-modal-content">'
        html_buffer += f'<div class="w3-container">'
        html_buffer += """<span onclick="document.getElementById('"""
        html_buffer += f"{id}"
        html_buffer += """').style.display='none'" class="w3-button w3-display-topright">&times;</span>"""
        html_buffer += f"<h3>{player.name} in GW{gw}</h3>"
        html_buffer += f"{summary}"

        # history table

        html_buffer += f"</div>"
        html_buffer += f"</div>"
        html_buffer += f"</div>"

        player_modals[player.id][gw] = html_buffer

    return player_modals[player.id][gw]


def get_player_history_table(player):
    """Add fixture scores/results"""

    global player_history_tables

    if player.id not in player_history_tables.keys():

        html_buffer = ""

        html_buffer += '<div class="w3-responsive">\n'
        html_buffer += '<table class="w3-table-all w3-hoverable">\n'
        html_buffer += "<thead>\n"
        html_buffer += "<tr>\n"
        html_buffer += '<th class="w3-center">GW</th>\n'
        html_buffer += '<th class="w3-center">Opponent</th>\n'
        html_buffer += '<th class="w3-center">xPts.</th>\n'
        html_buffer += '<th class="w3-center">Score</th>\n'
        html_buffer += "<th>Summary</th>\n"
        html_buffer += "</tr>\n"
        html_buffer += "</thead>\n"
        html_buffer += "<tbody>\n"

        now_gw = player._api._current_gw
        # start_gw = max(1,now_gw-prev_gw_count)
        # end_gw = min(38,now_gw+next_gw_count)

        # for gw in range(1,now_gw+1):
        for gw in range(1, 39):

            if gw == now_gw:
                html_buffer += f'<tr class="w3-green">\n'
            else:
                html_buffer += f"<tr>\n"

            html_buffer += f'<td class="w3-center">'
            html_buffer += f"{gw}"
            html_buffer += f"</td>\n"

            # difficulty = player.get_fixture_diff(gw,old=True,overall=False)
            # style_str = get_style_from_difficulty(difficulty,old=True)
            # if style_str is None:
            # style_str == ""
            style_str = ""
            flag_str = ""
            chance = player.get_playing_chance(gw)
            if chance < 0.25:
                flag_str = "⛔️ "
            elif chance < 1:
                flag_str = "⚠️ "
            html_buffer += f'<td class="w3-center" style={style_str}>'
            opp = player.team_obj.get_opponent(gw)
            if opp is not None:
                fixs = player.team_obj.get_gw_fixtures(gw)
                if isinstance(fixs, list):
                    many = True
                    is_home = False
                else:
                    many = False
                    is_home = player.team_obj.get_gw_fixtures(gw)["team_a"] == opp.id

                if many:
                    opp_strs = []
                    for o in opp:
                        opp_strs.append(o.shortname)
                    opp_str = " ".join(opp_strs)
                else:
                    opp_str = opp.shortname
                    if is_home:
                        opp_str += " (H)"
                    else:
                        opp_str += " (A)"
                    html_buffer += f'<img class="w3-image" src="{opp._badge_url}" alt="{opp.shortname}" width="20" height="20"> '
                html_buffer += f"{opp_str}{flag_str}"
            else:
                html_buffer += f"-"
            html_buffer += "</td>\n"

            # html_buffer += f'<td class="w3-center">'
            # html_buffer += f'{player.expected_points(gw=gw)}'
            # html_buffer += f'</td>\n'

            html_buffer += """<td class="w3-center" """
            exp = player.expected_points(gw=gw)
            style_str = get_style_from_event_score(exp)
            html_buffer += f" style={style_str}>"
            html_buffer += f"{exp:.1f}"
            html_buffer += f"</td>\n"

            if gw <= now_gw:

                score, summary = player.get_event_score(
                    gw,
                    summary=True,
                    md_bold=True,
                    return_str=True,
                    pts_line=False,
                    team_line=False,
                )

                # summary = summary.replace("\n","<br>")
                summary = summary.replace("\n", " ")

                status = None
                if score in ["Did not play", "Bench", "Yet to play"]:
                    status = score
                    score = None

                if score is not None:
                    style_str = get_style_from_event_score(score)

                html_buffer += """<td class="w3-center" """

                if score is None:
                    if status == "Did not play":
                        html_buffer += f' style="">x'
                    elif status == "Bench":
                        html_buffer += f' style="">🪑'
                    elif status == "Yet to play":
                        html_buffer += f' style="">-'
                    else:
                        html_buffer += f' style="">o'
                else:
                    html_buffer += f" style={style_str}>"
                    html_buffer += f"{score}"
                html_buffer += f"</td>\n"

                html_buffer += "<td>"
                html_buffer += f"{summary}"
                html_buffer += "</td>\n"

            # else:
            # 	html_buffer += '<td class="w3-center">'
            # 	html_buffer += '-'
            # 	html_buffer += '</td>\n'
            # 	html_buffer += '<td class="w3-center">'
            # 	html_buffer += '-'
            # 	html_buffer += '</td>\n'

            html_buffer += f"</tr>\n"

        html_buffer += f"</tbody>\n"
        html_buffer += f"</table>\n"
        html_buffer += f"</div>\n"

        # print(player.fixtures)

        player_history_tables[player.id] = html_buffer

    return player_history_tables[player.id]


# def get_style_from_event_score(score,border=False):
# 	if border:
# 		style_str = '"'
# 	else:
# 		style_str = '"'
# 	if score is None:
# 		style_str += 'background-color:black;color:white'
# 	elif score < 1:
# 		style_str += 'background-color:darkred;color:white'
# 	elif score == 2:
# 		style_str += 'background-color:orange;color:black'
# 	elif score > 9:
# 		style_str += 'background-color:darkgreen;color:white'
# 	elif score > 5:
# 		style_str += 'background-color:lightgreen;color:black'
# 	elif score > 2:
# 		style_str += 'background-color:yellow;color:black'
# 	elif score > 0:
# 		style_str += 'background-color:red;color:black'
# 	style_str += '"'
# 	return style_str


def get_style_from_event_score(score):
    style_str = '"'
    if score is None:
        # blackish
        style_str += "background-color:#17202A;color:white"
    elif score < 1:
        # dark red
        style_str += "background-color:#901517;color:white"
    elif score == 2:
        # orange
        style_str += "background-color:#DC7633;color:black"
    elif score > 9:
        # dark green
        style_str += "background-color:#196F3D;color:white"
    elif score > 5:
        # green
        style_str += "background-color:#52BE80;color:black"
    elif score > 2:
        # yellow
        style_str += "background-color:#F4D03F;color:black"
    elif score > 0:
        # red
        style_str += "background-color:#CB4335;color:black"
    style_str += '"'
    return style_str


def get_style_from_minutes_played(minutes):
    style_str = '"'
    if minutes is None:
        # blackish
        style_str += "background-color:#17202A;color:white"

    elif minutes > 89:
        # dark green
        style_str += "background-color:#196F3D;color:white"

    elif minutes > 59:
        # green
        style_str += "background-color:#52BE80;color:black"

    elif minutes > 29:
        # yellow
        style_str += "background-color:#F4D03F;color:black"

    elif minutes > 19:
        # orange
        style_str += "background-color:#DC7633;color:black"

    elif minutes > 9:
        # red
        style_str += "background-color:#CB4335;color:black"

    else:
        # dark red
        style_str += "background-color:#901517;color:white"

    style_str += '"'
    return style_str


def get_style_from_expected_return(value):
    style_str = '"'
    if value is None:
        # blackish
        style_str += "background-color:#17202A;color:white"

    elif value > 0.99:
        # dark green
        style_str += "background-color:#196F3D;color:white"

    elif value > 0.39:
        # green
        style_str += "background-color:#52BE80;color:black"

    elif value > 0.19:
        # yellow
        style_str += "background-color:#F4D03F;color:black"

    elif value > 0.09:
        # orange
        style_str += "background-color:#DC7633;color:black"

    elif value > 0.00:
        # red
        style_str += "background-color:#CB4335;color:black"

    else:
        # dark red
        style_str += "background-color:#901517;color:white"

    style_str += '"'
    return style_str


def get_style_from_xDCpts(value):
    style_str = '"'
    if value is None:
        # blackish
        style_str += "background-color:#17202A;color:white"

    elif value > 2 * 0.99:
        # dark green
        style_str += "background-color:#196F3D;color:white"

    elif value > 2 * 0.39:
        # green
        style_str += "background-color:#52BE80;color:black"

    elif value > 2 * 0.19:
        # yellow
        style_str += "background-color:#F4D03F;color:black"

    elif value > 2 * 0.09:
        # orange
        style_str += "background-color:#DC7633;color:black"

    elif value > 2 * 0.00:
        # red
        style_str += "background-color:#CB4335;color:black"

    else:
        # dark red
        style_str += "background-color:#901517;color:white"

    style_str += '"'
    return style_str


def get_style_from_bonus(value):
    style_str = '"'
    if value is None:
        # blackish
        style_str += "background-color:#17202A;color:white"

    elif value > 2.49:
        # dark green
        style_str += "background-color:#196F3D;color:white"

    elif value > 2.00:
        # green
        style_str += "background-color:#52BE80;color:black"

    elif value > 1.49:
        # yellow
        style_str += "background-color:#F4D03F;color:black"

    elif value > 0.99:
        # orange
        style_str += "background-color:#DC7633;color:black"

    elif value > 0.49:
        # red
        style_str += "background-color:#CB4335;color:black"

    else:
        # dark red
        style_str += "background-color:#901517;color:white"

    style_str += '"'
    return style_str
