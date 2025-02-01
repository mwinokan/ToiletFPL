#!/usr/bin/env python

import pytz
from league import League
import api as fpl_api
import plot
from collections import Counter
import mout
from player import Player
from manager import Manager
import json as js
from web import (
    html_page,
    player_summary_cell_modal,
    get_style_from_event_score,
    md2html,
    get_player_history_table,
    get_style_from_minutes_played,
    get_style_from_expected_return,
    get_style_from_bonus,
)
from squad import Squad
import time
from pprint import pprint
from sys import argv
import mrich

# https://stackoverflow.com/questions/60598837/html-to-image-using-python

from datetime import datetime

timestamp = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

# deployment configuration
DEPLOY_ROOT = "mwinokan.github.io/ToiletFPL"
JSON_PATH = "data_wiki_2425.json"  # store the award data in this JSON
TAGLINE = "Home of the RBS Diamond Invitational and Tesco Bean Value Toilet League"

# run options
run_push_changes = False  # push changes to github
test = False  # only run the 'run_test' function
offline = False  # use cached request data

### other options
force_generate_kits = False  # force the generation of manager's kits
scrape_kits = False  # scrape latest PL team jerseys and exit
fetch_latest = False  # pull latest changes from github before running
force_go_graphs = True  # force update of Assets graph

# gamestate options (to be automated)
halfway_awards = True  # generate half-season / christmas awards
season_awards = False  # generate full-season awards
cup_active = False  # activate the cup

christmas_gw = 17

if "--push" in argv:
    run_push_changes = True
if "--offline" in argv:
    offline = True
if "--kits" in argv:
    scrape_kits = True
if "--test" in argv:
    test = True

# configure the leagues

# 23/24
league_codes = [352961, 241682, 1678697, 352258]
league_icons = ["💎", "🚽", "🧭", "🍝"]
league_shortnames = ["Diamond", "Toilet", "SOLENT", "Dinner"]
league_colours = ["aqua", "dark-grey", "indigo", "dark-grey"]

award_flavourtext = dict(
    king="👑 King",
    cock="🐓 Cock",
    goals="⚽️ Massive Goal FC",
    boner="🦴 Boner",
    scientist="🧑‍🔬 Scientist",
    smooth_brain="🧠 Smooth Brain",
    chair="🪑 Chair",
    minutes="👹 Minutes Monster",
    asbo="🥊 ASBO",
    nerd="🤓 Nerd",
    hot_stuff="🥵 Hot Stuff",
    soggy_biscuit="🍪 Soggy Biscuit",
    innovator="🎓 Innovator",
    fortune="🔮 Fortune Teller",
    clown="🤡 Clown",
    oligarch="🛢 Oligarch",
    iceman="🥶 Iceman",
    peasant="🏚 Peasant",
    glow_up="💡 Glow-Up",
    has_been="👨‍🦳 Has-Been",
    kneejerker="🔨 Kneejerker",
    rocket="🚀 Rocket",
    flushed="🚽 #DownTheToilet",
    wc1_best="Best Wildcard 1",
    wc1_worst="Worst Wildcard 1",
    wc2_best="Best Wildcard 2",
    wc2_worst="Worst Wildcard 2",
    tc_best="Best Triple Captain",
    tc_worst="Worst Triple Captain",
    bb_best="Best Bench Boost",
    bb_worst="Worst Bench Boost",
    fh_best="Best Free Hit",
    fh_worst="Worst Free Hit",
    zombie="Best Dead Team",
)

award_unittext = dict(
    king="points",
    cock="points",
    goals="goals",
    boner="points",
    scientist="points",
    smooth_brain="points on the bench",
    chair="'",
    minutes="'",
    asbo="cards",
    nerd="%",
    innovator="%",
    rocket="%",
    flushed="%",
    fortune="points gained",
    clown="points lost",
    hot_stuff="points overperformed",
    soggy_biscuit="points underperformed",
    zombie="th place",
)

award_colour = dict(
    king="amber",
    cock="red",
    goals="indigo",
    scientist="green",
    boner="grey",
    smooth_brain="pale-red",
    chair="light-blue",
    minutes="deep-orange",
    asbo="yellow",
    fortune="purple",
    clown="pink",
    nerd="pale-yellow",
    innovator="grey",
    oligarch="black",
    iceman="aqua",
    peasant="brown",
    glow_up="pale-yellow",
    has_been="grey",
    kneejerker="deep-orange",
    wc1_best="red",
    wc1_worst="red",
    wc2_best="red",
    wc2_worst="red",
    tc_best="yellow",
    tc_worst="yellow",
    bb_best="blue",
    bb_worst="blue",
    fh_best="green",
    fh_worst="green",
    hot_stuff="orange",
    soggy_biscuit="teal",
    rocket="lime",
    flushed="brown",
    zombie="teal",
)

_league_table_html = {}

brk = "</p><p>"

league_halfway_text = {
    352961: f"PLACEHOLDER DIAMOND CHRISTMAS REVIEW",
    241682: f"PLACEHOLDER TOILET CHRISTMAS REVIEW",
}
league_season_text = {
    352961: f"PLACEHOLDER DIAMOND SEASON REVIEW",
    241682: f"PLACEHOLDER TOILET SEASON REVIEW",
}

preseason = False

completed_playerpages = []

mout.showDebug()

api = None
json = {}


def main():
    mout.debugOut("main()")
    import os

    if offline:
        os.system(
            f"terminal-notifier -title 'ToiletFPL' -message 'Started Wiki Update [OFFLINE]' -open 'index.html'"
        )
    else:
        os.system(
            f"terminal-notifier -title 'ToiletFPL' -message 'Started Wiki Update' -open 'index.html'"
        )

    if fetch_latest:
        pull_changes()

    global api
    api = fpl_api.FPL_API(
        offline=offline,
        quick=False,
        force_generate_kits=force_generate_kits,
        write_offline_data=True,
    )

    global halfway_awards
    if api._current_gw == 18 and not api._live_gw:
        halfway_awards = True

    global preseason
    preseason = api._current_gw < 1

    api._skip_kits = False

    global json
    json = load_json()
    if len(json) == 0:
        json = {}

    if test:
        run_test()

    if scrape_kits:
        api.scrape_team_kits()
        exit()

    extra_managers = None

    leagues = []
    for icon, code, colour, shortname in zip(
        league_icons, league_codes, league_colours, league_shortnames
    ):
        try:
            leagues.append(League(code, api))
            leagues[-1]._icon = icon
            leagues[-1]._shortname = shortname
            leagues[-1]._colour_str = colour
        except fpl_api.Request404:
            mout.error(f"Could not init League({code},{shortname})")

    leagues[1]._skip_awards.append(3900121)

    if api._current_gw < 38:
        create_comparison_page(api, leagues)

    navbar = create_navbar(leagues, path_root="html/")

    create_homepage(navbar)

    navbar = create_navbar(leagues)

    for i, l in enumerate(leagues):
        create_leaguepage(l, leagues, i)

    if cup_active:
        create_cup_page(api, leagues[1], leagues)

    if not api._live_gw or any(
        [f["started"] for f in api.get_gw_fixtures(api._current_gw)]
    ):
        generate_summary_template(api, leagues[1])

    create_teampage(api, leagues)

    if halfway_awards:
        # create_christmaspage(leagues)
        pass

    if season_awards:
        create_seasonpage(leagues)

    json["timestamp"] = timestamp

    dump_json(json)
    json = load_json()

    get_manager_json_awards(api, leagues)

    count = 0
    mout.debugOut("main()::ManagerPages")
    mout.hideDebug()
    maximum = len(api._managers)
    for i, m in enumerate(api._managers.values()):
        mout.progress(i, maximum)

        if m.valid:
            create_managerpage(api, m, leagues)

    mout.progress(maximum, maximum)
    mout.showDebug()

    count = 0
    mout.debugOut("main()::PlayerPages")
    mout.hideDebug()
    maximum = len(api._loaded_players)
    for pid in api._loaded_players:
        mout.progress(count, maximum, append=f" {count}/{maximum}")
        pid = int(pid)
        create_playerpage(
            api, Player(None, index=api.get_player_index(pid), api=api), leagues
        )
        count += 1
    mout.progress(maximum, maximum)
    mout.showDebug()

    create_assetpage(leagues)

    api.finish()

    if run_push_changes:
        push_changes()


def test_christmas():
    leagues = []
    for icon, code, colour, shortname in zip(
        league_icons, league_codes, league_colours, league_shortnames
    ):
        try:
            leagues.append(League(code, api))
            leagues[-1]._icon = icon
            leagues[-1]._shortname = shortname
            leagues[-1]._colour_str = colour
        except fpl_api.Request404:
            mout.error(f"Could not init League({code},{shortname})")

    for i, l in enumerate(leagues):
        create_leaguepage(l, leagues, i)

    create_christmaspage(leagues)


def run_test():

    # push_changes()
    # test_christmas()

    # print(api.fixtures.columns)

    # print(api.get_gw_fixtures(6))

    # print(api.elements_by_team['MCI'])

    # print(api.get_player_team_obj(15))
    # print(api.get_player_team_obj(17))

    # print(api.elements.columns)
    # print(api.get_player_index(664))
    # pprint(api.elements['web_name'][api.get_player_index(664)])

    # p = Player('Maddison',api)

    # s = p.get_event_score(8,debug=True)

    # print(p,s)

    p = Player("Iraola", api)

    s = p.get_event_score(23, debug=True)

    s2 = p.get_event_summary(23, html_highlight=False)

    create_playerpage(api, p, [])

    print(p, s)
    print(s2)

    # create_comparison_page(api,[])

    # l = League(352961, api)

    # print(l.last_gw_position_dict)

    # create_leaguepage(l,[],0)

    # p = Player('Havertz',api)

    # create_playerpage(api,p,[])

    # leagues = []
    # for icon,code,colour,shortname in zip(league_icons,league_codes,league_colours,league_shortnames):
    # 	try:
    # 		leagues.append(League(code,api))
    # 		leagues[-1]._icon = icon
    # 		leagues[-1]._shortname = shortname
    # 		leagues[-1]._colour_str = colour
    # 	except fpl_api.Request404:
    # 		mout.error(f'Could not init League({code},{shortname})')

    # # p.expected_points(gw=2,use_official=True,debug=True)
    # # p.new_expected_points(gw=2,use_official=False,debug=True,force=True)
    # man = Manager("Max Winokan", 1327451, api, team_name="Diamond Diogo's", authenticate=False)
    # man = Manager("Max Winokan", 264578, api, team_name="Diamond Diogo's", authenticate=False)
    # create_managerpage(api, man, leagues)

    api.finish()
    exit()


def create_comparison_page(api, leagues, prev_gw_count=5, next_gw_count=5):
    mout.debug(f"create_comparison_page()")

    # instantiate all the player objects
    players = []
    for pid in api._elements["id"]:
        index = api.get_player_index(pid)
        p = Player(None, api, index=index)
        players.append(p)

    players = sorted(players, key=lambda x: x.selected_by, reverse=True)

    html_buffer = ""

    ### SEARCH BOX
    html_buffer += '<div class="w3-col s12 m12 l12">\n'
    html_buffer += '<div class="w3-panel w3-black shadow89 w3-padding" style="padding:0px;padding-bottom:3px;">\n'

    html_buffer += (
        f'<h3><i class="fa fa-search"></i> Search for and click to add players: </h3>\n'
    )
    html_buffer += f'<h4><input class="w3-input w3-white shadow25" onkeyup="searchFunction()" id="searchInput" type="text" placeholder="Search players by name..."></h4>\n'
    html_buffer += f"</div>\n"
    html_buffer += f"</div>\n"

    html_buffer += f'<div class="w3-padding w3-center" id="searchTable">\n'
    for p in players:

        team_bg_color = p.team_obj.get_style()["background-color"]
        team_text_color = p.team_obj.get_style()["color"]
        team_style_str = f'"background-color:{team_bg_color};color:{team_text_color};margin-bottom:5px;"'

        html_buffer += f'<span style="display:none;">\n'
        html_buffer += f'<button class="w3-button" onclick="addPlayer({p.id})" style={team_style_str}>\n'
        html_buffer += f'<img class="w3-image" src="{p.team_obj._badge_url}" alt="{p.team_obj.shortname}" width="20" height="20">\n'
        html_buffer += f" {p.full_name}</button>\n"
        html_buffer += f"</span>\n"

    html_buffer += f"</div>\n"

    ### ADD PLAYER SCRIPTING
    html_buffer += "<script>\n"
    html_buffer += "function addPlayer(id) {\n"
    html_buffer += "  var id;\n"
    html_buffer += '  tr = document.getElementById("statRow"+id);\n'
    html_buffer += '  tr.style.display = "";\n'
    html_buffer += '  tr = document.getElementById("graphDiv");\n'
    html_buffer += '  tr.style.display = "";\n'
    html_buffer += "  showPlayerTrace(id);\n"
    html_buffer += "};\n"
    html_buffer += "</script>\n"

    ### REMOVE PLAYER SCRIPTING
    html_buffer += "<script>\n"
    html_buffer += "function removePlayer(id) {\n"
    html_buffer += "  var id;\n"
    html_buffer += '  tr = document.getElementById("statRow"+id);\n'
    html_buffer += '  tr.style.display = "none";\n'
    html_buffer += "  hidePlayerTrace(id);\n"
    html_buffer += "};\n"
    html_buffer += "</script>\n"

    ### SEARCH SCRIPTING (SPANS)
    html_buffer += "<script>\n"
    html_buffer += "function searchFunction() {\n"
    html_buffer += "  var input, filter, table, tr, td, i, txtValue;\n"
    html_buffer += '  input = document.getElementById("searchInput");\n'
    html_buffer += "  filter = input.value.toUpperCase();\n"
    html_buffer += '  table = document.getElementById("searchTable");\n'
    html_buffer += '  tr = table.getElementsByTagName("span");\n'
    html_buffer += "\n"
    html_buffer += "  if (filter.length < 1) {\n"
    html_buffer += "    for (i = 0; i < tr.length; i++) {\n"
    html_buffer += '      td = tr[i].getElementsByTagName("button")[0];\n'
    html_buffer += "      if (td) {\n"
    html_buffer += '        tr[i].style.display = "none";\n'
    html_buffer += "      } \n"
    html_buffer += "    }\n"
    html_buffer += "  } else {\n"
    html_buffer += "    for (i = 0; i < tr.length; i++) {\n"
    html_buffer += '      td = tr[i].getElementsByTagName("button")[0];\n'
    html_buffer += "      if (td) {\n"
    html_buffer += "        txtValue = td.textContent || td.innerText;\n"
    html_buffer += "        if (txtValue.toUpperCase().indexOf(filter) > -1) {\n"
    html_buffer += '          tr[i].style.display = "";\n'
    html_buffer += "        } else {\n"
    html_buffer += '          tr[i].style.display = "none";\n'
    html_buffer += "        }\n"
    html_buffer += "      } \n"
    html_buffer += "    }\n"
    html_buffer += "  }\n"
    html_buffer += "}\n"
    html_buffer += "</script>\n"

    ### STATS DATA
    html_buffer += '<div class="w3-col s12 m12 l12">\n'
    html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive" style="padding:0px;padding-bottom:3px;">\n'

    html_buffer += f'<table class="w3-table responsive-text" id="statTable">\n'

    now_gw = api._current_gw
    start_gw = max(1, now_gw - prev_gw_count)
    end_gw = min(37, now_gw + next_gw_count)

    ### HEADERS
    html_buffer += f"<tr>\n"
    html_buffer += f"<th></th>\n"
    html_buffer += f"<th>Name</th>\n"
    html_buffer += f'<th style="text-align:center;">Price</th>\n'
    html_buffer += f'<th style="text-align:center;">ΣPts</th>\n'
    html_buffer += f'<th style="text-align:center;">Trans.</th>\n'
    html_buffer += f'<th style="text-align:center;">xM</th>\n'
    html_buffer += f'<th style="text-align:center;">xG</th>\n'
    html_buffer += f'<th style="text-align:center;">xA</th>\n'
    html_buffer += f'<th style="text-align:center;">xC</th>\n'
    html_buffer += f'<th style="text-align:center;">xB</th>\n'

    for i in range(start_gw, now_gw + 1):
        html_buffer += f'<th style="text-align:center;">GW{i}</th>\n'

    html_buffer += f'<th style="text-align:center;">Form</th>\n'

    for i in range(now_gw + 1, end_gw + 1):
        html_buffer += f'<th style="text-align:center;">GW{i}</th>\n'

    html_buffer += f"</tr>\n"

    n = len(players)

    ### PLAYER ROWS
    for i, p in enumerate(players):

        mout.progress(i, n)

        html_buffer += f'<tr id="statRow{p.id}" style="display:none;">\n'

        html_buffer += f'<td class="w3-center w3-button w3-black" onclick="removePlayer({p.id})"><i class="fa fa-close"></i></td>\n'

        # name
        bg_color = p.team_obj.get_style()["background-color"]
        text_color = p.team_obj.get_style()["color"]
        style_str = (
            f'"background-color:{bg_color};color:{text_color};vertical-align:middle;"'
        )
        html_buffer += f"<td style={style_str}>\n"
        html_buffer += f'<img class="w3-image" src="{p.team_obj._badge_url}" alt="{p.team_obj.shortname}" width="20" height="20">\n'
        html_buffer += f'<a href="player_{p.id}.html"><b> {p.name}</a>\n'
        if p.is_yellow_flagged:
            html_buffer += f" ⚠️"
        elif p.is_red_flagged:
            html_buffer += f" ⛔️"
        html_buffer += f"</b></td>\n"

        html_buffer += (
            f'<td style="text-align:center;vertical-align:middle;">£{p.price}</td>\n'
        )

        # total points
        if p.appearances < 1:
            score = 0
        else:
            score = p.total_points / p.appearances
        style_str = (
            get_style_from_event_score(score).rstrip('"') + ';vertical-align:middle;"'
        )
        html_buffer += (
            f'<td class="w3-center" style={style_str}>{p.total_points}</td>\n'
        )

        # transfer percent
        value = p.transfer_percent
        text = f"{p.transfer_percent:.1f}%"
        if abs(value) > 10:
            if text.startswith("-"):
                style_str = '"color:darkred;vertical-align:middle;"'
            else:
                style_str = '"color:darkgreen;vertical-align:middle;"'
            html_buffer += (
                f'<td class="w3-center" style={style_str}><b>{text}</b></td>\n'
            )
        else:
            if text.startswith("-"):
                style_str = '"color:red;vertical-align:middle;"'
            else:
                style_str = '"color:green;vertical-align:middle;"'
            html_buffer += f'<td class="w3-center" style={style_str}>{text}</td>\n'

        # minutes
        style_str = (
            get_style_from_minutes_played(p.expected_minutes()).rstrip('"')
            + ';vertical-align:middle;text-align:right;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>'
        if p.xG_no_opponent is None:
            html_buffer += f"-"
        else:
            html_buffer += f"{p.expected_minutes():.0f}"
        html_buffer += "</td>\n"

        # xG
        style_str = (
            get_style_from_expected_return(p.xG_no_opponent).rstrip('"')
            + ';vertical-align:middle;text-align:right;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>'
        if p.xG_no_opponent is None:
            html_buffer += f"-"
        else:
            html_buffer += f"{p.xG_no_opponent:.2f}"
        html_buffer += "</td>\n"

        # xA
        style_str = (
            get_style_from_expected_return(p.xA_no_opponent).rstrip('"')
            + ';vertical-align:middle;text-align:right;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>'
        if p.xA_no_opponent is None:
            html_buffer += f"-"
        else:
            html_buffer += f"{p.xA_no_opponent:.2f}"
        html_buffer += "</td>\n"

        # xCS
        style_str = (
            get_style_from_expected_return(p.xC_no_opponent).rstrip('"')
            + ';vertical-align:middle;text-align:right;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>'
        if p.xC_no_opponent is None:
            html_buffer += f"-"
        else:
            html_buffer += f"{p.xC_no_opponent:.0%}"
        html_buffer += "</td>\n"

        # xB
        style_str = (
            get_style_from_bonus(p.xBpts).rstrip('"')
            + ';vertical-align:middle;text-align:right;border-right: 4px solid white;border-collapse:collapse;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>'
        if p.xBpts is None:
            html_buffer += f"-"
        else:
            html_buffer += f"{p.xBpts:.2f}"
        html_buffer += "</td>\n"

        # previous GWs
        for i in range(start_gw, now_gw + 1):
            html_buffer += player_summary_cell_modal(p, i)

        # form
        form = p.form
        style_str = (
            get_style_from_event_score(form).rstrip('"')
            + ';vertical-align:middle;border-right:4px solid white;border-left:4px solid white;border-collapse:collapse;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>{form}</td>\n'

        # upcoming GWs
        for i in range(now_gw + 1, end_gw + 1):
            exp = p.expected_points(gw=i, debug=False)
            style_str = (
                get_style_from_event_score(exp).rstrip('"') + ';vertical-align:middle;"'
            )
            html_buffer += f'<td class="w3-center" style={style_str}>{p.get_fixture_str(i,short=True,lower_away=True)}</td>\n'

        html_buffer += f"</tr>\n"

    mout.finish()

    html_buffer += f"</table>"

    html_buffer += f"</div>"
    html_buffer += f"</div>"

    ### GRAPH
    html_buffer += '<div class="w3-col s12 m12 l12">\n'
    html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive w3-padding" id="graphDiv" style="display:none;">\n'

    # html_buffer += f'<h3>Expected Points Graph</h3>\n'
    html_buffer += f'<div id="comparisonGraph" style="width:100%;height:500px">\n'
    html_buffer += f"</div>\n"

    ### BUILD THE PLOTTING DATA
    gw_indices = [i + 1 for i in range(now_gw, end_gw + 1)]
    gw_strs = [f"GW{i+1}" for i in range(now_gw, end_gw + 1)]

    plot_data = []
    player_id_to_trace_id = {}
    for i, p in enumerate(players):

        player_id_to_trace_id[p.id] = i

        plot_y = [round(p.expected_points(gw=i), 1) for i in gw_indices]

        plot_data.append(
            dict(
                name=p.name,
                x=gw_strs,
                y=plot_y,
                visible=False,
                mode="lines+markers",
            )
        )

    ### CREATE THE GRAPH
    html_buffer += "<script>\n"
    html_buffer += '	GRAPH = document.getElementById("comparisonGraph");\n'
    html_buffer += f"	Plotly.newPlot( GRAPH, {js.dumps(plot_data)}"
    html_buffer += ', {	title: "Expected Points", margin: { r:0 }, font: {size: 14}} , {responsive: true});\n'
    html_buffer += "</script>\n"

    ### SHOW TRACE SCRIPTING
    html_buffer += "<script>\n"
    html_buffer += "function showPlayerTrace(id) {\n"
    html_buffer += "  var id, player_id_to_trace_id, trace_id;\n"
    html_buffer += f"  player_id_to_trace_id = {js.dumps(player_id_to_trace_id)};\n"
    html_buffer += f"  trace_id = player_id_to_trace_id[id];\n"
    html_buffer += '  Plotly.update(GRAPH, {"visible":true}, {}, [trace_id]);\n'
    html_buffer += "};\n"
    html_buffer += "</script>\n"

    ### HIDE TRACE SCRIPTING
    html_buffer += "<script>\n"
    html_buffer += "function hidePlayerTrace(id) {\n"
    html_buffer += "  var id, player_id_to_trace_id, trace_id;\n"
    html_buffer += f"  player_id_to_trace_id = {js.dumps(player_id_to_trace_id)};\n"
    html_buffer += f"  trace_id = player_id_to_trace_id[id];\n"
    html_buffer += '  Plotly.update(GRAPH, {"visible":false}, {}, [trace_id]);\n'
    html_buffer += "};\n"
    html_buffer += "</script>\n"

    html_buffer += f"</div>\n"
    html_buffer += f"</div>\n"

    ### Help/Explainer
    html_buffer += '<div class="w3-col s12 m6 l6">\n'
    html_buffer += '<div class="w3-panel w3-blue shadow89 w3-responsive w3-padding">\n'

    html_buffer += f"<h3>Legend</h3>"
    html_buffer += f'<span class="w3-tag">T%</span> Net transfer percentage <br><br>\n'
    html_buffer += f'<span class="w3-tag"><sup>1</sup></span> Recent results are weighted higher <br><br>\n'
    html_buffer += (
        f'<span class="w3-tag"><sup>2</sup></span> Not adjusted for opponent <br><br>\n'
    )
    html_buffer += (
        f'<span class="w3-tag">xM</span> Expected Minutes <sup>1</sup><br><br>\n'
    )
    html_buffer += (
        f'<span class="w3-tag">xG</span> Expected Goals <sup>1,2</sup><br><br>\n'
    )
    html_buffer += (
        f'<span class="w3-tag">xA</span> Expected Assists <sup>1,2</sup><br><br>\n'
    )
    html_buffer += (
        f'<span class="w3-tag">xC</span> Expected Clean Sheets <sup>1,2</sup><br><br>\n'
    )
    html_buffer += (
        f'<span class="w3-tag">xB</span> Expected Bonus Points <sup>1,2</sup>\n'
    )

    html_buffer += f"</div>\n"
    html_buffer += f"</div>\n"

    navbar = create_navbar(leagues, colour="black")
    html_page(
        "html/comparison.html",
        None,
        title=f"Comparison Tool",
        gw=api._current_gw,
        html=html_buffer,
        showtitle=True,
        bar_html=navbar,
        colour="aqua",
        plotly=True,
    )


def create_cup_page(api, league, leagues):

    # try and get data pertaining to the cups

    # the page should be a bunch of tables separating by gameweek

    # each table row should contain:

    """

    Team Name  	 | Points         | vs. | Points         | Team Name
    Manager Name | Fixtures/Total |     | Fixtures/Total | Manager Name

    """

    all_matches = []

    mout.debugOut(f"Getting all cup matches in {league.name}...")
    for i, manager in enumerate(league.managers):
        mout.progress(i, league.num_managers, width=50)
        matches = manager.get_cup_matches(league)
        # print(i,manager.name,len(matches))
        all_matches += manager.get_cup_matches(league)
    mout.progress(league.num_managers, league.num_managers, width=50)

    # go by gameweek

    gws = list(set([m["gw"] for m in all_matches]))

    # gws = [gw for gw in gws if gw < 36]

    create_key(json[str(league.id)], "cup")

    total_buffer = ""

    if api._current_gw > 35:

        # total_buffer += floating_subtitle(f'Top 8 brackets',pad=0)

        print("brackets!")

        from cup import process_matches, bracket_table

        final = process_matches(api, [m for m in all_matches if m["gw"] == 38])
        semi_finals = process_matches(api, [m for m in all_matches if m["gw"] == 37])
        quarter_finals = process_matches(api, [m for m in all_matches if m["gw"] == 36])

        ### testing ##########

        # def man(id):
        #     return api.get_manager(id=id)

        # final=(man(264578), man(660251))

        # semi_finals=[
        #    (man(264578), man(5983)),
        #    (man(660251), man(566))
        # ]

        ######################

        total_buffer += bracket_table(
            final=final, semis=semi_finals, quarters=quarter_finals
        )

    # prog_step = (50/len(gws))

    for i, gw in enumerate(sorted(gws, reverse=True)):

        html_buffer = ""

        create_key(json[str(league.id)]["cup"], gw)

        json[str(league.id)]["cup"][gw]["n_diamond_winners"] = 0
        json[str(league.id)]["cup"][gw]["n_diamond_losers"] = 0

        json[str(league.id)]["cup"][gw]["lowest_winner_rank"] = (None, -1)
        json[str(league.id)]["cup"][gw]["highest_winner_rank"] = (None, 1_000_000_000)
        json[str(league.id)]["cup"][gw]["lowest_loser_rank"] = (None, -1)
        json[str(league.id)]["cup"][gw]["highest_loser_rank"] = (None, 1_000_000_000)

        json[str(league.id)]["cup"][gw]["lowest_winner_score"] = (None, 1_000_000_000)
        json[str(league.id)]["cup"][gw]["highest_winner_score"] = (None, -1_000_000_000)
        json[str(league.id)]["cup"][gw]["lowest_loser_score"] = (None, 1_000_000_000)
        json[str(league.id)]["cup"][gw]["highest_loser_score"] = (None, -1_000_000_000)

        matches = [m for m in all_matches if m["gw"] == gw]

        processed = []

        html_buffer += floating_subtitle(f'GW{gw}: {matches[0]["title"]}', pad=0)

        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += '<div class="w3-responsive">\n'
        html_buffer += '<table class="w3-table responsive-text w3-striped">\n'

        # html_buffer += f'<h2>GW{gw} Cup Matches: {matches[0]["title"]}</h2>\n'
        # html_buffer += '<table class="w3-table-all w3-responsive">\n'

        html_buffer += "<tr>\n"

        html_buffer += f'<th class="w3-right">\n'
        html_buffer += f"Player 1\n"
        html_buffer += f"</th>\n"

        html_buffer += f"<th>\n"
        html_buffer += f"</th>\n"
        html_buffer += f"<th>\n"
        html_buffer += f"</th>\n"

        html_buffer += f'<th class="w3-center">\n'
        html_buffer += f"</th>\n"

        html_buffer += f"<th>\n"
        html_buffer += f"</th>\n"
        html_buffer += f"<th>\n"
        html_buffer += f"</th>\n"

        html_buffer += f'<th class="w3-left">\n'
        html_buffer += f"Player 2\n"
        html_buffer += f"</th>\n"

        html_buffer += "</tr>\n"

        for j, match in enumerate(matches):

            # mout.progress(i*prog_step + j*prog_step/len(matches),50,width=50)

            man1 = match["self"]
            man1_score = man1.get_event_score(gw)

            processed.append(man1.id)

            is_bye = match["bye"]

            if not is_bye:

                man2 = match["opponent"]

                if man2.id in processed:
                    continue

                man2_score = man2.get_event_score(gw)

                if match["winner"]:

                    if man1.id == match["winner"]:
                        winner = 1

                    else:
                        winner = 2

                else:

                    if man1_score > man2_score:
                        winner = 1
                    elif man1_score == man2_score:
                        winner = 0
                    else:
                        winner = 2

            else:

                man2 = None
                winner = 1

            html_buffer += "<tr>\n"

            html_buffer += f'<td class="w3-right">\n'
            html_buffer += f'<a href="{man1.gui_url}">{man1.name}</a>'
            if man1.is_diamond:
                html_buffer += "💎"
                if winner == 1:
                    json[str(league.id)]["cup"][gw]["n_diamond_winners"] += 1
                else:
                    json[str(league.id)]["cup"][gw]["n_diamond_losers"] += 1

            html_buffer += f'<br><a href="{man1.gui_url}">{man1.team_name}</a>\n'
            html_buffer += "</td>\n"

            html_buffer += f'<td class="w3-center" style="vertical-align:middle;"><img class="w3-image" src="{man1._kit_path}" alt="Kit Icon" width="22" height="29"></td>\n'

            if winner == 1:
                html_buffer += f'<td class="w3-green w3-center">\n'

                if (r := man1.overall_rank) > json[str(league.id)]["cup"][gw][
                    "lowest_winner_rank"
                ][1]:
                    json[str(league.id)]["cup"][gw]["lowest_winner_rank"] = (
                        man1.id,
                        r,
                        man2.id if man2 else None,
                    )

                if (r := man1.overall_rank) < json[str(league.id)]["cup"][gw][
                    "highest_winner_rank"
                ][1]:
                    json[str(league.id)]["cup"][gw]["highest_winner_rank"] = (
                        man1.id,
                        r,
                        man2.id if man2 else None,
                    )

                if (s := man1.livescore) < json[str(league.id)]["cup"][gw][
                    "lowest_winner_score"
                ][1]:
                    json[str(league.id)]["cup"][gw]["lowest_winner_score"] = (
                        man1.id,
                        s,
                        man2.id if man2 else None,
                    )

                if (s := man1.livescore) > json[str(league.id)]["cup"][gw][
                    "highest_winner_score"
                ][1]:
                    json[str(league.id)]["cup"][gw]["highest_winner_score"] = (
                        man1.id,
                        s,
                        man2.id if man2 else None,
                    )

            else:
                html_buffer += f'<td class="w3-center">\n'

                if (r := man1.overall_rank) > json[str(league.id)]["cup"][gw][
                    "lowest_loser_rank"
                ][1]:
                    json[str(league.id)]["cup"][gw]["lowest_loser_rank"] = (
                        man1.id,
                        r,
                        man2.id if man2 else None,
                    )

                if (r := man1.overall_rank) < json[str(league.id)]["cup"][gw][
                    "highest_loser_rank"
                ][1]:
                    json[str(league.id)]["cup"][gw]["highest_loser_rank"] = (
                        man1.id,
                        r,
                        man2.id if man2 else None,
                    )

                if (s := man1.livescore) < json[str(league.id)]["cup"][gw][
                    "lowest_loser_score"
                ][1]:
                    json[str(league.id)]["cup"][gw]["lowest_loser_score"] = (
                        man1.id,
                        s,
                        man2.id if man2 else None,
                    )

                if (s := man1.livescore) > json[str(league.id)]["cup"][gw][
                    "highest_loser_score"
                ][1]:
                    json[str(league.id)]["cup"][gw]["highest_loser_score"] = (
                        man1.id,
                        s,
                        man2.id if man2 else None,
                    )

            html_buffer += f"{man1_score}"
            if gw == api._current_gw:
                html_buffer += f"<br>({man1.fixtures_played}/{man1.total_fixtures})\n"
            html_buffer += "</td>\n"

            html_buffer += f'<td class="w3-center">\n'
            html_buffer += f"vs.\n"
            html_buffer += "</td>\n"

            if is_bye:

                html_buffer += f'<td class="w3-center">\n'
                html_buffer += "</td>\n"

                html_buffer += f'<td class="w3-center">\n'
                html_buffer += "</td>\n"

                html_buffer += f'<td style="text-align:left;vertical-align:middle;">\n'
                html_buffer += "BYE!\n"
                html_buffer += "</td>\n"

            else:

                if winner == 2:
                    html_buffer += f'<td class="w3-green w3-center">\n'

                    if (r := man2.overall_rank) > json[str(league.id)]["cup"][gw][
                        "lowest_winner_rank"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["lowest_winner_rank"] = (
                            man2.id,
                            r,
                            man1.id,
                        )

                    if (r := man2.overall_rank) < json[str(league.id)]["cup"][gw][
                        "highest_winner_rank"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["highest_winner_rank"] = (
                            man2.id,
                            r,
                            man1.id,
                        )

                    if (s := man2.livescore) < json[str(league.id)]["cup"][gw][
                        "lowest_winner_score"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["lowest_winner_score"] = (
                            man2.id,
                            s,
                            man1.id,
                        )

                    if (s := man2.livescore) > json[str(league.id)]["cup"][gw][
                        "highest_winner_score"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["highest_winner_score"] = (
                            man2.id,
                            s,
                            man1.id,
                        )

                else:
                    html_buffer += f'<td class="w3-center">\n'

                    if (r := man2.overall_rank) > json[str(league.id)]["cup"][gw][
                        "lowest_loser_rank"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["lowest_loser_rank"] = (
                            man2.id,
                            r,
                            man1.id,
                        )

                    if (r := man2.overall_rank) < json[str(league.id)]["cup"][gw][
                        "highest_loser_rank"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["highest_loser_rank"] = (
                            man2.id,
                            r,
                            man1.id,
                        )

                    if (s := man2.livescore) < json[str(league.id)]["cup"][gw][
                        "lowest_loser_score"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["lowest_loser_score"] = (
                            man2.id,
                            s,
                            man1.id,
                        )

                    if (s := man2.livescore) > json[str(league.id)]["cup"][gw][
                        "highest_loser_score"
                    ][1]:
                        json[str(league.id)]["cup"][gw]["highest_loser_score"] = (
                            man2.id,
                            s,
                            man1.id,
                        )

                html_buffer += f"{man2_score}"
                if gw == api._current_gw:
                    html_buffer += (
                        f"<br>({man2.fixtures_played}/{man2.total_fixtures})\n"
                    )
                html_buffer += "</td>\n"

                html_buffer += f'<td class="w3-center" style="vertical-align:middle;"><img class="w3-image" src="{man2._kit_path}" alt="Kit Icon" width="22" height="29"></td>\n'

                html_buffer += f'<td class="w3-left">\n'
                html_buffer += f'<a href="{man2.gui_url}">{man2.name}</a>'
                if man2.is_diamond:
                    html_buffer += "💎"
                    if winner == 2:
                        json[str(league.id)]["cup"][gw]["n_diamond_winners"] += 1
                    else:
                        json[str(league.id)]["cup"][gw]["n_diamond_losers"] += 1

                html_buffer += f'<br><a href="{man2.gui_url}">{man2.team_name}</a>\n'
                html_buffer += "</td>\n"

            html_buffer += "</tr>\n"

        html_buffer += "</table>\n"
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        if gw < 36:
            total_buffer += html_buffer

    # mout.progress(50,50,width=50)

    navbar = create_navbar(leagues, active="K", colour="black", active_colour="green")
    html_page(
        "html/toilet_cup.html",
        None,
        title=f"Tesco Value Cup",
        gw=api._current_gw,
        html=total_buffer,
        showtitle=True,
        bar_html=navbar,
        colour="amber",
    )


def create_teampage(api, leagues):
    mout.debugOut(f"create_teampage()")

    from expected import weighted_average

    html_buffer = ""

    ### fixture table

    if api._current_gw < 38:

        html_buffer += floating_subtitle("Fixture Table", pad=0)

        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive" style="padding:0px;padding-bottom:3px;">\n'

        html_buffer += '<table class="w3-table responsive-text">\n'

        sorted_teams = sorted(api.teams, key=lambda x: x.difficulty_next5, reverse=True)

        table_buffer = ""

        gw_range = range(max(1, api._current_gw), min(api._current_gw + 8, 38))

        for i, team in enumerate(sorted_teams):

            team_bg_color = team.get_style()["background-color"]
            team_text_color = team.get_style()["color"]
            team_style_str = (
                f'"background-color:{team_bg_color};color:{team_text_color};"'
            )

            table_buffer += "<tr>\n"
            table_buffer += f"<th style={team_style_str}>"
            table_buffer += f'<img class="w3-image" src="{team._badge_url}" alt="{team.shortname}" width="20" height="20"> '
            table_buffer += f" {team.name}</th>\n"

            for gw in gw_range:
                fixs = team.get_gw_fixtures(gw)

                if not fixs:
                    table_buffer += f'<td class="w3-center">-</td>\n'
                    continue

                opps = team.get_opponent(gw)

                if not isinstance(opps, list):
                    fixs = [fixs]
                    opps = [opps]

                total = 0
                for fix, opp in zip(fixs, opps):
                    is_home = fix["team_a"] == opp.id
                    total += team.strength(is_home, overall=True) - opp.strength(
                        not is_home, overall=True
                    )
                diff_delta = total / len(opps)

                style_str = get_style_from_difficulty(diff_delta)
                table_buffer += f'<td class="w3-center" style={style_str}>\n'

                if len(opps) > 1:
                    table_buffer += "<strong>"
                table_buffer += " ".join(
                    [
                        t.shortname if f["team_a"] == t.id else t.shortname.lower()
                        for f, t in zip(fixs, opps)
                    ]
                )

                table_buffer += f"</td>\n"

            table_buffer += "</tr>\n"

        html_buffer += "<tr>\n"
        html_buffer += "<th>Team</th>\n"
        for gw in gw_range:
            gw_str = "GW"
            if gw in api._special_gws.keys():
                gw_str = api._special_gws[gw]
            if gw_str in ["DGW", "TGW"]:
                html_buffer += f'<th class="w3-center" style="background-color:yellow">{gw_str}{gw}</th>\n'
            elif gw_str == "BGW":
                html_buffer += f'<th class="w3-center" style="background-color:red">{gw_str}{gw}</th>\n'
            else:
                html_buffer += f'<th class="w3-center">{gw_str}{gw}</th>\n'
        html_buffer += "</tr>\n"

        html_buffer += table_buffer

        html_buffer += "</table>\n"

        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        html_buffer += "<br>\n"

    html_buffer += floating_subtitle("Best Assets by Team", pad=0)

    gw_range = range(max(1, api._current_gw - 3), min(api._current_gw + 5, 39))

    ### by team info

    for i, team in enumerate(api.teams):
        mout.progress(i, 20)

        team_bg_color = team.get_style()["background-color"]
        team_text_color = team.get_style()["color"]
        team_style_str = f"background-color:{team_bg_color};color:{team_text_color};"

        html_buffer += '<div class="w3-col s12 m12 l6">\n'
        html_buffer += f'<div class="w3-panel shadow89 w3-responsive" style="{team_style_str};padding:0px;padding-bottom:4px;">\n'

        html_buffer += '<div class="w3-padding">\n'
        html_buffer += f'<h2><img class="w3-image" src="{team._badge_url}" alt="Team" width="30" height="30">\t{team.name}</h2>\n'
        html_buffer += "</div>\n"

        players = api.elements_by_team[team.shortname]

        # Recent results

        html_buffer += '<table class="w3-table responsive-text">\n'

        table_buffer = "<tr>\n"

        ### opponents

        for gw in gw_range:
            fixs = team.get_gw_fixtures(gw)

            if not isinstance(fixs, list):

                opp = team.get_opponent(gw)
                is_home = fixs["team_a"] == opp.id

                diff_delta = team.strength(is_home, overall=True) - opp.strength(
                    not is_home, overall=True
                )
                style_str = get_style_from_difficulty(diff_delta)

                table_buffer += f'<td class="w3-center" style={style_str}>\n'
                table_buffer += f'<img class="w3-image" src="{opp._badge_url}" alt="{opp.shortname}" width="20" height="20"> '

                if is_home:
                    table_buffer += f"{opp.shortname} "
                else:
                    table_buffer += f"{opp.shortname.lower()} "

                table_buffer += "</td>\n"

            elif fixs:

                opps = team.get_opponent(gw)
                for fix, opp in zip(fixs, opps):

                    is_home = fix["team_a"] == opp.id

                    diff_delta = team.strength(is_home, overall=True) - opp.strength(
                        not is_home, overall=True
                    )
                    style_str = get_style_from_difficulty(diff_delta)

                    table_buffer += f'<td class="w3-center" style={style_str}>\n'
                    table_buffer += f'<img class="w3-image" src="{opp._badge_url}" alt="{opp.shortname}" width="20" height="20"> '

                    if is_home:
                        table_buffer += f"{opp.shortname} "
                    else:
                        table_buffer += f"{opp.shortname.lower()} "
                        table_buffer += "\t"

                table_buffer += "</td>\n"

            else:
                table_buffer += f'<td class="w3-center" style="background-color:black;color:white">-</td>\n'

        table_buffer += "</tr>\n"

        table_buffer += "<tr>\n"

        special_gws = {}

        ### results / game scores

        for gw in gw_range:

            fixs = team.get_gw_fixtures(gw)

            # multiple fixtures
            if isinstance(fixs, list) and len(fixs) > 0:

                special_gws[gw] = len(fixs)

                opps = team.get_opponent(gw)
                for fix, opp in zip(fixs, opps):

                    is_home = fix["team_a"] == opp.id

                    team_h_score = fix["team_h_score"]
                    team_a_score = fix["team_a_score"]

                    if not fix["started"]:
                        team_h_obj = api.get_player_team_obj(fix["team_h"])
                        team_a_obj = api.get_player_team_obj(fix["team_a"])
                        team_h_score = (
                            (
                                team_a_obj.goals_conceded_per_game
                                + team_h_obj.goals_scored_per_game
                            )
                            / 2
                            * (1 - team_a_obj.expected_clean_sheet(team_h_obj))
                        )
                        team_a_score = (
                            (
                                team_h_obj.goals_conceded_per_game
                                + team_a_obj.goals_scored_per_game
                            )
                            / 2
                            * (1 - team_h_obj.expected_clean_sheet(team_a_obj))
                        )

                    style_str = get_style_from_game_score(
                        is_home, team_h_score, team_a_score
                    )
                    table_buffer += f'<td class="w3-center" style={style_str}>\n'
                    if not fix["started"]:
                        table_buffer += f"({team_h_score:.0f} - {team_a_score:.0f})"
                    else:
                        table_buffer += f"{team_h_score:.0f} - {team_a_score:.0f}"

                    table_buffer += "\t"

                table_buffer += "</td>\n"

            # blank
            elif len(fixs) == 0:
                table_buffer += f'<td class="w3-center" style="background-color:black;color:white">-</td>\n'

            # single fixture
            else:

                opp = team.get_opponent(gw)
                is_home = fixs["team_a"] == opp.id

                team_h_score = fixs["team_h_score"]
                team_a_score = fixs["team_a_score"]

                # fixture hasn't started
                if not fixs["started"]:
                    table_buffer += f'<td class="w3-center" style="background-color:white;color:black;">\n'

                # fixture in progress
                else:
                    style_str = get_style_from_game_score(
                        is_home, team_h_score, team_a_score
                    )
                    table_buffer += f'<td class="w3-center" style={style_str}>\n'
                    table_buffer += f"{team_h_score:.0f} - {team_a_score:.0f}"

                table_buffer += "</td>\n"

        html_buffer += "<tr>\n"

        ### GW header row
        for gw in gw_range:

            if gw in special_gws.keys():
                num_fixs = special_gws[gw]
                if num_fixs == 2:
                    html_buffer += f'<th class="w3-center" scope="col" colspan="2" style="background-color:yellow">DGW{gw}</th>\n'
                elif num_fixs == 3:
                    html_buffer += f'<th class="w3-center" scope="col" colspan="3" style="background-color:yellow">TGW{gw}</th>\n'
                elif num_fixs == 0:
                    html_buffer += f'<th class="w3-center" style="background-color:red">BGW{gw}</th>\n'
            else:
                html_buffer += f'<th class="w3-center">GW{gw}</th>\n'

        html_buffer += "</tr>\n"

        html_buffer += table_buffer

        html_buffer += "</tr>\n"
        html_buffer += "</table>\n"

        if test:
            break

        ### team assets

        # if api._current_gw > 0:

        html_buffer += "<br>\n"
        html_buffer += '<table class="w3-table">\n'

        def player_name_str(p):
            str_buffer = ""
            if p.is_yellow_flagged:
                str_buffer += f"⚠️ "
            elif p.is_red_flagged:
                str_buffer += f"⛔️ "
            str_buffer += f'<a href="{p._gui_url}">{p.name}</a>\n'
            return str_buffer

        if api._current_gw > 0:

            # Top scoring assets
            html_buffer += "<tr>\n"
            html_buffer += f"<th style={team_style_str}>Total Points</th>\n"
            sorted_players = sorted(players, key=lambda x: x.total_points, reverse=True)
            for p in sorted_players[:5]:
                style_str = get_style_from_event_score(p.total_points / p.appearances)
                html_buffer += f'<td class="w3-center" style={style_str}>'
                html_buffer += f"{player_name_str(p)} {p.total_points}"
                html_buffer += "</td>\n"
            html_buffer += "</tr>\n"

            # Best form assets
            html_buffer += "<tr>\n"
            html_buffer += f"<th style={team_style_str}>Best Form</th>\n"
            sorted_players = sorted(players, key=lambda x: x.form, reverse=True)
            for p in sorted_players[:5]:
                style_str = get_style_from_event_score(p.form)
                html_buffer += f'<td class="w3-center" style={style_str}>'
                html_buffer += f"{player_name_str(p)} {p.form}"
                html_buffer += "</td>\n"
            html_buffer += "</tr>\n"

            if api._current_gw < 38:

                # Most minutes
                html_buffer += "<tr>\n"
                html_buffer += (
                    f"<th style={team_style_str}>GW{api._current_gw+1} xMins</th>\n"
                )
                sorted_players = sorted(
                    players, key=lambda x: x.expected_minutes() or 0.0, reverse=True
                )
                for p in sorted_players[:5]:
                    style_str = get_style_from_minutes_played(p.expected_minutes())
                    html_buffer += f'<td class="w3-center" style={style_str}>'
                    html_buffer += f"{player_name_str(p)} {p.expected_minutes():.0f}'"
                    html_buffer += "</td>\n"
                html_buffer += "</tr>\n"

        # Top predicted points assets
        html_buffer += "<tr>\n"
        html_buffer += f"<th style={team_style_str}>Next 5 xPts</th>\n"
        sorted_players = sorted(players, key=lambda x: x.next5_expected, reverse=True)
        for p in sorted_players[:5]:
            style_str = get_style_from_event_score(p.next5_expected / 5)
            html_buffer += f'<td class="w3-center" style={style_str}>'
            html_buffer += f"{player_name_str(p)} {p.next5_expected:.1f}"
            html_buffer += "</td>\n"
        html_buffer += "</tr>\n"

        html_buffer += "</table>\n"

        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    mout.progress(20, 20)

    navbar = create_navbar(leagues)
    html_page(
        "html/teams.html",
        None,
        title=f"Teams",
        gw=api._current_gw,
        html=html_buffer,
        showtitle=True,
        bar_html=navbar,
        colour="aqua",
    )


def create_assetpage(leagues):
    mout.debugOut(f"create_assetpage()")

    if force_go_graphs or not api._live_gw:

        gw = api._current_gw

        if gw > 1:
            minutes = 90
        else:
            minutes = 0

        player_minutes = {}

        # this season
        player_ids = api._elements["id"]
        for i, pid in enumerate(player_ids):
            player_minutes[pid] = api._elements["minutes"][i]
        player_ids = api._prev_elements["id"]

        # last season
        for i, pid in enumerate(player_ids):
            if pid in player_minutes:
                player_minutes[pid] += api._prev_elements["minutes"][i]

        players = []
        for pid, mins in player_minutes.items():
            if mins > minutes:
                index = api.get_player_index(pid)
                p = Player(None, api, index=index)
                if p.position_id == 5:
                    mrich.warning(f"Excluding manager {p.name} from asset page graphs")
                    continue
                players.append(p)

        import sys

        sys.path.insert(1, "go")
        from value import create_value_figure
        from gwexp import create_gwexp_figure
        from bonus import create_bonus_figure
        from xgi import create_xgi_figure
        from vapm import create_vapm_figure

        html_buffer = ""

        html_buffer += floating_subtitle("Attacking Points")
        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += '<div class="w3-padding">\n'
        html_buffer += "<p>Returned attacking points vs expected attacking points including previous season data. Using official xG and xA data.</p>"
        html_buffer += "</div>\n"
        html_buffer += create_xgi_figure(api, players)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        html_buffer += floating_subtitle("Best Value: Next 5 GWs")
        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += '<div class="w3-padding">\n'
        html_buffer += "<p>Expected points over the next five gameweeks per player price. Expected poins from Max's algorithm</p>"
        html_buffer += "</div>\n"
        html_buffer += create_value_figure(api, players)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        if gw > 0:

            html_buffer += floating_subtitle(f"Best GW{gw+1} Assets")
            html_buffer += '<div class="w3-col s12 m12 l12">\n'
            html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
            html_buffer += '<div class="w3-padding">\n'
            html_buffer += "<p>Next gameweek expected points (official FPL source) versus player form.</p>"
            html_buffer += "</div>\n"
            html_buffer += create_gwexp_figure(api, players)
            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

            html_buffer += floating_subtitle(f"Value added per million (form)")
            html_buffer += '<div class="w3-col s12 m12 l12">\n'
            html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
            html_buffer += '<div class="w3-padding">\n'
            html_buffer += "<p>Form versus spend above position minimum.</p>"
            html_buffer += "</div>\n"
            html_buffer += create_vapm_figure(api, players)
            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

        # navbar = None
        navbar = create_navbar(leagues)
        html_page(
            "html/assets.html",
            None,
            title=f"Asset Analysis",
            gw=gw,
            html=html_buffer,
            showtitle=True,
            bar_html=navbar,
            colour="aqua",
            plotly=True,
        )


def create_navbar(
    leagues, active=None, colour="black", active_colour="aqua", path_root=""
):

    html_buffer = ""

    html_buffer += f"\n"

    html_buffer += f'<div class="w3-bar w3-{colour} shadow89">\n'
    html_buffer += f'<a class="w3-bar-item w3-{colour} w3-text-{colour}"></a>\n'
    html_buffer += '<div class="w3-dropdown-hover">\n'
    html_buffer += '<button class="w3-button w3-hover-aqua"><h3><span class="w3-tag w3-white">toilet.football</span></h3></button>\n'
    html_buffer += '<div class="w3-dropdown-content w3-bar-block w3-card-4">\n'

    if not path_root:
        url = f"../index.html"
    else:
        url = f"index.html"
        # url = f"{DEPLOY_ROOT}/index.html"
    html_buffer += (
        f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">🏠 Home</a>\n'
    )

    url = f"{path_root}comparison.html"
    html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">📊 Comparison Tool</a>\n'

    url = f"{path_root}assets.html"
    html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">📈 Asset Graphs</a>\n'

    if season_awards:
        url = f"{path_root}season.html"
        html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">🏁 End of season</a>\n'

    if halfway_awards or api._current_gw > 18:
        url = f"{path_root}christmas.html"
        html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">🎄 Christmas</a>\n'

    url = f"{path_root}teams.html"
    html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">👨‍👨‍👦‍👦 Teams</a>\n'

    for i, league in enumerate(leagues):
        url = f'{path_root}{league.name.replace(" ","-")}.html'
        html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">{league._icon} {league.name}</a>\n'

    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    html_buffer += (
        f'<a class="w3-bar-item w3-{colour} w3-text-{colour} w3-right"></a>\n'
    )

    if cup_active:
        url = f"{path_root}toilet_cup.html"
        html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua w3-right"><h3>🏆</h3></a>\n'
    url = f"{path_root}Tesco-Bean-Value-Toilet-League.html"
    html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua w3-right"><h3>🚽</h3></a>\n'
    url = f"{path_root}The-RBS-Diamond-Invitational.html"
    html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua w3-right"><h3>💎</h3></a>\n'
    html_buffer += "</div>\n"

    html_buffer += f'<div class="w3-bar w3-{colour}">\n'

    html_buffer += f"</div>\n"

    return html_buffer


def create_fixturepage(api, leagues):
    mout.debugOut(f"create_fixturepage()")

    gw = api._current_gw

    html_buffer = fixture_table(api, gw)
    html_buffer += fixture_table(api, gw + 1)

    navbar = create_navbar(leagues, active="F", colour="black", active_colour="green")
    html_page(
        "html/fixtures.html",
        None,
        title=f"Fixtures",
        gw=gw,
        html=html_buffer,
        showtitle=False,
        bar_html=navbar,
    )


def create_playerpage(api, player, leagues):
    global completed_playerpages

    if int(player.id) not in completed_playerpages:

        mout.debugOut(f"create_playerpage({player.name})")

        gw = api._current_gw

        html_buffer = ""

        """
		- League Selections
		- Global Selection
		- ICT Index
		- Predicted Next 5 GW's
		- News
		- Transferred in %
		- (transferred in league?)

		Fixed: Price, %Selected, %change
		Fixed: Points, Form, GW+1 xPts

		Variable:
		Defenders: Goals, Assists
		Everyone: Cleans, Own Goals
		Everyone: Yellows, Reds
		
		Goalkeepers: Penalty Saves, Saves

		Everyone: Bonus, Minutes/game
		"""

        html_buffer += '<div class="w3-col s12 m12 l4">\n'
        html_buffer += f'<div class="w3-panel w3-{player.team_obj.shortname.lower()}-inv shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += f'<div class="w3-center">\n'
        html_buffer += f"<h2>{player.name}</h2>\n"
        html_buffer += f'<img class="w3-image" src="{player._photo_url}" alt="Player" width="220" height="280">\n'
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        html_buffer += f'<div class="w3-panel w3-{player.team_obj.shortname.lower()} shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += f'<div class="w3-responsive">\n'

        ######

        html_buffer += f'<div class="w3-center w3-padding-large">\n'
        html_buffer += f'<h5 class="double">\n'
        html_buffer += f"<h5>\n"

        color = f"{player.team_obj.shortname.lower()}-inv"
        #
        # if player.name in [p[0].name for p in risers]:
        # 	html_buffer += f'<span class="w3-tag w3-green">£{player.price}</span>\n'
        # elif player.name in [p[0].name for p in fallers]:
        # 	html_buffer += f'<span class="w3-tag w3-red">£{player.price}</span>\n'
        # else:
        html_buffer += f'<span class="w3-tag w3-{color}">£{player.price}</span>\n'

        html_buffer += (
            f'<span class="w3-tag w3-{color}">global {player.selected_by}%</span>\n'
        )

        if player.transfer_percent < 0:
            html_buffer += f'<span class="w3-tag w3-red">change {player.transfer_percent:.1f}%</span>\n'
        else:
            html_buffer += f'<span class="w3-tag w3-green">change +{player.transfer_percent:.1f}%</span>\n'

        # color by score?
        html_buffer += (
            f'<span class="w3-tag w3-{color}">total {player.total_points} pts</span>\n'
        )
        html_buffer += (
            f'<span class="w3-tag w3-{color}">form {player.form} pts/game</span>\n'
        )

        if player.total_goals > 0:
            html_buffer += (
                f'<span class="w3-tag w3-green">{player.total_goals} goals</span>\n'
            )

        if player.total_assists > 0:
            html_buffer += (
                f'<span class="w3-tag w3-blue">{player.total_assists} assists</span>\n'
            )

        if player._total_own_goals > 0:
            html_buffer += f'<span class="w3-tag w3-black">{player._total_own_goals} own goals</span>\n'

        if player._total_yellows > 0:
            html_buffer += f'<span class="w3-tag w3-yellow">{player._total_yellows} yellow cards</span>\n'

        if player._total_reds > 0:
            html_buffer += (
                f'<span class="w3-tag w3-red">{player._total_reds} red cards</span>\n'
            )

        if player.total_bonus > 0:
            html_buffer += (
                f'<span class="w3-tag w3-aqua">{player.total_bonus} bonus</span>\n'
            )

        if player.position_id < 4:
            if player._total_clean_sheets > 0:
                html_buffer += f'<span class="w3-tag w3-purple">{player._total_clean_sheets} clean sheets</span>\n'

        if player.position_id == 1:
            if player._total_penalties_saved > 0:
                html_buffer += f'<span class="w3-tag w3-green">{player._total_penalties_saved} penalties saves</span>\n'
            if player._total_saves > 0:
                html_buffer += (
                    f'<span class="w3-tag w3-blue">{player._total_saves} saves</span>\n'
                )

        if player.position_id < 3:
            if player._total_goals_conceded > 0:
                html_buffer += f'<span class="w3-tag w3-orange">{player._total_goals_conceded} goals conceded</span>\n'

        if player.appearances > 0:
            html_buffer += f'<span class="w3-tag w3-dark-grey">{player.total_minutes/player.appearances:.0f} mins/game</span>\n'

        html_buffer += f"</h5>\n"
        html_buffer += f"</div>\n"

        html_buffer += f"</div>\n"
        html_buffer += f"</div>\n"
        html_buffer += f"</div>\n"

        # if api._current_gw > 0 and (force_go_graphs or not api._live_gw):
        if force_go_graphs or not api._live_gw:

            html_buffer += '<div class="w3-col s12 m12 l8">\n'
            html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
            import sys

            sys.path.insert(1, "go")
            from playgo import create_player_figure

            html_buffer += create_player_figure(api, player)

            html_buffer += f"</div>\n"

        # if api._current_gw > 0:
        html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += get_player_history_table(player)
        html_buffer += f"</div>\n"
        html_buffer += f"</div>\n"

        navbar = create_navbar(leagues, active=None, colour="black")

        style = api.create_team_styles_css()

        html_page(
            f"html/player_{player.id}.html",
            None,
            title=f"{player.name}",
            sidebar_content=None,
            gw=gw,
            html=html_buffer,
            showtitle=False,
            bar_html=navbar,
            extra_style=style,
            colour=player.team_obj.style["accent"],
            nonw3_colour=True,
            plotly=True,
        )

        completed_playerpages.append(int(player.id))


def create_trophycabinet(api, man):

    html_buffer = ""

    leagues = man._leagues

    man._awards = sorted(man._awards, key=lambda x: x["gw"], reverse=False)

    html_buffer += '<div class="w3-bar w3-black">\n'

    for i, league in enumerate(leagues):

        if i == 0:
            html_buffer += f'<button class="w3-bar-item w3-button w3-mobile tablink w3-aqua" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
        else:
            html_buffer += f'<button class="w3-bar-item w3-mobile w3-button tablink" onclick="openLeague(event,{league.id})">{league.name}</button>\n'

    html_buffer += "</div>\n"

    for i, league in enumerate(leagues):

        if i == 0:
            html_buffer += f'<div id="{league.id}" class="w3-container w3-{league._colour_str} league">\n'
        else:
            html_buffer += f'<div id="{league.id}" class="w3-container w3-{league._colour_str} league" style="display:none">\n'

        html_buffer += '<div class="w3-justify w3-row-padding">\n'

        awards = [
            a
            for a in man._awards
            if league.name in a["league"] and a["gw"] not in ["half", "season", "chips"]
        ]

        half_awards = [
            a for a in man._awards if league.name in a["league"] and a["gw"] == "half"
        ]
        full_awards = [
            a for a in man._awards if league.name in a["league"] and a["gw"] == "season"
        ]
        chip_awards = [
            a for a in man._awards if league.name in a["league"] and a["gw"] == "chips"
        ]

        if len(awards + half_awards + full_awards + chip_awards) > 0:

            html_buffer += '<div class="w3-justify">'
            html_buffer += '<div class="w3-row-padding">'

            award_keys = list(set([a["key"] for a in awards]))

            award_panels = []

            # full > half > chips > normal
            for award in full_awards:

                key = award["key"]

                colour = award_colour[key]
                # icon = award_icon[key]

                html_buffer += '<div class="w3-col s12 m6 l4">\n'
                html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-card shadow89 w3-border-yellow">\n'
                html_buffer += '<table class="w3-table">\n'
                html_buffer += "<tr>\n"
                html_buffer += '<td style="text-align:left;vertical-align:middle;">\n'
                html_buffer += f"<h1>{award_flavourtext[key]}</h1>\n"
                html_buffer += "</td>\n"
                html_buffer += '<td style="text-align:right;vertical-align:middle;">\n'
                html_buffer += f'<h2><span class="w3-tag">Season</span></h2>\n'
                html_buffer += "</tr>\n"
                html_buffer += "</table>\n"
                html_buffer += "</div>\n"
                html_buffer += "</div>\n"

            for award in half_awards:

                key = award["key"]

                colour = award_colour[key]
                # icon = award_icon[key]

                html_buffer += '<div class="w3-col s12 m6 l4">\n'
                html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-card shadow89 w3-border-green">\n'
                html_buffer += '<table class="w3-table">\n'
                html_buffer += "<tr>\n"
                html_buffer += '<td style="text-align:left;vertical-align:middle;">\n'
                html_buffer += f"<h1>{award_flavourtext[key]}</h1>\n"
                html_buffer += "</td>\n"
                html_buffer += '<td style="text-align:right;vertical-align:middle;">\n'
                html_buffer += f'<h2><span class="w3-tag">Christmas</span></h2>\n'
                html_buffer += "</tr>\n"
                html_buffer += "</table>\n"
                html_buffer += "</div>\n"
                html_buffer += "</div>\n"

            for award in chip_awards:

                key = award["key"]

                colour = award_colour[key]
                # icon = award_icon[key]

                html_buffer += '<div class="w3-col s12 m6 l4">\n'
                html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-card shadow89 w3-border-black">\n'
                html_buffer += '<table class="w3-table">\n'
                html_buffer += "<tr>\n"
                html_buffer += '<td style="text-align:left;vertical-align:middle;">\n'
                html_buffer += f"<h1>{award_flavourtext[key]}</h1>\n"
                html_buffer += "</td>\n"
                html_buffer += '<td style="text-align:right;vertical-align:middle;">\n'

                html_buffer += "</tr>\n"
                html_buffer += "</table>\n"
                html_buffer += "</div>\n"
                html_buffer += "</div>\n"

            for key in award_keys:

                gws = sorted(
                    [a["gw"] for a in awards if a["key"] == key], key=lambda x: int(x)
                )
                count = len(gws)
                icon = ""

                colour = award_colour[key]

                award_buffer = '<div class="w3-col s12 m6 l4">\n'
                award_buffer += f'<div class="w3-panel w3-{colour} w3-card shadow89">\n'
                award_buffer += '<table class="w3-table">\n'
                award_buffer += "<tr>\n"
                award_buffer += '<td style="text-align:left;vertical-align:middle;">\n'

                if count == 1:
                    award_buffer += f"<h1>{icon} {award_flavourtext[key]}</h1>\n"
                else:
                    award_buffer += (
                        f"<h1>{count} &times {icon} {award_flavourtext[key]}</h1>\n"
                    )

                award_buffer += "</td>\n"
                award_buffer += '<td style="text-align:right;vertical-align:middle;">\n'
                award_buffer += (
                    f'<h2><span class="w3-tag">GW{", GW".join(gws)}</span></h2>\n'
                )
                award_buffer += "</tr>\n"
                award_buffer += "</table>\n"
                award_buffer += "</div>\n"
                award_buffer += "</div>\n"

                award_panels.append([count, award_buffer])

            for count, panel_buffer in sorted(
                award_panels, key=lambda x: x[0], reverse=True
            ):

                html_buffer += panel_buffer

            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

        else:
            html_buffer += "<p> Empty, no league awards to be found :(</p>\n"

        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    html_buffer += "<script>\n"
    html_buffer += "function openLeague(evt, leagueName) {\n"
    html_buffer += "var i, x, tablinks;\n"
    html_buffer += 'x = document.getElementsByClassName("league");\n'
    html_buffer += "for (i = 0; i < x.length; i++) {\n"
    html_buffer += 'x[i].style.display = "none";\n'
    html_buffer += "}\n"
    html_buffer += 'tablinks = document.getElementsByClassName("tablink");\n'
    html_buffer += "for (i = 0; i < x.length; i++) {\n"
    html_buffer += (
        'tablinks[i].className = tablinks[i].className.replace(" w3-aqua", "");\n'
    )
    html_buffer += "}\n"
    html_buffer += 'document.getElementById(leagueName).style.display = "block";\n'
    html_buffer += 'evt.currentTarget.className += " w3-aqua";\n'
    html_buffer += "}\n"
    html_buffer += "</script>\n"

    return html_buffer


def create_managerpage(api, man, leagues):
    mout.debugOut(f"create_managerpage({man.name})")

    """

		Trophy Cabinet:

		Current Team:

			Columns:

			Position
			Team
			Name
			Price
			Total Points
			Transfers in
			Previous NxGW scores
			Form
			Next MxGW Fixtures
			Fixture difficulty

		Transfer History:
		
		League History (Graph):
	"""

    # Awards

    gw = api._current_gw

    html_buffer = ""

    title_str = f"{man.name}'s " f'"{man.team_name}"'

    if gw > 0:
        html_buffer += create_manager_formation(man, gw)

        # season stats
        html_buffer += '<div class="w3-col s12 m6 l4">\n'
        html_buffer += '<div class="w3-panel w3-center w3-white w3-padding shadow89">\n'
        html_buffer += f"<h2>{api._season_str_fmt} Season</h2>\n"
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Total Score: {man.total_livescore}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Overall Rank: {api.big_number_format(man.overall_rank)}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Avg. Player Selection: {man.avg_selection:.1f}%</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Team Value: £{man.team_value}M</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">#hits: {man.num_hits}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">#transfers: {man.num_nonwc_transfers}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Total Transfer Gain: {man.total_transfer_gain}</span>\n'
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        # gw
        html_buffer += '<div class="w3-col s12 m6 l4">\n'
        html_buffer += '<div class="w3-panel w3-center w3-white w3-padding shadow89">\n'
        html_buffer += f"<h2>GW{gw}</h2>\n"
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Score: {man.livescore}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Rank: {api.big_number_format(man.gw_rank)}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Rank Gain: {man.gw_rank_gain:.1%}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">xG: {man.gw_xg:.1f}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">xA: {man.gw_xa:.1f}</span>\n'
        html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Performed xPts: {man.gw_performed_xpts:.1f}</span>\n'
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    # external links
    html_buffer += '<div class="w3-col s12 m12 l4">\n'
    html_buffer += '<div class="w3-panel w3-center w3-indigo w3-padding shadow89">\n'
    url = man.fpl_event_url
    html_buffer += (
        f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">🗓️ FPL Event</a>\n'
    )
    url = man.fpl_history_url
    html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">📈 FPL GW History</a>\n'
    html_buffer += f'<a class="w3-bar-item w3-button w3-hover-blue">ID: {man.id}</a>\n'
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    if gw > 0:
        html_buffer += floating_subtitle("🏆 Trophy Cabinet", pad=1)

        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;">\n'
        html_buffer += create_trophycabinet(api, man)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        if any(man._chip_dict.values()):
            html_buffer += floating_subtitle("Chips")

            html_buffer += '<div class="w3-col s12 m12 l12">\n'
            html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
            html_buffer += create_chip_table(api, man)
            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

    if gw > 0 and not (gw == 38 and not api._live_gw):
        html_buffer += floating_subtitle("Picks")

        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += create_picks_table(api, man.squad.sorted_players, manager=man)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        now_gw = gw
        end_gw = min(37, now_gw + 5)

        ### GRAPH
        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive w3-padding" id="graphDiv" style="display:block;">\n'

        html_buffer += f'<div id="comparisonGraph" style="width:100%;height:500px">\n'
        html_buffer += f"</div>\n"

        html_buffer += f"</div>\n"
        html_buffer += f"</div>\n"

        ### BUILD THE PLOTTING DATA
        gw_indices = [i + 1 for i in range(now_gw, end_gw + 1)]

        if len(gw_indices) == 1:

            gw = gw_indices[0]

            players = man.squad.sorted_players

            plot_data = [
                {
                    "x": [p.name for p in players],
                    "y": [round(p.expected_points(gw=gw), 1) for p in players],
                    "type": "bar",
                }
            ]

        else:

            gw_strs = [f"GW{i+1}" for i in range(now_gw, end_gw + 1)]
            plot_data = []
            player_id_to_trace_id = {}
            for i, p in enumerate(man.squad.sorted_players):

                player_id_to_trace_id[p.id] = i

                plot_y = [round(p.expected_points(gw=i), 1) for i in gw_indices]

                plot_data.append(
                    dict(
                        name=p.name,
                        x=gw_strs,
                        y=plot_y,
                        visible=True,
                        mode="lines+markers",
                    )
                )

        ### CREATE THE GRAPH
        html_buffer += "<script>\n"
        html_buffer += '	GRAPH = document.getElementById("comparisonGraph");\n'
        html_buffer += f"	Plotly.newPlot( GRAPH, {js.dumps(plot_data)}"
        html_buffer += ', {	title: "Expected Points", margin: { r:0 }, font: {size: 14}} , {responsive: true});\n'
        html_buffer += "</script>\n"

    if cup_active and not (gw == 38 and not api._live_gw):

        all_matches = []

        for league in leagues:
            matches = man.get_cup_matches(league)
            if matches:
                all_matches.append((league, matches))

        if all_matches:
            html_buffer += floating_subtitle(f"GW{gw} Cup Matches")

            html_buffer += '<div class="w3-col s12 m12 l12">\n'
            html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'

            from compare import compare_squads

            # html_buffer += compare_squads(man, )

            html_buffer += '<div class="w3-bar w3-black">\n'

            for i, (league, matches) in enumerate(all_matches):

                if i == 0:
                    html_buffer += f'<button class="w3-bar-item w3-button w3-mobile tablink2 w3-aqua" onclick="openLeague2(event,{league.id+90000000})">{league.name}</button>\n'
                else:
                    html_buffer += f'<button class="w3-bar-item w3-mobile w3-button tablink2" onclick="openLeague2(event,{league.id+90000000})">{league.name}</button>\n'

            html_buffer += "</div>\n"

            for i, (league, matches) in enumerate(all_matches):

                if i == 0:
                    html_buffer += f'<div id="{league.id+90000000}" class="w3-container w3-{league._colour_str} league2">\n'
                else:
                    html_buffer += f'<div id="{league.id+90000000}" class="w3-container w3-{league._colour_str} league2" style="display:none">\n'

                opponent = matches[0]["opponent"]

                # print(matches)
                try:
                    html_buffer += compare_squads(man, opponent)
                except Exception as e:
                    html_buffer += "Something went wrong!"
                    mout.error(
                        f"something went wrong with squad comparison {(man, opponent)}"
                    )
                    mout.error(str(e))

                html_buffer += "</div>\n"

            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

            html_buffer += "<script>\n"
            html_buffer += "function openLeague2(evt, leagueName2) {\n"
            html_buffer += "var i, x, tablinks;\n"
            html_buffer += 'x = document.getElementsByClassName("league2");\n'
            html_buffer += "for (i = 0; i < x.length; i++) {\n"
            html_buffer += 'x[i].style.display = "none";\n'
            html_buffer += "}\n"
            html_buffer += 'tablinks = document.getElementsByClassName("tablink2");\n'
            html_buffer += "for (i = 0; i < x.length; i++) {\n"
            html_buffer += 'tablinks[i].className = tablinks[i].className.replace(" w3-aqua", "");\n'
            html_buffer += "}\n"
            html_buffer += (
                'document.getElementById(leagueName2).style.display = "block";\n'
            )
            html_buffer += 'evt.currentTarget.className += " w3-aqua";\n'
            html_buffer += "}\n"
            html_buffer += "</script>\n"

    if gw > 0:

        html_buffer += floating_subtitle("History")

        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += create_manager_history_table(api, man)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        html_buffer += floating_subtitle("Graphs")

        import sys

        sys.path.insert(1, "go")
        from goleague import create_league_figure
        from goman import manager_rank_waterfall

        ### ADD GAMEWEEK RANKS!

        html_buffer += '<div class="w3-col s12 m12 l6">\n'
        html_buffer += '<div class="w3-panel w3-center w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += create_league_figure(
            api, league=None, subset=None, single=man, rank=True
        )
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        html_buffer += '<div class="w3-col s12 m12 l6">\n'
        html_buffer += '<div class="w3-panel w3-center w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += manager_rank_waterfall(api, man)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        html_buffer += '<div class="w3-col s12 m12 l6">\n'
        html_buffer += '<div class="w3-panel w3-center w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += create_league_figure(
            api, league=None, subset=None, single=man, rank=False
        )
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    navbar = create_navbar(leagues)

    style = api.create_team_styles_css()
    html_page(
        f"html/{man.gui_path}",
        None,
        title=title_str,
        gw=gw,
        html=html_buffer,
        showtitle=True,
        bar_html=navbar,
        colour="blue-gray",
        extra_style=style,
        plotly=True,
    )


def create_manager_formation(man, gw):

    html_buffer = ""

    html_buffer += '<div class="w3-col s12 m12 l12">\n'
    html_buffer += '<div class="w3-center w3-padding">\n'
    html_buffer += '<div style="text-align:center;width:90%;max-width:900px;display:block;margin-left:auto;margin-right:auto;">\n'

    last_pos_id = 1
    for p in man.squad.sorted_players:

        if p.multiplier == 0:
            continue

        if last_pos_id != p.position_id:
            html_buffer += "</div>\n"
            html_buffer += '<div style="text-align:center;width:90%;max-width:900px;display:block;margin-left:auto;margin-right:auto;">\n'

        html_buffer += '<div style="width:18%;display:inline-block;text-align:center;vertical-align:top;padding:0px;padding-top:16px;padding-left:2px;padding-right:2px;">\n'

        html_buffer += f'<img class="w3-image" style="width:80%;display:block;margin-left:auto;margin-right:auto;" src="{p._photo_url}?raw=true"></img>\n'

        score = p.get_event_score(gw)

        style_str = (
            get_style_from_event_score(score).rstrip('"')
            + ';width:100%;padding:0px;padding-top:2px;padding-bottom:6px;"'
        )

        if p.multiplier == 3:
            c_str = " (TC)"
        elif p.multiplier == 2:
            c_str = " (C)"
        elif p.is_vice_captain:
            c_str = " (VC)"
        else:
            c_str = ""

        html_buffer += f'<div class="w3-tag shadow89 w3-reponsive responsive-text" style={style_str}><b><a href="{p._gui_url}">{p.name}</a>{c_str}</b>\n'

        html_buffer += f"<br>\n"
        style_str = (
            get_style_from_event_score(score).rstrip('"')
            + ';width:90%;margin-bottom:2px;"'
        )
        html_buffer += p.event_stat_emojis(gw)

        if score is None:
            html_buffer += f" <b>-</b>\n"
            # print(p,score)
        else:
            html_buffer += f" <b>{p.multiplier*score}pts</b>\n"

        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

        last_pos_id = p.position_id

    ## BENCH
    bench = [p for p in man.squad.sorted_players if p.multiplier == 0]

    if bench:
        html_buffer += "</div>\n"
        html_buffer += '<div style="text-align:center;width:90%;max-width:900px;display:block;margin-left:auto;margin-right:auto;">\n'

        for p in bench:
            html_buffer += '<div style="width:18%;display:inline-block;text-align:center;vertical-align:top;padding:0px;padding-top:16px;padding-left:2px;padding-right:2px;">\n'

            html_buffer += f'<img class="w3-image" style="width:80%;display:block;margin-left:auto;margin-right:auto;" src="{p._photo_url}?raw=true"></img>\n'

            score = p.get_event_score(gw)

            style_str = (
                get_style_from_event_score(score).rstrip('"')
                + ';width:100%;padding:0px;padding-top:2px;padding-bottom:6px;"'
            )

            c_str = ""

            html_buffer += f'<div class="w3-tag shadow89 w3-reponsive responsive-text" style={style_str}><b><a href="{p._gui_url}">{p.name}</a>{c_str}</b>\n'

            html_buffer += f"<br>\n"
            style_str = (
                get_style_from_event_score(score).rstrip('"')
                + ';width:90%;margin-bottom:2px;"'
            )
            html_buffer += p.event_stat_emojis(gw)

            if score is None:
                html_buffer += f" <b>-</b>\n"
            else:
                html_buffer += f" <b>{score}pts</b>\n"

            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

    html_buffer += "</div>\n"
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    return html_buffer


def create_manager_history_table(api, man):
    html_buffer = ""

    html_buffer += '<div class="w3-responsive">\n'
    html_buffer += '<table class="w3-table w3-hoverable">\n'

    html_buffer += "<tr>\n"
    html_buffer += '<th class="w3-center">GW</th>\n'
    html_buffer += '<th class="w3-center">Score</th>\n'
    html_buffer += '<th class="w3-center">Overall Rank</th>\n'
    html_buffer += '<th class="w3-center">GW Score</th>\n'
    html_buffer += '<th class="w3-center">GW Rank</th>\n'
    html_buffer += '<th class="w3-center">Transfers Taken</th>\n'
    html_buffer += '<th class="w3-center">Total Value</th>\n'
    html_buffer += "</tr>\n"

    now_gw = api._current_gw
    start_gw = 0
    delta = 0

    if len(man._overall_rank) < now_gw:
        start_gw = now_gw - len(man._overall_rank)

    for i in range(now_gw, start_gw, -1):

        j = i - start_gw
        html_buffer += "<tr>\n"
        html_buffer += f'<td class="w3-center">{i}</td>\n'
        if j == now_gw:
            html_buffer += f'<td class="w3-center">{man.total_livescore}</td>\n'
        else:

            html_buffer += f'<td class="w3-center">{man._total_points[j-1]}</td>\n'
        html_buffer += f'<td class="w3-center">{api.big_number_format(man._overall_rank[j-1])}</td>\n'
        if j == now_gw:
            html_buffer += f'<td class="w3-center">{man.livescore}</td>\n'
        else:
            html_buffer += f'<td class="w3-center">{man._event_points[j-1]}</td>\n'
        html_buffer += f'<td class="w3-center">{api.big_number_format(man._event_rank[j-1])}</td>\n'
        transfer_str = (
            man.get_transfer_str(i)
            .replace("\n", "<br>")
            .replace("**WC**", "<strong>WC</strong>")
        )
        if transfer_str.startswith("<br>"):
            transfer_str = transfer_str[4:]

        html_buffer += f"<td>{transfer_str}</td>\n"
        html_buffer += f'<td class="w3-center">£{man._squad_value[j-1]:.1f}</td>\n'
        html_buffer += "</tr>\n"

    html_buffer += "</table>\n"
    html_buffer += "</div>\n"

    return html_buffer


def create_chip_table(api, man):

    html_buffer = ""

    chips = [v for v in man._chip_dict.items() if v[1] is not None]

    chips = sorted(chips, key=lambda x: x[1])

    if len(chips) > 0:

        html_buffer += '<div class="w3-responsive">\n'
        html_buffer += '<table class="w3-table w3-border w3-hoverable">\n'

        html_buffer += "<tr>\n"
        html_buffer += f'<th class="w3-center">Chip</th>\n'
        html_buffer += f'<th class="w3-center">GW</th>\n'
        html_buffer += f'<th class="w3-center">Detail</th>\n'
        html_buffer += "</tr>\n"

        for chip in chips:

            chip_html = ""

            match chip[0]:
                case "wc1":
                    color = "red"
                    pts_delta = man.calculate_transfer_gain(gw=chip[1])
                    if pts_delta > 0:
                        detail = f"+{pts_delta} points gained"
                    else:
                        detail = f"{pts_delta} points lost"

                    delta = man._wc1_ordelta_percent
                    if delta > 0:
                        delta = f"+{delta:.0f}"
                    else:
                        delta = f"{delta:.0f}"
                    detail += f"({delta}% OR)"

                case "wc2":
                    color = "red"
                    pts_delta = man.calculate_transfer_gain(gw=chip[1])
                    if pts_delta > 0:
                        detail = f"+{pts_delta} points gained"
                    else:
                        detail = f"{pts_delta} points lost"

                    delta = man._wc2_ordelta_percent
                    if delta > 0:
                        delta = f" +{delta:.0f}"
                    else:
                        delta = f" {delta:.0f}"
                    detail += f"({delta}% OR)"
                case "fh":
                    color = "green"
                    pts = man.get_event_score(chip[1])
                    rank = [
                        r
                        for i, r in zip(man.active_gws, man._event_rank)
                        if i == chip[1]
                    ][0]
                    detail = f"GW Points: {pts}, GW Rank: {api.big_number_format(rank)}"
                case "bb":
                    color = "blue"
                    pts = man._bb_ptsgain
                    if pts > 0:
                        detail = f"+{pts} points gained"
                    else:
                        detail = f"{pts} points lost"
                case "tc":
                    color = "amber"
                    old_squad = man._squad
                    squad = man.get_current_squad(gw=chip[1], force=True)
                    if squad is None:
                        mout.warningOut(
                            f"Squad is none for GW{chip[1]} (manager {man.id})"
                        )
                        detail = f"-"
                        break

                    # mout.out(f"{man} TC{chip[1]}")

                    # pts_delta = squad.captain.get_event_score(gw=chip[1],not_playing_is_none=False)

                    pts_delta = man._tc_ptsgain

                    try:
                        if pts_delta > 0:
                            detail = f"+{pts_delta} points gained "
                        else:
                            detail = f"{pts_delta} points lost "
                    except TypeError:
                        detail = ""

                    detail += f"with {man._tc_name}"

                    man._squad = old_squad
                case _:
                    color = "black"
                    detail = f"-"

            chip_html += "<tr>\n"
            chip_html += (
                f'<td class="w3-center w3-{color}">{man._chip_names[chip[0]]}</td>\n'
            )
            chip_html += f'<td class="w3-center">{chip[1]}</td>\n'
            chip_html += f'<td class="w3-center">{detail}</td>\n'
            chip_html += "</tr>\n"

            html_buffer += chip_html

        html_buffer += f"</table>\n"
        html_buffer += f"</div>\n"

    return html_buffer


def create_picks_table(api, players, prev_gw_count=5, next_gw_count=5, manager=None):

    html_buffer = ""

    html_buffer += '<div class="w3-responsive">\n'
    html_buffer += '<table class="w3-table responsive-text">\n'

    now_gw = api._current_gw
    start_gw = max(1, now_gw - prev_gw_count)
    end_gw = min(38, now_gw + next_gw_count)

    html_buffer += "<tr>\n"
    html_buffer += f'<th class="w3-center">Pos</th>\n'
    html_buffer += f'<th class="w3-center">Team</th>\n'
    html_buffer += f"<th>Name</th>\n"
    html_buffer += f'<th class="w3-center">Price</th>\n'
    html_buffer += f'<th class="w3-center">ΣPts</th>\n'
    html_buffer += f'<th class="w3-center">Trans.</th>\n'
    for i in range(start_gw, now_gw + 1):
        html_buffer += f'<th class="w3-center">GW{i}</th>\n'
    html_buffer += f'<th class="w3-center">Form</th>\n'
    for i in range(now_gw + 1, end_gw + 1):
        html_buffer += f'<th class="w3-center">GW{i}</th>\n'
    html_buffer += "</tr>\n"

    for player in players:
        html_buffer += "<tr>\n"

        ### Styled based on team

        bg_color = player.team_obj.get_style()["background-color"]
        text_color = player.team_obj.get_style()["color"]
        style_str = (
            f'"background-color:{bg_color};color:{text_color};vertical-align:middle;"'
        )

        html_buffer += f'<td class="w3-center" style={style_str}><b>{["GKP","DEF","MID","FWD","MAN"][player.position_id-1]}</b></td>\n'
        html_buffer += (
            f'<td class="w3-center" style={style_str}><b>{player.shortteam}</b></td>\n'
        )
        html_buffer += f"<td style={style_str}><b>"
        if player.is_captain:
            html_buffer += f"(C) "
        if player.is_yellow_flagged:
            html_buffer += f"⚠️ "
        elif player.is_red_flagged:
            html_buffer += f"⛔️ "
        if player.was_subbed:
            html_buffer += f"🔄 "
        html_buffer += (
            f'<a href="html/player_{player.id}.html">{player.name}</a></b></td>\n'
        )

        ###

        # if player.name in [p[0].name for p in risers]:
        # 	style_str = '"color:green;vertical-align:middle;"'
        # elif player.name in [p[0].name for p in fallers]:
        # 	style_str = '"color:red;vertical-align:middle;"'
        # else:
        style_str = None

        if style_str is None:
            html_buffer += f'<td class="w3-center" style="vertical-align:middle;">£{player.price}</td>\n'
        else:
            html_buffer += (
                f'<td class="w3-center" style={style_str}><b>£{player.price}</b></td>\n'
            )

        if player.appearances < 1:
            score = 0.0
        else:
            score = player.total_points / player.appearances
        style_str = (
            get_style_from_event_score(score).rstrip('"') + ';vertical-align:middle;"'
        )
        html_buffer += (
            f'<td class="w3-center" style={style_str}>{player.total_points}</td>\n'
        )

        value = player.transfer_percent
        text = f"{player.transfer_percent:.1f}%"
        if abs(value) > 10:
            if text.startswith("-"):
                style_str = '"color:darkred;vertical-align:middle;"'
            else:
                style_str = '"color:darkgreen;vertical-align:middle;"'
            html_buffer += (
                f'<td class="w3-center" style={style_str}><b>{text}</b></td>\n'
            )
        else:
            if text.startswith("-"):
                style_str = '"color:red;vertical-align:middle;"'
            else:
                style_str = '"color:green;vertical-align:middle;"'
            html_buffer += f'<td class="w3-center" style={style_str}>{text}</td>\n'

        for i in range(start_gw, now_gw + 1):
            html_buffer += player_summary_cell_modal(player, i)

        form = player.form
        style_str = (
            get_style_from_event_score(form).rstrip('"') + ';vertical-align:middle;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>{player.form}</td>\n'

        for i in range(now_gw + 1, end_gw + 1):
            exp = player.expected_points(gw=i, debug=False)
            style_str = (
                get_style_from_event_score(exp).rstrip('"') + ';vertical-align:middle;"'
            )
            assert style_str is not None
            flag_str = ""
            chance = player.get_playing_chance(i)
            if chance < 0.25:
                flag_str = "⛔️ "
            elif chance < 1:
                flag_str = "⚠️ "
            html_buffer += f'<td class="w3-center" style={style_str}>{flag_str}{player.get_fixture_str(i,short=True,lower_away=True)}</td>\n'

        html_buffer += "</tr>\n"

    if manager is not None:

        html_buffer += "<tr>\n"
        # pos
        html_buffer += f'<td class="w3-center" style="vertical-align:middle;"></td>\n'
        # team
        html_buffer += f'<td class="w3-center" style="vertical-align:middle;"></td>\n'
        # name
        html_buffer += f'<td class="w3-center" style="vertical-align:middle;">{manager.name}</td>\n'
        # price
        html_buffer += f'<td class="w3-center" style="vertical-align:middle;">£{manager.team_value:.1f}</td>\n'
        # points
        score = manager.score
        style_str = (
            get_style_from_event_score(score / 12 / now_gw).rstrip('"')
            + ';vertical-align:middle;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>{score:1}</td>\n'
        # transfers
        html_buffer += f'<td class="w3-center" style="vertical-align:middle;"> </td>\n'
        # previous + live
        for i in range(start_gw, now_gw + 1):
            score = manager.get_event_score(gw=i)
            style_str = (
                get_style_from_event_score(score / 12).rstrip('"')
                + ';vertical-align:middle;"'
            )
            html_buffer += f'<td class="w3-center" style={style_str}>{score:1n}</td>\n'
        # form
        form = sum([p.form for p in players])
        style_str = (
            get_style_from_event_score(form / len(players)).rstrip('"')
            + ';vertical-align:middle;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>{form:.1f}</td>\n'
        # upcoming
        for i in range(now_gw + 1, end_gw + 1):
            manager.squad.set_best_multipliers(gw=i)
            exp = manager.squad.expected_points(gw=i)
            style_str = (
                get_style_from_event_score(exp / 12).rstrip('"')
                + ';vertical-align:middle;"'
            )
            html_buffer += f'<td class="w3-center" style={style_str}>{exp:.1f}</td>\n'
        html_buffer += "</tr>\n"

    html_buffer += "</table>\n"
    html_buffer += "</div>\n"

    return html_buffer


def create_manager_pick_history(api, man):

    squad = man.get_squad_history()

    for p in squad.players:
        # print(p,p._points_while_started,p._points_while_owned,p.total_points,p._weeks_owned,p._weeks_started)
        print(
            f"{p.name.rjust(20)} {p._num_weeks_owned:2n} started:{p._avg_pts_started} benched:{p._avg_pts_benched} total:{p._avg_pts_total}"
        )
        # print(f'{p.name.rjust(20)} {p._num_weeks_owned:2n} started/owned={100*p._points_while_started/p._points_while_owned if p._points_while_owned > 0 else 0:5.1f}% owned/total={100*p._points_while_started/p.total_points:5.1f}%')

    for p in squad.players:
        print(f"{p.name.rjust(20)}", end=" ")
        for gw in man.active_gws:
            if gw in p._weeks_captained:
                print("C", end="")
            elif gw in p._weeks_started:
                print("*", end="")
            elif gw in p._weeks_benched:
                print("-", end="")
            else:
                print(" ", end="")
        print(" ")


def get_style_from_difficulty(difficulty, old=False):

    style_str = '"'

    if old:

        if difficulty == 1:
            style_str += "background-color:darkgreen;color:white"
        elif difficulty == 2:
            style_str += "background-color:lightgreen;color:black"
        elif difficulty == 3:
            pass
        elif difficulty == 4:
            style_str += "background-color:red;color:black"
        elif difficulty == 5:
            style_str += "background-color:darkred;color:white"
    else:
        if not isinstance(difficulty, float):
            style_str += 'background-color: black;""color:white'
            return style_str

        if abs(difficulty) < 1.0:
            style_str += "background-color:white;color:black"
        elif difficulty > 0.0:
            if difficulty < 2.0:
                style_str += "background-color:lightgreen;color:black"
            else:
                style_str += "background-color:darkgreen;color:white"
        elif difficulty < 0.0:
            if difficulty > -2.0:
                style_str += "background-color:red;color:black"
            else:
                style_str += "background-color:darkred;color:white"

    style_str += '"'
    return style_str


def get_style_from_game_score(is_home, team_h_score, team_a_score):

    _team_h_score = float(team_h_score)
    _team_a_score = float(team_a_score)

    if not is_home:
        _team_h_score, _team_a_score = _team_a_score, _team_h_score

    style_str = '"'

    won = _team_h_score > _team_a_score
    draw = _team_h_score == _team_a_score
    clean_sheet = _team_a_score == 0
    opp_clean_sheet = _team_h_score == 0

    if won:
        if clean_sheet:
            style_str += "background-color:darkgreen;color:white"
        else:
            style_str += "background-color:lightgreen;color:black"
    elif not draw:
        if opp_clean_sheet:
            style_str += "background-color:darkred;color:white"
        else:
            style_str += "background-color:red;color:black"
    else:
        style_str += "background-color:white;color:black"
    style_str += '"'

    return style_str


def get_manager_json_positions(api, leagues):

    for l_id, l_data in json.items():

        if l_id == "timestamp":
            continue

        l_name = [l.name for l in leagues if l.id == int(l_id)][0]

        for gw_id, gw_data in l_data.items():

            for d_id, d_data in gw_data.items():

                if d_id == "positions":

                    for m_id, m_pos in d_data.items():

                        m_id = int(m_id)

                        if m_id not in api._managers.keys():
                            # mout.warningOut(f'{m_id} not in api._managers')
                            continue

                        m = api.get_manager(id=m_id)

                        if l_name not in m._league_positions.keys():
                            m._league_positions[l_name] = {}

                        m._league_positions[l_name][gw_id] = m_pos


def get_manager_json_awards(api, leagues):
    mout.debug("get_manager_json_awards()")

    for l_id, l_data in json.items():

        if l_id == "timestamp":
            continue

        l_name = [l.name for l in leagues if l.id == int(l_id)][0]

        for gw_id, gw_data in l_data.items():

            if "half" in gw_id:

                for key, data in gw_data["awards"].items():

                    try:
                        m = api.get_manager(id=data[0])
                        m._awards.append(
                            dict(key=key, score=data[-1], league=l_name, gw="half")
                        )
                    except TypeError as e:
                        mout.error(key, data)
                        mout.error(str(e))
                        raise e

                continue

            if "season" in gw_id:

                for key, data in gw_data["awards"].items():

                    # print(key, data)

                    try:
                        m = api.get_manager(id=data[0])
                        m._awards.append(
                            dict(key=key, score=data[-1], league=l_name, gw="season")
                        )
                    except TypeError as e:
                        mout.error(key, data)
                        mout.error(str(e))
                        raise e

                continue

            if "chips" in gw_id:

                for key, data in gw_data.items():
                    for key2, data2 in data.items():

                        # for m_id in data2[1]:
                        m = api.get_manager(id=data2[1])
                        m._awards.append(
                            dict(
                                key=f"{key}_{key2}",
                                score=data2[0],
                                league=l_name,
                                gw="chips",
                            )
                        )

                continue

            for d_id, d_data in gw_data.items():

                if d_id == "awards":

                    for key, data in d_data.items():

                        if data is None:
                            continue

                        if key == "scientist":
                            if data[0] in api._managers.keys():
                                m = api.get_manager(id=data[0])
                                m._awards.append(
                                    dict(
                                        key=key,
                                        player=data[1],
                                        multiplier=data[2],
                                        score=data[3],
                                        gw=gw_id,
                                        league=l_name,
                                    )
                                )
                        else:
                            subset = data[0:-1]
                            for id in subset:
                                if id in api._managers.keys():
                                    m = api.get_manager(id=id)
                                    m._awards.append(
                                        dict(
                                            key=key,
                                            score=data[-1],
                                            gw=gw_id,
                                            league=l_name,
                                        )
                                    )


def fixture_table(api, gw):

    html_buffer = ""

    fixtures = api.get_gw_fixtures(gw)

    if len(fixtures) < 1:
        html_buffer += '<div class="w3-center">'
        html_buffer += f"<h2>GW{gw}</h2>"
        html_buffer += f"<strong>No fixtures!</strong>"
        html_buffer += "</div>"
        return html_buffer

    html_buffer += '<div class="w3-center">'
    html_buffer += f"<h2>GW{gw} Fixtures</h2>"
    html_buffer += "</div>"
    html_buffer += '<div class="w3-responsive">'
    html_buffer += '<table class="w3-table w3-hoverable responsive-text">'

    new = True
    for i, fix in enumerate(fixtures):
        fix["date_str"] = fix["kickoff"].split("T")[0]
        fix["day_str"] = datetime.strptime(
            fix["kickoff"], "%Y-%m-%dT%H:%M:%SZ"
        ).strftime("%A")

        if not new and fix["day_str"] != fixtures[i - 1]["day_str"]:
            new = True

        if new:
            html_buffer += "<tr>"
            html_buffer += f'<td class="w3-right"></td>'
            html_buffer += f'<td class="w3-center"><h4>{fix["day_str"]}</h4></td>'
            html_buffer += f"<td></td>"
            html_buffer += "</tr>"
            new = False

        team_h_obj = api.get_player_team_obj(fix["team_h"])
        team_a_obj = api.get_player_team_obj(fix["team_a"])

        html_buffer += "<tr>"
        html_buffer += f'<td class="w3-right">{team_h_obj._shortname}\t<img class="w3-image" src="{team_h_obj._badge_url}" alt="Team" width="30" height="30"></td>'
        if not fix["started"]:
            local_tz = pytz.timezone("Europe/London")
            utc_dt = datetime.strptime(fix["kickoff"], "%Y-%m-%dT%H:%M:%SZ")
            utc_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
            time_str = utc_dt.strftime("%H:%M")
            html_buffer += f'<td class="w3-center">{time_str}</td>'
        else:

            team_h_score = fix["team_h_score"]
            team_a_score = fix["team_a_score"]

            html_buffer += f'<td class="w3-center"><b>{team_h_score:.0f} - {team_a_score:.0f}</b></td>'
        html_buffer += f'<td><img class="w3-image" src="{team_a_obj._badge_url}" alt="Team" width="30" height="30">\t{team_a_obj._shortname}</td>'
        html_buffer += "</tr>"

    html_buffer += "</table>"
    html_buffer += "</div>"

    return html_buffer


def generate_graphs(league):
    mout.debugOut(f"generate_graphs()")

    global api

    global graph_captain_points
    global graph_event_points
    global graph_player_selection
    global graph_gw_rank
    global graph_overall_rank

    gw = api.current_gw

    key = league.name.replace(" ", "")

    # if gw > 0:
    # 	# gw score vs league average (global average)
    # 	# graph_captain_points = plot.captain_points(league.managers,key, show=False)
    # 	# graph_event_points = plot.event_points(league.managers,key=key,relative=True,show=False)
    # 	# graph_player_selection = plot.player_selection(league.managers,key=key,show=False)
    # 	# graph_gw_rank = plot.gameweek_rank(league.managers,key=key,show=False)
    # 	# graph_overall_rank = plot.overall_rank(league.managers,key=key,show=False)
    # 	pass

    graph_past_rank = plot.rank_history(league.managers, key, show=False)


def previous_player_table(min_minutes=200, show_top=10):

    html_buffer = ""

    temp_elements = api._prev_elements[
        [
            "element_type",
            "first_name",
            "now_cost",
            "second_name",
            "web_name",
            "photo",
            "team",
            "team_code",
            "total_points",
            "minutes",
            "goals_scored",
            "assists",
            "clean_sheets",
            "goals_conceded",
            "own_goals",
            "penalties_saved",
            "penalties_missed",
            "yellow_cards",
            "red_cards",
            "saves",
            "bonus",
            "starts",
            "expected_goals",
            "expected_assists",
            "expected_goal_involvements",
            "expected_goals_conceded",
            "expected_goals_per_90",
            "saves_per_90",
            "expected_assists_per_90",
            "expected_goal_involvements_per_90",
            "expected_goals_conceded_per_90",
            "goals_conceded_per_90",
            "points_per_game_rank",
            "points_per_game_rank_type",
            "starts_per_90",
            "clean_sheets_per_90",
        ]
    ]

    temp_elements[temp_elements["minutes"] > min_minutes]

    # top scoring by position

    show_columns = {
        1: ("starts", "clean_sheets_per_90"),
    }

    def stat_spans(pd):
        buffer = ""
        if pd["goals_scored"] > 0:
            buffer += (
                f'<span class="w3-tag w3-green">{pd["goals_scored"]} goals</span>\n'
            )

        if pd["assists"] > 0:
            buffer += f'<span class="w3-tag w3-blue">{pd["assists"]} assists</span>\n'

        if pd["yellow_cards"] > 0:
            buffer += f'<span class="w3-tag w3-yellow">{pd["yellow_cards"]} yellow cards</span>\n'

        if pd["red_cards"] > 0:
            buffer += (
                f'<span class="w3-tag w3-red">{pd["red_cards"]} red cards</span>\n'
            )

        if pd["bonus"] > 0:
            buffer += f'<span class="w3-tag w3-aqua">{pd["bonus"]} bonus</span>\n'

        if pd["element_type"] < 4:
            if pd["clean_sheets"] > 0:
                buffer += f'<span class="w3-tag w3-purple">{pd["clean_sheets"]} clean sheets</span>\n'

        if pd["element_type"] == 1:
            if pd["penalties_saved"] > 0:
                buffer += f'<span class="w3-tag w3-green">{pd["penalties_saved"]} penalties saves</span>\n'
            if pd["saves"] > 0:
                buffer += f'<span class="w3-tag w3-blue">{pd["saves"]} saves</span>\n'

        if pd["element_type"] < 3:
            if pd["goals_conceded"] > 0:
                buffer += f'<span class="w3-tag w3-orange">{pd["goals_conceded"]} goals conceded</span>\n'

        if pd["minutes"] > 0:
            buffer += (
                f'<span class="w3-tag w3-dark-grey">{pd["minutes"]:.0f} mins</span>\n'
            )
        return buffer

    for i in range(4):

        table_buffer = ""

        html_buffer += '<div class="w3-col s12 m12 l6">\n'

        table_buffer += '<table class="w3-table w3-bordered responsive-text">\n'
        table_buffer += "<tr>\n"
        table_buffer += "<th>Player</th>\n"
        table_buffer += "<th>Points</th>\n"
        table_buffer += '<th class="w3-center">Stats</th>\n'
        table_buffer += "</tr>\n"

        elements = temp_elements[temp_elements["element_type"] == i + 1]
        elements = elements.sort_values(by=["total_points"], ascending=False)

        for j in range(show_top - 1):

            pd = elements.iloc[j + 1]

            name = f'<b>{pd["web_name"]}</b>'
            tot_pts = f'{pd["total_points"]}'

            table_buffer += f"<tr>\n"

            table_buffer += f"<td>\n"
            table_buffer += f"{name}</td>\n"
            table_buffer += f"<td>{tot_pts}</td>\n"

            table_buffer += f"<td>\n"

            table_buffer += stat_spans(pd)

            table_buffer += "</td>\n"
            table_buffer += "</tr>\n"

        table_buffer += "</table>\n"

        pd = elements.iloc[0]

        html_buffer += f'<div class="w3-panel w3-{api._short_team_pairs[pd["team_code"]-1].lower()}-inv shadow89" style="padding:0px;padding-bottom:4px;">\n'
        html_buffer += f'<div class="w3-center">\n'
        html_buffer += (
            f"<h2>Best {['Goalkeeper','Defender','Midfielder','Forward'][i]}</h2>"
        )

        html_buffer += f'<h2>{pd["web_name"]}: {pd["total_points"]} points</h2>'

        html_buffer += f'<img class="w3-image" style="width:30%" src="https://resources.premierleague.com/premierleague/photos/players/110x140/p{pd["photo"].replace(".jpg",".png")}"></img>\n'

        html_buffer += f'<div class="w3-panel w3-{api._short_team_pairs[pd["team_code"]-1].lower()} w3-padding-large">\n'
        html_buffer += stat_spans(pd)
        html_buffer += f"</div>\n"  # panel

        html_buffer += f"</div>\n"  # center

        html_buffer += table_buffer

        html_buffer += "</div>\n"  # panel
        html_buffer += "</div>\n"  # col

    return html_buffer

    # import plotly.graph_objects as go
    # fig = go.Figure()
    # trace = go.Histogram(x=temp_elements['minutes'])
    # fig.add_trace(trace)

    # fig.show()/


def create_homepage(navbar):
    mout.debugOut(f"create_homepage()")

    html_buffer = ""

    gw = api._current_gw

    html_buffer += ""

    # tagline
    html_buffer += '<div class="w3-col s12 m12 l4">\n'
    html_buffer += '<div class="w3-panel w3-amber w3-center w3-padding shadow89">\n'
    html_buffer += f"<h3>{TAGLINE}</h3>\n"
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    # navigation links
    html_buffer += '<div class="w3-col s12 m6 l4">\n'
    html_buffer += '<div class="w3-panel w3-center w3-white w3-padding shadow89">\n'
    html_buffer += "\n".join(navbar.split("\n")[7:-9])
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    # external links
    html_buffer += '<div class="w3-col s12 m6 l4">\n'
    html_buffer += '<div class="w3-panel w3-center w3-indigo w3-padding shadow89">\n'
    # url = 'https://www.facebook.com/groups/1488748394903477/'
    # html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">🗯️ Facebook Group</a>\n'
    url = "https://github.com/mwinokan/ToiletFPL/issues/new"
    html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">❓ Feature Request</a>\n'
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    if preseason:

        # table of total player information
        html_buffer += floating_subtitle("22/23 Top Assets", pad=0)

        html_buffer += previous_player_table()

    html_buffer += floating_subtitle("🗓 Fixtures", pad=1 if preseason else 0)

    if gw > 0:
        html_buffer += '<div class="w3-col s12 m12 l6">\n'
        html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
        html_buffer += fixture_table(api, gw)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"
    if gw < 38:
        html_buffer += '<div class="w3-col s12 m12 l6">\n'
        html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
        html_buffer += fixture_table(api, gw + 1)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    style = api.create_team_styles_css()
    html_page(
        "index.html",
        html=html_buffer,
        title="toilet.football",
        gw=api._current_gw,
        bar_html=navbar,
        colour="aqua",
        extra_style=style,
        timestamp=True,
    )


def create_seasonpage(leagues):
    mout.debugOut("create_seasonpage()")

    title = f"The RBS Diamond Invitational / Tesco Bean Value Toilet League"

    html_buffer = ""

    html_buffer += '<div class="w3-center">\n'
    html_buffer += f"<h2>{title}</h2>\n"
    html_buffer += "</div>\n"

    html_buffer += '<div class="w3-bar w3-black">\n'

    for i, league in enumerate(leagues[:2]):

        if i == 0:
            html_buffer += f'<button class="w3-bar-item w3-button w3-mobile tablink w3-red" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
        else:
            html_buffer += f'<button class="w3-bar-item w3-mobile w3-button tablink" onclick="openLeague(event,{league.id})">{league.name}</button>\n'

    html_buffer += "</div>\n"

    for i, league in enumerate(leagues[:2]):

        if i == 0:
            html_buffer += f'<div id="{league.id}" class="w3-container w3-border w3-white league">\n'
        else:
            html_buffer += f'<div id="{league.id}" class="w3-container w3-border w3-white league" style="display:none">\n'

        html_buffer += '<div class="w3-justify w3-row-padding">\n'

        html_buffer += "<h3>Chip Usage</h3>\n"
        html_buffer += league_best_chips(league)

        award_buffer = ""
        award_buffer += "<h3>Season Awards</h3>\n"
        award_buffer += make_season_awards(league)

        if league.num_managers > 20:
            subset = []
            subset += [d[0] for d in json[str(league.id)]["season"]["awards"].values()]
            subset += [d[0] for d in json[str(league.id)]["chips"]["wc2"].values()]
        else:
            subset = None

        html_buffer += "<h3>League Graph</h3>\n"
        import sys

        sys.path.insert(1, "go")
        from goleague import create_league_figure

        html_buffer += create_league_figure(api, league, subset)

        html_buffer += award_buffer

        html_buffer += "</div>\n"

        # md_buffer = ""
        # md_buffer += f"\n## League Table:\n"
        # md_buffer += f"Is your team's kit the boring default? Design it [here](https://fantasy.premierleague.com/entry-update)\n\n"
        # html_buffer += md2html(md_buffer)
        html_buffer += league_table_html(
            league, api._current_gw, awardkey="season", seasontable=True
        )

        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    html_buffer += "<script>\n"
    html_buffer += "function openLeague(evt, leagueName) {\n"
    html_buffer += "var i, x, tablinks;\n"
    html_buffer += 'x = document.getElementsByClassName("league");\n'
    html_buffer += "for (i = 0; i < x.length; i++) {\n"
    html_buffer += 'x[i].style.display = "none";\n'
    html_buffer += "}\n"
    html_buffer += 'tablinks = document.getElementsByClassName("tablink");\n'
    html_buffer += "for (i = 0; i < x.length; i++) {\n"
    html_buffer += (
        'tablinks[i].className = tablinks[i].className.replace(" w3-red", "");\n'
    )
    html_buffer += "}\n"
    html_buffer += 'document.getElementById(leagueName).style.display = "block";\n'
    html_buffer += 'evt.currentTarget.className += " w3-red";\n'
    html_buffer += "}\n"
    html_buffer += "</script>\n"

    navbar = create_navbar(leagues, active="S", colour="black", active_colour="green")
    html_page(
        f"html/season.html",
        None,
        title="22/23 Season Review",
        gw=api._current_gw,
        html=html_buffer,
        bar_html=navbar,
        showtitle=True,
        plotly=True,
        colour="indigo",
    )


def create_christmaspage(leagues):
    mout.debugOut("create_christmaspage()")

    # title = f"Christmas Review"
    title = f"The RBS Diamond Invitational / Tesco Bean Value Toilet League"

    html_buffer = ""

    html_buffer += '<div class="w3-center" style="padding-bottom:0px">\n'
    html_buffer += floating_subtitle(title)
    # html_buffer += f"<h2>{title}</h2>\n"
    html_buffer += f'<img class="w3-image" src="../images/christmas2024.png" alt="Banner" width="1320" height="702">\n'
    html_buffer += "</div>\n"

    html_buffer += '<div class="w3-col s12 m12 l12">\n'
    html_buffer += '<div class="w3-panel w3-white shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

    html_buffer += '<div class="w3-bar w3-black">\n'

    for i, league in enumerate(reversed(leagues[:2])):

        if i == 0:
            html_buffer += f'<button class="w3-bar-item w3-button w3-mobile tablink w3-red" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
        else:
            html_buffer += f'<button class="w3-bar-item w3-mobile w3-button tablink" onclick="openLeague(event,{league.id})">{league.name}</button>\n'

    html_buffer += "</div>\n"

    for i, league in enumerate(reversed(leagues[:2])):

        if i == 0:
            html_buffer += f'<div id="{league.id}" class="w3-container league">\n'
        else:
            html_buffer += f'<div id="{league.id}" class="w3-container league" style="display:none">\n'

        html_buffer += '<div class="w3-justify w3-row-padding">\n'

        # html_buffer += "<p>\n"
        # html_buffer += league_halfway_text[league.id]
        # html_buffer += "</p>\n"

        # html_buffer += "<h3>Chip Usage</h3>\n"
        html_buffer += floating_subtitle("Chip Usage")
        html_buffer += league_best_chips(league)

        # html_buffer += "</div>\n"

        award_buffer = ""
        award_buffer += floating_subtitle("Halfway Awards")
        # award_buffer += "<h3>Halfway Awards</h3>\n"
        award_buffer += christmas_awards(league)

        if league.num_managers > 20:
            subset = []
            subset += [d[0] for d in json[str(league.id)]["half"]["awards"].values()]
            subset += [d[-1] for d in json[str(league.id)]["chips"]["wc1"].values()]
            subset += json[str(league.id)][christmas_gw].get("promotion", [])
        else:
            subset = None

        html_buffer += floating_subtitle("League Graph")
        # html_buffer += "<h3>League Graph</h3>\n"
        import sys

        sys.path.insert(1, "go")
        from goleague import create_league_figure

        html_buffer += create_league_figure(api, league, subset)

        html_buffer += award_buffer

        html_buffer += floating_subtitle("League Table")
        md_buffer = ""
        # md_buffer += f"\n## League Table:\n"
        # md_buffer += f"Is your team's kit the boring default? Design it [here](https://fantasy.premierleague.com/entry-update)\n\n"
        html_buffer += md2html(md_buffer)
        html_buffer += "</div>\n"
        html_buffer += _league_table_html[league.id]

        html_buffer += "<br>\n"

        html_buffer += "</div>\n"

    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    html_buffer += "<script>\n"
    html_buffer += "function openLeague(evt, leagueName) {\n"
    html_buffer += "var i, x, tablinks;\n"
    html_buffer += 'x = document.getElementsByClassName("league");\n'
    html_buffer += "for (i = 0; i < x.length; i++) {\n"
    html_buffer += 'x[i].style.display = "none";\n'
    html_buffer += "}\n"
    html_buffer += 'tablinks = document.getElementsByClassName("tablink");\n'
    html_buffer += "for (i = 0; i < x.length; i++) {\n"
    html_buffer += (
        'tablinks[i].className = tablinks[i].className.replace(" w3-red", "");\n'
    )
    html_buffer += "}\n"
    html_buffer += 'document.getElementById(leagueName).style.display = "block";\n'
    html_buffer += 'evt.currentTarget.className += " w3-red";\n'
    html_buffer += "}\n"
    html_buffer += "</script>\n"

    navbar = create_navbar(leagues, active="C", colour="black", active_colour="red")
    html_page(
        f"html/christmas.html",
        None,
        title="2024 Christmas Review",
        gw=api._current_gw,
        html=html_buffer,
        bar_html=navbar,
        showtitle=True,
        plotly=True,
        colour="seagreen",
        nonw3_colour=True,
        text_colour="white",
    )


def manager_ids(mans):
    return [m.id for m in mans]


def league_best_chips(league):

    global json

    html_buffer = ""

    create_key(json[str(league.id)], "chips")

    finished = api._current_gw == 38 and not api._live_gw

    # bench boost
    bb_subset = [m for m in league.managers if m._bb_week]
    if len(bb_subset) > 1:
        bb_best = get_winners(
            "Best BB",
            bb_subset,
            lambda x: (x._bb_ptsgain, -x.get_specific_event_rank(x._bb_week)),
        )
        bb_worst = get_losers(
            "Worst BB",
            bb_subset,
            lambda x: (x._bb_ptsgain, -x.get_specific_event_rank(x._bb_week)),
        )
        create_key(json[str(league.id)]["chips"], "bb")
        json[str(league.id)]["chips"]["bb"]["best"] = [bb_best[0], bb_best[1].id]
        json[str(league.id)]["chips"]["bb"]["worst"] = [bb_worst[0], bb_worst[1].id]

    # triple captain
    tc_subset = [m for m in league.managers if m._tc_week]
    if len(tc_subset) > 1:
        tc_best = get_winners(
            "Best TC",
            tc_subset,
            lambda x: (x._tc_ptsgain, -x.get_specific_event_rank(x._tc_week)),
        )
        tc_worst = get_losers(
            "Worst TC",
            tc_subset,
            lambda x: (x._tc_ptsgain, -x.get_specific_event_rank(x._tc_week)),
        )
        create_key(json[str(league.id)]["chips"], "tc")
        json[str(league.id)]["chips"]["tc"]["best"] = [tc_best[0], tc_best[1].id]
        json[str(league.id)]["chips"]["tc"]["worst"] = [tc_worst[0], tc_worst[1].id]

    # Free hit
    fh_subset = [m for m in league.managers if m._fh_week]
    if len(fh_subset) > 1:
        fh_best = get_losers("Best fh", fh_subset, lambda x: x._fh_gwrank)
        fh_worst = get_winners("Worst fh", fh_subset, lambda x: x._fh_gwrank)
        create_key(json[str(league.id)]["chips"], "fh")
        json[str(league.id)]["chips"]["fh"]["best"] = [fh_best[0], fh_best[1].id]
        json[str(league.id)]["chips"]["fh"]["worst"] = [fh_worst[0], fh_worst[1].id]

    # First wildcard
    wc1_subset = [m for m in league.managers if m._wc1_week]
    wc1_best = get_winners("Best wc1", wc1_subset, lambda x: x._wc1_ordelta_percent)
    wc1_worst = get_losers("Worst wc1", wc1_subset, lambda x: x._wc1_ordelta_percent)
    create_key(json[str(league.id)]["chips"], "wc1")
    json[str(league.id)]["chips"]["wc1"]["best"] = [wc1_best[0], wc1_best[1].id]
    json[str(league.id)]["chips"]["wc1"]["worst"] = [wc1_worst[0], wc1_worst[1].id]

    # Second wildcard
    wc2_subset = [m for m in league.managers if m._wc2_week]
    if finished:
        wc2_best = get_winners("Best wc2", wc2_subset, lambda x: x._wc2_ordelta_percent)
        wc2_worst = get_losers(
            "Worst wc2", wc2_subset, lambda x: x._wc2_ordelta_percent
        )
        create_key(json[str(league.id)]["chips"], "wc2")
        json[str(league.id)]["chips"]["wc2"]["best"] = [wc2_best[0], wc2_best[1].id]
        json[str(league.id)]["chips"]["wc2"]["worst"] = [wc2_worst[0], wc2_worst[1].id]

    # table
    html_buffer += '<table class="w3-table-all w3-hoverable">\n'
    html_buffer += "<thead>\n"
    html_buffer += "<tr>\n"

    html_buffer += '<th style="text-align:center;">Chip</th>\n'
    html_buffer += '<th style="text-align:center;">Best</th>\n'
    html_buffer += f'<th style="text-align:center;">Delta</th>\n'
    html_buffer += '<th style="text-align:center;">Worst</th>\n'
    html_buffer += f'<th style="text-align:center;">Delta</th>\n'
    html_buffer += "</tr>\n"
    html_buffer += "</thead>\n"

    html_buffer += "<tbody>\n"

    ### triple captain
    if len(tc_subset) > 1:
        html_buffer += "<tr>\n"
        html_buffer += f'<td class="w3-amber" style="text-align:center;">TC</td>\n'
        html_buffer += f'<td style="text-align:center;">\n'
        man = tc_best[1]
        html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
        if "Toilet" in league.name and man.is_diamond:
            html_buffer += "💎"
        html_buffer += f"with {man._tc_name} in GW{man._tc_week}\n"

        html_buffer += "</td>\n"
        html_buffer += (
            f'<td style="text-align:center;">{pts_delta_format(tc_best[0][0])}</td>\n'
        )
        if len(tc_subset) == 1:
            html_buffer += f"<td></td>\n"
            html_buffer += f"<td></td>\n"
        else:
            man = tc_worst[1]
            html_buffer += f'<td style="text-align:center;">\n'
            html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
            if "Toilet" in league.name and man.is_diamond:
                html_buffer += "💎"
            html_buffer += f"with {man._tc_name} in GW{man._tc_week}\n"
            html_buffer += "</td>\n"
            html_buffer += f'<td style="text-align:center;">{pts_delta_format(tc_worst[0][0])}</td>\n'
        html_buffer += "</tr>\n"

    ### wildcard 1
    html_buffer += "<tr>\n"
    html_buffer += f'<td class="w3-red" style="text-align:center;">WC1</td>\n'
    html_buffer += f'<td style="text-align:center;">\n'
    man = wc1_best[1]
    html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
    if "Toilet" in league.name and man.is_diamond:
        html_buffer += "💎"
    html_buffer += f" in GW{man._wc1_week}\n"
    html_buffer += "</td>\n"
    delta = man._wc1_ordelta_percent
    if delta > 0:
        delta = f"+{delta:.0f}"
    else:
        delta = f"{delta:.0f}"
    html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'

    if len(wc1_subset) == 1:
        html_buffer += f"<td></td>\n"
        html_buffer += f"<td></td>\n"
    else:
        html_buffer += f'<td style="text-align:center;">\n'
        man = wc1_worst[1]
        html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
        if "Toilet" in league.name and man.is_diamond:
            html_buffer += "💎"
        html_buffer += f" in GW{man._wc1_week}\n"
        html_buffer += "</td>\n"
        delta = man._wc1_ordelta_percent
        if delta > 0:
            delta = f"+{delta:.0f}"
        else:
            delta = f"{delta:.0f}"
        html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
    html_buffer += "</tr>\n"

    ### wildcard 2
    if finished:
        html_buffer += "<tr>\n"
        html_buffer += f'<td class="w3-red" style="text-align:center;">WC2</td>\n'
        html_buffer += f'<td style="text-align:center;">\n'
        man = wc2_best[1]
        html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
        if "Toilet" in league.name and man.is_diamond:
            html_buffer += "💎"
        html_buffer += f" in GW{man._wc2_week}\n"
        html_buffer += "</td>\n"
        delta = man._wc2_ordelta_percent
        if delta > 0:
            delta = f"+{delta:.0f}"
        else:
            delta = f"{delta:.0f}"
        html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
        if len(wc2_subset) == 1:
            html_buffer += f"<td></td>\n"
            html_buffer += f"<td></td>\n"
        else:
            html_buffer += f'<td style="text-align:center;">\n'
            man = wc2_worst[1]
            html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
            if "Toilet" in league.name and man.is_diamond:
                html_buffer += "💎"
            html_buffer += f" in GW{man._wc2_week}\n"
            html_buffer += "</td>\n"
            delta = man._wc2_ordelta_percent
            if delta > 0:
                delta = f"+{delta:.0f}"
            else:
                delta = f"{delta:.0f}"
            html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
        html_buffer += "</tr>\n"

    ### free hit
    if len(fh_subset) > 1:
        html_buffer += "<tr>\n"
        html_buffer += f'<td class="w3-green" style="text-align:center;">FH</td>\n'
        html_buffer += f'<td style="text-align:center;">\n'
        man = fh_best[1]
        html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
        if "Toilet" in league.name and man.is_diamond:
            html_buffer += "💎"
        html_buffer += f" with {man._fh_total}pts in GW{man._fh_week}\n"
        html_buffer += "</td>\n"
        delta = 100 * (man._fh_orprev - man._fh_or) / man._fh_orprev
        if delta > 0:
            delta = f"+{delta:.0f}"
        else:
            delta = f"{delta:.0f}"
        html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
        if len(fh_subset) == 1:
            html_buffer += f"<td></td>\n"
            html_buffer += f"<td></td>\n"
        else:
            html_buffer += f'<td style="text-align:center;">\n'
            man = fh_worst[1]
            html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
            if "Toilet" in league.name and man.is_diamond:
                html_buffer += "💎"
            html_buffer += f"with {man._fh_total}pts in GW{man._fh_week}\n"
            html_buffer += "</td>\n"
            delta = 100 * (man._fh_orprev - man._fh_or) / man._fh_orprev
            if delta > 0:
                delta = f"+{delta:.0f}"
            else:
                delta = f"{delta:.0f}"
            html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
        html_buffer += "</tr>\n"

    ### bench boost
    if len(bb_subset) > 1:
        html_buffer += "<tr>\n"
        html_buffer += f'<td class="w3-blue" style="text-align:center;">BB</td>\n'
        html_buffer += f'<td style="text-align:center;">\n'
        man = bb_best[1]
        html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
        if "Toilet" in league.name and man.is_diamond:
            html_buffer += "💎"
        html_buffer += f"in GW{man._bb_week}\n"
        html_buffer += "</td>\n"
        html_buffer += (
            f'<td style="text-align:center;">{pts_delta_format(bb_best[0][0])}</td>\n'
        )
        if len(bb_subset) == 1:
            html_buffer += f"<td></td>\n"
            html_buffer += f"<td></td>\n"
        else:
            html_buffer += f'<td style="text-align:center;">\n'
            man = bb_worst[1]
            html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
            if "Toilet" in league.name and man.is_diamond:
                html_buffer += "💎"
            html_buffer += f"in GW{man._bb_week}\n"
            html_buffer += "</td>\n"
            html_buffer += f'<td style="text-align:center;">{pts_delta_format(bb_worst[0][0])}</td>\n'
        html_buffer += "</tr>\n"

    html_buffer += "</tbody>\n"
    html_buffer += "</table>\n"

    return html_buffer


def pts_delta_format(delta):
    if delta < 0:
        return f"{delta}pts"
    else:
        return f"+{delta}pts"


def get_losers(name, managers, criterium):
    return get_winners(name, managers, criterium, reverse=False)


def get_winners(name, managers, criterium, reverse=True):
    sorted_managers = sorted(managers, key=criterium, reverse=reverse)
    man = sorted_managers[0]
    score = criterium(man)
    return score, man


def make_season_awards(league):

    html_buffer = ""

    global json

    create_key(json[str(league.id)], "season")
    create_key(json[str(league.id)]["season"], "awards")

    sorted_managers = sorted(
        league.active_managers, key=lambda x: x.overall_rank, reverse=False
    )
    score = sorted_managers[0].total_livescore
    scores = [m.overall_rank for m in sorted_managers]
    html_buffer += award_panel(
        "👑",
        f"King",
        "Best Score",
        f"{score} pts, {api.big_number_format(sorted_managers[0].overall_rank)} OR",
        sorted_managers[0],
        colour="amber",
        border="yellow",
        name_class="h2",
        halfonly=True,
    )
    json[str(league.id)]["season"]["awards"]["king"] = [sorted_managers[0].id, score]

    sorted_managers.reverse()
    scores.reverse()
    data = Counter(scores)
    num = data[scores[0]]
    if num == 1:
        html_buffer += award_panel(
            "🐓",
            f"Cock",
            "Worst Score",
            f"{sorted_managers[0].total_livescore} pts, {api.big_number_format(sorted_managers[0].overall_rank)} OR",
            sorted_managers[0],
            colour="red",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )
        json[str(league.id)]["season"]["awards"]["cock"] = [
            sorted_managers[0].id,
            scores[0],
        ]
    else:
        mout.warningOut("Too many people sharing cock award")
        json[str(league.id)]["season"]["awards"]["cock"] = None

    sorted_managers = sorted(
        league.active_managers, key=lambda x: x.total_transfer_gain, reverse=True
    )
    scores = [x.total_transfer_gain for x in sorted_managers]
    data = Counter(scores)
    num = data[scores[0]]
    if num == 1:
        html_buffer += award_panel(
            "🔮",
            f"Fortune Teller",
            "Best Total Transfer Gain",
            f"+{scores[0]} pts",
            sorted_managers[0],
            colour="purple",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )
        json[str(league.id)]["season"]["awards"]["fortune"] = [
            sorted_managers[0].id,
            scores[0],
        ]
    else:
        mout.warningOut("Too many people sharing fortune spot")
        json[str(league.id)]["season"]["awards"]["fortune"] = None

    sorted_managers.reverse()
    scores.reverse()
    data = Counter(scores)
    num = data[scores[0]]
    if num == 1:
        html_buffer += award_panel(
            "🤡",
            f"Clown",
            "Worst Total Transfer Gain",
            f"{scores[0]} pts",
            sorted_managers[0],
            colour="pale-red",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )
        json[str(league.id)]["season"]["awards"]["clown"] = [
            sorted_managers[0].id,
            scores[0],
        ]
    else:
        mout.warningOut("Too many people sharing clown spot")
        json[str(league.id)]["season"]["awards"]["clown"] = None

    # kneejerker
    sorted_managers = sorted(
        league.active_managers,
        key=lambda x: (x.num_nonwc_transfers, x.num_hits),
        reverse=True,
    )
    scores = [(x.num_nonwc_transfers, x.num_hits) for x in sorted_managers]
    data = Counter(scores)
    num = data[scores[0]]
    if num > 1:
        mout.warningOut("Too many people sharing kneejerker spot")
        json[str(league.id)]["season"]["awards"]["kneejerker"] = None
        # sorted_managers2 = [sorted(sorted_managers[0:num], key=lambda x: x.num_hits, reverse=True)[0]]
        # scores2 = [[x.num_hits for x in sorted_managers][0]]
        # data = Counter(scores2)
        # num = data[scores2[0]]
        # print("Kneejerker",sorted_managers2[0:num],scores[0],scores2[0])
        # json[str(league.id)]['season']['awards']['kneejerker'] = [[m.id for m in sorted_managers2[0:num]],scores[0],scores2[0]]
        # html_buffer += award_panel('🔨',f'Kneejerker','Most Transfers',f'{scores[0]} transfers, {scores2[0]} hits',sorted_managers2[0:num],colour='deep-orange',border='yellow',name_class="h2",halfonly=True)
    else:
        print(
            "Kneejerker", sorted_managers[0:num], scores[0], sorted_managers[0].num_hits
        )
        json[str(league.id)]["season"]["awards"]["kneejerker"] = [
            sorted_managers[0].id,
            sorted_managers[0].num_nonwc_transfers,
            sorted_managers[0].num_hits,
        ]
        html_buffer += award_panel(
            "🔨",
            f"Kneejerker",
            "Most Transfers",
            f"{scores[0][0]} transfers, {sorted_managers[0].num_hits} hits",
            sorted_managers[0],
            colour="deep-orange",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )

    # iceman
    sorted_managers.reverse()
    scores.reverse()
    data = Counter(scores)
    num = data[scores[0]]
    if num > 1:
        mout.warningOut("Too many people sharing iceman spot")
        json[str(league.id)]["season"]["awards"]["iceman"] = None
        # sorted_managers2 = sorted(sorted_managers[0:num], key=lambda x: x.num_hits, reverse=False)
        # scores2 = [x.num_hits for x in sorted_managers]
        # data = Counter(scores2)
        # num = data[scores2[0]]
        # print("Iceman",sorted_managers2[0:num],scores[0],scores2[0])
        # json[str(league.id)]['season']['awards']['iceman'] = [[m.id for m in sorted_managers2[0:num]],scores[0],scores2[0]]
        # html_buffer += award_panel('🥶',f'Iceman','Least Transfers',f'{scores[0]} transfers, {scores2[0]} hits',sorted_managers2[0:num],colour='aqua',border='yellow',name_class="h2",halfonly=True)
    else:
        print("Iceman", sorted_managers[0:num], scores[0], sorted_managers[0].num_hits)
        json[str(league.id)]["season"]["awards"]["iceman"] = [
            sorted_managers[0].id,
            sorted_managers[0].num_nonwc_transfers,
            sorted_managers[0].num_hits,
        ]
        html_buffer += award_panel(
            "🥶",
            f"Iceman",
            "Least Transfers",
            f"{scores[0][0]} transfers, {sorted_managers[0].num_hits} hits",
            sorted_managers[0],
            colour="aqua",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )

    # oligarch
    sorted_managers = sorted(
        league.active_managers, key=lambda x: x.team_value, reverse=True
    )
    scores = [x.team_value for x in sorted_managers]
    data = Counter(scores)
    num = data[scores[0]]
    json[str(league.id)]["season"]["awards"]["oligarch"] = [
        sorted_managers[0].id,
        scores[0],
    ]
    html_buffer += award_panel(
        "🛢",
        f"Oligarch",
        "Highest Team Value",
        f"£{scores[0]:.1f}",
        sorted_managers[0],
        colour="black",
        border="yellow",
        name_class="h2",
        halfonly=True,
    )

    # peasant
    sorted_managers.reverse()
    scores.reverse()
    data = Counter(scores)
    num = data[scores[0]]
    json[str(league.id)]["season"]["awards"]["peasant"] = [
        sorted_managers[0].id,
        scores[0],
    ]
    html_buffer += award_panel(
        "🏚",
        f"Peasant",
        "Lowest Team Value",
        f"£{scores[0]:.1f}",
        sorted_managers[0],
        colour="brown",
        border="yellow",
        name_class="h2",
        halfonly=True,
    )

    # glow-up (best improvement in the quarter season (GW8-GW16))
    sorted_managers = sorted(
        league.active_managers,
        key=lambda x: (
            x.get_specific_overall_rank(19)
            - x.get_specific_overall_rank(api._current_gw)
        )
        / x.get_specific_overall_rank(19),
        reverse=True,
    )
    m = sorted_managers[0]
    s = (
        m.get_specific_overall_rank(19) - m.get_specific_overall_rank(api._current_gw)
    ) / m.get_specific_overall_rank(19)
    json[str(league.id)]["season"]["awards"]["glow_up"] = [m.id, s]
    if s > 0:
        html_buffer += award_panel(
            "💡",
            f"Glow-Up",
            "Best improvement since Christmas",
            f"{api.big_number_format(m.get_specific_overall_rank(19))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = +{100*s:.1f}%",
            m,
            colour="pale-yellow",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )
    else:
        html_buffer += award_panel(
            "💡",
            f"Glow-Up",
            "Best improvement since Christmas",
            f"{api.big_number_format(m.get_specific_overall_rank(19))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = {100*s:.1f}%",
            m,
            colour="pale-yellow",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )

    # hasbeen
    m = sorted_managers[-1]
    s = m.get_specific_overall_rank(19) - m.get_specific_overall_rank(api._current_gw)
    s = s / m.get_specific_overall_rank(19)
    json[str(league.id)]["season"]["awards"]["has_been"] = [m.id, s]
    if s > 0:
        html_buffer += award_panel(
            "👨‍🦳",
            f"Has-Been",
            "Worst improvement since Christmas",
            f"{api.big_number_format(m.get_specific_overall_rank(19))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = +{100*s:.1f}%",
            m,
            colour="grey",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )
    else:
        html_buffer += award_panel(
            "👨‍🦳",
            f"Has-Been",
            "Worst improvement since Christmas",
            f"{api.big_number_format(m.get_specific_overall_rank(19))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = {100*s:.1f}%",
            m,
            colour="grey",
            border="yellow",
            name_class="h2",
            halfonly=True,
        )

    return html_buffer


def christmas_awards(league):

    html_buffer = ""

    global json

    create_key(json[str(league.id)], "half")
    create_key(json[str(league.id)]["half"], "awards")

    ### KING
    sorted_managers = sorted(
        league.active_managers,
        key=lambda x: (x.total_livescore, x.gw_rank_gain),
        reverse=True,
    )
    man = sorted_managers[0]
    score = man.total_livescore
    html_buffer += award_panel(
        "👑",
        f"King",
        "Best Score",
        f"{score} pts, {api.big_number_format(man.overall_rank)} OR",
        man,
        colour="amber",
        border="green",
        name_class="h2",
        halfonly=True,
    )
    json[str(league.id)]["half"]["awards"]["king"] = [man.id, score]

    ### COCK
    man = sorted_managers[-1]
    score = man.total_livescore
    html_buffer += award_panel(
        "🐓",
        f"Cock",
        "Worst Score",
        f"{score} pts, {api.big_number_format(man.overall_rank)} OR",
        man,
        colour="red",
        border="green",
        name_class="h2",
        halfonly=True,
    )
    json[str(league.id)]["half"]["awards"]["cock"] = [man.id, score]

    result = json[str(league.id)][api._current_gw]["awards"].get("zombie", None)
    print("zombie", result)
    if result:
        m_id, place = result
        m = api.get_manager(id=m_id)
        html_buffer += award_panel(
            "🧟",
            f"Zombie",
            "Best Dead Team",
            f"{place}th place, {api.big_number_format(m.overall_rank)} OR",
            m,
            colour="teal",
            border="green",
            name_class="h2",
            halfonly=True,
        )
        json[str(league.id)]["half"]["awards"]["zombie"] = [
            m_id,
            place,
        ]

    ### FORTUNE TELLER
    sorted_managers = sorted(
        league.active_managers,
        key=lambda x: (x.total_transfer_gain, x.avg_selection),
        reverse=True,
    )
    man = sorted_managers[0]
    score = man.total_transfer_gain
    html_buffer += award_panel(
        "🔮",
        f"Fortune Teller",
        "Best Total Transfer Gain",
        f"{score:+} pts",
        man,
        colour="purple",
        border="green",
        name_class="h2",
        halfonly=True,
    )
    json[str(league.id)]["half"]["awards"]["fortune"] = [man.id, score]

    ### CLOWN
    man = sorted_managers[-1]
    score = man.total_transfer_gain
    html_buffer += award_panel(
        "🤡",
        f"Clown",
        "Worst Total Transfer Gain",
        f"{score:+} pts",
        man,
        colour="pale-red",
        border="green",
        name_class="h2",
        halfonly=True,
    )
    json[str(league.id)]["half"]["awards"]["clown"] = [man.id, score]

    # kneejerker
    sorted_managers = sorted(
        league.active_managers,
        key=lambda x: (x.num_nonwc_transfers, x.num_hits, x._transfer_uniqueness),
        reverse=True,
    )
    man = sorted_managers[0]
    json[str(league.id)]["half"]["awards"]["kneejerker"] = [
        man.id,
        man.num_nonwc_transfers,
        man.num_hits,
    ]
    html_buffer += award_panel(
        "🔨",
        f"Kneejerker",
        "Most Transfers",
        f"{man.num_nonwc_transfers} transfers, {man.num_hits} hits",
        man,
        colour="deep-orange",
        border="green",
        name_class="h2",
        halfonly=True,
    )

    # iceman
    man = sorted_managers[-1]
    json[str(league.id)]["half"]["awards"]["iceman"] = [
        man.id,
        man.num_nonwc_transfers,
        man.num_hits,
    ]
    html_buffer += award_panel(
        "🥶",
        f"Iceman",
        "Least Transfers",
        f"{man.num_nonwc_transfers} transfers, {man.num_hits} hits",
        man,
        colour="aqua",
        border="green",
        name_class="h2",
        halfonly=True,
    )

    # oligarch
    sorted_managers = sorted(
        league.active_managers,
        key=lambda x: (x.team_value, -x.total_livescore),
        reverse=True,
    )
    man = sorted_managers[0]
    json[str(league.id)]["half"]["awards"]["oligarch"] = [man.id, man.team_value]
    html_buffer += award_panel(
        "🛢",
        f"Oligarch",
        "Highest Team Value",
        f"£{man.team_value:.1f}",
        man,
        colour="black",
        border="green",
        name_class="h2",
        halfonly=True,
    )

    # peasant
    man = sorted_managers[-1]
    json[str(league.id)]["half"]["awards"]["peasant"] = [man.id, man.team_value]
    html_buffer += award_panel(
        "🏚",
        f"Peasant",
        "Lowest Team Value",
        f"£{man.team_value:.1f}",
        man,
        colour="brown",
        border="green",
        name_class="h2",
        halfonly=True,
    )

    # glow-up (best improvement in the quarter season (GW8-GW16))
    sorted_managers = sorted(
        league.active_managers,
        key=lambda x: (
            x.get_specific_overall_rank(christmas_gw // 2)
            - x.get_specific_overall_rank(christmas_gw)
        )
        / x.get_specific_overall_rank(christmas_gw // 2),
        reverse=True,
    )
    m = sorted_managers[0]
    s = (
        m.get_specific_overall_rank(christmas_gw // 2)
        - m.get_specific_overall_rank(christmas_gw)
    ) / m.get_specific_overall_rank(christmas_gw // 2)
    json[str(league.id)]["half"]["awards"]["glow_up"] = [m.id, s]
    html_buffer += award_panel(
        "💡",
        f"Glow-Up",
        f"Best {int(christmas_gw // 2):d}GW improvement",
        f"{api.big_number_format(m.get_specific_overall_rank(christmas_gw // 2))}→{api.big_number_format(m.get_specific_overall_rank(christmas_gw))} = {100*s:+.1f}%",
        m,
        colour="pale-yellow",
        border="green",
        name_class="h2",
        halfonly=True,
    )

    # has-been
    m = sorted_managers[-1]
    s = m.get_specific_overall_rank(christmas_gw) - m.get_specific_overall_rank(
        christmas_gw // 2
    )
    s = -s / m.get_specific_overall_rank(christmas_gw // 2)
    json[str(league.id)]["half"]["awards"]["has_been"] = [m.id, s]
    html_buffer += award_panel(
        "👨‍🦳",
        f"Has-Been",
        f"Worst {int(christmas_gw // 2):d}GW improvement",
        f"{api.big_number_format(m.get_specific_overall_rank(christmas_gw // 2))}→{api.big_number_format(m.get_specific_overall_rank(christmas_gw))} = {100*s:+.1f}%",
        m,
        colour="grey",
        border="green",
        name_class="h2",
        halfonly=True,
    )

    return html_buffer


def award_panel(
    icon,
    name,
    description,
    value,
    manager,
    colour="light-grey",
    border=None,
    name_class="h1",
    value_class="h2",
    halfonly=False,
):

    many = isinstance(manager, list)
    m = manager

    if many and len(manager) > 1:
        mout.error("Awards are not supposed to be shared anymore!!")
        print(icon, name, description, value, manager)

    html_buffer = ""

    if halfonly:
        html_buffer += f'<div class="w3-col s12 m12 l6">\n'
    else:
        html_buffer += f'<div class="w3-col s12 m6 l4">\n'

    if border:
        html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-border-{border} shadow89">\n'
    else:
        html_buffer += f'<div class="w3-panel w3-{colour} shadow89">\n'

    html_buffer += f'<table style="width:100%;padding:0px;border-spacing:0px;padding-bottom:10px">\n'
    html_buffer += f"<tr>\n"
    html_buffer += f'<td style="text-align:left;vertical-align:middle;">\n'
    html_buffer += f'<{name_class} style="text-shadow: 1px 2px 4px rgba(0,0,0,0.5);">{icon} {name}</{name_class}>\n'

    html_buffer += f"<h4>{description}</h4>\n"

    html_buffer += f"</td>\n"

    html_buffer += f'<td style="text-align:right;vertical-align:middle;">\n'
    html_buffer += f'<h2><span class="w3-tag shadow89">{value}</span></h2>\n'

    html_buffer += f'<a href="{m.gui_url}">{m.team_name}</a>'
    html_buffer += f"<br>"
    html_buffer += f'<a href="{m.gui_url}">{m.name}</a>'

    html_buffer += f"</td>\n"
    html_buffer += f"</tr>\n"
    html_buffer += f"</table>\n"
    html_buffer += f"</div>\n"
    html_buffer += f"</div>\n"

    return html_buffer


def floating_subtitle(text, pad=1, button=False):
    html_buffer = ""
    html_buffer += '<div class="w3-col s12 m12 l12">\n'
    for i in range(pad):
        html_buffer += "<br>\n"

    if button:
        html_buffer += (
            f'\t<a href="{button}"><h1 class="w3-tag shadow89">{text}</h1></a>\n'
        )
    else:
        html_buffer += f'\t<h1 class="w3-tag shadow89">{text}</h1>\n'

    html_buffer += "</div>\n"
    return html_buffer


def create_leaguepage(league, leagues, i):
    mout.debugOut(f"create_leaguepage({league})")

    global api
    global json

    md_buffer = ""
    html_buffer = ""

    gw = api.current_gw

    create_key(json, str(league.id))
    create_key(json[str(league.id)], gw)

    mout.debugOut(f"create_leaguepage({league})::differential_buffer")
    differential_buffer = league_differentials(league, gw)

    mout.debugOut(f"create_leaguepage({league})::Awards")

    create_key(json[str(league.id)][gw], "awards")

    awards = gw > 0 and (
        not api._live_gw or any([f["started"] for f in api.get_gw_fixtures(gw)])
    )

    if awards:

        if gw > 0:

            gw_str = "GW"
            if gw in api._special_gws.keys():
                gw_str = api._special_gws[gw]
            gw_str = f"{gw_str}{gw}"

            if api._live_gw:
                html_buffer += floating_subtitle(f"🏆 {gw_str} Awards (Live)", pad=0)
            else:
                html_buffer += floating_subtitle(f"🏆 {gw_str} Awards", pad=0)

            ### KING
            sorted_managers = sorted(
                league.active_managers,
                key=lambda x: (x.livescore, x.gw_rank_gain, x.gw_performed_xpts),
                reverse=True,
            )
            m = sorted_managers[0]
            score = m.livescore
            html_buffer += award_panel(
                "👑",
                "King",
                "Best GW",
                f"{score} pts",
                m,
                colour=award_colour["king"],
                name_class="h2",
            )
            json[str(league.id)][gw]["awards"]["king"] = [m.id, score]

            ### COCK

            m = sorted_managers[-1]
            score = m.livescore
            html_buffer += award_panel(
                "🐓",
                "Cock",
                "Worst GW",
                f"{score} pts",
                m,
                colour=award_colour["cock"],
                name_class="h2",
            )
            json[str(league.id)][gw]["awards"]["cock"] = [m.id, score]

            ### MASSIVE GOALS

            sorted_managers = sorted(
                league.active_managers,
                key=lambda x: (x.goals, x.gw_xg, x.gw_xa, x.livescore),
                reverse=True,
            )
            m = sorted_managers[0]
            score = m.goals
            if score > 4:
                score_str = f"{score}×⚽️"
            else:
                score_str = f'{"⚽️"*score}'
            html_buffer += award_panel(
                "⚽️",
                "Massive Goal FC",
                "Most Goals",
                score_str,
                m,
                colour=award_colour["goals"],
                name_class="h3",
            )
            json[str(league.id)][gw]["awards"]["goals"] = [m.id, score]

            ### SCIENTIST

            p_id, m_id, p_is_captain, score, pts_gain = json[str(league.id)][gw][
                "differentials"
            ][0]

            # print(p_id, m_id, p_is_captain, score, pts_gain)

            m = api.get_manager(id=m_id)

            squad = m.get_current_squad(gw=gw)

            p = [p for p in squad.players if p.id == p_id][0]

            p_str = p.name
            if p.multiplier == 3:
                p_str += " (TC)"
            elif p.multiplier == 2:
                p_str += " (C)"

            html_buffer += award_panel(
                "🧑‍🔬",
                "Scientist",
                "Best Differential",
                p_str,
                m,
                colour=award_colour["scientist"],
                value_class="h3",
                name_class="h2",
            )

            json[str(league.id)][gw]["awards"]["scientist"] = [
                m_id,
                p_id,
                p.multiplier,
                score,
            ]

            ### HOT STUFF

            # sorted_managers = sorted([m for m in league.active_managers if m.gw_performed_xpts > 0], key=lambda x: ((x.livescore - x.gw_performed_xpts)/x.gw_performed_xpts, x.gw_performed_xpts), reverse=True)
            # if len(sorted_managers) > 0:
            # 	m = sorted_managers[0]
            # 	score = (m.livescore - m.gw_performed_xpts)/m.gw_performed_xpts

            # 	html_buffer += award_panel('🥵','Hot Stuff','xGI Overperformer',f'{score:+.1%}',m,colour=award_colour['hot_stuff'],name_class="h2")
            # 	json[str(league.id)][gw]['awards']['hot_stuff'] = [m.id,score]

            # 	### SOGGY BISCUIT

            # 	m = sorted_managers[-1]
            # 	score = (m.livescore - m.gw_performed_xpts)/m.gw_performed_xpts
            # 	html_buffer += award_panel('🍪','Soggy Biscuit','xGI Underperformer',f'{score:+.1%}',m,colour=award_colour['soggy_biscuit'],name_class="h3")
            # 	json[str(league.id)][gw]['awards']['soggy_biscuit'] = [m.id,score]

            if gw > 1:

                # sorted_managers = sorted(league.active_managers, key=lambda x: x.gw_rank_gain, reverse=True)

                pairs = sorted(
                    league.position_change_dict.items(),
                    key=lambda x: (x[1], -api.get_manager(id=x[0]).gw_rank_gain),
                    reverse=False,
                )

                pairs = [
                    (m, delta) for m, delta in pairs if m not in league._skip_awards
                ]

                ### rocketeer

                m = api.get_manager(id=pairs[-1][0])
                delta = pairs[-1][-1]
                score = m.gw_rank_gain
                html_buffer += award_panel(
                    "🚀",
                    "Rocketeer",
                    "Best Rank Gain",
                    f"{delta:+} places",
                    m,
                    colour=award_colour["rocket"],
                    name_class="h2",
                )
                json[str(league.id)][gw]["awards"]["rocket"] = [m.id, score]

                ### down the toilet

                m = api.get_manager(id=pairs[0][0])
                delta = pairs[0][-1]
                score = m.gw_rank_gain
                html_buffer += award_panel(
                    "🚽",
                    "#DownTheToilet",
                    "Worst Rank Loss",
                    f"{delta:+} places",
                    m,
                    colour=award_colour["flushed"],
                    name_class="h3",
                )
                json[str(league.id)][gw]["awards"]["flushed"] = [m.id, score]

            ### BONER

            m = sorted(league.active_managers, key=lambda x: x.bps, reverse=True)[0]
            html_buffer += award_panel(
                "🦴",
                f"Boner",
                "Highest Bonus",
                f"{m.bps} BPS",
                m,
                colour=award_colour["boner"],
                name_class="h2",
            )
            json[str(league.id)][gw]["awards"]["boner"] = [m.id, m.bps]

            ### SMOOTH BRAIN

            m = sorted(
                league.active_managers, key=lambda x: x.bench_points, reverse=True
            )[0]
            html_buffer += award_panel(
                "🧠",
                f"Smooth Brain",
                "Most Bench Points",
                f"{m.bench_points} pts",
                m,
                colour=award_colour["smooth_brain"],
                name_class="h3",
            )
            json[str(league.id)][gw]["awards"]["smooth_brain"] = [m.id, m.bench_points]

            ### CHAIR

            sorted_managers = sorted(
                league.active_managers,
                key=lambda x: x.minutes_per_player,
                reverse=False,
            )
            # m = sorted_managers[0]
            # html_buffer += award_panel('🪑',f'Chair','Least Minutes Played',f"{m.minutes_per_player}'",m,colour=award_colour['chair'],name_class="h2")
            # json[str(league.id)][gw]['awards']['chair'] = [m.id,m.minutes_per_player]

            ### CHAIR

            m = sorted_managers[-1]
            html_buffer += award_panel(
                "👹",
                f"Minutes Monster",
                "Best Avg. Minutes",
                f"{m.minutes_per_player:.1f}'",
                m,
                colour=award_colour["minutes"],
                name_class="h3",
            )
            json[str(league.id)][gw]["awards"]["minutes"] = [m.id, m.minutes_per_player]

            ### ASBO

            sorted_managers = sorted(
                league.active_managers,
                key=lambda x: (x.get_card_count(), -x.minutes),
                reverse=True,
            )
            m = sorted_managers[0]
            html_buffer += award_panel(
                "🥊",
                f"ASBO",
                "Most Carded",
                m.card_emojis,
                m,
                colour=award_colour["asbo"],
                name_class="h2",
            )
            json[str(league.id)][gw]["awards"]["asbo"] = [m.id, m.card_emojis]

        if gw > 1:

            ### FORTUNE TELLER

            sorted_managers = sorted(
                league.active_managers,
                key=lambda x: (x.calculate_transfer_gain(), x._transfer_uniqueness),
                reverse=True,
            )
            m = sorted_managers[0]
            score = m.calculate_transfer_gain()
            html_buffer += award_panel(
                "🔮",
                "Fortune Teller",
                "Best Transfers",
                f"{score:+d} pts",
                m,
                colour=award_colour["fortune"],
                name_class="h2",
            )
            json[str(league.id)][gw]["awards"]["fortune"] = [m.id, score]

            ### CLOWN

            m = sorted_managers[-1]
            score = m.calculate_transfer_gain()
            html_buffer += award_panel(
                "🤡",
                "Clown",
                "Worst Transfers",
                f"{score:+d} pts",
                m,
                colour=award_colour["clown"],
                name_class="h2",
            )
            json[str(league.id)][gw]["awards"]["clown"] = [m.id, score]

            ### NERD AND INNOVATOR (REMOVED)

            # m = sorted(league.active_managers, key=lambda x: x.avg_selection, reverse=True)[0]
            # html_buffer += award_panel('🤓',f'Nerd','Most Template Team',f'{m.avg_selection:.1f}%',m,colour='pale-yellow',name_class="h2")
            # json[str(league.id)][gw]['awards']['nerd'] = [m.id,m.avg_selection]

            # m = sorted(league.active_managers, key=lambda x: x.avg_selection, reverse=False)[0]
            # html_buffer += award_panel('🎓',f'Innovator','Least Template Team',f'{m.avg_selection:.1f}%',m,colour='grey',name_class="h2")
            # json[str(league.id)][gw]['awards']['innovator'] = [m.id,m.avg_selection]

            # most in form team
            # most out of form team

    if gw > 0:
        mout.debugOut(f"create_leaguepage({league})::Template")
        html_buffer += floating_subtitle("League Template")
        html_buffer += league_template(league, gw)

    if awards:
        mout.debugOut(f"create_leaguepage({league})::Differentials")
        html_buffer += floating_subtitle("Killer Differentials")
        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'
        html_buffer += differential_buffer
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    if preseason:
        mout.debugOut(f"create_leaguepage({league})::PreseasonTable")
        html_buffer += floating_subtitle("Last Season")
        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
        html_buffer += preseason_table(league)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    if gw > 1:
        mout.debugOut(f"create_leaguepage({league})::Transfers")
        ids_in, ids_out = league.get_league_transfers(gw)

        html_buffer += floating_subtitle("Popular Moves")

        html_buffer += transfer_table(ids_in, "In", "pale-green")

        html_buffer += transfer_table(ids_out, "Out", "pale-red")

    if not preseason:

        mout.debugOut(f"create_leaguepage({league})::Chips")
        html_buffer += league_chips(league, gw)

        mout.debugOut(f"create_leaguepage({league})::Table")
        html_buffer += floating_subtitle("League Table")

        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

        html_buffer += f'<div class="w3-padding">\n'
        html_buffer += f"<h2>League Table:</h2>\n"
        html_buffer += (
            "<p>Is your team"
            + f's kit the boring default? Design it <a href="https://fantasy.premierleague.com/entry-update">here</a><p>\n'
        )
        html_buffer += f"</div>\n"
        html_buffer += league_table_html(league, gw)

        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    if league.num_managers > 20 and awards:
        subset = []
        subset += [d[0] for d in json[str(league.id)][gw]["awards"].values()]
        subset += json[str(league.id)][gw].get("promotion", [])
    else:
        subset = None

    import sys

    sys.path.insert(1, "go")
    from goleague import create_league_figure, create_league_histogram

    if api._current_gw > 1:
        html_buffer += floating_subtitle("League Graphs")

        if len(league.managers) > 30:
            html_buffer += '<div class="w3-col s12 m12 l12">\n'
            html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
            html_buffer += create_league_histogram(api, league, subset, all_gws=True)
            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

            html_buffer += '<div class="w3-col s12 m12 l12">\n'
            html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
            html_buffer += create_league_histogram(api, league, subset, all_gws=False)
            html_buffer += "</div>\n"
            html_buffer += "</div>\n"

        html_buffer += '<div class="w3-col s12 m12 l12">\n'
        html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
        html_buffer += create_league_figure(api, league, subset)
        html_buffer += "</div>\n"
        html_buffer += "</div>\n"

    style = api.create_team_styles_css()
    navbar = create_navbar(leagues, active=i, colour="black", active_colour="green")
    html_page(
        f'html/{league.name.replace(" ","-")}.html',
        None,
        title=f"{league._icon} {league.name}",
        gw=gw,
        html=html_buffer,
        bar_html=navbar,
        showtitle=True,
        colour=league._colour_str,
        extra_style=style,
        plotly=True,
    )


def league_chips(league, gw):
    """

    Chip | Team | Manager | GW Score | Detail

    """

    global api

    html_buffer = ""

    total_chip_count = 0
    chip_managers = []

    for man in league.managers:
        chip = man.get_event_chip(gw)
        if chip is None:
            continue
        total_chip_count += 1
        chip_managers.append(man)

    if total_chip_count == 0:
        return ""

    html_buffer += floating_subtitle("Chips")

    html_buffer += '<div class="w3-col s12 m12 l12">\n'
    html_buffer += '<div class="w3-panel w3-white shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

    html_buffer += '<table class="w3-table w3-hoverable">\n'
    html_buffer += "<thead>\n"
    html_buffer += "<tr>\n"

    html_buffer += '<th style="text-align:center;">Chip</th>\n'
    html_buffer += "<th>Team</th>\n"
    html_buffer += "<th>Manager</th>\n"
    html_buffer += f'<th style="text-align:center;">GW{gw} Score</th>\n'

    html_buffer += "</tr>\n"
    html_buffer += "</thead>\n"

    html_buffer += "<tbody>\n"

    for man in sorted(
        chip_managers,
        key=lambda x: x.get_event_score(
            gw,
        ),
        reverse=True,
    ):

        chip = man.get_event_chip(gw)

        if chip == "TC":
            color = "amber"
        elif chip.startswith("WC"):
            color = "red"
        elif chip == "BB":
            color = "blue"
        elif chip == "FH":
            color = "green"
        elif chip.startswith("AM"):
            color = "purple"
            chip = "AM"
        else:
            mrich.error("Unsupported chip:", chip)

        html_buffer += f'<td class="w3-{color}" style="text-align:center;">{man.get_event_chip(gw)}</td>\n'

        # team
        html_buffer += f'<td><img class="w3-image" src="{man._kit_path}" alt="Kit Icon" width="22" height="29"> <a href="{man.gui_url}">{man.team_name}</a></td>\n'

        # manager
        html_buffer += f'<td><a href="{man.gui_url}">{man.name}</a>\n'
        if "Toilet" in league.name and man.is_diamond:
            html_buffer += "💎"
        html_buffer += "</td>\n"

        html_buffer += (
            f'<td style="text-align:center;">{man.get_event_score(gw)}</td>\n'
        )

        html_buffer += "</tr>\n"

    html_buffer += "</tbody>\n"
    html_buffer += "</table>\n"

    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    return html_buffer


def transfer_table(ids, title_str, colour_str):

    global api
    html_buffer = ""

    html_buffer += '<div class="w3-col s12 m12 l6">\n'
    html_buffer += f'<div class="w3-panel w3-{colour_str} shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

    html_buffer += '<div class="w3-responsive w3-padding">\n'
    html_buffer += f"<h2>Transferred {title_str}:</h2>\n"
    html_buffer += "</div>\n"
    html_buffer += '<div class="w3-responsive">\n'
    html_buffer += '<table class="w3-table w3-hoverable responsive-text">\n'
    html_buffer += "<thead>\n"
    html_buffer += "<tr>\n"

    html_buffer += "<th>Player</th>\n"
    html_buffer += '<th class="w3-center">#Trans.</th>\n'
    html_buffer += '<th class="w3-center">Form</th>\n'

    now_gw = api._current_gw
    end_gw = min(38, now_gw + 5)
    for i in range(now_gw, end_gw + 1):
        html_buffer += f'<th class="w3-center">GW{i}</th>\n'

    html_buffer += "</tr>\n"
    html_buffer += "</thead>\n"

    html_buffer += "<tbody>\n"

    counter = Counter(ids)

    for i, (id, count) in enumerate(counter.most_common(5)):

        if i == 0 and count == 1:
            return ""

        if count == 1:
            break

        p = Player(None, api, index=api.get_player_index(id))

        html_buffer += "<tr>\n"

        html_buffer += '<td style="vertical-align:middle;">'
        html_buffer += p.kit_name_html
        html_buffer += "</td>\n"

        html_buffer += '<td class="w3-center">'
        html_buffer += f"{count}"
        html_buffer += "</td>\n"

        form = p.form
        style_str = (
            get_style_from_event_score(form).rstrip('"') + ';vertical-align:middle;"'
        )
        html_buffer += f'<td class="w3-center" style={style_str}>{form}</td>\n'

        html_buffer += player_summary_cell_modal(p, now_gw)

        for i in range(now_gw + 1, end_gw + 1):
            exp = p.expected_points(gw=i)
            style_str = (
                get_style_from_event_score(exp).rstrip('"') + ';vertical-align:middle;"'
            )
            if style_str is None:
                html_buffer += f'<td class="w3-center" style="vertical-align:middle;">{p.get_fixture_str(i,short=True,lower_away=True)}</td>\n'
            else:
                html_buffer += f'<td class="w3-center" style={style_str}>{p.get_fixture_str(i,short=True,lower_away=True)} ({exp:.1f})</td>\n'

        html_buffer += "</tr>\n"

    html_buffer += "</tbody>\n"
    html_buffer += "</table>\n"
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    return html_buffer


def preseason_table(league):

    html_buffer = ""
    html_buffer += '<table class="w3-table responsive-text">\n'
    html_buffer += "\t<tr>\n"
    html_buffer += "\t\t<th></th>\n"
    html_buffer += "\t\t<th>Team Name</th>\n"
    html_buffer += "\t\t<th>Manager</th>\n"
    html_buffer += "\t\t<th>Score</th>\n"
    html_buffer += "\t\t<th>Rank</th>\n"
    html_buffer += "\t</tr>\n"

    sorted_managers = sorted(
        league.managers, key=lambda x: x.last_season_score, reverse=True
    )
    for i, m in enumerate(sorted_managers):

        html_buffer += "\t<tr>\n"
        html_buffer += f'\t\t<td style="text-align:right;">{i+1}</td>\n'
        html_buffer += f'\t\t<td><img src="{m._kit_path}" alt="Kit Icon" width="22" height="29"></img>\n'

        html_buffer += f'\t\t<a href="{m.gui_url}">{m.team_name}</a></td>\n'

        if "Tesco Bean Value" in league.name and m.is_diamond:
            html_buffer += f"\t\t<td>{m.name} 💎</td>\n"
        else:
            html_buffer += f"\t\t<td>{m.name}</td>\n"

        if len(m._past_points) < 1:
            html_buffer += f"<td>N/A</td><td>N/A</td>\n"
        else:
            html_buffer += f"<td>{m._past_points[-1]}</td>\n"
            html_buffer += f"<td>{api.big_number_format(m._past_ranks[-1])}</td>\n"

        html_buffer += "\t</tr>\n"

    html_buffer += "</table>\n"

    return html_buffer

    f.write(f"| # | Team Name | Manager | Last Season Score | Last Season Rank |\n")
    f.write(f"| --- | --- | --- | --- | ---: |\n")
    sorted_managers = sorted(
        league.managers, key=lambda x: x.last_season_score, reverse=True
    )
    for i, m in enumerate(sorted_managers):
        if i + 1 == len(sorted_managers):
            f.write(f"| 🥚 ")
        else:
            f.write(f"| {i+1} ")

        f.write(f"| [[{m._kit_path}]]")
        f.write(f" [{m.team_name}]({m.gui_url})")
        f.write(f"| [{m.name}]({m.gui_url}) ")

        if len(m._past_points) < 1:
            f.write(f"| N/A | N/A |\n")
        else:
            f.write(f"| {m._past_points[-1]} ")
            f.write(f"| {m._past_ranks[-1]} ")

        f.write(f"|\n")


def league_table_html(league, gw, awardkey=None, seasontable=False):
    global api
    global json

    html_buffer = ""

    if awardkey == "season":
        print(json[str(league.id)]["season"])

    create_key(json[str(league.id)][gw], "positions")

    show_fix_played = api._live_gw
    show_avg_select = gw == 1
    show_team_value = False
    show_pos_delta = True
    show_tot_score = gw > 1
    show_gw_rank = gw > 1
    show_transfers = gw > 1
    show_gw_score = True
    show_captain = True
    show_transfer_summary = False

    last_gw_position_dict = league.last_gw_position_dict

    if seasontable:
        show_gw_rank = False
        show_gw_score = False
        show_team_value = True
        show_transfers = False
        show_transfer_summary = True
        show_captain = False

    html_buffer += '<div class="w3-responsive">\n'
    html_buffer += '<table class="w3-table w3-hoverable responsive-text">\n'
    html_buffer += "<thead>\n"
    html_buffer += "<tr>\n"

    html_buffer += '<th class="w3-center">#</th>\n'
    html_buffer += "<th>Team Name</th>\n"
    html_buffer += "<th>Manager</th>\n"

    if show_tot_score:
        html_buffer += '<th style="text-align:center;">Score</th>\n'

    html_buffer += f'<th style="text-align:center;">(GW{gw})</th>\n'
    html_buffer += '<th style="text-align:right;">Rank</th>\n'

    if show_gw_rank:
        html_buffer += f'<th style="text-align:right;">(GW{gw})</th>\n'

    if show_captain:
        html_buffer += "<th>Captain</th>\n"

    if show_fix_played:
        html_buffer += '<th style="text-align:center;">Fix.</th>\n'

    if show_avg_select:
        html_buffer += '<th style="text-align:center;">Ownership</th>\n'

    if show_team_value:
        html_buffer += '<th style="text-align:center;">Team Value</th>\n'

    if show_transfers or show_transfer_summary:
        html_buffer += "<th>Trans.</th>\n"

    html_buffer += "</tr>\n"
    html_buffer += "</thead>\n"

    html_buffer += "<tbody>\n"

    sorted_managers = sorted(
        league.managers, key=lambda x: x.total_livescore, reverse=True
    )

    diamond_count = 0
    zombie = None

    for i, m in enumerate(sorted_managers):

        is_last = i + 1 == len(sorted_managers)

        if "Toilet" in league.name and m.is_diamond and m.id != 3902717:
            diamond_count += 1
        elif "Toilet" in league.name and not m.is_diamond and i <= 2 + diamond_count:
            html_buffer += '<tr class="w3-pale-green">\n'
            l = json[str(league.id)][gw].get("promotion", [])
            l.append(m.id)
            json[str(league.id)][gw]["promotion"] = l
        elif "Diamond" in league.name and i >= len(sorted_managers) - 4:
            html_buffer += '<tr class="w3-pale-red">\n'
        elif i == 0:
            html_buffer += '<tr class="w3-pale-yellow">\n'
        else:
            html_buffer += "<tr>\n"

        if is_last:
            pos_str = "🥚"
        else:
            pos_str = f"{i+1}"

        if not show_pos_delta:
            delta = 0
        else:
            now_gw_position = i + 1
            last_gw_position = last_gw_position_dict[m.id]
            delta = last_gw_position - now_gw_position

        if delta != 0:
            if delta < 0:
                color = "red"
            else:
                color = "green"
            html_buffer += (
                f'<td class="w3-center">{pos_str} <span class="w3-text-{color}">'
            )
            html_buffer += f"({delta:+})</span></td>\n"
        else:
            html_buffer += f'<td class="w3-center">{pos_str}</td>\n'

        # team
        html_buffer += f'<td><img class="w3-image" src="{m._kit_path}" alt="Kit Icon" width="22" height="29"> <a href="{m.gui_url}">{m.team_name}</a>'

        if cup_active:
            matches = m.get_cup_matches(league)
            matches = [x for x in matches if x["gw"] == gw]
            if matches:
                match = matches[0]
                if match["winner"] == m.id:
                    html_buffer += " 🏆✅"
                elif match["winner"] is not None:
                    html_buffer += " 🏆❌"

        html_buffer += "</td>\n"

        # manager
        html_buffer += f'<td><a href="{m.gui_url}">{m.name}</a>'
        if "Toilet" in league.name and m.is_diamond:
            html_buffer += " 💎"
        elif m.id == 3902717:
            html_buffer += " 🚫"

        if awardkey is None:
            awardkey = gw

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["king"]:
                html_buffer += " 👑"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["cock"]:
                html_buffer += " 🐓"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["goals"]:
                html_buffer += " ⚽️"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["scientist"]:
                html_buffer += " 🧑‍🔬"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["boner"]:
                html_buffer += " 🦴"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["smooth_brain"]:
                html_buffer += " 🧠"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["chair"]:
                html_buffer += " 🪑"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["asbo"]:
                html_buffer += " 🥊"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["fortune"]:
                html_buffer += " 🔮"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["clown"]:
                html_buffer += " 🤡"
        except:
            pass

        try:
            if m.id in json[str(league.id)][awardkey]["awards"]["innovator"]:
                html_buffer += " 🎓"
        except:
            pass

        html_buffer += "</td>\n"

        if show_tot_score:
            html_buffer += (
                f'<td style="text-align:center;">{m.total_livescore:,}</td>\n'
            )

        if m._bb_week == gw:
            html_buffer += f'<td class="w3-blue" style="text-align:center;"><strong>BB</strong> {m.livescore}</td>\n'
        elif m._fh_week == gw:
            html_buffer += f'<td class="w3-green" style="text-align:center;"><strong>FH</strong> {m.livescore}</td>\n'
        elif gw in [m._am1_week, m._am2_week, m._am3_week]:
            html_buffer += f'<td class="w3-purple" style="text-align:center;"><strong>AM</strong> {m.livescore}</td>\n'
        else:
            html_buffer += f'<td style="text-align:center;">{m.livescore}</td>\n'

        html_buffer += f'<td style="text-align:right;">{api.big_number_format(m.overall_rank)}</td>\n'

        if show_gw_rank:
            html_buffer += f'<td style="text-align:right;">{api.big_number_format(m.gw_rank)}</td>\n'

        if show_captain:
            if m._tc_week == gw:
                html_buffer += f'<td class="w3-amber"><strong>TC</strong> {m.captain} ({3*m.captain_points})'
                html_buffer += "</td>\n"
            else:
                html_buffer += f"<td>{m.captain} ({2*m.captain_points})"
                html_buffer += "</td>\n"

        if show_fix_played:
            html_buffer += f'<td style="text-align:center;">{m.fixtures_played}/{m.total_fixtures}</td>\n'

        if show_avg_select:
            html_buffer += (
                f'<td style="text-align:center;">{m.avg_selection:.1f}%</td>\n'
            )

        if show_team_value:
            html_buffer += f'<td style="text-align:center;">£{m.team_value:.1f}</td>\n'

        if show_transfers:
            if m.is_dead:
                if zombie is None:
                    json[str(league.id)][awardkey]["awards"]["zombie"] = (m.id, i + 1)
                    zombie = m
                    print("zombie", awardkey, (m.id, i + 1))
                html_buffer += (
                    f'<td class="w3-black" style="text-align:center;">💀</td>\n'
                )
            else:
                transfer_str = (
                    m.get_transfer_str(short=True).rstrip().replace("\n", "<br>")
                )
                if "**WC**" in transfer_str:
                    transfer_str = transfer_str.replace("**WC**", "<strong>WC</strong>")
                    html_buffer += f'<td class="w3-red" style="text-align:center;">{transfer_str}</td>\n'
                else:
                    html_buffer += f'<td style="text-align:center;">{transfer_str}'
                    hits = int(m.get_transfer_cost(gw) / 4)
                    if hits > 0:
                        for i in range(hits):
                            html_buffer += (
                                f' <span class="w3-tag"><strong>H</strong></span>'
                            )
                    html_buffer += "</td>\n"
        elif show_transfer_summary:
            html_buffer += f'<td style="text-align:center;">'
            html_buffer += f'{m.num_nonwc_transfers} <span class="w3-tag">'
            if n_hits := m.num_hits:
                html_buffer += f"<strong>{n_hits} Hs</strong>"
            html_buffer += f"</span>"
            html_buffer += "</td>\n"

        html_buffer += f"</tr>\n"

        json[str(league.id)][gw]["positions"][m.id] = i

    html_buffer += "</tbody>\n"
    html_buffer += "</table>\n"
    html_buffer += "</div>\n"

    global _league_table_html
    _league_table_html[league.id] = html_buffer

    return html_buffer


def league_template(league, gw):

    html_buffer = ""

    html_buffer += position_template(league, league.captains, "Captain", gw)
    html_buffer += position_template(
        league, league.starting_goalkeepers, "Goalkeeper", gw
    )
    html_buffer += position_template(league, league.starting_defenders, "Defence", gw)
    html_buffer += position_template(
        league, league.starting_midfielders, "Midfield", gw
    )
    html_buffer += position_template(league, league.starting_forwards, "Forwards", gw)

    html_buffer += ownership_template(league, "Effective Ownership", gw)

    html_buffer += f"</table>\n"

    return html_buffer


def ownership_template(league, title, gw):

    global json

    ### BUILD THE DATA

    data = []
    for team in api.teams:

        mult_attacker = 0
        mult_defender = 0
        sum_attacker = 0
        sum_defender = 0

        started = None

        for p in [p for p in league.all_players if p.shortteam == team.shortname]:
            if p.position_id > 2:
                mult_attacker += p.multiplier
                if p.multiplier > 0:
                    sum_attacker += p.get_event_score(not_playing_is_none=False)
            else:
                mult_defender += p.multiplier
                if p.multiplier > 0:
                    sum_defender += p.get_event_score(not_playing_is_none=False)

            if started is None:
                started = p.has_fixture_started

        if mult_attacker > 0:
            d = dict(
                shortteam=team.shortname,
                position="Attack",
                multiplier=mult_attacker / league.num_managers,
                kit_path=team._kit_path,
                points=sum_attacker / mult_attacker,
                started=started,
            )
            data.append(d)

        if mult_defender > 0:
            d = dict(
                shortteam=team.shortname,
                position="Defence",
                multiplier=mult_defender / league.num_managers,
                kit_path=team._kit_path,
                points=sum_defender / mult_defender,
                started=started,
            )
            data.append(d)

    data = sorted(data, key=lambda x: x["multiplier"], reverse=True)

    ### STORE THE DATA
    create_key(json[str(league.id)][gw], "template")
    create_key(json[str(league.id)][gw]["template"], "ownership")
    json[str(league.id)][gw]["template"]["ownership"] = data

    ### DO THE HTML
    html_buffer = ""
    html_buffer += '<div class="w3-col s12 m6 l4">\n'

    html_buffer += f'<div class="w3-panel w3-white w3-center shadow89" style="padding:0px;padding-top:0px;padding-bottom:4px;">\n'
    html_buffer += f"<h2>{title}</h2>\n"

    html_buffer += f'<table class="w3-table w3-hoverable responsive-text">\n'

    ranks = [
        "1<sup>st</sup>",
        "2<sup>nd</sup>",
        "3<sup>rd</sup>",
        "4<sup>th</sup>",
        "5<sup>th</sup>",
        "6<sup>th</sup>",
        "7<sup>th</sup>",
        "8<sup>th</sup>",
        "9<sup>th</sup>",
        "10<sup>th</sup>",
    ]

    for i, d in enumerate(data[:10]):
        html_buffer += f'<tr style="vertical-align:middle;">\n'

        html_buffer += f'<td style="vertical-align:middle;text-align:right;"><b>{ranks[i]}</b></td>'

        html_buffer += f'<td style="vertical-align:middle;">'
        html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/ToiletFPL/blob/main/{d["kit_path"]}?raw=true" alt="Kit Icon" width="22" height="29">'

        html_buffer += f' {d["shortteam"]} \n'
        html_buffer += f'{d["position"]}</td>\n'
        html_buffer += f'<td style="vertical-align:middle;text-align:right;">{d["multiplier"]:.0%}   </td>\n'

        html_buffer += f'<td style="text-align:center;">\n'

        if d["started"]:
            style_str = (
                get_style_from_event_score(d["points"]).rstrip('"')
                + ';text-align:right;vertical-align:middle;"'
            )
            html_buffer += (
                f'<span class="w3-tag" style={style_str}>{d["points"]:.1f}pts</span>\n'
            )

        html_buffer += f"</td>\n"

        html_buffer += f"</tr>\n"

    html_buffer += f"</table>\n"
    html_buffer += f"</div>\n"
    html_buffer += f"</div>\n"

    return html_buffer


def position_template(league, players, pos_str, gw):
    global json

    html_buffer = ""

    html_buffer += '<div class="w3-col s12 m6 l4">\n'

    create_key(json[str(league.id)][gw], "template")
    create_key(json[str(league.id)][gw]["template"], pos_str.lower())

    ranks = [
        "1<sup>st</sup>",
        "2<sup>nd</sup>",
        "3<sup>rd</sup>",
        "4<sup>th</sup>",
        "5<sup>th</sup>",
    ]

    lst = [p.full_name for p in players]
    data = Counter(lst)
    archive = []
    for i, (name, count) in enumerate(data.most_common()[0:5]):

        if i == 0:
            p = Player(name, api)
            score = p.get_event_score()

            html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-top:0px;padding-bottom:4px;">\n'
            html_buffer += f'<div class="w3-center w3-{p.shortteam.lower()}-inv w3-{p.shortteam.lower()}-border-inv" style="padding:0px;padding-bottom:0px;">\n'

            html_buffer += f"<h2>{pos_str}</h2>\n"

            html_buffer += f'<img class="w3-image hide-if-narrow" style="width:30%" src="{p._photo_url}?raw=true"></img>\n'

            html_buffer += f"</div>\n"

            html_buffer += '<div class="w3-white">\n'

            html_buffer += f'<table class="w3-table w3-hoverable responsive-text">\n'

        html_buffer += f'<tr style="vertical-align:middle;">\n'
        if count > 1:
            p = Player(name, api)
            score = p.get_event_score()
            flag_str = ""
            if p.is_yellow_flagged:
                flag_str = f"⚠️ "
            elif p.is_yellow_flagged:
                flag_str = f"⛔️ "
            html_buffer += f'<td style="vertical-align:middle;text-align:left;">\n'
            html_buffer += f"<b>{ranks[i]}</b>\n"
            html_buffer += f"</td>\n"
            html_buffer += f'<td style="vertical-align:middle;text-align:right;">\n'
            html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/ToiletFPL/blob/main/{p.kit_path}?raw=true" alt="Kit Icon" width="22" height="29">'
            html_buffer += f"</td>\n"
            html_buffer += f'<td style="vertical-align:middle;">\n'
            html_buffer += f'<a href="{p._gui_url}">{p.name}</a>\n'
            html_buffer += f"</td>\n"
            html_buffer += f'<td style="vertical-align:middle;text-align:right;">\n'
            html_buffer += f"{count/league.num_managers:.1%}\n"
            html_buffer += f"</td>\n"
            if score is not None:
                style_str = (
                    get_style_from_event_score(score).rstrip('"')
                    + ';text-align:right;vertical-align:middle;"'
                )
                html_buffer += f'<td style="text-align:center;">\n'
                html_buffer += (
                    f'<span class="w3-tag" style={style_str}>{score}pts</span>\n'
                )
                html_buffer += f"</td>\n"
            else:
                html_buffer += f"<td>\n"
                html_buffer += f"</td>\n"
            archive.append([p.id, count / league.num_managers, score])
        else:
            break
        html_buffer += f"</tr>\n"
    json[str(league.id)][gw]["template"][pos_str.lower()] = archive

    html_buffer += f"</table>\n"

    html_buffer += f"</div>\n"
    html_buffer += f"</div>\n"
    html_buffer += f"</div>\n"

    return html_buffer


def effective_points_gained(player, n):
    # return player.multiplier*player.get_event_score(not_playing_is_none=False)/player.league_count
    # return player.get_event_score(not_playing_is_none=False) * (player.multiplier - player.league_count/n)
    return player.get_event_score(not_playing_is_none=False) * (
        player.multiplier - player.league_multiplier_count / n
    )


def league_differentials(league, gw):
    global json

    html_buffer = ""

    players = league.get_starting_players(unique=False, active_only=True)

    n = league.num_managers

    sorted_players = sorted(
        players,
        key=lambda p: (effective_points_gained(p, n), -p._parent_manager.avg_selection),
        reverse=True,
    )

    html_buffer += f'<table class="w3-table responsive-text">\n'

    archive = []
    ids_so_far = []

    for p in sorted_players:

        if len(ids_so_far) > 4:
            break

        if p.id not in ids_so_far:

            pts_gain = effective_points_gained(p, n)

            # print(p.name, pts_gain, p.league_count, p.league_multiplier_count, p._parent_manager)

            ids_so_far.append(p.id)

            m = p._parent_manager
            score, summary = p.get_event_score(
                summary=True, not_playing_is_none=False, team_line=False
            )
            summary = summary.replace("\n", "<br>")

            html_buffer += f"<tr>\n"
            html_buffer += f'<td style="vertical-align:middle;mid-width:25px;">\n'
            html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/ToiletFPL/blob/main/{p.kit_path}?raw=true" alt="Kit Icon" width="22" height="29">'
            html_buffer += f"</td>\n"
            html_buffer += f'<td style="vertical-align:middle;">\n'
            html_buffer += f'<a href="{p._gui_url}">{p.name}</a>\n'

            if p.is_yellow_flagged:
                html_buffer += f"⚠️ "
            elif p.is_yellow_flagged:
                html_buffer += f"⛔️ "
            if p.multiplier == 3:
                html_buffer += f" (TC) "
            elif p.multiplier == 2:
                html_buffer += f" (C) "

            html_buffer += f"</td>\n"

            html_buffer += f'<td style="vertical-align:middle;">\n'
            style_str = (
                get_style_from_event_score(pts_gain).rstrip('"')
                + ';text-align:right;vertical-align:middle;"'
            )
            html_buffer += (
                f'<span class="w3-tag" style={style_str}>{pts_gain:+.1f}pts</span>\n'
            )
            html_buffer += f"</td>\n"

            html_buffer += f'<td style="vertical-align:middle;mid-width:25px;">\n'
            html_buffer += f'<img class="w3-image" src="{m._kit_path}" alt="Kit Icon" width="22" height="29">'
            html_buffer += f"</td>\n"
            html_buffer += f'<td style="vertical-align:middle;">\n'
            html_buffer += f'<a href="{m.gui_url}">{m.team_name}</a>\n'
            html_buffer += f'<br><a href="{m.gui_url}">{m.name}</a>\n'
            html_buffer += f"</td>\n"
            html_buffer += f'<td style="vertical-align:middle;">\n'
            style_str = (
                get_style_from_event_score(score).rstrip('"') + ';text-align:right"'
            )
            html_buffer += f'<span class="w3-tag" style={style_str}>{p.multiplier*score}pts</span>\n'
            html_buffer += f": {summary}"
            html_buffer += f"</td>\n"
            html_buffer += f"</tr>\n"
            archive.append([p.id, m.id, p.is_captain, p.multiplier * score, pts_gain])

    html_buffer += f"</table>\n"

    json[str(league.id)][gw]["differentials"] = archive

    # print(archive)

    return html_buffer


def generate_summary_template(api, league):
    mout.debugOut(f"generate_summary_template({league.name})")

    # GW string
    gw = api._current_gw
    gw_str = "GW"
    if gw in api._special_gws.keys():
        gw_str = api._special_gws[gw]
    gw_str = f"{gw_str}{gw}"

    data = json[str(league.id)][gw]["awards"]

    # aggregate by manager
    by_manager = {}
    for k, v in data.items():
        m_id = v[0]
        score = v[1]
        if m_id not in by_manager:
            by_manager[m_id] = []
        by_manager[m_id].append((k, score))

    with open("summary_template.txt", "wt") as f:

        if cup_active:
            round_size = pow(2, 38 - gw + 1)

            if round_size > 8:
                round_str = f"round of {round_size}"
            elif round_size == 2:
                round_str = f"Final"
            elif round_size == 4:
                round_str = f"Semi-Finals"
            elif round_size == 8:
                round_str = f"Quarter-Finals"

            f.write(f"{gw_str} Awards and Cup {round_str}\n\n")
            f.write(f"Tesco Bean Value Toilet League \n\n")
        else:
            f.write(f"{gw_str} Awards \n\n")

        for m_id, awards in by_manager.items():

            award_strings = []
            for award_name, score in awards:
                award_strings.append(f"{award_flavourtext[award_name]}")
                # award_strings.append(f'{award_flavourtext[award_name]} {score}')

            m = api.get_manager(id=m_id)

            f.write(f"{', '.join(award_strings)} {m.name}\n")

        # cup summary

        try:

            if cup_active:

                f.write(f"\nTesco Value Cup\n\n")

                f.write(
                    f"{json[str(league.id)]['cup'][gw]['n_diamond_winners']}💎 managers progress in the cup\n"
                )
                f.write(
                    f"{json[str(league.id)]['cup'][gw]['n_diamond_losers']}💎 managers crash out of the cup\n"
                )

                m1, r, m2 = json[str(league.id)]["cup"][gw]["highest_loser_rank"]
                m1, m2 = api.get_manager(id=m1), api.get_manager(id=m2)
                f.write(f"Highest ranked loser: {m1.name} (vs {m2.name})\n")

                m1, r, m2 = json[str(league.id)]["cup"][gw]["lowest_winner_rank"]
                m1 = api.get_manager(id=m1)
                m2 = api.get_manager(id=m2) if m2 else None
                f.write(
                    f"Lowest ranked winner: {m1.name} (vs {m2.name if m2 else 'BYE'})\n"
                )

                m1, r, m2 = json[str(league.id)]["cup"][gw]["lowest_loser_rank"]
                m1, m2 = api.get_manager(id=m1), api.get_manager(id=m2)
                f.write(f"Lowest ranked loser: {m1.name} (vs {m2.name})\n")

                m1, r, m2 = json[str(league.id)]["cup"][gw]["highest_winner_rank"]
                m1 = api.get_manager(id=m1)
                m2 = api.get_manager(id=m2) if m2 else None
                f.write(
                    f"Highest ranked winner: {m1.name} (vs {m2.name if m2 else 'BYE'})\n"
                )

                m1, s, m2 = json[str(league.id)]["cup"][gw]["highest_loser_score"]
                m1, m2 = api.get_manager(id=m1), api.get_manager(id=m2)
                f.write(
                    f"Highest scoring loser: {m1.name} {s} (vs {m2.name} w/ {m2.livescore})\n"
                )

                m1, s, m2 = json[str(league.id)]["cup"][gw]["lowest_winner_score"]
                m1 = api.get_manager(id=m1)
                m2 = api.get_manager(id=m2) if m2 else None
                f.write(
                    f"Lowest scoring winner: {m1.name} {s} (vs {m2.name if m2 else 'BYE'} w/ {m2.name if m2 else 'BYE'})\n"
                )

                m1, s, m2 = json[str(league.id)]["cup"][gw]["lowest_loser_score"]
                m1, m2 = api.get_manager(id=m1), api.get_manager(id=m2)
                f.write(
                    f"Lowest scoring loser: {m1.name} {s} (vs {m2.name} w/ {m2.livescore})\n"
                )

                m1, s, m2 = json[str(league.id)]["cup"][gw]["highest_winner_score"]
                m1 = api.get_manager(id=m1)
                m2 = api.get_manager(id=m2) if m2 else None
                f.write(
                    f"Highest scoring winner: {m1.name} {s} (vs {m2.name if m2 else 'BYE'} w/ {m2.name if m2 else 'BYE'})\n"
                )

                f.write(f"\n({api._current_gw} {api._live_gw})\n")

        except Exception as e:
            mout.error("Something went wrong with the cup summary")
            mout.error(str(e))

            # #managers
            # #diamond managers
            # highest and lowest ranked remaining in the cup

            # raise NotImplementedError


def push_changes():
    mout.debugOut(f"push_changes()")
    import os

    os.system(r"rm -v html/*\@*")
    # num_changes = int(os.popen("git status | grep 'modified:' | grep -v '.pyc' | wc -l").read())
    num_changes = 1
    if num_changes > 0:
        # os.system(f'cd {path}; git add *.md; git commit -m "auto-generated {timestamp}"; git push; cd {path.replace(".wiki","")}')
        os.system(
            f'rm kits/*.webp; git add *.py go/*.html go/*.py graphs/*.png index.html html/*.html *.json kits/*.png; git commit -m "auto-generated {timestamp}"; git push'
        )
        os.system(
            f"terminal-notifier -title 'ToiletFPL' -message 'Completed Wiki Update' -open 'index.html'"
        )
        exit(code=69)
    else:
        os.system(
            f"terminal-notifier -title 'ToiletFPL' -message 'No changes pushed' -open 'index.html'"
        )
        exit(code=70)


def pull_changes():
    mout.debugOut(f"pull_changes()")
    import os

    os.system(f"git pull")


def create_key(json, key):
    if key not in json.keys():
        json[key] = {}


def load_json():
    mout.debug("load_json()")
    from os.path import exists

    if exists(JSON_PATH):
        f = open(JSON_PATH, "rt")
        return js.load(f)
    else:
        return {}


def dump_json(data):
    mout.debug("dump_json()")

    new_dict = {}

    for pair in data.items():
        if pair[0] not in new_dict.keys():
            new_dict[pair[0]] = pair[1]

    f = open(JSON_PATH, "wt")
    js.dump(new_dict, f, indent="\t")


if __name__ == "__main__":
    main()

"""

	Issues:

	- Bench points incorrect
	- Differentials not including autosubs?

	To-Do's
	
	- Can there be an offline w3.css?

	* Use gitpython to handle pushing changes and catching errors

	* Get player image for template & captain stats

	GW: 	0000|111111111111111111111111111111111111111|22222222222222
	Live: 	FFFFFFFFFFFFFFFF|TTTTTTTTTTTTTTT|FFFFFFFFFFFFFFFFFFFFFFFFFF
				^ Deadline
							^ Games Begin
											^ Games End
														^ Next Deadline

"""
