#!/usr/bin/env python3

import pytz
from league import League
import api as fpl_api
import plot
from collections import Counter
import mout
from player import Player
from manager import Manager
import json as js
from web import html_page, player_summary_cell_modal, get_style_from_event_score, md2html, get_player_history_table, get_style_from_minutes_played, get_style_from_expected_return, get_style_from_bonus
from squad import Squad
import time
from pprint import pprint

# https://stackoverflow.com/questions/60598837/html-to-image-using-python

from datetime import datetime
timestamp = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

path = '../FPL_GUI.wiki'

run_push_changes = True
test = True
offline = False

create_launchd_plist = False
force_generate_kits = False

scrape_kits = False
fetch_latest = True
force_plot = False
force_go_graphs = True

force = False
halfway_awards = False
season_awards = False
cup_active = False

wc1_cutoff = 19

JSON_PATH = "data_wiki_2324.json"

import sys
if len(sys.argv) > 1 and sys.argv[1] == '-daemon':
	create_launchd_plist = True
elif len(sys.argv) > 1 and sys.argv[1] == '-f':
	force = True

# 22/23
league_codes = [663873,910674,937886,1020381,696154]
league_colours = ['aqua','brown','green','red','purple']
league_colours = ['aqua','dark-grey','pale-green','pale-red','dark-grey']
league_shortnames = ['Diamond','Toilet','GU','RU','Dinner']
league_icons = ["💎","🚽","🦌","📚","🍝"]

# 23/24
league_codes = [146330,121011,114707]
league_icons = ["💎","🚽","🍝"]
league_shortnames = ['Diamond','Toilet','Dinner']
league_colours = ['aqua','dark-grey','dark-grey']

award_flavourtext = dict(
	king="👑 King",
	cock="🐓 Cock",
	goals="⚽️ Massive Goal FC",
	boner="🦴 Boner",
	scientist="🧑‍🔬 Scientist",
	smooth_brain="🧠 Smooth Brain",
	chair="🪑 Chair",
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
	tc_best='Best Triple Captain',
	tc_worst='Worst Triple Captain',
	bb_best='Best Bench Boost',
	bb_worst='Worst Bench Boost',
	fh_best='Best Free Hit',
	fh_worst='Worst Free Hit'
)
award_unittext = dict(
	king="points",
	cock="points",
	goals="goals",
	boner="points",
	scientist="points",
	smooth_brain="points on the bench",
	chair="'",
	asbo="cards",
	nerd="%",
	innovator="%",
	rocket="%",
	flushed="%",
	fortune="points gained",
	clown="points lost",
	hot_stuff="points overperformed",
	soggy_biscuit="points underperformed",
)

award_colour = dict(king="amber",
	cock="red",
	goals="indigo",
	scientist="green",
	boner="grey",
	smooth_brain="pale-red",
	chair="light-blue",
	asbo="yellow",
	fortune="purple",
	clown="pink",
	nerd="pale-yellow",
	innovator="grey",
	oligarch="black",
	iceman="aqua",
	peasant='brown',
	glow_up='pale-yellow',
	has_been='grey',
	kneejerker='deep-orange',
	wc1_best="red",
	wc1_worst="red",
	wc2_best="red",
	wc2_worst="red",
	tc_best='yellow',
	tc_worst='yellow',
	bb_best='blue',
	bb_worst='blue',
	fh_best='green',
	fh_worst='green',
	hot_stuff='orange',
	soggy_biscuit='teal',
	rocket='lime',
	flushed='brown',
)


_league_table_html = {}

brk = '</p><p>'

league_halfway_text = {663873:f"The RBS Diamond Invitational has proved to be a wild ride so far, in which our elite members saw ups and downs; triumphs and tragedies; hauls and blanks. This special festive summary, will recount some of the notable events, and award some shiny new limited-edition awards to a lucky few recipients.{brk}<a href=\"https://mwinokan.github.io/FPL_GUI/html/man_1731530.html\">Ed Lees</a> saw himself off to a strong start with some clever picks in GW1, and a daring triple captain on <a href=\"https://mwinokan.github.io/FPL_GUI/html/player_318.html\">Erling Haaland</a> in GW2 (he did only net five points but hey it's something!). Personally, the most memorable part of Ed's FPL so far was transferring out Haaland for <a href=\"https://mwinokan.github.io/FPL_GUI/html/player_80.html\">Toney</a> in GW5 in a combined move that saw him lose 19 points. In fact, most weeks had Ed not made any transfers he would have been better off, and this is reflected in his Christmas Clown award for having the worst total transfer gain in the league.{brk}Following Ed's demise, GW6 turned out to be a real turning point where managers <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_1153277.html\">Thomas Allan</a> and <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_3106633.html\">Rob Sutton</a> would escape the pack and prove exceptionally hard to chase as they sit in second and first place respectively. Rob's trophy cabinet of course contains his Christmas King award but there's barely any room as he averaged 1.5 awards every week, totalling 24 (with only one actually bad one with his GW4 clown!) Rob's consistent differential power moves were not always an instant success (except when he brought in <a href=\"https://mwinokan.github.io/FPL_GUI/html/player_428.html\">Son</a> for his 19-pointer before promptly wildcarding him out) but his faith in <a href=\"https://mwinokan.github.io/FPL_GUI/html/player_261.html\">Maddison</a>, <a href=\"https://mwinokan.github.io/FPL_GUI/html/player_160.html\">Zaha</a>, <a href=\"https://mwinokan.github.io/FPL_GUI/html/player_80.html\">Toney</a>, and <a href=\"https://mwinokan.github.io/FPL_GUI/html/player_283.html\">Salah</a> particularly rewarded him throughout the season so far. Rob's Take the Plange now sit comfortably at 44k worldwide. Will Rob find himself topping the diamond league at the end of GW38?{brk}Thomas Allan' season does seem to look a bit like Rob's with only a few missteps. An impressive GW8 wildcard brought about a +95% improvement in overall rank within five gameweeks, and a tactical GW12 free hit helped cement a solid top 100k rank and the Christmas Fortune Teller award with an impressive +62 point total for his transfers up to the world cup.{brk}Going further down the table my team <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_780664.html\">Loyd's Groß Men</a> sits in third place after a relatively quiet start, and a decent GW12 wildcard that saw my boys climb a few ranks and a Robertson 9-pointer sat me nicely in the top 650k OR, hopefully onwards and upwards.{brk}As we approach mid-table the points totals all get a bit more compressed, <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_123660.html\">Horatio Turner</a> and <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_1636178.html\">Tanya Fozzard</a> sit in fourth and fifth place. While their ranks are quite similar the journeys these two managers have been on are wildly different. Tanya's 'Mikel ArTanya' reached a gameweek rank height of 44k in GW5 with a massive 97 points, while Horatio's gameweek ranks have been more modest, but consistent. What impresses me most, however, is that Tanya has managed to achieve such success with only ten non-wildcard transfers, earning her the first Iceman award. Well done.{brk}Before we get to the relegation battle, <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_2778113.html\">Matthew Wiggins</a>' escape from the bottom has to be commended. In GW6 he sat dead last, trailing the global average by 17 points. Matthew's improvement since that GW6 wildcard has been remarkable, however, and a fantastic GW16 bench boost confirmed his escape from relegation (at least for now). Matthew has won the Glow-Up award for his improvement since GW8.{brk}Now we turn to the relegation battle. Some managers like <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_1731530.html\">Ed</a> and <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_1737071.html\">Joe Pashley</a> only narrowly ended up down here with a couple unlucky results in recent gameweeks. Joe's season was off to a bad start with a GW2 wildcard that lost him 20 points. Nevertheless, his rank did climb as he won his own 'Massive Goal FC' award four times, before taking a bit of a plunge with two bad gameweeks in 15 and 16.{brk}Second to last is <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_5279233.html\">Joseph Conlon</a>, who hasn't made a transfer since GW7. That's probably how he ended up with his eight Chair awards. We've seen that big comebacks are possible so please come back, Joe...{brk}And finally, the man we've all been waiting to discuss is of course <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_1105564.html\">Ethan Barker</a>. Ethan's journey can only be described as a Shakespearean tragedy, and this man must have nerves of steel to not have done an Elon and just perma-banned all of us. His trophy cabinet contains six cocks and four clowns, and unfortunately, the Christmas awards don't look any better with the Christmas Cock, Kneejerker, Peasant, and Has-Been awards.{brk}What a fun season it has been so far with shake-ups and drama. I can't wait to see what GW17 and beyond have in store for us. Will Ethan, Ed, and the Joe's be relegated? Will anyone catch Rob and Tom?",910674:f"Now we turn to the Tesco Bean Value Toilet League which boasts over 60 active managers competing for glory, awards, and of course promotion to the Diamond League. With such a large pool of players each gameweek the awards have been exciting and varied, with managers from all over the table adding to their trophy cabinets. The Christmas awards are no exception.{brk}In first place sits <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_3106633.html\">Rob Sutton</a> on 965 points, earning him the Christmas King award in both leagues. Our Christmas Cock and egg-holder in 75th place in the league is <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_9680336.html\">Yasir Arafat</a> who did only join in GW5, but this does not protect him from the dreaded cock. Our fortune teller is <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_4237714.html\">Andrew Toon</a> who managed to gain an astounding 109 points through his net transfers so far. The clown award goes to <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_7545553.html\">Priam Ghatak</a> who lost a net 20 points to transfers.{brk}All the following awards are new for Christmas. The Kneejerker and Iceman awards relate to the total number of transfers made so far won by <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_3677532.html\">Jacob Clipsham</a> and <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_5250876.html\">Aldo Ventresca</a>, respectively. Team value, although not as important as at the start of the season, is still an interesting gauge of a manager's wisdom, and <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_587733.html\">Jonah Varney</a> (depicted as Roman Abramovich above) takes the Oligarch award with an astounding £104.1M total squad value. <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_4376362.html\">Sam Watkins</a> will have rather less money to spend on their free world cup transfers with £98.4M and the Peasant award. Our final two awards split the season so far into two 8 GW chunks, and look at who's improved the most - <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_71985.html\">Ben Pelling</a> with his Glow-Up - and the least - <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_4542423.html\">Reece Smith</a> as our Has-Been.{brk}Now we turn to those with the prospect of promotion tantalisingly in sight. Currently, <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_1629225.html\">Kieran Sabine</a>, <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_3754813.html\">Kajan Kugananthajothy</a>, <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_105722.html\">Owen Wilmot</a>, and <a href=\"https://mwinokan.github.io/FPL_GUI/html/man_6441720.html\">Sam Collins</a> stand to make history. Nevertheless, over half the season still remains to be played and make shake-ups are undubitably still in store. I hope you have enjoyed the season so far, and look forward to all the gossip to come."}
league_season_text = {663873:f"PLACEHOLDER DIAMOND SEASON REVIEW",910674:f"PLACEHOLDER TOILET SEASON REVIEW"}

watchlist = [
			]

squad = None
preseason = False

risers = []
fallers = []

completed_playerpages = []

mout.showDebug()

api = None
json = {}

def main():
	mout.debugOut("main()")
	import os
	if offline:
		os.system("terminal-notifier -title 'FPL_GUI' -message 'Started Wiki Update [OFFLINE]' -open 'https://mwinokan.github.io/FPL_GUI/index.html'")
	else:
		os.system("terminal-notifier -title 'FPL_GUI' -message 'Started Wiki Update' -open 'https://mwinokan.github.io/FPL_GUI/index.html'")

	if create_launchd_plist:
		# launchd_plist(interval=300)
		# launchd_plist(interval=600)
		launchd_plist(interval=3600)
		# launchd_plist(interval=14400)
		exit()

	if fetch_latest:
		pull_changes()

	global api
	api = fpl_api.FPL_API(offline=offline,quick=False,force_generate_kits=force_generate_kits,write_offline_data=True)

	global preseason
	preseason = api._current_gw < 1

	global squad
	squad = Squad()
	for name in watchlist:
		squad.add_player(Player(name,api))

	# api._force_generate_kits = not api._live_gw
	api._skip_kits = False

	clear_logs()

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
	for icon,code,colour,shortname in zip(league_icons,league_codes,league_colours,league_shortnames):
		# if code == 910674:
		# 	leagues.append(League(code,api,extra=[
		# 		[3106633,'Rob','Sutton','Take the Plange*'],
		# 		[2778113,'Matthew','Wiggins','Makin Emile Of It FC*'],
		# 		# [5977880,'Magnus','Carlsen','KFUM Tjuvholmen**']
		# 		]))
		# elif code == 696154:
		# 	leagues.append(League(code,api,extra=extra_managers))
		# else:
		try:
			leagues.append(League(code,api))
			leagues[-1]._icon = icon
			leagues[-1]._shortname = shortname
			leagues[-1]._colour_str = colour
		except fpl_api.Request404:
			mout.error(f'Could not init League({code},{shortname})')

	create_comparison_page(api,leagues)

	navbar = create_navbar(leagues)

	create_homepage(navbar)

	# get_manager_json_positions(api,leagues)
	
	if api._current_gw > 28:
		create_cup_page(api,leagues[1],leagues)

	# leagues[0].create_points_graph()
	# leagues[-1].create_points_graph()

	for i,l in enumerate(leagues):
		create_leaguepage(l,leagues,i)
		# exit()
	# exit()
	
	create_teampage(api,leagues)

	global halfway_awards
	if api._current_gw == 19 and not api._live_gw:
		halfway_awards = True
	if halfway_awards:
		create_christmaspage(leagues)
		# api.finish()
		# exit()

	# global season_awards
	# if api._current_gw == 38 and not api._live_gw:
	# 	season_awards = True
	if season_awards:
		create_seasonpage(leagues)
		# api.finish()
		# exit()

	json['timestamp'] = timestamp

	dump_json(json)
	json = load_json()

	get_manager_json_awards(api,leagues)
	# get_manager_json_positions(api,leagues)

	count = 0
	mout.debugOut("main()::ManagerPages")
	mout.hideDebug()
	maximum = len(api._managers)
	plot = force_plot or not api._live_gw
	for i,m in enumerate(api._managers.values()):
		mout.progress(i,maximum)
		if api._current_gw > 1:
			m.create_rank_graph(plot=plot,show=False)
			m.create_points_graph(plot=plot,show=False)
		# m.create_leaguepos_graph(plot=plot,show=False)
		create_managerpage(api, m, leagues)
	mout.progress(maximum,maximum)
	mout.showDebug()

	count = 0
	mout.debugOut("main()::PlayerPages")
	mout.hideDebug()
	maximum = len(api._loaded_players)
	for pid in api._loaded_players:
		mout.progress(count,maximum,append=f' {count}/{maximum}')
		pid = int(pid)
		create_playerpage(api,Player(None,index=api.get_player_index(pid),api=api),leagues)
		# if count > 10:
		# 	exit()	
		count += 1
	mout.progress(maximum,maximum)
	mout.showDebug()
	
	# if api._current_gw > 0:
	create_assetpage(leagues)

	# mout.varOut("#requests=",len(api._request_log))

	# # sorted_managers = sorted(league.managers, key=lambda x: x.livescore, reverse=True)
	# reqs = [x for x in api._request_log]
	# data = Counter(reqs)
	# for req in api._request_log:
	# 	if data[req] > 1:
	# 		mout.warningOut(f"Multiple requests ({data[req]}) to {req}")

	# js.dump(api._request_log,open('requests.json','wt'), indent="\t")

	api.finish()

	if run_push_changes:
		push_changes()

def run_test():

	push_changes()
	return

	# print(api.fixtures.columns)

	# print(api.get_gw_fixtures(6))

	# print(api.elements_by_team['MCI'])

	# print(api.get_player_team_obj(15))
	# print(api.get_player_team_obj(17))

	# print(api.elements.columns)
	print(api.get_player_index(664))
	pprint(api.elements['web_name'][api.get_player_index(664)])

	p = Player('Maddison',api)

	s = p.get_event_score(8,debug=True)

	print(p,s)

	p = Player('Ward-Prowse',api)

	s = p.get_event_score(8,debug=True)

	print(p,s)

	# create_comparison_page(api,[])

	# l = League(146330,api)

	# create_leaguepage(l,[],0)

	# p = Player('Havertz',api)

	# create_playerpage(api,p,[])

	# # p.expected_points(gw=2,use_official=True,debug=True)
	# # p.new_expected_points(gw=2,use_official=False,debug=True,force=True)
	# man = Manager("Max Winokan", 264578, api, team_name="Diamond Diogo's", authenticate=False)
	# # man = Manager("Max Winokan", 1327451, api, team_name="Diamond Diogo's", authenticate=False)
	# create_managerpage(api, man, [])

	api.finish()
	exit()

def create_comparison_page(api,leagues,prev_gw_count=5,next_gw_count=5):
	mout.debug(f'create_comparison_page()')

	# instantiate all the player objects
	players = []
	for pid in api._elements['id']:
		index = api.get_player_index(pid)
		p = Player(None, api, index=index)
		players.append(p)

	players = sorted(players,key=lambda x: x.selected_by,reverse=True)

	# subset = ['Luis','Martinelli','Foden','Ederson','Chukwu']
	# subset = [Player(n,api) for n in subset]

	html_buffer = ""

	### SEARCH BOX
	html_buffer += '<div class="w3-col s12 m12 l12">\n'
	html_buffer += '<div class="w3-panel w3-black shadow89 w3-padding" style="padding:0px;padding-bottom:3px;">\n'

	html_buffer += f'<h3><i class="fa fa-search"></i> Search for and click to add players: </h3>\n'
	html_buffer += f'<h4><input class="w3-input w3-white shadow25" onkeyup="searchFunction()" id="searchInput" type="text" placeholder="Search players by name..."></h4>\n'
	html_buffer += f'</div>\n'
	html_buffer += f'</div>\n'

	html_buffer += f'<div class="w3-padding w3-center" id="searchTable">\n'
	for p in players:

		team_bg_color = p.team_obj.get_style()['background-color']
		team_text_color = p.team_obj.get_style()['color']
		team_style_str = f'"background-color:{team_bg_color};color:{team_text_color};margin-bottom:5px;"'

		html_buffer += f'<span style="display:none;">\n'
		html_buffer += f'<button class="w3-button" onclick="addPlayer({p.id})" style={team_style_str}>\n'
		html_buffer += f'<img class="w3-image" src="{p.team_obj._badge_url}" alt="{p.team_obj.shortname}" width="20" height="20">\n'
		html_buffer += f' {p.full_name}</button>\n'
		html_buffer += f'</span>\n'

	html_buffer += f'</div>\n'

	### ADD PLAYER SCRIPTING
	html_buffer += '<script>\n'
	html_buffer += 'function addPlayer(id) {\n'
	html_buffer += '  var id;\n'
	html_buffer += '  tr = document.getElementById("statRow"+id);\n'
	html_buffer += '  tr.style.display = "";\n'
	html_buffer += '  tr = document.getElementById("graphDiv");\n'
	html_buffer += '  tr.style.display = "";\n'
	html_buffer += '  showPlayerTrace(id);\n'
	html_buffer += '};\n'
	html_buffer += '</script>\n'

	### REMOVE PLAYER SCRIPTING
	html_buffer += '<script>\n'
	html_buffer += 'function removePlayer(id) {\n'
	html_buffer += '  var id;\n'
	html_buffer += '  tr = document.getElementById("statRow"+id);\n'
	html_buffer += '  tr.style.display = "none";\n'
	html_buffer += '  hidePlayerTrace(id);\n'
	html_buffer += '};\n'
	html_buffer += '</script>\n'

	### SEARCH SCRIPTING (SPANS)
	html_buffer += '<script>\n'
	html_buffer += 'function searchFunction() {\n'
	html_buffer += '  var input, filter, table, tr, td, i, txtValue;\n'
	html_buffer += '  input = document.getElementById("searchInput");\n'
	html_buffer += '  filter = input.value.toUpperCase();\n'
	html_buffer += '  table = document.getElementById("searchTable");\n'
	html_buffer += '  tr = table.getElementsByTagName("span");\n'
	html_buffer += '\n'
	html_buffer += '  if (filter.length < 1) {\n'
	html_buffer += '    for (i = 0; i < tr.length; i++) {\n'
	html_buffer += '      td = tr[i].getElementsByTagName("button")[0];\n'
	html_buffer += '      if (td) {\n'
	html_buffer += '        tr[i].style.display = "none";\n'
	html_buffer += '      } \n'
	html_buffer += '    }\n'
	html_buffer += '  } else {\n'
	html_buffer += '    for (i = 0; i < tr.length; i++) {\n'
	html_buffer += '      td = tr[i].getElementsByTagName("button")[0];\n'
	html_buffer += '      if (td) {\n'
	html_buffer += '        txtValue = td.textContent || td.innerText;\n'
	html_buffer += '        if (txtValue.toUpperCase().indexOf(filter) > -1) {\n'
	html_buffer += '          tr[i].style.display = "";\n'
	html_buffer += '        } else {\n'
	html_buffer += '          tr[i].style.display = "none";\n'
	html_buffer += '        }\n'
	html_buffer += '      } \n'
	html_buffer += '    }\n'
	html_buffer += '  }\n'
	html_buffer += '}\n'
	html_buffer += '</script>\n'

	### STATS DATA
	html_buffer += '<div class="w3-col s12 m12 l12">\n'
	html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive" style="padding:0px;padding-bottom:3px;">\n'

	html_buffer += f'<table class="w3-table responsive-text" id="statTable">\n'

	now_gw = api._current_gw
	start_gw = max(1,now_gw-prev_gw_count)
	end_gw = min(38,now_gw+next_gw_count)

	### HEADERS
	html_buffer += f'<tr>\n'
	html_buffer += f'<th></th>\n'
	html_buffer += f'<th>Name</th>\n'
	html_buffer += f'<th style="text-align:center;">Price</th>\n'
	html_buffer += f'<th style="text-align:center;">ΣPts</th>\n'
	html_buffer += f'<th style="text-align:center;">Trans.</th>\n'
	html_buffer += f'<th style="text-align:center;">xM</th>\n'
	html_buffer += f'<th style="text-align:center;">xG</th>\n'
	html_buffer += f'<th style="text-align:center;">xA</th>\n'
	html_buffer += f'<th style="text-align:center;">xC</th>\n'
	html_buffer += f'<th style="text-align:center;">xB</th>\n'

	for i in range(start_gw,now_gw+1):
		html_buffer += f'<th style="text-align:center;">GW{i}</th>\n'

	html_buffer += f'<th style="text-align:center;">Form</th>\n'

	for i in range(now_gw+1,end_gw+1):
		html_buffer += f'<th style="text-align:center;">GW{i}</th>\n'

	html_buffer += f'</tr>\n'

	n = len(players)


	### PLAYER ROWS
	for i,p in enumerate(players):

		mout.progress(i,n)

		html_buffer += f'<tr id="statRow{p.id}" style="display:none;">\n'
		
		html_buffer += f'<td class="w3-center w3-button w3-black" onclick="removePlayer({p.id})"><i class="fa fa-close"></i></td>\n'

		# name
		bg_color = p.team_obj.get_style()['background-color']
		text_color = p.team_obj.get_style()['color']
		style_str = f'"background-color:{bg_color};color:{text_color};vertical-align:middle;"'
		html_buffer += f'<td style={style_str}>\n'
		html_buffer += f'<img class="w3-image" src="{p.team_obj._badge_url}" alt="{p.team_obj.shortname}" width="20" height="20">\n'
		html_buffer += f'<a href="https://mwinokan.github.io/FPL_GUI/html/player_{p.id}.html"><b> {p.name}</a>\n'
		if p.is_yellow_flagged:
			html_buffer += f' ⚠️'
		elif p.is_red_flagged:
			html_buffer += f' ⛔️'
		html_buffer += f'</b></td>\n'

		html_buffer += f'<td style="text-align:center;vertical-align:middle;">£{p.price}</td>\n'
		
		# total points
		if p.appearances < 1:
			score = 0
		else:
			score = p.total_points/p.appearances
		style_str = get_style_from_event_score(score).rstrip('"')+';vertical-align:middle;"'
		html_buffer += f'<td class="w3-center" style={style_str}>{p.total_points}</td>\n'

		# transfer percent
		value = p.transfer_percent
		text = f'{p.transfer_percent:.1f}%'
		if abs(value) > 10:
			if text.startswith("-"):
				style_str = '"color:darkred;vertical-align:middle;"'
			else:
				style_str = '"color:darkgreen;vertical-align:middle;"'
			html_buffer += f'<td class="w3-center" style={style_str}><b>{text}</b></td>\n'
		else:
			if text.startswith("-"):
				style_str = '"color:red;vertical-align:middle;"'
			else:
				style_str = '"color:green;vertical-align:middle;"'
			html_buffer += f'<td class="w3-center" style={style_str}>{text}</td>\n'

		# minutes
		style_str = get_style_from_minutes_played(p.expected_minutes()).rstrip('"')+';vertical-align:middle;text-align:right;"'
		html_buffer += f'<td class="w3-center" style={style_str}>'
		if p.xG_no_opponent is None:
			html_buffer += f"-"
		else:
			html_buffer += f"{p.expected_minutes():.0f}"
		html_buffer += '</td>\n'

		# xG
		style_str = get_style_from_expected_return(p.xG_no_opponent).rstrip('"')+';vertical-align:middle;text-align:right;"'
		html_buffer += f'<td class="w3-center" style={style_str}>'
		if p.xG_no_opponent is None:
			html_buffer += f"-"
		else:
			html_buffer += f"{p.xG_no_opponent:.2f}"
		html_buffer += '</td>\n'

		# xA
		style_str = get_style_from_expected_return(p.xA_no_opponent).rstrip('"')+';vertical-align:middle;text-align:right;"'
		html_buffer += f'<td class="w3-center" style={style_str}>'
		if p.xA_no_opponent is None:
			html_buffer += f"-"
		else:
			html_buffer += f"{p.xA_no_opponent:.2f}"
		html_buffer += '</td>\n'

		# xCS
		style_str = get_style_from_expected_return(p.xC_no_opponent).rstrip('"')+';vertical-align:middle;text-align:right;"'
		html_buffer += f'<td class="w3-center" style={style_str}>'
		if p.xC_no_opponent is None:
			html_buffer += f"-"
		else:
			html_buffer += f"{p.xC_no_opponent:.0%}"
		html_buffer += '</td>\n'

		# xB
		style_str = get_style_from_bonus(p.xBpts).rstrip('"')+';vertical-align:middle;text-align:right;border-right: 4px solid white;border-collapse:collapse;"'
		html_buffer += f'<td class="w3-center" style={style_str}>'
		if p.xBpts is None:
			html_buffer += f"-"
		else:
			html_buffer += f"{p.xBpts:.2f}"
		html_buffer += '</td>\n'

		# previous GWs
		for i in range(start_gw,now_gw+1):
			html_buffer += player_summary_cell_modal(p,i)

		# form
		form = p.form
		style_str = get_style_from_event_score(form).rstrip('"')+';vertical-align:middle;border-right:4px solid white;border-left:4px solid white;border-collapse:collapse;"'
		html_buffer += f'<td class="w3-center" style={style_str}>{form}</td>\n'

		# upcoming GWs
		for i in range(now_gw+1,end_gw+1):
			exp = p.expected_points(gw=i,debug=False)
			style_str = get_style_from_event_score(exp).rstrip('"')+';vertical-align:middle;"'
			# html_buffer += f'<td class="w3-center" style={style_str}>{exp:.1f}</td>\n'
			html_buffer += f'<td class="w3-center" style={style_str}>{p.get_fixture_str(i,short=True,lower_away=True)}</td>\n'

		html_buffer += f'</tr>\n'

	mout.finish()

	html_buffer += f'</table>'
	
	html_buffer += f'</div>'
	html_buffer += f'</div>'

	### GRAPH
	html_buffer += '<div class="w3-col s12 m12 l12">\n'
	html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive w3-padding" id="graphDiv" style="display:none;">\n'
	
	# html_buffer += f'<h3>Expected Points Graph</h3>\n'
	html_buffer += f'<div id="comparisonGraph" style="width:100%;height:500px">\n'
	html_buffer += f'</div>\n'

	### BUILD THE PLOTTING DATA
	gw_indices = [i+1 for i in range(now_gw,end_gw+1)]
	gw_strs = [f'GW{i+1}' for i in range(now_gw,end_gw+1)]

	plot_data = []
	player_id_to_trace_id = {}
	for i,p in enumerate(players):

		player_id_to_trace_id[p.id] = i

		plot_y = [round(p.expected_points(gw=i),1) for i in gw_indices]

		plot_data.append(dict(
			name=p.name,
			x=gw_strs,
			y=plot_y,
			visible=False,
			mode='lines+markers',
		))

	### CREATE THE GRAPH
	html_buffer += '<script>\n'
	html_buffer += '	GRAPH = document.getElementById("comparisonGraph");\n'
	html_buffer += f'	Plotly.newPlot( GRAPH, {js.dumps(plot_data)}'
	html_buffer += ', {	title: "Expected Points", margin: { r:0 }, font: {size: 14}} , {responsive: true});\n'
	html_buffer += '</script>\n'

	### SHOW TRACE SCRIPTING
	html_buffer += '<script>\n'
	html_buffer += 'function showPlayerTrace(id) {\n'
	html_buffer += '  var id, player_id_to_trace_id, trace_id;\n'
	html_buffer += f'  player_id_to_trace_id = {js.dumps(player_id_to_trace_id)};\n'
	html_buffer += f'  trace_id = player_id_to_trace_id[id];\n'
	html_buffer += '  Plotly.update(GRAPH, {"visible":true}, {}, [trace_id]);\n'
	html_buffer += '};\n'
	html_buffer += '</script>\n'

	### HIDE TRACE SCRIPTING
	html_buffer += '<script>\n'
	html_buffer += 'function hidePlayerTrace(id) {\n'
	html_buffer += '  var id, player_id_to_trace_id, trace_id;\n'
	html_buffer += f'  player_id_to_trace_id = {js.dumps(player_id_to_trace_id)};\n'
	html_buffer += f'  trace_id = player_id_to_trace_id[id];\n'
	html_buffer += '  Plotly.update(GRAPH, {"visible":false}, {}, [trace_id]);\n'
	html_buffer += '};\n'
	html_buffer += '</script>\n'

	html_buffer += f'</div>\n'
	html_buffer += f'</div>\n'

	### Help/Explainer
	html_buffer += '<div class="w3-col s12 m6 l6">\n'
	html_buffer += '<div class="w3-panel w3-blue shadow89 w3-responsive w3-padding">\n'

	html_buffer += f'<h3>Legend</h3>'
	html_buffer += f'<span class="w3-tag">T%</span> Net transfer percentage <br><br>\n'
	html_buffer += f'<span class="w3-tag"><sup>1</sup></span> Recent results are weighted higher <br><br>\n'
	html_buffer += f'<span class="w3-tag"><sup>2</sup></span> Not adjusted for opponent <br><br>\n'
	html_buffer += f'<span class="w3-tag">xM</span> Expected Minutes <sup>1</sup><br><br>\n'
	html_buffer += f'<span class="w3-tag">xG</span> Expected Goals <sup>1,2</sup><br><br>\n'
	html_buffer += f'<span class="w3-tag">xA</span> Expected Assists <sup>1,2</sup><br><br>\n'
	html_buffer += f'<span class="w3-tag">xC</span> Expected Clean Sheets <sup>1,2</sup><br><br>\n'
	html_buffer += f'<span class="w3-tag">xB</span> Expected Bonus Points <sup>1,2</sup>\n'

	html_buffer += f'</div>\n'
	html_buffer += f'</div>\n'

	navbar = create_navbar(leagues, colour='black')
	html_page('html/comparison.html',None,title=f"Comparison Tool", gw=api._current_gw, html=html_buffer, showtitle=True, bar_html=navbar, colour='aqua', plotly=True)

def create_cup_page(api,league,leagues):

	# try and get data pertaining to the cups

	# the page should be a bunch of tables separating by gameweek

	# each table row should contain:

	"""

	Team Name  	 | Points         | vs. | Points         | Team Name
	Manager Name | Fixtures/Total |     | Fixtures/Total | Manager Name

	"""

	all_matches = []

	# for manager in [Manager("Max Winokan",780664,api)]:

	mout.debugOut(f"Getting all cup matches in {league.name}...")
	for i,manager in enumerate(league.managers):
		mout.progress(i,league.num_managers,width=50)
		matches = manager.get_cup_matches(league)
		# print(i,manager.name,len(matches))
		all_matches += manager.get_cup_matches(league)
	mout.progress(league.num_managers,league.num_managers,width=50)

	# go by gameweek

	gws = list(set([m['gw'] for m in all_matches]))
	

	html_buffer = ""

	prog_step = (50/len(gws))

	for i,gw in enumerate(sorted(gws,reverse=True)):

		matches = [m for m in all_matches if m['gw'] == gw]
	
		processed = []

		# print(f'GW{gw} Cup Matches')

		html_buffer += f'<h2>GW{gw} Cup Matches: {matches[0]["title"]}</h2>\n'
		html_buffer += '<table class="w3-table-all">\n'

		html_buffer += '<tr>\n'

		html_buffer += f'<th class="w3-right">\n'
		html_buffer += f'Player 1\n'
		html_buffer += f'</th>\n'

		html_buffer += f'<th>\n'
		html_buffer += f'</th>\n'
		html_buffer += f'<th>\n'
		html_buffer += f'</th>\n'

		html_buffer += f'<th class="w3-center">\n'
		html_buffer += f'</th>\n'

		html_buffer += f'<th>\n'
		html_buffer += f'</th>\n'
		html_buffer += f'<th>\n'
		html_buffer += f'</th>\n'

		html_buffer += f'<th class="w3-left">\n'
		html_buffer += f'Player 2\n'
		html_buffer += f'</th>\n'
		
		html_buffer += '</tr>\n'

		for j,match in enumerate(matches):

			mout.progress(i*prog_step + j*prog_step/len(matches),50,width=50)

			man1 = match['self']
			man1_score = man1.get_event_score(gw)

			processed.append(man1.id)

			is_bye = match['bye']

			if not is_bye:

				man2 = match['opponent']
				
				if man2.id in processed:
					# print('Skipping!')
					continue

				man2_score = man2.get_event_score(gw)

				if match['winner']:
					
					if man1.id == match['winner']:
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

			# print(man1,man2)

			html_buffer += '<tr>\n'

			html_buffer += f'<td class="w3-right">\n'
			html_buffer += f'<a href="{man1.gui_url}">{man1.name}</a>'
			if man1.is_diamond:
				html_buffer += '💎'
			html_buffer += f'<br><a href="{man1.gui_url}">{man1.team_name}</a>\n'
			html_buffer += '</td>\n'

			html_buffer += f'<td class="w3-center" style="vertical-align:middle;"><img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{man1._kit_path}?raw=true" alt="Kit Icon" width="22" height="29"></td>\n'
			
			if winner == 1:
				html_buffer += f'<td class="w3-green w3-center">\n'
			else:
				html_buffer += f'<td class="w3-center">\n'

			html_buffer += f'{man1_score}'
			if gw == api._current_gw:
				html_buffer += f'<br>({man1.fixtures_played}/{man1.total_fixtures})\n'
			html_buffer += '</td>\n'

			html_buffer += f'<td class="w3-center">\n'
			html_buffer += f'vs.\n'
			html_buffer += '</td>\n'

			if is_bye:

				html_buffer += f'<td class="w3-center">\n'
				html_buffer += '</td>\n'

				html_buffer += f'<td class="w3-center">\n'
				html_buffer += '</td>\n'
				
				html_buffer += f'<td style="text-align:left;vertical-align:middle;">\n'
				html_buffer += 'BYE!\n'
				html_buffer += '</td>\n'

			else:

				if winner == 2:
					html_buffer += f'<td class="w3-green w3-center">\n'
				else:
					html_buffer += f'<td class="w3-center">\n'

				html_buffer += f'{man2_score}'
				if gw == api._current_gw:
					html_buffer += f'<br>({man2.fixtures_played}/{man2.total_fixtures})\n'
				html_buffer += '</td>\n'

				html_buffer += f'<td class="w3-center" style="vertical-align:middle;"><img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{man2._kit_path}?raw=true" alt="Kit Icon" width="22" height="29"></td>\n'

				html_buffer += f'<td class="w3-left">\n'
				html_buffer += f'<a href="{man2.gui_url}">{man2.name}</a>'
				if man2.is_diamond:
					html_buffer += '💎'
				html_buffer += f'<br><a href="{man2.gui_url}">{man2.team_name}</a>\n'
				html_buffer += '</td>\n'

			html_buffer += '</tr>\n'
		
		html_buffer += '</table>\n'

	mout.progress(50,50,width=50)

	navbar = create_navbar(leagues, active='K', colour='black', active_colour='green')
	html_page('html/toilet_cup.html',None,title=f"Tesco Value Cup", gw=api._current_gw, html=html_buffer, showtitle=True, bar_html=navbar)

def create_teampage(api,leagues):
	mout.debugOut(f"create_teampage()")

	from expected import weighted_average

	html_buffer = ""

	### fixture table
	
	if api._current_gw < 38:

		html_buffer += floating_subtitle('Fixture Table',pad=0)

		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive" style="padding:0px;padding-bottom:3px;">\n'

		html_buffer += '<table class="w3-table responsive-text">\n'

		sorted_teams = sorted(api.teams,key=lambda x: x.difficulty_next5, reverse=True)

		table_buffer = ""

		gw_range = range(max(1,api._current_gw),min(api._current_gw+8,38))

		for i,team in enumerate(sorted_teams):

			team_bg_color = team.get_style()['background-color']
			team_text_color = team.get_style()['color']
			team_style_str = f'"background-color:{team_bg_color};color:{team_text_color};"'

			table_buffer += '<tr>\n'
			table_buffer += f'<th style={team_style_str}>'
			table_buffer += f'<img class="w3-image" src="{team._badge_url}" alt="{team.shortname}" width="20" height="20"> '
			table_buffer += f' {team.name}</th>\n'

			for gw in gw_range:
				fixs = team.get_gw_fixtures(gw)

				if not fixs:
					table_buffer += f'<td class="w3-center">-</td>\n'
					continue

				opps = team.get_opponent(gw)

				if not isinstance(opps,list):
					fixs = [fixs]
					opps = [opps]

				total = 0
				for fix,opp in zip(fixs,opps):
					is_home = fix['team_a'] == opp.id
					total += team.strength(is_home,overall=True) - opp.strength(not is_home,overall=True)
				diff_delta = total / len(opps)

				style_str = get_style_from_difficulty(diff_delta)
				table_buffer += f'<td class="w3-center" style={style_str}>\n'

				if len(opps) > 1:
					table_buffer += "<strong>"
				table_buffer += " ".join([t.shortname if f['team_a'] == t.id else t.shortname.lower() for f,t in zip(fixs,opps)])

				table_buffer += f'</td>\n'

			table_buffer += '</tr>\n'

		html_buffer += '<tr>\n'
		html_buffer += '<th>Team</th>\n'
		for gw in gw_range:
			gw_str = "GW"
			if gw in api._special_gws.keys():
				gw_str = api._special_gws[gw]
			if gw_str in ["DGW","TGW"]:
				html_buffer += f'<th class="w3-center" style="background-color:yellow">{gw_str}{gw}</th>\n'
			elif gw_str == "BGW":
				html_buffer += f'<th class="w3-center" style="background-color:red">{gw_str}{gw}</th>\n'
			else:
				html_buffer += f'<th class="w3-center">{gw_str}{gw}</th>\n'
		html_buffer += '</tr>\n'

		html_buffer += table_buffer
		
		html_buffer += '</table>\n'

		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

		html_buffer += '<br>\n'

	html_buffer += floating_subtitle('Best Assets by Team',pad=0)

	gw_range = range(max(1,api._current_gw-3),min(api._current_gw+5,39))

	### by team info

	for i,team in enumerate(api.teams):
		mout.progress(i,20)

		team_bg_color = team.get_style()['background-color']
		team_text_color = team.get_style()['color']
		team_style_str = f'background-color:{team_bg_color};color:{team_text_color};'

		html_buffer += '<div class="w3-col s12 m12 l6">\n'
		html_buffer += f'<div class="w3-panel shadow89 w3-responsive" style="{team_style_str};padding:0px;padding-bottom:4px;">\n'

		html_buffer += '<div class="w3-padding">\n'
		html_buffer += f'<h2><img class="w3-image" src="{team._badge_url}" alt="Team" width="30" height="30">\t{team.name}</h2>\n'
		html_buffer += '</div>\n'

		players = api.elements_by_team[team.shortname]

		# Recent results

		html_buffer += '<table class="w3-table responsive-text">\n'

		# table_buffer += '<tr>\n'
		# html_buffer += f'<th class="w3-center" style={team_style_str}>Opponent</th>\n'

		table_buffer = "<tr>\n"

		### opponents

		for gw in gw_range:
			fixs = team.get_gw_fixtures(gw)

			if not isinstance(fixs, list):

				opp = team.get_opponent(gw)
				is_home = fixs['team_a'] == opp.id
				
				diff_delta = team.strength(is_home,overall=True) - opp.strength(not is_home,overall=True)
				style_str = get_style_from_difficulty(diff_delta)

				table_buffer += f'<td class="w3-center" style={style_str}>\n'
				table_buffer += f'<img class="w3-image" src="{opp._badge_url}" alt="{opp.shortname}" width="20" height="20"> '

				if is_home:
					table_buffer += f'{opp.shortname} '
				else:
					table_buffer += f'{opp.shortname.lower()} '

				table_buffer += '</td>\n'

			elif fixs:

				opps = team.get_opponent(gw)
				for fix,opp in zip(fixs,opps):


					is_home = fix['team_a'] == opp.id
					
					diff_delta = team.strength(is_home,overall=True) - opp.strength(not is_home,overall=True)
					style_str = get_style_from_difficulty(diff_delta)

					table_buffer += f'<td class="w3-center" style={style_str}>\n'
					table_buffer += f'<img class="w3-image" src="{opp._badge_url}" alt="{opp.shortname}" width="20" height="20"> '

					if is_home:
						table_buffer += f'{opp.shortname} '
					else:
						table_buffer += f'{opp.shortname.lower()} '
						table_buffer += '\t'

				table_buffer += '</td>\n'

			else:
				table_buffer += f'<td class="w3-center" style="background-color:black;color:white">-</td>\n'

		table_buffer += '</tr>\n'

		table_buffer += '<tr>\n'
		# table_buffer += f'<th class="w3-center" style={team_style_str}>Score</th>\n'

		special_gws = {}

		### results / game scores

		for gw in gw_range:

			fixs = team.get_gw_fixtures(gw)

			# multiple fixtures
			if isinstance(fixs,list) and len(fixs) > 0:

				special_gws[gw] = len(fixs)

				opps = team.get_opponent(gw)
				for fix,opp in zip(fixs,opps):

					is_home = fix['team_a'] == opp.id

					team_h_score = fix['team_h_score']
					team_a_score = fix['team_a_score']

					if not fix['started']:
						team_h_obj = api.get_player_team_obj(fix['team_h'])
						team_a_obj = api.get_player_team_obj(fix['team_a'])
						team_h_score = (team_a_obj.goals_conceded_per_game + team_h_obj.goals_scored_per_game)/2 * (1-team_a_obj.expected_clean_sheet(team_h_obj))
						team_a_score = (team_h_obj.goals_conceded_per_game + team_a_obj.goals_scored_per_game)/2 * (1-team_h_obj.expected_clean_sheet(team_a_obj))

					style_str = get_style_from_game_score(is_home, team_h_score, team_a_score)
					table_buffer += f'<td class="w3-center" style={style_str}>\n'
					if not fix['started']:
						table_buffer += f"({team_h_score:.0f} - {team_a_score:.0f})"
					else:
						table_buffer += f"{team_h_score:.0f} - {team_a_score:.0f}"
					
					table_buffer += '\t'

				table_buffer += '</td>\n'

			# blank
			elif len(fixs) == 0:
				table_buffer += f'<td class="w3-center" style="background-color:black;color:white">-</td>\n'

			# single fixture
			else:

				opp = team.get_opponent(gw)
				is_home = fixs['team_a'] == opp.id

				team_h_score = fixs['team_h_score']
				team_a_score = fixs['team_a_score']

				# fixture hasn't started
				if not fixs['started']:
					table_buffer += f'<td class="w3-center" style="background-color:white;color:black;">\n'

				# fixture in progress
				else:
					style_str = get_style_from_game_score(is_home, team_h_score, team_a_score)
					table_buffer += f'<td class="w3-center" style={style_str}>\n'
					table_buffer += f"{team_h_score:.0f} - {team_a_score:.0f}"
				
				table_buffer += '</td>\n'

		html_buffer += '<tr>\n'
		
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

		html_buffer += '</tr>\n'

		html_buffer += table_buffer

		html_buffer += '</tr>\n'		
		html_buffer += '</table>\n'

		if test:
			break

		### team assets

		if api._current_gw > 0:

			html_buffer += '<br>\n'
			html_buffer += '<table class="w3-table">\n'

			def player_name_str(p):
				str_buffer = ""
				if p.is_yellow_flagged:
					str_buffer += f'⚠️ '
				elif p.is_red_flagged:
					str_buffer += f'⛔️ '
				str_buffer += f'<a href="https://mwinokan.github.io/FPL_GUI/html/player_{p.id}.html">{p.name}</a>\n'
				return str_buffer

			# Top scoring assets
			html_buffer += '<tr>\n'
			html_buffer += f'<th style={team_style_str}>Total Points</th>\n'
			sorted_players = sorted(players,key=lambda x: x.total_points,reverse=True)
			for p in sorted_players[:5]:
				style_str = get_style_from_event_score(p.total_points/p.appearances)
				html_buffer += f'<td class="w3-center" style={style_str}>'
				html_buffer += f'{player_name_str(p)} {p.total_points}'
				html_buffer += '</td>\n'
			html_buffer += '</tr>\n'

			# Best form assets
			html_buffer += '<tr>\n'
			html_buffer += f'<th style={team_style_str}>Best Form</th>\n'
			sorted_players = sorted(players,key=lambda x: x.form,reverse=True)
			for p in sorted_players[:5]:
				style_str = get_style_from_event_score(p.form)
				html_buffer += f'<td class="w3-center" style={style_str}>'
				html_buffer += f'{player_name_str(p)} {p.form}'
				html_buffer += '</td>\n'
			html_buffer += '</tr>\n'

			if api._current_gw < 38:

				# Most minutes
				html_buffer += '<tr>\n'
				html_buffer += f'<th style={team_style_str}>GW{api._current_gw+1} xMins</th>\n'
				sorted_players = sorted(players,key=lambda x: x.expected_minutes() or 0.0,reverse=True)
				for p in sorted_players[:5]:
					style_str = get_style_from_minutes_played(p.expected_minutes())
					html_buffer += f'<td class="w3-center" style={style_str}>'
					html_buffer += f"{player_name_str(p)} {p.expected_minutes():.0f}'"
					html_buffer += '</td>\n'
				html_buffer += '</tr>\n'

			# Top predicted points assets
			html_buffer += '<tr>\n'
			html_buffer += f'<th style={team_style_str}>Next 5 xPts</th>\n'
			sorted_players = sorted(players,key=lambda x: x.next5_expected,reverse=True)
			for p in sorted_players[:5]:
				style_str = get_style_from_event_score(p.next5_expected/5)
				html_buffer += f'<td class="w3-center" style={style_str}>'
				html_buffer += f'{player_name_str(p)} {p.next5_expected:.1f}'
				html_buffer += '</td>\n'
			html_buffer += '</tr>\n'
		
			html_buffer += '</table>\n'

		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

		# break

	mout.progress(20,20)

	navbar = create_navbar(leagues)
	html_page('html/teams.html',None,title=f"Teams", gw=api._current_gw, html=html_buffer, showtitle=True, bar_html=navbar, colour='aqua')

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
		player_ids = api._elements['id']
		for i,pid in enumerate(player_ids):
			player_minutes[pid] = api._elements['minutes'][i]
		player_ids = api._prev_elements['id']
		
		# last season
		for i,pid in enumerate(player_ids):
			if pid in player_minutes:
				player_minutes[pid] += api._prev_elements['minutes'][i]

		players = []
		for pid,mins in player_minutes.items():
			if mins > minutes:
				index = api.get_player_index(pid)
				p = Player(None, api, index=index)
				players.append(p)

		import sys
		sys.path.insert(1,'go')
		from value import create_value_figure
		from gwexp import create_gwexp_figure
		from bonus import create_bonus_figure
		from xgi import create_xgi_figure

		html_buffer = ""

		html_buffer += floating_subtitle('Attacking Points')
		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
		html_buffer += '<div class="w3-padding">\n'
		html_buffer += '<p>Returned attacking points vs expected attacking points including previous season data. Using official xG and xA data.</p>'
		html_buffer += '</div>\n'
		html_buffer += create_xgi_figure(api,players)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'
		
		if gw > 0:
			html_buffer += floating_subtitle('Best Value: Next 5 GWs')
			html_buffer += '<div class="w3-col s12 m12 l12">\n'
			html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
			html_buffer += '<div class="w3-padding">\n'
			html_buffer += "<p>Expected points over the next five gameweeks per player price. Expected poins from Max's algorithm</p>"
			html_buffer += '</div>\n'
			html_buffer += create_value_figure(api,players)
			html_buffer += '</div>\n'
			html_buffer += '</div>\n'

			html_buffer += floating_subtitle(f'Best GW{gw+1} Assets')
			html_buffer += '<div class="w3-col s12 m12 l12">\n'
			html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
			html_buffer += '<div class="w3-padding">\n'
			html_buffer += "<p>Next gameweek expected points (official FPL source) versus player form.</p>"
			html_buffer += '</div>\n'
			html_buffer += create_gwexp_figure(api,players)
			html_buffer += '</div>\n'
			html_buffer += '</div>\n'

		# if gw > 3:
		# 	html_buffer += floating_subtitle('BPS vs ')
		# 	html_buffer += '<div class="w3-col s12 m12 l12">\n'
		# 	html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
		# 	html_buffer += "<p>Player </p>"
		# 	html_buffer += create_bonus_figure(api,players)
		# 	html_buffer += '</div>\n'
		# 	html_buffer += '</div>\n'
			
		# navbar = None
		navbar = create_navbar(leagues)
		html_page('html/assets.html',None,title=f"Asset Analysis", gw=gw, html=html_buffer, showtitle=True, bar_html=navbar,colour='aqua', plotly=True)

def create_navbar(leagues,active=None,colour='black',active_colour='aqua'):

	html_buffer = ""

	html_buffer += f'\n'

	html_buffer += f'<div class="w3-bar w3-{colour} shadow89">\n'
	html_buffer += f'<a class="w3-bar-item w3-{colour} w3-text-{colour}"></a>\n'
	html_buffer += '<div class="w3-dropdown-hover">\n'
	html_buffer += '<button class="w3-button w3-hover-aqua"><h3><span class="w3-tag w3-white">toilet.football</span></h3></button>\n'
	# html_buffer += '<button class="w3-button w3-hover-aqua"><h3>FPL <span class="w3-tag w3-white">GUI</span></h3></button>\n'
	html_buffer += '<div class="w3-dropdown-content w3-bar-block w3-card-4">\n'

	url = f'https://mwinokan.github.io/FPL_GUI/index.html'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">🏠 Home</a>\n'

	url = f'https://mwinokan.github.io/FPL_GUI/html/comparison.html'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">📊 Comparison Tool</a>\n'

	url = f'https://mwinokan.github.io/FPL_GUI/html/assets.html'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">📈 Asset Graphs</a>\n'

	if season_awards:
		url = f'https://mwinokan.github.io/FPL_GUI/html/season.html'
		html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">🏁 End of season</a>\n'

	if halfway_awards:
		url = f'https://mwinokan.github.io/FPL_GUI/html/christmas.html'
		html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">🎄 Christmas</a>\n'

	url = f'https://mwinokan.github.io/FPL_GUI/html/teams.html'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">👨‍👨‍👦‍👦 Teams</a>\n'

	if cup_active:
		url = f'https://mwinokan.github.io/FPL_GUI/html/toilet_cup.html'
		html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">🏆 Toilet Cup</a>\n'

	for i,league in enumerate(leagues):
		url = f'https://mwinokan.github.io/FPL_GUI/html/{league.name.replace(" ","-")}.html'
		html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua">{league._icon} {league.name}</a>\n'

	html_buffer += '</div>\n'
	html_buffer += '</div>\n'
	html_buffer += f'<a class="w3-bar-item w3-{colour} w3-text-{colour} w3-right"></a>\n'
	url = f'https://mwinokan.github.io/FPL_GUI/html/Tesco-Bean-Value-Toilet-League.html'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua w3-right"><h3>🚽</h3></a>\n'
	url = f'https://mwinokan.github.io/FPL_GUI/html/The-RBS-Diamond-Invitational.html'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-aqua w3-right"><h3>💎</h3></a>\n'
	html_buffer += '</div>\n'

	html_buffer += f'<div class="w3-bar w3-{colour}">\n'

	html_buffer += f'</div>\n'

	return html_buffer

def create_fixturepage(api,leagues):
	mout.debugOut(f"create_fixturepage()")

	gw = api._current_gw

	html_buffer = fixture_table(api, gw)
	html_buffer += fixture_table(api, gw+1)

	navbar = create_navbar(leagues, active='F', colour='black', active_colour='green')
	html_page('html/fixtures.html',None,title=f"Fixtures", gw=gw, html=html_buffer, showtitle=False, bar_html=navbar)

def create_playerpage(api,player,leagues):
	global completed_playerpages

	if int(player.id) not in completed_playerpages:

		mout.debugOut(f"create_playerpage({player.name})")

		gw = api._current_gw

		html_buffer = ""

		'''
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
		'''

		html_buffer += '<div class="w3-col s12 m12 l4">\n'
		html_buffer += f'<div class="w3-panel w3-{player.team_obj.shortname.lower()}-inv shadow89" style="padding:0px;padding-bottom:4px;">\n'
		html_buffer += f'<div class="w3-center">\n'
		html_buffer += f'<h2>{player.name}</h2>\n'
		html_buffer += f'<img class="w3-image" src="{player._photo_url}" alt="Player" width="220" height="280">\n'
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

		html_buffer += f'<div class="w3-panel w3-{player.team_obj.shortname.lower()} shadow89" style="padding:0px;padding-bottom:4px;">\n'
		html_buffer += f'<div class="w3-responsive">\n'

		######

		html_buffer += f'<div class="w3-center w3-padding-large">\n'
		html_buffer += f'<h5 class="double">\n'
		html_buffer += f'<h5>\n'

		color = f'{player.team_obj.shortname.lower()}-inv'

		if player.name in [p[0].name for p in risers]:
			html_buffer += f'<span class="w3-tag w3-green">£{player.price}</span>\n'
		elif player.name in [p[0].name for p in fallers]:
			html_buffer += f'<span class="w3-tag w3-red">£{player.price}</span>\n'
		else:
			html_buffer += f'<span class="w3-tag w3-{color}">£{player.price}</span>\n'

		html_buffer += f'<span class="w3-tag w3-{color}">global {player.selected_by}%</span>\n'
		
		if player.transfer_percent < 0:
			html_buffer += f'<span class="w3-tag w3-red">change {player.transfer_percent:.1f}%</span>\n'
		else:
			html_buffer += f'<span class="w3-tag w3-green">change +{player.transfer_percent:.1f}%</span>\n'
		
		# color by score?
		html_buffer += f'<span class="w3-tag w3-{color}">total {player.total_points} pts</span>\n'
		html_buffer += f'<span class="w3-tag w3-{color}">form {player.form} pts/game</span>\n'

		if player.total_goals > 0:
			html_buffer += f'<span class="w3-tag w3-green">{player.total_goals} goals</span>\n'

		if player.total_assists > 0:
			html_buffer += f'<span class="w3-tag w3-blue">{player.total_assists} assists</span>\n'

		if player._total_own_goals > 0:
			html_buffer += f'<span class="w3-tag w3-black">{player._total_own_goals} own goals</span>\n'

		if player._total_yellows > 0:
			html_buffer += f'<span class="w3-tag w3-yellow">{player._total_yellows} yellow cards</span>\n'

		if player._total_reds > 0:
			html_buffer += f'<span class="w3-tag w3-red">{player._total_reds} red cards</span>\n'

		if player.total_bonus > 0:
			html_buffer += f'<span class="w3-tag w3-aqua">{player.total_bonus} bonus</span>\n'

		if player.position_id < 4:
			if player._total_clean_sheets > 0:
				html_buffer += f'<span class="w3-tag w3-purple">{player._total_clean_sheets} clean sheets</span>\n'
		
		if player.position_id == 1:
			if player._total_penalties_saved > 0:
				html_buffer += f'<span class="w3-tag w3-green">{player._total_penalties_saved} penalties saves</span>\n'
			if player._total_saves > 0:
				html_buffer += f'<span class="w3-tag w3-blue">{player._total_saves} saves</span>\n'

		if player.position_id < 3:
			if player._total_goals_conceded > 0:
				html_buffer += f'<span class="w3-tag w3-orange">{player._total_goals_conceded} goals conceded</span>\n'
		
		if player.appearances > 0:
			html_buffer += f'<span class="w3-tag w3-dark-grey">{player.total_minutes/player.appearances:.0f} mins/game</span>\n'

		html_buffer += f'</h5>\n'
		html_buffer += f'</div>\n'

		html_buffer += f'</div>\n'
		html_buffer += f'</div>\n'
		html_buffer += f'</div>\n'
		
		if api._current_gw > 0 and (force_go_graphs or not api._live_gw):

			html_buffer += '<div class="w3-col s12 m12 l8">\n'
			html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
			import sys
			sys.path.insert(1,'go')
			from playgo import create_player_figure

			html_buffer += create_player_figure(api, player)
		
			html_buffer += f'</div>\n'

		if api._current_gw > 0:
			html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
			html_buffer += get_player_history_table(player)
			html_buffer += f'</div>\n'
			html_buffer += f'</div>\n'

		navbar = create_navbar(leagues, active=None, colour='black')

		style = api.create_team_styles_css()

		html_page(f'html/player_{player.id}.html',None,title=f"{player.name}",sidebar_content=None, gw=gw, html=html_buffer, showtitle=False, bar_html=navbar,extra_style=style,colour=player.team_obj.style['accent'],nonw3_colour=True,plotly=True)

		completed_playerpages.append(int(player.id))

def create_trophycabinet(api,man):

	html_buffer = ''

	leagues = man._leagues

	man._awards = sorted(man._awards, key=lambda x: x["gw"], reverse=False)

	html_buffer += '<div class="w3-bar w3-black">\n'
	
	for i,league in enumerate(leagues):

		if i == 0:
			html_buffer += f'<button class="w3-bar-item w3-button w3-mobile tablink w3-aqua" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
		else:
			html_buffer += f'<button class="w3-bar-item w3-mobile w3-button tablink" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
	
	html_buffer += '</div>\n'

	for i,league in enumerate(leagues):

		if i==0:
			html_buffer += f'<div id="{league.id}" class="w3-container w3-{league._colour_str} league">\n'
		else:
			html_buffer += f'<div id="{league.id}" class="w3-container w3-{league._colour_str} league" style="display:none">\n'

		html_buffer += '<div class="w3-justify w3-row-padding">\n'

		awards = [a for a in man._awards if league.name in a['league'] and a['gw'] not in ['half','season','chips']]

		half_awards = [a for a in man._awards if league.name in a['league'] and a['gw'] == 'half']
		full_awards = [a for a in man._awards if league.name in a['league'] and a['gw'] == 'season']
		chip_awards = [a for a in man._awards if league.name in a['league'] and a['gw'] == 'chips']

		if len(awards+half_awards+full_awards+chip_awards) > 0:

			html_buffer += '<div class="w3-justify">'
			html_buffer += '<div class="w3-row-padding">'

			award_keys = list(set([a["key"] for a in awards]))

			award_panels = []

			# full > half > chips > normal
			for award in full_awards:

				key = award['key']
				
				colour = award_colour[key]
				# icon = award_icon[key]

				html_buffer += '<div class="w3-col s12 m6 l4">\n'
				html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-card shadow89 w3-border-yellow">\n'
				html_buffer += '<table class="w3-table">\n'
				html_buffer += '<tr>\n'
				html_buffer += '<td style="text-align:left;vertical-align:middle;">\n'
				html_buffer += f'<h1>{award_flavourtext[key]}</h1>\n'
				html_buffer += '</td>\n'
				html_buffer += '<td style="text-align:right;vertical-align:middle;">\n'
				html_buffer += f'<h2><span class="w3-tag">Season</span></h2>\n'
				html_buffer += '</tr>\n'
				html_buffer += '</table>\n'
				html_buffer += '</div>\n'
				html_buffer += '</div>\n'

			for award in half_awards:

				key = award['key']
				
				colour = award_colour[key]
				# icon = award_icon[key]

				html_buffer += '<div class="w3-col s12 m6 l4">\n'
				html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-card shadow89 w3-border-green">\n'
				html_buffer += '<table class="w3-table">\n'
				html_buffer += '<tr>\n'
				html_buffer += '<td style="text-align:left;vertical-align:middle;">\n'
				html_buffer += f'<h1>{award_flavourtext[key]}</h1>\n'
				html_buffer += '</td>\n'
				html_buffer += '<td style="text-align:right;vertical-align:middle;">\n'
				html_buffer += f'<h2><span class="w3-tag">Christmas</span></h2>\n'
				html_buffer += '</tr>\n'
				html_buffer += '</table>\n'
				html_buffer += '</div>\n'
				html_buffer += '</div>\n'

			for award in chip_awards:

				key = award['key']
				
				colour = award_colour[key]
				# icon = award_icon[key]

				html_buffer += '<div class="w3-col s12 m6 l4">\n'
				html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-card shadow89 w3-border-black">\n'
				html_buffer += '<table class="w3-table">\n'
				html_buffer += '<tr>\n'
				html_buffer += '<td style="text-align:left;vertical-align:middle;">\n'
				html_buffer += f'<h1>{award_flavourtext[key]}</h1>\n'
				html_buffer += '</td>\n'
				html_buffer += '<td style="text-align:right;vertical-align:middle;">\n'

				# delta = man._wc1_ordelta_percent
				# if delta > 0:
				# 	delta = f"+{delta:.0f}"
				# else:
				# 	delta = f"{delta:.0f}"

				# html_buffer += f'<h2><span class="w3-tag">Christmas</span></h2>\n'
				html_buffer += '</tr>\n'
				html_buffer += '</table>\n'
				html_buffer += '</div>\n'
				html_buffer += '</div>\n'

			# if chip_awards:
			# 	print(man.name,chip_awards)

			for key in award_keys:

				gws = sorted([a["gw"] for a in awards if a["key"] == key],key=lambda x: int(x))
				count = len(gws)
				icon = ""

				colour = award_colour[key]

				award_buffer = '<div class="w3-col s12 m6 l4">\n'
				award_buffer += f'<div class="w3-panel w3-{colour} w3-card shadow89">\n'
				award_buffer += '<table class="w3-table">\n'
				award_buffer += '<tr>\n'
				award_buffer += '<td style="text-align:left;vertical-align:middle;">\n'
					
				if count == 1:
					award_buffer += f'<h1>{icon} {award_flavourtext[key]}</h1>\n'
				else:
					award_buffer += f'<h1>{count} &times {icon} {award_flavourtext[key]}</h1>\n'

				award_buffer += '</td>\n'
				award_buffer += '<td style="text-align:right;vertical-align:middle;">\n'
				award_buffer += f'<h2><span class="w3-tag">GW{", GW".join(gws)}</span></h2>\n'
				award_buffer += '</tr>\n'
				award_buffer += '</table>\n'
				award_buffer += '</div>\n'
				award_buffer += '</div>\n'

				award_panels.append([count,award_buffer])

			for count,panel_buffer in sorted(award_panels,key=lambda x: x[0],reverse=True):

				html_buffer += panel_buffer

			html_buffer += '</div>\n'
			html_buffer += '</div>\n'

		else:
			html_buffer += '<p> Empty, no league awards to be found :(</p>\n'
	
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	html_buffer += '<script>\n'
	html_buffer += 'function openLeague(evt, leagueName) {\n'
	html_buffer += 'var i, x, tablinks;\n'
	html_buffer += 'x = document.getElementsByClassName("league");\n'
	html_buffer += 'for (i = 0; i < x.length; i++) {\n'
	html_buffer += 'x[i].style.display = "none";\n'
	html_buffer += '}\n'
	html_buffer += 'tablinks = document.getElementsByClassName("tablink");\n'
	html_buffer += 'for (i = 0; i < x.length; i++) {\n'
	html_buffer += 'tablinks[i].className = tablinks[i].className.replace(" w3-aqua", "");\n'
	html_buffer += '}\n'
	html_buffer += 'document.getElementById(leagueName).style.display = "block";\n'
	html_buffer += 'evt.currentTarget.className += " w3-aqua";\n'
	html_buffer += '}\n'
	html_buffer += '</script>\n'

	return html_buffer

def create_managerpage(api,man,leagues):
	mout.debugOut(f"create_managerpage({man.name})")

	'''

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
	'''

	# Awards

	gw = api._current_gw

	html_buffer = ''
	
	title_str = f"{man.name}'s " f'"{man.team_name}"'

	html_buffer += create_manager_formation(man,gw)

	# season stats
	html_buffer += '<div class="w3-col s12 m6 l4">\n'
	html_buffer += '<div class="w3-panel w3-center w3-white w3-padding shadow89">\n'
	html_buffer += f'<h2>{api._season_str_fmt} Season</h2>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Total Score: {man.total_livescore}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Overall Rank: {api.big_number_format(man.overall_rank)}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Avg. Player Selection: {man.avg_selection:.1f}%</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Team Value: £{man.team_value}M</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">#hits: {man.num_hits}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">#transfers: {man.num_nonwc_transfers}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Total Transfer Gain: {man.total_transfer_gain}</span>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	# gw
	html_buffer += '<div class="w3-col s12 m6 l4">\n'
	html_buffer += '<div class="w3-panel w3-center w3-white w3-padding shadow89">\n'
	html_buffer += f'<h2>GW{gw}</h2>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Score: {man.livescore}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Rank: {api.big_number_format(man.gw_rank)}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Rank Gain: {man.gw_rank_gain:.1%}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">xG: {man.gw_xg:.1f}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">xA: {man.gw_xa:.1f}</span>\n'
	html_buffer += f'<span class="w3-tag" style="margin-bottom:4px">Performed xPts: {man.gw_performed_xpts:.1f}</span>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'
	
	# external links
	html_buffer += '<div class="w3-col s12 m12 l4">\n'
	html_buffer += '<div class="w3-panel w3-center w3-indigo w3-padding shadow89">\n'
	url = man.fpl_event_url
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">🗓️ FPL Event</a>\n'
	url = man.fpl_history_url
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">📈 FPL GW History</a>\n'
	html_buffer += f'<a class="w3-bar-item w3-button w3-hover-blue">ID: {man.id}</a>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	html_buffer += floating_subtitle('🏆 Trophy Cabinet',pad=1)
	
	html_buffer += '<div class="w3-col s12 m12 l12">\n'
	html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;">\n'
	html_buffer += create_trophycabinet(api, man)
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'
	
	if any(man._chip_dict.values()):
		html_buffer += floating_subtitle('Chips')

		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
		html_buffer += create_chip_table(api,man)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'
		
	if api._current_gw > 0:
		html_buffer += floating_subtitle('Picks')

		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
		html_buffer += create_picks_table(api, man.squad.sorted_players, manager=man)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

		now_gw = api._current_gw
		end_gw = min(38,now_gw+5)

		### GRAPH
		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white shadow89 w3-responsive w3-padding" id="graphDiv" style="display:block;">\n'
		
		# html_buffer += f'<h3>Expected Points Graph</h3>\n'
		html_buffer += f'<div id="comparisonGraph" style="width:100%;height:500px">\n'
		html_buffer += f'</div>\n'

		html_buffer += f'</div>\n'
		html_buffer += f'</div>\n'

		### BUILD THE PLOTTING DATA
		gw_indices = [i+1 for i in range(now_gw,end_gw+1)]
		gw_strs = [f'GW{i+1}' for i in range(now_gw,end_gw+1)]

		plot_data = []
		player_id_to_trace_id = {}
		for i,p in enumerate(man.squad.sorted_players):

			player_id_to_trace_id[p.id] = i

			plot_y = [round(p.expected_points(gw=i),1) for i in gw_indices]

			plot_data.append(dict(
				name=p.name,
				x=gw_strs,
				y=plot_y,
				visible=True,
				mode='lines+markers',
			))

		### CREATE THE GRAPH
		html_buffer += '<script>\n'
		html_buffer += '	GRAPH = document.getElementById("comparisonGraph");\n'
		html_buffer += f'	Plotly.newPlot( GRAPH, {js.dumps(plot_data)}'
		html_buffer += ', {	title: "Expected Points", margin: { r:0 }, font: {size: 14}} , {responsive: true});\n'
		html_buffer += '</script>\n'

		# if int(man.id) == 780664:
		# 	html_buffer += '<h2>Watchlist</h2>\n'
		# 	html_buffer += create_picks_table(api, squad.sorted_players, manager=None)

		html_buffer += floating_subtitle('History')

		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
		html_buffer += create_manager_history_table(api,man)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	if len(man._graph_paths) > 0:

		html_buffer += floating_subtitle('Graphs')

		for path in man._graph_paths:
			html_buffer += '<div class="w3-col s12 m12 l6">\n'
			html_buffer += '<div class="w3-panel w3-center w3-white shadow89" style="padding:0px;padding-bottom:4px;">\n'
			html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{path}?raw=true" alt="Manager Graph">\n'
			html_buffer += '</div>\n'
			html_buffer += '</div>\n'
		
	navbar = create_navbar(leagues)

	style = api.create_team_styles_css()
	html_page(man.gui_path,None,title=title_str, gw=gw, html=html_buffer, showtitle=True,bar_html=navbar, colour='blue-gray', extra_style=style, plotly=True)

def create_manager_formation(man,gw):

	html_buffer = ''

	html_buffer += '<div class="w3-col s12 m12 l12">\n'
	html_buffer += '<div class="w3-center w3-padding">\n'
	html_buffer += '<div style="text-align:center;width:90%;max-width:900px;display:block;margin-left:auto;margin-right:auto;">\n'

	last_pos_id = 1
	for p in man.squad.sorted_players:

		if p.multiplier == 0:
			continue

		if last_pos_id != p.position_id:
			html_buffer += '</div>\n'
			html_buffer += '<div style="text-align:center;width:90%;max-width:900px;display:block;margin-left:auto;margin-right:auto;">\n'

		html_buffer += '<div style="width:18%;display:inline-block;text-align:center;vertical-align:top;padding:0px;padding-top:16px;padding-left:2px;padding-right:2px;">\n'

		html_buffer += f'<img class="w3-image" style="width:80%;display:block;margin-left:auto;margin-right:auto;" src="{p._photo_url}?raw=true"></img>\n'
		
		score = p.get_event_score(gw)

		style_str = get_style_from_event_score(score).rstrip('"')+';width:100%;padding:0px;padding-top:2px;padding-bottom:6px;"'
		
		if p.multiplier == 3:
			c_str = ' (TC)'
		elif p.multiplier == 2:
			c_str = ' (C)'
		elif p.is_vice_captain:
			c_str = ' (VC)'
		else:
			c_str = ''

		html_buffer += f'<div class="w3-tag shadow89 w3-reponsive responsive-text" style={style_str}><b><a href="https://mwinokan.github.io/FPL_GUI/html/player_{p.id}.html">{p.name}</a>{c_str}</b>\n'

		html_buffer += f'<br>\n'
		style_str = get_style_from_event_score(score).rstrip('"')+';width:90%;margin-bottom:2px;"'
		html_buffer += p.event_stat_emojis(gw)

		if score is None:
			html_buffer += f' <b>-</b>\n'
			# print(p,score)
		else:
			html_buffer += f' <b>{p.multiplier*score}pts</b>\n'

		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

		last_pos_id = p.position_id

	## BENCH
	bench = [p for p in man.squad.sorted_players if p.multiplier == 0]

	if bench:
		html_buffer += '</div>\n'
		html_buffer += '<div style="text-align:center;width:90%;max-width:900px;display:block;margin-left:auto;margin-right:auto;">\n'

		for p in bench:
			html_buffer += '<div style="width:18%;display:inline-block;text-align:center;vertical-align:top;padding:0px;padding-top:16px;padding-left:2px;padding-right:2px;">\n'

			html_buffer += f'<img class="w3-image" style="width:80%;display:block;margin-left:auto;margin-right:auto;" src="{p._photo_url}?raw=true"></img>\n'
			
			score = p.get_event_score(gw)

			style_str = get_style_from_event_score(score).rstrip('"')+';width:100%;padding:0px;padding-top:2px;padding-bottom:6px;"'
			
			c_str = ''

			html_buffer += f'<div class="w3-tag shadow89 w3-reponsive responsive-text" style={style_str}><b><a href="https://mwinokan.github.io/FPL_GUI/html/player_{p.id}.html">{p.name}</a>{c_str}</b>\n'

			html_buffer += f'<br>\n'
			style_str = get_style_from_event_score(score).rstrip('"')+';width:90%;margin-bottom:2px;"'
			html_buffer += p.event_stat_emojis(gw)

			if score is None:
				html_buffer += f' <b>-</b>\n'
			else:
				html_buffer += f' <b>{score}pts</b>\n'

			html_buffer += '</div>\n'
			html_buffer += '</div>\n'

	html_buffer += '</div>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	return html_buffer

def create_manager_history_table(api,man):
	html_buffer = ""
	
	html_buffer += '<div class="w3-responsive">\n'
	html_buffer += '<table class="w3-table w3-hoverable">\n'
	# html_buffer += '<table class="w3-table w3-border w3-hoverable">\n'
	
	html_buffer += '<tr>\n'
	html_buffer += '<th class="w3-center">GW</th>\n'
	html_buffer += '<th class="w3-center">Score</th>\n'
	html_buffer += '<th class="w3-center">Overall Rank</th>\n'
	html_buffer += '<th class="w3-center">GW Score</th>\n'
	html_buffer += '<th class="w3-center">GW Rank</th>\n'
	# html_buffer += '<th class="w3-center">Captain</th>\n'
	# html_buffer += '<th class="w3-center">Bench Points</th>\n'
	html_buffer += '<th class="w3-center">Transfers Taken</th>\n'
	# html_buffer += '<th class="w3-center">Avg.Selection</th>\n'
	html_buffer += '<th class="w3-center">Total Value</th>\n'
	html_buffer += '</tr>\n'

	now_gw = api._current_gw
	start_gw = 0
	delta = 0

	if len(man._overall_rank) < now_gw:
		start_gw = now_gw - len(man._overall_rank)
	
	for i in range(now_gw,start_gw,-1):
		j = i - start_gw
		html_buffer += '<tr>\n'
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
		# html_buffer += f'<td class="w3-center">Captain</td>\n'
		# html_buffer += f'<td class="w3-center">Bench Points</td>\n'
		transfer_str = man.get_transfer_str(j).replace("\n","<br>").replace('**WC**','<strong>WC</strong>')
		if transfer_str.startswith('<br>'):
			transfer_str = transfer_str[4:]
		html_buffer += f'<td>{transfer_str}</td>\n'
		# html_buffer += f'<td class="w3-center">{man.avg_selection:.1f}%</td>\n'
		html_buffer += f'<td class="w3-center">£{man._squad_value[j-1]:.1f}</td>\n'
		html_buffer += '</tr>\n'

	html_buffer += '</table>\n'
	html_buffer += '</div>\n'

	return html_buffer

def create_chip_table(api,man):

	html_buffer = ""


	chips = [v for v in man._chip_dict.items() if v[1] is not None]

	chips = sorted(chips,key=lambda x: x[1])

	if len(chips) > 0:

		# html_buffer += '<h2>Chips</h2>\n'

		html_buffer += '<div class="w3-responsive">\n'
		html_buffer += '<table class="w3-table w3-border w3-hoverable">\n'

		html_buffer += '<tr>\n'
		html_buffer += f'<th class="w3-center">Chip</th>\n'
		html_buffer += f'<th class="w3-center">GW</th>\n'
		html_buffer += f'<th class="w3-center">Detail</th>\n'
		html_buffer += '</tr>\n'
		
		for chip in chips:

			chip_html = ""

			match chip[0]:
				case 'wc1':
					color = 'red'
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
					detail += f'({delta}% OR)'

				case 'wc2':
					color = 'red'
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
					detail += f'({delta}% OR)'
				case 'fh':
					color = 'green'
					pts = man.get_event_score(chip[1])
					rank = [r for i,r in zip(man.active_gws,man._event_rank) if i == chip[1]][0]
					detail = f"GW Points: {pts}, GW Rank: {api.big_number_format(rank)}"
				case 'bb':
					color = 'blue'
					pts = man._bb_ptsgain
					if pts > 0:
						detail = f"+{pts} points gained"
					else:
						detail = f"{pts} points lost"
				case 'tc':
					color = 'amber'
					old_squad = man._squad
					squad = man.get_current_squad(gw=chip[1],force=True)
					if squad is None:
						mout.warningOut(f"Squad is none for GW{chip[1]} (manager {man.id})")
						detail = f"-"
						break

					pts_delta = squad.captain.get_event_score(gw=chip[1],not_playing_is_none=False)
					if pts_delta > 0:
						detail = f"+{pts_delta} points gained"
					else:
						detail = f"{pts_delta} points lost"

					detail += f'with {man._tc_name}'

					man._squad = old_squad
				case _:
					color = 'black'
					detail = f"-"

			chip_html += '<tr>\n'
			chip_html += f'<td class="w3-center w3-{color}">{man._chip_names[chip[0]]}</td>\n'
			chip_html += f'<td class="w3-center">{chip[1]}</td>\n'
			chip_html += f'<td class="w3-center">{detail}</td>\n'
			chip_html += '</tr>\n'

			html_buffer += chip_html

		html_buffer += f'</table>\n'
		html_buffer += f'</div>\n'

	return html_buffer

def create_picks_table(api,players,prev_gw_count=5,next_gw_count=5,manager=None):

	html_buffer = ""

	html_buffer += '<div class="w3-responsive">\n'
	html_buffer += '<table class="w3-table responsive-text">\n'

	now_gw = api._current_gw
	start_gw = max(1,now_gw-prev_gw_count)
	end_gw = min(38,now_gw+next_gw_count)
	
	html_buffer += '<tr>\n'
	html_buffer += f'<th class="w3-center">Pos</th>\n'
	html_buffer += f'<th class="w3-center">Team</th>\n'
	html_buffer += f'<th>Name</th>\n'
	html_buffer += f'<th class="w3-center">Price</th>\n'
	html_buffer += f'<th class="w3-center">ΣPts</th>\n'
	html_buffer += f'<th class="w3-center">Trans.</th>\n'
	for i in range(start_gw,now_gw+1):
		html_buffer += f'<th class="w3-center">GW{i}</th>\n'
	html_buffer += f'<th class="w3-center">Form</th>\n'
	for i in range(now_gw+1,end_gw+1):
		html_buffer += f'<th class="w3-center">GW{i}</th>\n'
	html_buffer += '</tr>\n'

	for player in players:
		html_buffer += '<tr>\n'

		### Styled based on team

		bg_color = player.team_obj.get_style()['background-color']
		text_color = player.team_obj.get_style()['color']
		style_str = f'"background-color:{bg_color};color:{text_color};vertical-align:middle;"'

		html_buffer += f'<td class="w3-center" style={style_str}><b>{["GKP","DEF","MID","FWD"][player.position_id-1]}</b></td>\n'
		html_buffer += f'<td class="w3-center" style={style_str}><b>{player.shortteam}</b></td>\n'
		html_buffer += f'<td style={style_str}><b>'
		if player.is_captain:
			html_buffer += f'(C) '
		if player.is_yellow_flagged:
			html_buffer += f'⚠️ '
		elif player.is_red_flagged:
			html_buffer += f'⛔️ '
		if player.was_subbed:
			html_buffer += f'🔄 '
		html_buffer += f'<a href="https://mwinokan.github.io/FPL_GUI/html/player_{player.id}.html">{player.name}</a></b></td>\n'

		###

		if player.name in [p[0].name for p in risers]:
			style_str = '"color:green;vertical-align:middle;"'
		elif player.name in [p[0].name for p in fallers]:
			style_str = '"color:red;vertical-align:middle;"'
		else:
			style_str = None

		if style_str is None:
			html_buffer += f'<td class="w3-center" style="vertical-align:middle;">£{player.price}</td>\n'
		else:
			html_buffer += f'<td class="w3-center" style={style_str}><b>£{player.price}</b></td>\n'

		if player.appearances < 1:
			score = 0.0
		else:
			score = player.total_points/player.appearances
		style_str = get_style_from_event_score(score).rstrip('"')+';vertical-align:middle;"'
		html_buffer += f'<td class="w3-center" style={style_str}>{player.total_points}</td>\n'

		value = player.transfer_percent
		text = f'{player.transfer_percent:.1f}%'
		if abs(value) > 10:
			if text.startswith("-"):
				style_str = '"color:darkred;vertical-align:middle;"'
			else:
				style_str = '"color:darkgreen;vertical-align:middle;"'
			html_buffer += f'<td class="w3-center" style={style_str}><b>{text}</b></td>\n'
		else:
			if text.startswith("-"):
				style_str = '"color:red;vertical-align:middle;"'
			else:
				style_str = '"color:green;vertical-align:middle;"'
			html_buffer += f'<td class="w3-center" style={style_str}>{text}</td>\n'

		for i in range(start_gw,now_gw+1):
			html_buffer += player_summary_cell_modal(player,i)

		form = player.form
		style_str = get_style_from_event_score(form).rstrip('"')+';vertical-align:middle;"'
		html_buffer += f'<td class="w3-center" style={style_str}>{player.form}</td>\n'

		for i in range(now_gw+1,end_gw+1):
			exp = player.expected_points(gw=i,debug=False)
			style_str = get_style_from_event_score(exp).rstrip('"')+';vertical-align:middle;"'
			assert style_str is not None
			flag_str = ""
			chance = player.get_playing_chance(i)
			if chance < 0.25:
				flag_str = '⛔️ '
			elif chance < 1:
				flag_str = '⚠️ '
			# html_buffer += f'<td class="w3-center" style={style_str}>{flag_str}{player.get_fixture_str(i,short=True,lower_away=True)} ({exp:.1f})</td>\n'
			html_buffer += f'<td class="w3-center" style={style_str}>{flag_str}{player.get_fixture_str(i,short=True,lower_away=True)}</td>\n'

		html_buffer += '</tr>\n'

	if manager is not None:

		html_buffer += '<tr>\n'
		#pos
		html_buffer += f'<td class="w3-center" style="vertical-align:middle;"></td>\n'
		#team
		html_buffer += f'<td class="w3-center" style="vertical-align:middle;"></td>\n'
		#name
		html_buffer += f'<td class="w3-center" style="vertical-align:middle;">{manager.name}</td>\n'
		#price
		html_buffer += f'<td class="w3-center" style="vertical-align:middle;">£{manager.team_value:.1f}</td>\n'
		#points
		score = manager.score
		style_str = get_style_from_event_score(score/12/now_gw).rstrip('"')+';vertical-align:middle;"'
		html_buffer += f'<td class="w3-center" style={style_str}>{score:1}</td>\n'
		#transfers
		html_buffer += f'<td class="w3-center" style="vertical-align:middle;"> </td>\n'
		#previous + live
		for i in range(start_gw,now_gw+1):
			score = manager.get_event_score(gw=i)
			style_str = get_style_from_event_score(score/12).rstrip('"')+';vertical-align:middle;"'
			html_buffer += f'<td class="w3-center" style={style_str}>{score:1n}</td>\n'
		#form
		form = sum([p.form for p in players])
		style_str = get_style_from_event_score(form/len(players)).rstrip('"')+';vertical-align:middle;"'
		html_buffer += f'<td class="w3-center" style={style_str}>{form:.1f}</td>\n'
		#upcoming
		for i in range(now_gw+1,end_gw+1):
			manager.squad.set_best_multipliers(gw=i)
			exp = manager.squad.expected_points(gw=i)
			style_str = get_style_from_event_score(exp/12).rstrip('"')+';vertical-align:middle;"'
			html_buffer += f'<td class="w3-center" style={style_str}>{exp:.1f}</td>\n'
		html_buffer += '</tr>\n'

	html_buffer += '</table>\n'
	html_buffer += '</div>\n'

	return html_buffer

def create_manager_pick_history(api,man):

	squad = man.get_squad_history()

	for p in squad.players:
		# print(p,p._points_while_started,p._points_while_owned,p.total_points,p._weeks_owned,p._weeks_started)
		print(f'{p.name.rjust(20)} {p._num_weeks_owned:2n} started:{p._avg_pts_started} benched:{p._avg_pts_benched} total:{p._avg_pts_total}')
		# print(f'{p.name.rjust(20)} {p._num_weeks_owned:2n} started/owned={100*p._points_while_started/p._points_while_owned if p._points_while_owned > 0 else 0:5.1f}% owned/total={100*p._points_while_started/p.total_points:5.1f}%')

	for p in squad.players:
		print(f'{p.name.rjust(20)}',end=' ')
		for gw in man.active_gws:
			if gw in p._weeks_captained:
				print("C",end='')
			elif gw in p._weeks_started:
				print("*",end='')
			elif gw in p._weeks_benched:
				print("-",end='')
			else:
				print(" ",end='')
		print(" ")

def get_style_from_difficulty(difficulty,old=False):

	style_str = '"'

	if old:

		# difficulty = round(difficulty+1)

		if difficulty == 1:
			style_str += 'background-color:darkgreen;color:white'
		elif difficulty == 2:
			style_str += 'background-color:lightgreen;color:black'
		elif difficulty == 3:
			pass
		elif difficulty == 4:
			style_str += 'background-color:red;color:black'
		elif difficulty == 5:
			style_str += 'background-color:darkred;color:white'
	else:
		if not isinstance(difficulty,float):
			style_str += 'background-color: black;""color:white'
			return style_str

		if abs(difficulty) < 1.0:
			style_str += 'background-color:white;color:black'
		elif difficulty > 0.0:
			if difficulty < 2.0:
				style_str += 'background-color:lightgreen;color:black'
			else:
				style_str += 'background-color:darkgreen;color:white'
		elif difficulty < 0.0:
			if difficulty > -2.0:
				style_str += 'background-color:red;color:black'
			else:
				style_str += 'background-color:darkred;color:white'
		
	style_str += '"'
	return style_str

def get_style_from_game_score(is_home,team_h_score,team_a_score):

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
			style_str += 'background-color:darkgreen;color:white'
		else:
			style_str += 'background-color:lightgreen;color:black'
	elif not draw:
		if opp_clean_sheet:
			style_str += 'background-color:darkred;color:white'
		else:
			style_str += 'background-color:red;color:black'
	else:
		style_str += 'background-color:white;color:black'
	style_str += '"'

	return style_str

def get_manager_json_positions(api,leagues):

	for l_id,l_data in json.items():

		if l_id == 'timestamp':
			continue

		l_name = [l.name for l in leagues if l.id == int(l_id)][0]

		for gw_id, gw_data in l_data.items():

			for d_id, d_data in gw_data.items():

				if d_id == 'positions':
					
					for m_id, m_pos in d_data.items():

						m_id = int(m_id)

						if m_id not in api._managers.keys():
							# mout.warningOut(f'{m_id} not in api._managers')
							continue

						m = api.get_manager(id=m_id)

						if l_name not in m._league_positions.keys():
							m._league_positions[l_name] = {}

						m._league_positions[l_name][gw_id] = m_pos

# @mout.debug_log
def get_manager_json_awards(api,leagues):

	# print(json)

	for l_id,l_data in json.items():

		if l_id == 'timestamp':
			continue

		l_name = [l.name for l in leagues if l.id == int(l_id)][0]

		for gw_id, gw_data in l_data.items():

			if 'half' in gw_id:

				for key,data in gw_data['awards'].items():

					# print(key,data)

					for m_id in data[0]:
						m = api.get_manager(id=m_id)
						m._awards.append(dict(key=key,score=data[-1],league=l_name,gw='half'))

				continue

			if 'season' in gw_id:

				for key,data in gw_data['awards'].items():

					# print(key,data)

					for m_id in data[0]:
						m = api.get_manager(id=m_id)
						m._awards.append(dict(key=key,score=data[-1],league=l_name,gw='season'))

				continue

			if 'chips' in gw_id:

				for key,data in gw_data.items():
					for key2,data2 in data.items():

						for m_id in data2[1]:
							m = api.get_manager(id=m_id)
							m._awards.append(dict(key=f'{key}_{key2}',score=data2[0],league=l_name,gw='chips'))

				continue

			for d_id, d_data in gw_data.items():

				if d_id == 'awards':

					for key,data in d_data.items():

						if data is None:
							continue

						if key == 'scientist':
							if data[0] in api._managers.keys():
								m = api.get_manager(id=data[0])
								m._awards.append(dict(key=key,player=data[1],is_captain=data[2],score=data[3],gw=gw_id,league=l_name))
						else:
							subset = data[0:-1]
							# print(subset)
							# print(key)
							# print(data)
							for id in subset:
								if id in api._managers.keys():
									m = api.get_manager(id=id)
									m._awards.append(dict(key=key,score=data[-1],gw=gw_id,league=l_name))

def fixture_table(api,gw):

	html_buffer = ""

	fixtures = api.get_gw_fixtures(gw)

	if len(fixtures) < 1:
		html_buffer += '<div class="w3-center">'
		html_buffer += f'<h2>GW{gw}</h2>'
		html_buffer += f'<strong>No fixtures!</strong>'
		html_buffer += '</div>'
		return html_buffer

	# f = api.get_gw_fixtures(gw)
	# fixtures = []
	# for i,c in enumerate(f['code']):
	# 	this_fix = dict(index=i,finished=f['finished'][i],started=f['started'][i],team_a=f['team_a'][i],team_h=f['team_h'][i],team_a_score=f['team_a_score'][i],team_h_score=f['team_h_score'][i],kickoff=f['kickoff_time'][i])
	# 	fixtures.append(this_fix)

	html_buffer += '<div class="w3-center">'
	html_buffer += f'<h2>GW{gw} Fixtures</h2>'
	html_buffer += '</div>'
	html_buffer += '<div class="w3-responsive">'
	html_buffer += '<table class="w3-table w3-hoverable responsive-text">'
	# html_buffer += '<table class="w3-table w3-small w3-hoverable">'

	new = True
	for i,fix in enumerate(fixtures):
		fix['date_str'] = fix['kickoff'].split("T")[0]
		fix['day_str'] = datetime.strptime(fix['kickoff'], '%Y-%m-%dT%H:%M:%SZ').strftime('%A')

		if not new and fix['day_str'] != fixtures[i-1]['day_str']:
			new = True

		if new:
			html_buffer += '<tr>'
			html_buffer += f'<td class="w3-right"></td>'
			html_buffer += f'<td class="w3-center"><h4>{fix["day_str"]}</h4></td>'
			html_buffer += f'<td></td>'
			html_buffer += '</tr>'
			new = False

		team_h_obj = api.get_player_team_obj(fix['team_h'])
		team_a_obj = api.get_player_team_obj(fix['team_a'])
		# pred_h_score = (team_a_obj.goals_conceded_per_game + team_h_obj.goals_scored_per_game)/2 * (1-team_a_obj.expected_clean_sheet(team_h_obj))
		# pred_a_score = (team_h_obj.goals_conceded_per_game + team_a_obj.goals_scored_per_game)/2 * (1-team_h_obj.expected_clean_sheet(team_a_obj))

		html_buffer += '<tr>'
		# url = f'https://github.com/mwinokan/FPL_GUI/blob/main/{p.team_obj._badge_path}'
		html_buffer += f'<td class="w3-right">{team_h_obj._shortname}\t<img class="w3-image" src="{team_h_obj._badge_url}" alt="Team" width="30" height="30"></td>'
		if not fix['started']:
			local_tz = pytz.timezone("Europe/London")
			utc_dt = datetime.strptime(fix['kickoff'], '%Y-%m-%dT%H:%M:%SZ')
			utc_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
			time_str = utc_dt.strftime('%H:%M')
			html_buffer += f'<td class="w3-center">{time_str}</td>'
			# html_buffer += f'<td class="w3-center">{time_str} ({pred_h_score:.0f} - {pred_a_score:.0f})</td>'
		# elif not fix['started']:
		# 	html_buffer += f'<td class="w3-center w3-text-green"><b>{fix["team_h_score"]:.0f} - {fix["team_a_score"]:.0f}</b></td>'
		else:

			team_h_score = fix["team_h_score"]
			team_a_score = fix["team_a_score"]

			html_buffer += f'<td class="w3-center"><b>{team_h_score:.0f} - {team_a_score:.0f}</b></td>'
			# print(team_h_obj._shortname,team_a_obj._shortname)
			# print(f"Real: {team_h_score:.0f} {team_a_score:.0f}")
			# print(f"Pred: {pred_h_score:.0f} {pred_a_score:.0f}")

			# if team_h_score == team_a_score:
			# 	real_result = 'D'
			# elif team_h_score > team_a_score:
			# 	real_result = 'H'
			# else:
			# 	real_result = 'A'

			# if round(pred_h_score,0) == round(pred_a_score,0):
			# 	pred_result = 'D'
			# elif round(pred_h_score,0) > round(pred_a_score,0):
			# 	pred_result = 'H'
			# else:
			# 	pred_result = 'A'

			# if real_result == pred_result:
			# 	result = True
			# else:
			# 	result = False

			# print(f"Result: {result}")
			# print(f"d#Goals: {team_h_score+team_a_score-pred_h_score-pred_a_score:.1f}")

			# 	if round((team_a_obj.goals_conceded_per_game + team_h_obj.goals_scored_per_game)/2,0) == round((team_h_obj.goals_conceded_per_game + team_a_obj.goals_scored_per_game),0):
			# 		result = True
			# 	else:
			# 		result = False
			# print(f"Predicted: {(team_a_obj.goals_conceded_per_game + team_h_obj.goals_scored_per_game)/2:.1f} {(team_h_obj.goals_conceded_per_game + team_a_obj.goals_scored_per_game)/2:.1f}")
			# print(f"xClean: {team_h_obj.expected_clean_sheet(team_a_obj):.1f} {team_a_obj.expected_clean_sheet(team_h_obj):.1f}")
			# print("")
		html_buffer += f'<td><img class="w3-image" src="{team_a_obj._badge_url}" alt="Team" width="30" height="30">\t{team_a_obj._shortname}</td>'
		html_buffer += '</tr>'

	html_buffer += '</table>'
	html_buffer += '</div>'

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

	key = league.name.replace(" ","")

	# if gw > 0:
	# 	# gw score vs league average (global average)
	# 	# graph_captain_points = plot.captain_points(league.managers,key, show=False)
	# 	# graph_event_points = plot.event_points(league.managers,key=key,relative=True,show=False)
	# 	# graph_player_selection = plot.player_selection(league.managers,key=key,show=False)
	# 	# graph_gw_rank = plot.gameweek_rank(league.managers,key=key,show=False)
	# 	# graph_overall_rank = plot.overall_rank(league.managers,key=key,show=False)
	# 	pass

	graph_past_rank = plot.rank_history(league.managers,key, show=False)

def create_sidebar(leagues):
	url = f'https://mwinokan.github.io/FPL_GUI/index.html'
	md_buffer = f"##### [Home]({url})\n\n"

	url = f'https://mwinokan.github.io/FPL_GUI/html/fixtures.html'
	md_buffer += f"##### [Fixtures]({url})\n\n"

	md_buffer += f"##### League Summaries\n\n"
	for l in leagues:
		url = f'https://mwinokan.github.io/FPL_GUI/html/{l.name.replace(" ","-")}.html'
		md_buffer += f'* [{l}]({url})\n'

	return md_buffer

def previous_player_table(min_minutes=200,show_top=10):

	html_buffer = ""

	# print(api._prev_elements.columns)

	temp_elements = api._prev_elements[[
		'element_type',
		'first_name',
		'now_cost',
		'second_name',
		'web_name',
		'photo',
		'team',
		'team_code',
		
		'total_points',
		'minutes',

		'goals_scored',
		'assists',
		'clean_sheets',
		'goals_conceded',
		'own_goals',
		'penalties_saved',
		'penalties_missed',
		'yellow_cards',
		'red_cards',
		'saves',
		'bonus',
		'starts',
		'expected_goals',
		'expected_assists',
		'expected_goal_involvements',
		'expected_goals_conceded',

		'expected_goals_per_90',
		'saves_per_90',
		'expected_assists_per_90',
		'expected_goal_involvements_per_90',
		'expected_goals_conceded_per_90',
		'goals_conceded_per_90',
		
		'points_per_game_rank',
		'points_per_game_rank_type',
		'starts_per_90',
		'clean_sheets_per_90',
	]]

	temp_elements[temp_elements['minutes'] > min_minutes]

	# top scoring by position

	show_columns = {
		1: ('starts','clean_sheets_per_90'),
	}

	def stat_spans(pd):
		buffer = ""
		if pd["goals_scored"] > 0:
			buffer += f'<span class="w3-tag w3-green">{pd["goals_scored"]} goals</span>\n'

		if pd["assists"] > 0:
			buffer += f'<span class="w3-tag w3-blue">{pd["assists"]} assists</span>\n'

		# if pd["own_goals"] > 0:
		# 	buffer += f'<span class="w3-tag w3-black">{pd["own_goals"]} own goals</span>\n'

		if pd["yellow_cards"] > 0:
			buffer += f'<span class="w3-tag w3-yellow">{pd["yellow_cards"]} yellow cards</span>\n'

		if pd["red_cards"] > 0:
			buffer += f'<span class="w3-tag w3-red">{pd["red_cards"]} red cards</span>\n'

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
			buffer += f'<span class="w3-tag w3-dark-grey">{pd["minutes"]:.0f} mins</span>\n'
		return buffer

	for i in range(4):

		table_buffer = ""

		html_buffer += '<div class="w3-col s12 m12 l6">\n'
		# html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'

		table_buffer += '<table class="w3-table w3-bordered responsive-text">\n'
		table_buffer += '<tr>\n'
		table_buffer += '<th>Player</th>\n'
		table_buffer += '<th>Points</th>\n'
		table_buffer += '<th class="w3-center">Stats</th>\n'
		table_buffer += '</tr>\n'

		elements = temp_elements[temp_elements['element_type'] == i+1]
		elements = elements.sort_values(by=['total_points'],ascending=False)

		for j in range(show_top-1):

			pd = elements.iloc[j+1]

			name = f'<b>{pd["web_name"]}</b>'
			tot_pts = f'{pd["total_points"]}'

			# table_buffer += f'<tr class="w3-{api._short_team_pairs[pd["team_code"]-1].lower()}">\n'
			table_buffer += f'<tr>\n'

			# table_buffer += f'<td><img class="w3-image" style="height:20px" src="https://resources.premierleague.com/premierleague/photos/players/110x140/p{pd["photo"].replace(".jpg",".png")}"></img>\n'
			table_buffer += f'<td>\n'
			table_buffer += f'{name}</td>\n'
			table_buffer += f'<td>{tot_pts}</td>\n'

			table_buffer += f'<td>\n'

			table_buffer += stat_spans(pd)
			
			table_buffer += '</td>\n'
			table_buffer += '</tr>\n'

		table_buffer += '</table>\n'

		# photo_url = f'https://resources.premierleague.com/premierleague/photos/players/110x140/p{player_data["photo"].replace(".jpg",".png")}'


		pd = elements.iloc[0]

		html_buffer += f'<div class="w3-panel w3-{api._short_team_pairs[pd["team_code"]-1].lower()}-inv shadow89" style="padding:0px;padding-bottom:4px;">\n'
		html_buffer += f'<div class="w3-center">\n'
		html_buffer += f"<h2>Best {['Goalkeeper','Defender','Midfielder','Forward'][i]}</h2>"

		html_buffer += f'<h2>{pd["web_name"]}: {pd["total_points"]} points</h2>'
		# html_buffer += f'{pd["team_code"]}</h2>'

		html_buffer += f'<img class="w3-image" style="width:30%" src="https://resources.premierleague.com/premierleague/photos/players/110x140/p{pd["photo"].replace(".jpg",".png")}"></img>\n'

		html_buffer += f'<div class="w3-panel w3-{api._short_team_pairs[pd["team_code"]-1].lower()} w3-padding-large">\n'
		html_buffer += stat_spans(pd)
		html_buffer += f'</div>\n' # panel

		html_buffer += f'</div>\n' # center

		html_buffer += table_buffer

		html_buffer += '</div>\n' # panel
		html_buffer += '</div>\n' # col

		# exit()

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

	html_buffer += ''

	# tagline
	html_buffer += '<div class="w3-col s12 m12 l4">\n'
	html_buffer += '<div class="w3-panel w3-amber w3-center w3-padding shadow89">\n'
	html_buffer += '<h3>Home of the RBS Diamond Invitational and Tesco Bean Value Toilet League</h3>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	# navigation links
	html_buffer += '<div class="w3-col s12 m6 l4">\n'
	html_buffer += '<div class="w3-panel w3-center w3-white w3-padding shadow89">\n'
	html_buffer += '\n'.join(navbar.split('\n')[7:-9])
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	# external links
	html_buffer += '<div class="w3-col s12 m6 l4">\n'
	html_buffer += '<div class="w3-panel w3-center w3-indigo w3-padding shadow89">\n'
	url = 'https://www.facebook.com/groups/1488748394903477/'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">🗯️ Facebook Group</a>\n'
	url = 'https://github.com/mwinokan/FPL_GUI/issues/new'
	html_buffer += f'<a href="{url}" class="w3-bar-item w3-button w3-hover-blue">❓ Feature Request</a>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	if preseason:

		# table of total player information
		html_buffer += floating_subtitle('22/23 Top Assets',pad=0)

		html_buffer += previous_player_table()

	html_buffer += floating_subtitle('🗓 Fixtures',pad=1 if preseason else 0)

	if gw > 0:
		html_buffer += '<div class="w3-col s12 m12 l6">\n'
		html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
		html_buffer += fixture_table(api, gw)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'
	if gw < 38:
		html_buffer += '<div class="w3-col s12 m12 l6">\n'
		html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
		html_buffer += fixture_table(api, gw+1)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	style = api.create_team_styles_css()
	html_page('index.html', html=html_buffer,title="toilet.football", gw=api._current_gw,bar_html=navbar,colour='aqua',extra_style=style)

		# html_page(f'html/player_{player.id}.html',None,title=f"{player.name}",sidebar_content=None, gw=gw, html=html_buffer, showtitle=False, bar_html=navbar,extra_style=style,colour=player.team_obj.style['accent'],nonw3_colour=True)


def create_seasonpage(leagues):
	mout.debugOut("create_seasonpage()")

	title = f"The RBS Diamond Invitational / Tesco Bean Value Toilet League"

	html_buffer = ""

	html_buffer += '<div class="w3-center">\n'
	html_buffer += f"<h2>{title}</h2>\n"
	# html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/psd/christmas22.png?raw=true" alt="Banner" width="1320" height="702">\n'
	html_buffer += '</div>\n'

	html_buffer += '<div class="w3-bar w3-black">\n'
	
	for i,league in enumerate(leagues[:2]):

		if i == 0:
			html_buffer += f'<button class="w3-bar-item w3-button w3-mobile tablink w3-red" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
		else:
			html_buffer += f'<button class="w3-bar-item w3-mobile w3-button tablink" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
	
	html_buffer += '</div>\n'

	for i,league in enumerate(leagues[:2]):

		if i==0:
			html_buffer += f'<div id="{league.id}" class="w3-container w3-border league">\n'
		else:
			html_buffer += f'<div id="{league.id}" class="w3-container w3-border league" style="display:none">\n'

		html_buffer += '<div class="w3-justify w3-row-padding">\n'

		# html_buffer += "<p>\n"
		# html_buffer += league_season_text[league.id]
		# html_buffer += "</p>\n"

		html_buffer += "<h3>Chip Usage</h3>\n"
		html_buffer += league_best_chips(league)

		award_buffer = ""
		award_buffer += "<h3>Season Awards</h3>\n"
		award_buffer += make_season_awards(league)

		if league.num_managers > 20:
			subset = []
			subset += sum([d[0] for d in json[str(league.id)]['season']['awards'].values()],[])
			subset += sum([d[-1] for d in json[str(league.id)]['chips']['wc2'].values()],[])
		else:
			subset = None

		html_buffer += "<h3>League Graph</h3>\n"
		import sys
		sys.path.insert(1,'go')
		from goleague import create_league_figure
		html_buffer += create_league_figure(api, league, subset)

		html_buffer += award_buffer

		md_buffer = ""
		md_buffer += f"\n## League Table:\n"
		md_buffer += f"Is your team's kit the boring default? Design it [here](https://fantasy.premierleague.com/entry-update)\n\n"
		html_buffer += md2html(md_buffer)
		html_buffer += league_table_html(league, api._current_gw, awardkey='season')
		# html_buffer += _league_table_html[league.id]

		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	html_buffer += '<script>\n'
	html_buffer += 'function openLeague(evt, leagueName) {\n'
	html_buffer += 'var i, x, tablinks;\n'
	html_buffer += 'x = document.getElementsByClassName("league");\n'
	html_buffer += 'for (i = 0; i < x.length; i++) {\n'
	html_buffer += 'x[i].style.display = "none";\n'
	html_buffer += '}\n'
	html_buffer += 'tablinks = document.getElementsByClassName("tablink");\n'
	html_buffer += 'for (i = 0; i < x.length; i++) {\n'
	html_buffer += 'tablinks[i].className = tablinks[i].className.replace(" w3-red", "");\n'
	html_buffer += '}\n'
	html_buffer += 'document.getElementById(leagueName).style.display = "block";\n'
	html_buffer += 'evt.currentTarget.className += " w3-red";\n'
	html_buffer += '}\n'
	html_buffer += '</script>\n'

	navbar = create_navbar(leagues, active='S', colour='black', active_colour='green')
	html_page(f'html/season.html',None,title='22/23 Season Review', gw=api._current_gw, html=html_buffer, bar_html=navbar, showtitle=True,plotly=True)

def create_christmaspage(leagues):
	mout.debugOut("create_christmaspage()")

	# title = f"Christmas Review"
	title = f"The RBS Diamond Invitational / Tesco Bean Value Toilet League"

	html_buffer = ""

	html_buffer += '<div class="w3-center">\n'
	html_buffer += f"<h2>{title}</h2>\n"
	html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/psd/christmas22.png?raw=true" alt="Banner" width="1320" height="702">\n'
	html_buffer += '</div>\n'

	# html_buffer += '<div class="w3-black">\n'
	# html_buffer += "<p>Foreword</p>\n"
	# html_buffer += "<p>Promotion/relegation</p>\n"
	# html_buffer += '</div>\n'
	# html_buffer += "<p>League statistics</p>"

	# html_buffer += '<p><strong>Choose which league awards to show:</strong></p>\n'
	html_buffer += '<div class="w3-bar w3-black">\n'
	
	for i,league in enumerate(leagues[:2]):

		if i == 0:
			html_buffer += f'<button class="w3-bar-item w3-button w3-mobile tablink w3-red" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
		else:
			html_buffer += f'<button class="w3-bar-item w3-mobile w3-button tablink" onclick="openLeague(event,{league.id})">{league.name}</button>\n'
	
	html_buffer += '</div>\n'

	for i,league in enumerate(leagues[:2]):

		if i==0:
			html_buffer += f'<div id="{league.id}" class="w3-container w3-border league">\n'
		else:
			html_buffer += f'<div id="{league.id}" class="w3-container w3-border league" style="display:none">\n'

		html_buffer += '<div class="w3-justify w3-row-padding">\n'

		html_buffer += "<p>\n"
		html_buffer += league_halfway_text[league.id]
		html_buffer += "</p>\n"

		html_buffer += "<h3>Chip Usage</h3>\n"
		html_buffer += league_best_chips(league)

		award_buffer = ""
		award_buffer += "<h3>Halfway Awards</h3>\n"
		award_buffer += christmas_awards(league)

		if league.num_managers > 20:
			subset = []
			subset += sum([d[0] for d in json[str(league.id)]['half']['awards'].values()],[])
			subset += sum([d[-1] for d in json[str(league.id)]['chips']['wc1'].values()],[])
		else:
			subset = None

		html_buffer += "<h3>League Graph</h3>\n"
		import sys
		sys.path.insert(1,'go')
		from goleague import create_league_figure
		html_buffer += create_league_figure(api, league, subset)

		html_buffer += award_buffer

		md_buffer = ""
		md_buffer += f"\n## League Table:\n"
		md_buffer += f"Is your team's kit the boring default? Design it [here](https://fantasy.premierleague.com/entry-update)\n\n"
		html_buffer += md2html(md_buffer)
		html_buffer += _league_table_html[league.id]

		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	html_buffer += '<script>\n'
	html_buffer += 'function openLeague(evt, leagueName) {\n'
	html_buffer += 'var i, x, tablinks;\n'
	html_buffer += 'x = document.getElementsByClassName("league");\n'
	html_buffer += 'for (i = 0; i < x.length; i++) {\n'
	html_buffer += 'x[i].style.display = "none";\n'
	html_buffer += '}\n'
	html_buffer += 'tablinks = document.getElementsByClassName("tablink");\n'
	html_buffer += 'for (i = 0; i < x.length; i++) {\n'
	html_buffer += 'tablinks[i].className = tablinks[i].className.replace(" w3-red", "");\n'
	html_buffer += '}\n'
	html_buffer += 'document.getElementById(leagueName).style.display = "block";\n'
	html_buffer += 'evt.currentTarget.className += " w3-red";\n'
	html_buffer += '}\n'
	html_buffer += '</script>\n'

	navbar = create_navbar(leagues, active='C', colour='black', active_colour='red')
	html_page(f'html/christmas.html',None,title='2022 Christmas Review', gw=api._current_gw, html=html_buffer, bar_html=navbar, showtitle=True,plotly=True)

def manager_ids(mans):
	return [m.id for m in mans]

def league_best_chips(league):

	global json

	html_buffer = ""

	create_key(json[str(league.id)],'chips')

	finished = api._current_gw == 38 and not api._live_gw

	# bench boost
	bb_subset = [m for m in league.managers if m._bb_week]
	bb_best = get_winners("Best BB", bb_subset, lambda x: x._bb_ptsgain)
	bb_worst = get_losers("Worst BB", bb_subset, lambda x: x._bb_ptsgain)
	if finished:
		create_key(json[str(league.id)]['chips'],'bb')
		json[str(league.id)]['chips']['bb']['best'] = [bb_best[0],manager_ids(bb_best[1])]
		json[str(league.id)]['chips']['bb']['worst'] = [bb_worst[0],manager_ids(bb_worst[1])]

	# triple captain
	tc_subset = [m for m in league.managers if m._tc_week]
	tc_best = get_winners("Best TC", tc_subset, lambda x: x._tc_ptsgain)
	tc_worst = get_losers("Worst TC", tc_subset, lambda x: x._tc_ptsgain)
	if finished:
		create_key(json[str(league.id)]['chips'],'tc')
		json[str(league.id)]['chips']['tc']['best'] = [tc_best[0],manager_ids(tc_best[1])]
		json[str(league.id)]['chips']['tc']['worst'] = [tc_worst[0],manager_ids(tc_worst[1])]

	# Free hit
	fh_subset = [m for m in league.managers if m._fh_week]
	fh_best = get_losers("Best fh", fh_subset, lambda x: x._fh_gwrank)
	fh_worst = get_winners("Worst fh", fh_subset, lambda x: x._fh_gwrank)
	if finished:
		create_key(json[str(league.id)]['chips'],'fh')
		json[str(league.id)]['chips']['fh']['best'] = [fh_best[0],manager_ids(fh_best[1])]
		json[str(league.id)]['chips']['fh']['worst'] = [fh_worst[0],manager_ids(fh_worst[1])]

	# First wildcard
	wc1_subset = [m for m in league.managers if m._wc1_week]
	wc1_best = get_winners("Best wc1", wc1_subset, lambda x: x._wc1_ordelta_percent)
	wc1_worst = get_losers("Worst wc1", wc1_subset, lambda x: x._wc1_ordelta_percent)
	create_key(json[str(league.id)]['chips'],'wc1')
	json[str(league.id)]['chips']['wc1']['best'] = [wc1_best[0],manager_ids(wc1_best[1])]
	json[str(league.id)]['chips']['wc1']['worst'] = [wc1_worst[0],manager_ids(wc1_worst[1])]

	# Second wildcard
	wc2_subset = [m for m in league.managers if m._wc2_week]
	wc2_best = get_winners("Best wc2", wc2_subset, lambda x: x._wc2_ordelta_percent)
	wc2_worst = get_losers("Worst wc2", wc2_subset, lambda x: x._wc2_ordelta_percent)
	create_key(json[str(league.id)]['chips'],'wc2')
	json[str(league.id)]['chips']['wc2']['best'] = [wc2_best[0],manager_ids(wc2_best[1])]
	json[str(league.id)]['chips']['wc2']['worst'] = [wc2_worst[0],manager_ids(wc2_worst[1])]

	# table
	html_buffer += '<table class="w3-table-all w3-hoverable">\n'
	html_buffer += '<thead>\n'
	html_buffer += '<tr>\n'

	html_buffer += '<th style="text-align:center;">Chip</th>\n'	
	html_buffer += '<th style="text-align:center;">Best</th>\n'
	html_buffer += f'<th style="text-align:center;">Delta</th>\n'
	html_buffer += '<th style="text-align:center;">Worst</th>\n'
	html_buffer += f'<th style="text-align:center;">Delta</th>\n'
	html_buffer += '</tr>\n'
	html_buffer += '</thead>\n'

	html_buffer += '<tbody>\n'

	### triple captain
	html_buffer += '<tr>\n'
	html_buffer += f'<td class="w3-amber" style="text-align:center;">TC</td>\n'
	html_buffer += f'<td style="text-align:center;">\n'
	for i,man in enumerate(tc_best[1]):
		if i != 0:
			html_buffer += "<br>\n"
		html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
		if 'Toilet' in league.name and man.is_diamond:
			html_buffer += "💎"
		html_buffer += f'with {man._tc_name} in GW{man._tc_week}\n'

		# html_buffer += f'<a href="https://mwinokan.github.io/FPL_GUI/html/player_{player.id}.html">{player.name}</a></b></td>\n'

	html_buffer +='</td>\n'
	html_buffer += f'<td style="text-align:center;">{pts_delta_format(tc_best[0])}</td>\n'
	if len(tc_subset) == 1:
		html_buffer += f'<td></td>\n'
		html_buffer += f'<td></td>\n'
	else:
		html_buffer += f'<td style="text-align:center;">\n'
		for i,man in enumerate(tc_worst[1]):
			if i != 0:
				html_buffer += "<br>\n"
			html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
			if 'Toilet' in league.name and man.is_diamond:
				html_buffer += "💎"
			html_buffer += f'with {man._tc_name} in GW{man._tc_week}\n'
		html_buffer +='</td>\n'
		html_buffer += f'<td style="text-align:center;">{pts_delta_format(tc_worst[0])}</td>\n'
	html_buffer += '</tr>\n'

	### wildcard 1
	html_buffer += '<tr>\n'
	html_buffer += f'<td class="w3-red" style="text-align:center;">WC1</td>\n'
	html_buffer += f'<td style="text-align:center;">\n'
	for i,man in enumerate(wc1_best[1]):
		if i != 0:
			html_buffer += "<br>\n"
		html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
		if 'Toilet' in league.name and man.is_diamond:
			html_buffer += "💎"
		html_buffer += f' in GW{man._wc1_week}\n'
	html_buffer +='</td>\n'
	delta = man._wc1_ordelta_percent
	if delta > 0:
		delta = f"+{delta:.0f}"
	else:
		delta = f"{delta:.0f}"
	html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
	if len(wc1_subset) == 1:
		html_buffer += f'<td></td>\n'
		html_buffer += f'<td></td>\n'
	else:
		html_buffer += f'<td style="text-align:center;">\n'
		for i,man in enumerate(wc1_worst[1]):
			if i != 0:
				html_buffer += "<br>\n"
			html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
			if 'Toilet' in league.name and man.is_diamond:
				html_buffer += "💎"
			html_buffer += f' in GW{man._wc1_week}\n'
		html_buffer +='</td>\n'
		delta = man._wc1_ordelta_percent
		if delta > 0:
			delta = f"+{delta:.0f}"
		else:
			delta = f"{delta:.0f}"
		html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
	html_buffer += '</tr>\n'

	### wildcard 2
	html_buffer += '<tr>\n'
	html_buffer += f'<td class="w3-red" style="text-align:center;">WC2</td>\n'
	html_buffer += f'<td style="text-align:center;">\n'
	for i,man in enumerate(wc2_best[1]):
		if i != 0:
			html_buffer += "<br>\n"
		html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
		if 'Toilet' in league.name and man.is_diamond:
			html_buffer += "💎"
		html_buffer += f' in GW{man._wc2_week}\n'
	html_buffer +='</td>\n'
	delta = man._wc2_ordelta_percent
	if delta > 0:
		delta = f"+{delta:.0f}"
	else:
		delta = f"{delta:.0f}"
	html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
	if len(wc2_subset) == 1:
		html_buffer += f'<td></td>\n'
		html_buffer += f'<td></td>\n'
	else:
		html_buffer += f'<td style="text-align:center;">\n'
		for i,man in enumerate(wc2_worst[1]):
			if i != 0:
				html_buffer += "<br>\n"
			html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
			if 'Toilet' in league.name and man.is_diamond:
				html_buffer += "💎"
			html_buffer += f' in GW{man._wc2_week}\n'
		html_buffer +='</td>\n'
		delta = man._wc2_ordelta_percent
		if delta > 0:
			delta = f"+{delta:.0f}"
		else:
			delta = f"{delta:.0f}"
		html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
	html_buffer += '</tr>\n'

	### free hit
	html_buffer += '<tr>\n'
	html_buffer += f'<td class="w3-green" style="text-align:center;">FH</td>\n'
	html_buffer += f'<td style="text-align:center;">\n'
	for i,man in enumerate(fh_best[1]):
		if i != 0:
			html_buffer += "<br>\n"
		html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
		if 'Toilet' in league.name and man.is_diamond:
			html_buffer += "💎"
		html_buffer += f' with {man._fh_total}pts in GW{man._fh_week}\n'
	html_buffer +='</td>\n'
	delta = 100*(man._fh_orprev-man._fh_or)/man._fh_orprev
	if delta > 0:
		delta = f"+{delta:.0f}"
	else:
		delta = f"{delta:.0f}"
	html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
	if len(fh_subset) == 1:
		html_buffer += f'<td></td>\n'
		html_buffer += f'<td></td>\n'
	else:
		html_buffer += f'<td style="text-align:center;">\n'
		for i,man in enumerate(fh_worst[1]):
			if i != 0:
				html_buffer += "<br>\n"
			html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
			if 'Toilet' in league.name and man.is_diamond:
				html_buffer += "💎"
			html_buffer += f'with {man._fh_total}pts in GW{man._fh_week}\n'
		html_buffer +='</td>\n'
		delta = 100*(man._fh_orprev-man._fh_or)/man._fh_orprev
		if delta > 0:
			delta = f"+{delta:.0f}"
		else:
			delta = f"{delta:.0f}"
		html_buffer += f'<td style="text-align:center;">{delta}% OR</td>\n'
	html_buffer += '</tr>\n'

	### bench boost
	html_buffer += '<tr>\n'
	html_buffer += f'<td class="w3-blue" style="text-align:center;">BB</td>\n'
	html_buffer += f'<td style="text-align:center;">\n'
	for i,man in enumerate(bb_best[1]):
		if i != 0:
			html_buffer += "<br>\n"
		html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
		if 'Toilet' in league.name and man.is_diamond:
			html_buffer += "💎"
		html_buffer += f'in GW{man._bb_week}\n'
	html_buffer +='</td>\n'
	html_buffer += f'<td style="text-align:center;">{pts_delta_format(bb_best[0])}</td>\n'
	if len(bb_subset) == 1:
		html_buffer += f'<td></td>\n'
		html_buffer += f'<td></td>\n'
	else:
		html_buffer += f'<td style="text-align:center;">\n'
		for i,man in enumerate(bb_worst[1]):
			if i != 0:
				html_buffer += "<br>\n"
			html_buffer += f'<a href="{man.gui_url}">{man.name}</a>\n'
			if 'Toilet' in league.name and man.is_diamond:
				html_buffer += "💎"
			html_buffer += f'in GW{man._bb_week}\n'
		html_buffer +='</td>\n'
		html_buffer += f'<td style="text-align:center;">{pts_delta_format(bb_worst[0])}</td>\n'
	html_buffer += '</tr>\n'

	# triple captain

	# 	if chip == 'TC':
	# 		color = 'amber'
	# 	elif chip.startswith('WC'):
	# 		color = 'red'
	# 	elif chip == 'BB':
	# 		color = 'blue'
	# 	elif chip == 'FH':
	# 		color = 'green'

	html_buffer += '</tbody>\n'
	html_buffer += '</table>\n'

	return html_buffer

def pts_delta_format(delta):
	if delta < 0:
		return f'{delta}pts'
	else:
		return f'+{delta}pts'

def get_losers(name,managers,criterium,cutoff=4):
	return get_winners(name, managers, criterium,reverse=False,cutoff=cutoff)

def get_winners(name,managers,criterium,reverse=True,cutoff=4):

	# print(criterium(managers[0]))
	# print(managers)
	# print([criterium(x) for x in managers])

	sorted_managers = sorted(managers, key=criterium, reverse=reverse)
	scores = [criterium(x) for x in sorted_managers]
	data = Counter(scores)
	num = data[scores[0]]
	if num < cutoff:
		if num > 1: 
			s = "s"
		else: 		
			s = ""
		return scores[0],sorted_managers[0:num]
	else:
		mout.warningOut(f"Too many people sharing {name} award")
		return scores[0],sorted_managers[0:num]

def make_season_awards(league):

	html_buffer = ""

	global json

	create_key(json[str(league.id)],'season')
	create_key(json[str(league.id)]['season'],'awards')

	# print(league.managers)
	# print(league.active_managers)

	sorted_managers = sorted(league.active_managers, key=lambda x: x.total_livescore, reverse=True)
	scores = [x.total_livescore for x in sorted_managers]
	data = Counter(scores)
	# print(data)
	# print(scores)
	num = data[scores[0]]
	if num < 4:
		if num > 1: 
			s = "s"
		else: 		
			s = ""
		html_buffer += award_panel('👑',f'King{s}','Best Score',f'{scores[0]} pts, {api.big_number_format(sorted_managers[0].overall_rank)} OR',sorted_managers[0:num],colour='amber',border='yellow',name_class="h2",halfonly=True)
		json[str(league.id)]['season']['awards']['king'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing king award")
		json[str(league.id)]['season']['awards']['king'] = None

	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	if num < 4:
		if num > 1: s = "s"
		else: 		s = ""
		html_buffer += award_panel('🐓',f'Cock{s}','Worst Score',f'{scores[0]} pts, {api.big_number_format(sorted_managers[0].overall_rank)} OR',sorted_managers[0:num],colour='red',border='yellow',name_class="h2",halfonly=True)
		json[str(league.id)]['season']['awards']['cock'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing cock award")
		json[str(league.id)]['season']['awards']['cock'] = None

	sorted_managers = sorted(league.active_managers, key=lambda x: x.total_transfer_gain, reverse=True)
	scores = [x.total_transfer_gain for x in sorted_managers]
	data = Counter(scores)
	num = data[scores[0]]
	if num < 4:
		html_buffer += award_panel('🔮',f'Fortune Teller','Best Total Transfer Gain',f"+{scores[0]} pts",sorted_managers[0:num],colour='purple',border='yellow',name_class="h2",halfonly=True)
		json[str(league.id)]['season']['awards']['fortune'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing fortune spot")
		json[str(league.id)]['season']['awards']['fortune'] = None

	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	if num < 4:
		html_buffer += award_panel('🤡',f'Clown','Worst Total Transfer Gain',f"{scores[0]} pts",sorted_managers[0:num],colour='pale-red',border='yellow',name_class="h2",halfonly=True)
		json[str(league.id)]['season']['awards']['clown'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing clown spot")
		json[str(league.id)]['season']['awards']['clown'] = None

	# kneejerker
	sorted_managers = sorted(league.active_managers, key=lambda x: x.num_nonwc_transfers, reverse=True)
	scores = [x.num_nonwc_transfers for x in sorted_managers]
	data = Counter(scores)
	num = data[scores[0]]
	if num > 1:
		sorted_managers2 = [sorted(sorted_managers[0:num], key=lambda x: x.num_hits, reverse=True)[0]]
		scores2 = [[x.num_hits for x in sorted_managers][0]]
		data = Counter(scores2)
		num = data[scores2[0]]
		print("Kneejerker",sorted_managers2[0:num],scores[0],scores2[0])
		json[str(league.id)]['season']['awards']['kneejerker'] = [[m.id for m in sorted_managers2[0:num]],scores[0],scores2[0]]
		html_buffer += award_panel('🔨',f'Kneejerker','Most Transfers',f'{scores[0]} transfers, {scores2[0]} hits',sorted_managers2[0:num],colour='deep-orange',border='yellow',name_class="h2",halfonly=True)
	else:
		print("Kneejerker",sorted_managers[0:num],scores[0],sorted_managers[0].num_hits)
		json[str(league.id)]['season']['awards']['kneejerker'] = [[sorted_managers[0].id],scores[0],sorted_managers[0].num_hits]
		html_buffer += award_panel('🔨',f'Kneejerker','Most Transfers',f'{scores[0]} transfers, {sorted_managers[0].num_hits} hits',sorted_managers[0],colour='deep-orange',border='yellow',name_class="h2",halfonly=True)

	# iceman
	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	if num > 1:
		sorted_managers2 = sorted(sorted_managers[0:num], key=lambda x: x.num_hits, reverse=False)
		scores2 = [x.num_hits for x in sorted_managers]
		data = Counter(scores2)
		num = data[scores2[0]]
		print("Iceman",sorted_managers2[0:num],scores[0],scores2[0])
		json[str(league.id)]['season']['awards']['iceman'] = [[m.id for m in sorted_managers2[0:num]],scores[0],scores2[0]]
		html_buffer += award_panel('🥶',f'Iceman','Least Transfers',f'{scores[0]} transfers, {scores2[0]} hits',sorted_managers2[0:num],colour='aqua',border='yellow',name_class="h2",halfonly=True)
	else:
		print("Iceman",sorted_managers[0:num],scores[0],sorted_managers[0].num_hits)
		json[str(league.id)]['season']['awards']['iceman'] = [[sorted_managers[0].id],scores[0],sorted_managers[0].num_hits]
		html_buffer += award_panel('🥶',f'Iceman','Least Transfers',f'{scores[0]} transfers, {sorted_managers[0].num_hits} hits',sorted_managers[0],colour='aqua',border='yellow',name_class="h2",halfonly=True)

	# oligarch
	sorted_managers = sorted(league.active_managers, key=lambda x: x.team_value, reverse=True)
	scores = [x.team_value for x in sorted_managers]
	data = Counter(scores)
	num = data[scores[0]]
	json[str(league.id)]['season']['awards']['oligarch'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	html_buffer += award_panel('🛢',f'Oligarch','Highest Team Value',f'£{scores[0]:.1f}',sorted_managers[0:num],colour='black',border='yellow',name_class="h2",halfonly=True)

	# peasant
	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	json[str(league.id)]['season']['awards']['peasant'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	html_buffer += award_panel('🏚',f'Peasant','Lowest Team Value',f'£{scores[0]:.1f}',sorted_managers[0:num],colour='brown',border='yellow',name_class="h2",halfonly=True)
	
	# glow-up (best improvement in the quarter season (GW8-GW16))
	sorted_managers = sorted(league.active_managers, key=lambda x: (x.get_specific_overall_rank(16)-x.get_specific_overall_rank(api._current_gw))/x.get_specific_overall_rank(16), reverse=True)
	m = sorted_managers[0]
	s = (m.get_specific_overall_rank(16)-m.get_specific_overall_rank(api._current_gw))/m.get_specific_overall_rank(16)
	json[str(league.id)]['season']['awards']['glow_up'] = [[m.id],s]
	if s > 0:
		html_buffer += award_panel('💡',f'Glow-Up','Best improvement since Christmas',f'{api.big_number_format(m.get_specific_overall_rank(16))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = +{100*s:.1f}%',m,colour='pale-yellow',border='yellow',name_class="h2",halfonly=True)
	else:
		html_buffer += award_panel('💡',f'Glow-Up','Best improvement since Christmas',f'{api.big_number_format(m.get_specific_overall_rank(16))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = {100*s:.1f}%',m,colour='pale-yellow',border='yellow',name_class="h2",halfonly=True)

	# iceman
	m = sorted_managers[-1]
	s = m.get_specific_overall_rank(16)-m.get_specific_overall_rank(api._current_gw)
	s = -s/m.get_specific_overall_rank(16)
	json[str(league.id)]['season']['awards']['has_been'] = [[m.id],s]
	if s > 0:
		html_buffer += award_panel('👨‍🦳',f'Has-Been','Worst improvement since Christmas',f'{api.big_number_format(m.get_specific_overall_rank(16))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = +{100*s:.1f}%',m,colour='grey',border='yellow',name_class="h2",halfonly=True)
	else:
		html_buffer += award_panel('👨‍🦳',f'Has-Been','Worst improvement since Christmas',f'{api.big_number_format(m.get_specific_overall_rank(16))}→{api.big_number_format(m.get_specific_overall_rank(api._current_gw))} = {100*s:.1f}%',m,colour='grey',border='yellow',name_class="h2",halfonly=True)

	return html_buffer

def christmas_awards(league):

	html_buffer = ""

	global json

	create_key(json[str(league.id)],'half')
	create_key(json[str(league.id)]['half'],'awards')

	# print(league.managers)
	# print(league.active_managers)

	sorted_managers = sorted(league.active_managers, key=lambda x: x.total_livescore, reverse=True)
	scores = [x.total_livescore for x in sorted_managers]
	data = Counter(scores)
	# print(data)
	# print(scores)
	num = data[scores[0]]
	if num < 4:
		if num > 1: 
			s = "s"
		else: 		
			s = ""
		html_buffer += award_panel('👑',f'King{s}','Best Score',f'{scores[0]} pts, {api.big_number_format(sorted_managers[0].overall_rank)} OR',sorted_managers[0:num],colour='amber',border='green',name_class="h2",halfonly=True)
		json[str(league.id)]['half']['awards']['king'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing king award")
		json[str(league.id)]['half']['awards']['king'] = None

	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	if num < 4:
		if num > 1: s = "s"
		else: 		s = ""
		html_buffer += award_panel('🐓',f'Cock{s}','Worst Score',f'{scores[0]} pts, {api.big_number_format(sorted_managers[0].overall_rank)} OR',sorted_managers[0:num],colour='red',border='green',name_class="h2",halfonly=True)
		json[str(league.id)]['half']['awards']['cock'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing cock award")
		json[str(league.id)]['half']['awards']['cock'] = None

	sorted_managers = sorted(league.active_managers, key=lambda x: x.total_transfer_gain, reverse=True)
	scores = [x.total_transfer_gain for x in sorted_managers]
	data = Counter(scores)
	num = data[scores[0]]
	if num < 4:
		html_buffer += award_panel('🔮',f'Fortune Teller','Best Total Transfer Gain',f"+{scores[0]} pts",sorted_managers[0:num],colour='purple',border='green',name_class="h2",halfonly=True)
		json[str(league.id)]['half']['awards']['fortune'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing fortune spot")
		json[str(league.id)]['half']['awards']['fortune'] = None

	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	if num < 4:
		html_buffer += award_panel('🤡',f'Clown','Worst Total Transfer Gain',f"{scores[0]} pts",sorted_managers[0:num],colour='pale-red',border='green',name_class="h2",halfonly=True)
		json[str(league.id)]['half']['awards']['clown'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	else:
		mout.warningOut("Too many people sharing clown spot")
		json[str(league.id)]['half']['awards']['clown'] = None

	# kneejerker
	sorted_managers = sorted(league.active_managers, key=lambda x: x.num_nonwc_transfers, reverse=True)
	scores = [x.num_nonwc_transfers for x in sorted_managers]
	data = Counter(scores)
	num = data[scores[0]]
	if num > 1:
		sorted_managers2 = [sorted(sorted_managers[0:num], key=lambda x: x.num_hits, reverse=True)[0]]
		scores2 = [[x.num_hits for x in sorted_managers][0]]
		data = Counter(scores2)
		num = data[scores2[0]]
		print("Kneejerker",sorted_managers2[0:num],scores[0],scores2[0])
		json[str(league.id)]['half']['awards']['kneejerker'] = [[m.id for m in sorted_managers2[0:num]],scores[0],scores2[0]]
		html_buffer += award_panel('🔨',f'Kneejerker','Most Transfers',f'{scores[0]} transfers, {scores2[0]} hits',sorted_managers2[0:num],colour='deep-orange',border='green',name_class="h2",halfonly=True)
	else:
		print("Kneejerker",sorted_managers[0:num],scores[0],sorted_managers[0].num_hits)
		json[str(league.id)]['half']['awards']['kneejerker'] = [[sorted_managers[0].id],scores[0],sorted_managers[0].num_hits]
		html_buffer += award_panel('🔨',f'Kneejerker','Most Transfers',f'{scores[0]} transfers, {sorted_managers[0].num_hits} hits',sorted_managers[0],colour='deep-orange',border='green',name_class="h2",halfonly=True)

	# iceman
	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	if num > 1:
		sorted_managers2 = sorted(sorted_managers[0:num], key=lambda x: x.num_hits, reverse=False)
		scores2 = [x.num_hits for x in sorted_managers]
		data = Counter(scores2)
		num = data[scores2[0]]
		print("Iceman",sorted_managers2[0:num],scores[0],scores2[0])
		json[str(league.id)]['half']['awards']['iceman'] = [[m.id for m in sorted_managers2[0:num]],scores[0],scores2[0]]
		html_buffer += award_panel('🥶',f'Iceman','Least Transfers',f'{scores[0]} transfers, {scores2[0]} hits',sorted_managers2[0:num],colour='aqua',border='green',name_class="h2",halfonly=True)
	else:
		print("Iceman",sorted_managers[0:num],scores[0],sorted_managers[0].num_hits)
		json[str(league.id)]['half']['awards']['iceman'] = [[sorted_managers[0].id],scores[0],sorted_managers[0].num_hits]
		html_buffer += award_panel('🥶',f'Iceman','Least Transfers',f'{scores[0]} transfers, {sorted_managers[0].num_hits} hits',sorted_managers[0],colour='aqua',border='green',name_class="h2",halfonly=True)

	# oligarch
	sorted_managers = sorted(league.active_managers, key=lambda x: x.team_value, reverse=True)
	scores = [x.team_value for x in sorted_managers]
	data = Counter(scores)
	num = data[scores[0]]
	json[str(league.id)]['half']['awards']['oligarch'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	html_buffer += award_panel('🛢',f'Oligarch','Highest Team Value',f'£{scores[0]:.1f}',sorted_managers[0:num],colour='black',border='green',name_class="h2",halfonly=True)

	# peasant
	sorted_managers.reverse()
	scores.reverse()
	data = Counter(scores)
	num = data[scores[0]]
	json[str(league.id)]['half']['awards']['peasant'] = [[m.id for m in sorted_managers[0:num]],scores[0]]
	html_buffer += award_panel('🏚',f'Peasant','Lowest Team Value',f'£{scores[0]:.1f}',sorted_managers[0:num],colour='brown',border='green',name_class="h2",halfonly=True)
	
	# glow-up (best improvement in the quarter season (GW8-GW16))
	sorted_managers = sorted(league.active_managers, key=lambda x: (x.get_specific_overall_rank(8)-x.get_specific_overall_rank(16))/x.get_specific_overall_rank(8), reverse=True)
	m = sorted_managers[0]
	s = (m.get_specific_overall_rank(8)-m.get_specific_overall_rank(16))/m.get_specific_overall_rank(8)
	json[str(league.id)]['half']['awards']['glow_up'] = [[m.id],s]
	if s > 0:
		html_buffer += award_panel('💡',f'Glow-Up','Best 8GW improvement',f'{api.big_number_format(m.get_specific_overall_rank(8))}→{api.big_number_format(m.get_specific_overall_rank(16))} = +{100*s:.1f}%',m,colour='pale-yellow',border='green',name_class="h2",halfonly=True)
	else:
		html_buffer += award_panel('💡',f'Glow-Up','Best 8GW improvement',f'{api.big_number_format(m.get_specific_overall_rank(8))}→{api.big_number_format(m.get_specific_overall_rank(16))} = {100*s:.1f}%',m,colour='pale-yellow',border='green',name_class="h2",halfonly=True)

	# iceman
	m = sorted_managers[-1]
	s = m.get_specific_overall_rank(16)-m.get_specific_overall_rank(8)
	s = -s/m.get_specific_overall_rank(8)
	json[str(league.id)]['half']['awards']['has_been'] = [[m.id],s]
	if s > 0:
		html_buffer += award_panel('👨‍🦳',f'Has-Been','Worst 8GW improvement',f'{api.big_number_format(m.get_specific_overall_rank(8))}→{api.big_number_format(m.get_specific_overall_rank(16))} = +{100*s:.1f}%',m,colour='grey',border='green',name_class="h2",halfonly=True)
	else:
		html_buffer += award_panel('👨‍🦳',f'Has-Been','Worst 8GW improvement',f'{api.big_number_format(m.get_specific_overall_rank(8))}→{api.big_number_format(m.get_specific_overall_rank(16))} = {100*s:.1f}%',m,colour='grey',border='green',name_class="h2",halfonly=True)

	# has-been (best improvement in the quarter season (GW8-GW16))

	# best chip uses

	return html_buffer

def price_changes(f):

	global api
	global risers
	global fallers

	risers = []
	fallers = []

	for first,name,delta in zip(api.elements['first_name'],api.elements['web_name'],api.elements['cost_change_event']):
		delta = float(delta)
		if delta == 0:
			continue
		elif delta > 0:
			risers.append([Player(f"{first} {name}",api),delta])
		elif delta < 0:
			fallers.append([Player(f"{first} {name}",api),delta])

	risers = sorted(risers,key=lambda x: x[0].selected_by, reverse=True)
	fallers = sorted(fallers,key=lambda x: x[0].selected_by, reverse=True)

	f.write(f"| Risers | Fallers |\n")
	f.write(f"| --- | --- |\n")

	for i in range(max([len(risers),len(fallers),1])):

		f.write(f"| ")

		if i > len(risers)-1:
			if i == 0:
				f.write(f"No risers this week")
			else:
				f.write(f" | ")
		else:
			p = risers[i][0]
			f.write(f"[[https://github.com/mwinokan/FPL_GUI/blob/main/{p.kit_path}]] ")
			f.write(f"[{p.name}]({p._gui_url})")

			f.write(f" +{risers[i][1]/10:.1f} = ")
			f.write(f"{p.price}")
			f.write(" |")

		if i > len(fallers)-1:
			if i == 0:
				f.write(f"No fallers this week")
			else:
				f.write(f" | ")
		else:
			p = fallers[i][0]
			f.write(f"[[https://github.com/mwinokan/FPL_GUI/blob/main/{p.kit_path}]] ")
			f.write(f"[{p.name}]({p._gui_url})")
			f.write(f" {fallers[i][1]/10:.1f} = ")
			f.write(f"{p.price}")
			f.write(" |")

		f.write(f"\n")

	f.write(f"\n\n")
		# print(name,delta)

def create_overall_page():
	mout.debugOut(f"create_overall_page()")

	file = f'{path}/Overall.md'

	with open(file,mode='w') as f:
		# f.write(f"# Max's FPL GUI\n")
		f.write(f"N/A\n")

		# f.write(f"## League Summaries\n")
		# for l in leagues:
		# 	f.write(f'* [{l}]({l.name.replace(" ","-")})\n')

def award_panel(icon,name,description,value,manager,colour='light-grey',border=None,name_class="h1",value_class="h2",halfonly=False):

	many = isinstance(manager,list)
	m = manager

	if many and len(manager) > 1:
		mout.error('Awards are not supposed to be shared anymore!!')
		print(icon,name,description,value,manager)

	html_buffer = ""

	if halfonly:
		html_buffer += f'<div class="w3-col s12 m12 l6">\n'
	else:
		html_buffer += f'<div class="w3-col s12 m6 l4">\n'

	if border:
		html_buffer += f'<div style="border:8px solid" class="w3-panel w3-{colour} w3-border-{border} shadow89">\n'
	else:
		html_buffer += f'<div class="w3-panel w3-{colour} shadow89">\n'
	
	# html_buffer += f'<table style="width:100%;padding:0px;border-spacing:0px;">\n'
	html_buffer += f'<table style="width:100%;padding:0px;border-spacing:0px;padding-bottom:10px">\n'
	html_buffer += f'<tr>\n'
	html_buffer += f'<td style="text-align:left;vertical-align:middle;">\n'
	# html_buffer += f'<td style="text-align:left;vertical-align:middle;">\n'
	html_buffer += f'<{name_class} style="text-shadow: 1px 2px 4px rgba(0,0,0,0.5);">{icon} {name}</{name_class}>\n'

	html_buffer += f'<h4>{description}</h4>\n'

	html_buffer += f'</td>\n'

	html_buffer += f'<td style="text-align:right;vertical-align:middle;">\n'
	# html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}?raw=true" alt="Kit Icon" width="22" height="29">\n'
	html_buffer += f'<h2><span class="w3-tag shadow89">{value}</span></h2>\n'
	# html_buffer += f'<h2><span class="w3-tag shadow89"><img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}?raw=true" alt="Kit Icon" width="22" height="29">{value}</span></h2>\n'

	# html_buffer += '</table>\n'
	
	# html_buffer += '<table style="width:100%;padding:0px;border-spacing:0px;padding-bottom:10px;">\n'

	# html_buffer += '<tr>\n'
	# html_buffer += '<td style="vertical-align:top;">\n'
	# html_buffer += f'<h4>{description}</h4>\n'
	# html_buffer += '</td>\n'
	# html_buffer += '<td style="text-align:right">\n'
	# html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}?raw=true" alt="Kit Icon" width="22" height="29">\n'
	# html_buffer += '</td>\n'

	# html_buffer += '<td style="text-align:right">\n'
	html_buffer += f'<a href="{m.gui_url}">{m.team_name}</a>'
	html_buffer += f'<br>'
	html_buffer += f'<a href="{m.gui_url}">{m.name}</a>'

	# html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}?raw=true" alt="Kit Icon" width="22" height="29">\n'

	html_buffer += f'</td>\n'
	html_buffer += f'</tr>\n'
	html_buffer += f'</table>\n'
	html_buffer += f'</div>\n'
	html_buffer += f'</div>\n'

	return html_buffer

def floating_subtitle(text,pad=1,button=False):
	html_buffer = ""
	html_buffer += '<div class="w3-col s12 m12 l12">\n'
	for i in range(pad):
		html_buffer += '<br>\n'

	if button:
		html_buffer += f'\t<a href="{button}"><h1 class="w3-tag shadow89">{text}</h1></a>\n'
	else:
		html_buffer += f'\t<h1 class="w3-tag shadow89">{text}</h1>\n'

	html_buffer += '</div>\n'
	return html_buffer	

def award_rules_md():
	return '''
	* King (Most GW Points)
		* Tiebreakers: 
			* Biggest rank gain %
			* Best GW performed xPts

	* King (Least GW Points)
		* Tiebreakers: 
			* Biggest rank loss %
			* Worst GW performed xPts

	* Massive Goal FC (Most goals)
		* Tiebreakers:
			* Highest xG

	* Scientist (Best differential)
		* Tiebreakers:
			* Most unique differential

	* Boner (Highest BPS)

	* ASBO (Most carded team)

	* Fortune Teller (Best transfers)
		* Tiebreaker:
			* Highest transfer uniqueness

	* Clown (Worst transfers)
		* Tiebreaker:
			* Lowest transfer uniqueness

	* Highest non-haaland captain points (Christmas)
	* Which managers consistently bring players in and their average drops
	* Rank gain and drop awards 

	'''

def create_leaguepage(league,leagues,i):
	mout.debugOut(f"create_leaguepage({league})")

	global api
	global json

	md_buffer = ""
	html_buffer = ""

	file = f'{path}/{league.name.replace(" ","-")}.md'

	# gw = api.current_gw
	gw = api._wiki_gw

	mout.debugOut(f"create_leaguepage({league})::Awards")

	create_key(json,str(league.id))
	create_key(json[str(league.id)], gw)
	create_key(json[str(league.id)][gw], 'awards')

	awards = not api._live_gw or any([f['started'] for f in api.get_gw_fixtures(gw)])
	
	if awards:

		# print(award_rules_md())

		if gw > 0:
			html_buffer += floating_subtitle(f'🏆 GW{gw} Awards',pad=0)

			### KING
			# start = time.perf_counter()
			sorted_managers = sorted(league.active_managers, key=lambda x: (x.livescore, x.gw_rank_gain), reverse=True)
			m = sorted_managers[0]
			score = m.livescore
			html_buffer += award_panel('👑','King','Best GW',f'{score} pts',m,colour=award_colour['king'],name_class="h2")
			json[str(league.id)][gw]['awards']['king'] = [m.id,score]
			# mout.out(f'King {time.perf_counter()-start:.1f}s')

			### COCK

			# start = time.perf_counter()
			m = sorted_managers[-1]
			score = m.livescore
			html_buffer += award_panel('🐓','Cock','Worst GW',f'{score} pts',m,colour=award_colour['cock'],name_class="h2")
			json[str(league.id)][gw]['awards']['cock'] = [m.id,score]
			# mout.out(f'Cock {time.perf_counter()-start:.1f}s')

			### MASSIVE GOALS

			# start = time.perf_counter()
			sorted_managers = sorted(league.active_managers, key=lambda x: (x.goals, x.gw_xg, x.gw_xa, x.livescore), reverse=True)
			m = sorted_managers[0]
			score = m.goals
			if score > 4:
				score_str = f'{score}×⚽️'
			else:
				score_str = f'{"⚽️"*score}'
			html_buffer += award_panel('⚽️','Massive Goal FC','Most Goals',score_str,m,colour=award_colour['goals'],name_class="h3")
			json[str(league.id)][gw]['awards']['goals'] = [m.id,score]
			# mout.out(f'Massive Goals {time.perf_counter()-start:.1f}s')

			### SCIENTIST

			# start = time.perf_counter()
			players = league.get_starting_players(unique=False)
			p = sorted(players, key=lambda p: (p.multiplier*p.get_event_score(not_playing_is_none=False)/p.league_count, 1/p.league_count), reverse=True)[0]
			m = p._parent_manager
			p_str = p.name
			if p.is_captain:
				p_str += " (C)"
			elif p.is_vice_captain:
				p_str += " (VC)"
			html_buffer += award_panel('🧑‍🔬','Scientist','Best Differential',p_str,m,colour=award_colour['scientist'],value_class='h3',name_class="h2")
			json[str(league.id)][gw]['awards']['scientist'] = [m.id,p.id,p.is_captain,int(p.multiplier*p.get_event_score(not_playing_is_none=False))]
			# mout.out(f'Scientist {time.perf_counter()-start:.1f}s')

			### HOT STUFF

			sorted_managers = sorted([m for m in league.active_managers if m.gw_performed_xpts > 0], key=lambda x: ((x.livescore - x.gw_performed_xpts)/x.gw_performed_xpts, x.gw_performed_xpts), reverse=True)
			if len(sorted_managers) > 0:
				# start = time.perf_counter()
				m = sorted_managers[0]
				score = (m.livescore - m.gw_performed_xpts)/m.gw_performed_xpts

				html_buffer += award_panel('🥵','Hot Stuff','xGI Overperformer',f'{score:+.1%}',m,colour=award_colour['hot_stuff'],name_class="h2")
				json[str(league.id)][gw]['awards']['hot_stuff'] = [m.id,score]
				# mout.out(f'Hot Stuff {time.perf_counter()-start:.1f}s')

				### SOGGY BISCUIT

				# start = time.perf_counter()
				m = sorted_managers[-1]
				score = (m.livescore - m.gw_performed_xpts)/m.gw_performed_xpts
				html_buffer += award_panel('🍪','Soggy Biscuit','xGI Underperformer',f'{score:+.1%}',m,colour=award_colour['soggy_biscuit'],name_class="h3")
				json[str(league.id)][gw]['awards']['soggy_biscuit'] = [m.id,score]
				# mout.out(f'Soggy Biscuit {time.perf_counter()-start:.1f}s')

			if gw > 1:

				# start = time.perf_counter()
				sorted_managers = sorted(league.active_managers, key=lambda x: x.gw_rank_gain, reverse=True)

				### rocketeer

				m = sorted_managers[0]
				score = m.gw_rank_gain
				html_buffer += award_panel('🚀','Rocketeer','Best Rank Gain',f'{score:+.1f}%',m,colour=award_colour['rocket'],name_class="h2")
				json[str(league.id)][gw]['awards']['rocket'] = [m.id,score]
				# mout.out(f'Rocket {time.perf_counter()-start:.1f}s')

				### down the toilet

				# start = time.perf_counter()
				m = sorted_managers[-1]
				score = m.gw_rank_gain
				html_buffer += award_panel('🚽','#DownTheToilet','Worst Rank Loss',f'{score:.1f}%',m,colour=award_colour['flushed'],name_class="h3")
				json[str(league.id)][gw]['awards']['flushed'] = [m.id,score]
				# mout.out(f'Toilet {time.perf_counter()-start:.1f}s')

			### BONER

			# start = time.perf_counter()
			m = sorted(league.active_managers, key=lambda x: x.bps, reverse=True)[0]
			html_buffer += award_panel('🦴',f'Boner','Highest Bonus',f'{m.bps} BPS',m,colour=award_colour['boner'],name_class="h2")
			json[str(league.id)][gw]['awards']['boner'] = [m.id,m.bps]
			# mout.out(f'Boner {time.perf_counter()-start:.1f}s')

			### SMOOTH BRAIN

			# start = time.perf_counter()
			m = sorted(league.active_managers, key=lambda x: x.bench_points, reverse=True)[0]
			html_buffer += award_panel('🧠',f'Smooth Brain','Most Bench Points',f'{m.bench_points} pts',m,colour=award_colour['smooth_brain'],name_class="h3")
			json[str(league.id)][gw]['awards']['smooth_brain'] = [m.id,m.bench_points]
			# mout.out(f'Smooth Brain {time.perf_counter()-start:.1f}s')

			### CHAIR

			# start = time.perf_counter()
			m = sorted(league.active_managers, key=lambda x: x.minutes, reverse=False)[0]
			html_buffer += award_panel('🪑',f'Chair','Least Minutes Played',f"{m.minutes}'",m,colour=award_colour['chair'],name_class="h2")
			json[str(league.id)][gw]['awards']['chair'] = [m.id,m.minutes]
			# mout.out(f'Chair {time.perf_counter()-start:.1f}s')

			### ASBO

			# start = time.perf_counter()
			sorted_managers = sorted(league.active_managers, key=lambda x: (x.get_card_count(), -x.minutes), reverse=True)
			m = sorted_managers[0]
			html_buffer += award_panel('🥊',f'ASBO','Most Carded',m.card_emojis,m,colour=award_colour['asbo'],name_class="h2")
			json[str(league.id)][gw]['awards']['asbo'] = [m.id,m.card_emojis]
			# mout.out(f'ASBO {time.perf_counter()-start:.1f}s')

		if gw > 1:

			### FORTUNE TELLER

			# start = time.perf_counter()
			sorted_managers = sorted(league.active_managers, key=lambda x: (x.calculate_transfer_gain(), x._transfer_uniqueness), reverse=True)
			m = sorted_managers[0]
			score = m.calculate_transfer_gain()
			html_buffer += award_panel('🔮','Fortune Teller','Best Transfers',f"{score:+d} pts",m,colour=award_colour['fortune'],name_class="h2")
			json[str(league.id)][gw]['awards']['fortune'] = [m.id,score]
			# mout.out(f'Fortune {time.perf_counter()-start:.1f}s')

			### CLOWN

			# start = time.perf_counter()
			m = sorted_managers[-1]
			score = m.calculate_transfer_gain()
			html_buffer += award_panel('🤡','Clown','Worst Transfers',f"{score:+d} pts",m,colour=award_colour['clown'],name_class="h2")
			json[str(league.id)][gw]['awards']['clown'] = [m.id,score]
			# mout.out(f'Clown {time.perf_counter()-start:.1f}s')

		# if gw > 0:

			### NERD AND INNOVATOR (REMOVED)

			# m = sorted(league.active_managers, key=lambda x: x.avg_selection, reverse=True)[0]
			# html_buffer += award_panel('🤓',f'Nerd','Most Template Team',f'{m.avg_selection:.1f}%',m,colour='pale-yellow',name_class="h2")
			# json[str(league.id)][gw]['awards']['nerd'] = [m.id,m.avg_selection]

			# m = sorted(league.active_managers, key=lambda x: x.avg_selection, reverse=False)[0]
			# html_buffer += award_panel('🎓',f'Innovator','Least Template Team',f'{m.avg_selection:.1f}%',m,colour='grey',name_class="h2")
			# json[str(league.id)][gw]['awards']['innovator'] = [m.id,m.avg_selection]

			# md_buffer += f"### 👻 Ghost team (longest time since transfer)"
			# md_buffer += f"### 🥶 Iceman (least transfers made)"
			# md_buffer += f"### 🦿 Billy's Knees (most transfers made)"
			# md_buffer += f"### 🤑 Most Valuable Team\n"
			# # md_buffer += f"### 📈 Best team value gain\n"
			# # md_buffer += f"### 📉 Biggest team value loss\n"
			# f.write(f"### 💎 GW{gw} Diamond Award (Biggest green arrow)\n")
			# f.write(f"### 💀 RIP (Biggest red arrow)\n")
			# md_buffer += f"### 🚩 Most flagged team\n"
			# most in form team
			# most out of form team

		#### halfway awards

	if gw > 0:
		mout.debugOut(f"create_leaguepage({league})::Template")
		html_buffer += floating_subtitle('League Template')
		html_buffer += league_template(league, gw)

		mout.debugOut(f"create_leaguepage({league})::Differentials")
		html_buffer += floating_subtitle('Killer Differentials')
		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

	if awards:
		html_buffer += league_differentials(league, gw)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	if preseason:
		mout.debugOut(f"create_leaguepage({league})::PreseasonTable")
		html_buffer += floating_subtitle('Last Season')
		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
		html_buffer += preseason_table(league)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'
	
	if gw > 1:
		mout.debugOut(f"create_leaguepage({league})::Transfers")
		ids_in, ids_out = league.get_league_transfers(gw)
		
		html_buffer += floating_subtitle('Popular Moves')
		
		html_buffer += transfer_table(ids_in, 'In', 'pale-green')

		html_buffer += transfer_table(ids_out, 'Out', 'pale-red')
	
	if not preseason:

		mout.debugOut(f"create_leaguepage({league})::Chips")
		html_buffer += league_chips(league,gw)

		mout.debugOut(f"create_leaguepage({league})::Table")
		html_buffer += floating_subtitle('League Table')

		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

		html_buffer += f'<div class="w3-padding">\n'
		html_buffer += f"<h2>League Table:</h2>\n"
		html_buffer += '<p>Is your team'+f's kit the boring default? Design it <a href="https://fantasy.premierleague.com/entry-update">here</a><p>\n'
		html_buffer += f"</div>\n"
		html_buffer += league_table_html(league, gw)

		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	if league.num_managers > 20 and awards:
		subset = []
		subset += [d[0] for d in json[str(league.id)][gw]['awards'].values()]
	else:
		subset = None

	import sys
	sys.path.insert(1,'go')
	from goleague import create_league_figure, create_league_histogram

	if api._current_gw > 1:
		html_buffer += floating_subtitle('League Graphs')

		if len(league.managers) > 30:
			html_buffer += '<div class="w3-col s12 m12 l12">\n'
			html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
			html_buffer += create_league_histogram(api, league, subset, all_gws=True)
			html_buffer += '</div>\n'
			html_buffer += '</div>\n'

			html_buffer += '<div class="w3-col s12 m12 l12">\n'
			html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
			html_buffer += create_league_histogram(api, league, subset, all_gws=False)
			html_buffer += '</div>\n'
			html_buffer += '</div>\n'
		
		html_buffer += '<div class="w3-col s12 m12 l12">\n'
		html_buffer += '<div class="w3-panel w3-white w3-padding shadow89">\n'
		html_buffer += create_league_figure(api, league, subset)
		html_buffer += '</div>\n'
		html_buffer += '</div>\n'

	style = api.create_team_styles_css()
	navbar = create_navbar(leagues, active=i, colour='black', active_colour='green')
	html_page(f'html/{league.name.replace(" ","-")}.html',None,title=f"{league._icon} {league.name}", gw=gw, html=html_buffer, bar_html=navbar, showtitle=True,colour=league._colour_str, extra_style=style, plotly=True)

	# exit()

def league_chips(league,gw):

	'''
	
	Chip | Team | Manager | GW Score | Detail
	
	'''

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

	# if total_chip_count > 0: mout.headerOut(f'{league.shortname} Chips')

	if total_chip_count == 0:
		return ""

	html_buffer += floating_subtitle('Chips')

	html_buffer += '<div class="w3-col s12 m12 l12">\n'
	html_buffer += '<div class="w3-panel w3-white shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

	# html_buffer += f'<h2>Chips Played:</h2>\n'
	html_buffer += '<table class="w3-table w3-hoverable">\n'
	html_buffer += '<thead>\n'
	html_buffer += '<tr>\n'

	html_buffer += '<th style="text-align:center;">Chip</th>\n'
	html_buffer += '<th>Team</th>\n'
	html_buffer += '<th>Manager</th>\n'
	html_buffer += f'<th style="text-align:center;">GW{gw} Score</th>\n'

	html_buffer += '</tr>\n'
	html_buffer += '</thead>\n'

	html_buffer += '<tbody>\n'

	for man in sorted(chip_managers, key=lambda x: x.get_event_score(gw,), reverse=True):

		chip = man.get_event_chip(gw)

		if chip == 'TC':
			color = 'amber'
		elif chip.startswith('WC'):
			color = 'red'
		elif chip == 'BB':
			color = 'blue'
		elif chip == 'FH':
			color = 'green'

		html_buffer += f'<td class="w3-{color}" style="text-align:center;">{man.get_event_chip(gw)}</td>\n'

		# team
		html_buffer += f'<td><img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{man._kit_path}?raw=true" alt="Kit Icon" width="22" height="29"> <a href="{man.gui_url}">{man.team_name}</a></td>\n'

		# manager
		html_buffer += f'<td><a href="{man.gui_url}">{man.name}</a>\n'
		if 'Toilet' in league.name and man.is_diamond:
			html_buffer += "💎"
		html_buffer += '</td>\n'
		
		html_buffer += f'<td style="text-align:center;">{man.get_event_score(gw)}</td>\n'
		
		html_buffer += '</tr>\n'

	html_buffer += '</tbody>\n'
	html_buffer += '</table>\n'

	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	return html_buffer

def transfer_table(ids,title_str,colour_str):

	global api
	html_buffer = ""

	html_buffer += '<div class="w3-col s12 m12 l6">\n'
	html_buffer += f'<div class="w3-panel w3-{colour_str} shadow89" style="padding-left:0px;padding-right:0px;padding-bottom:4px">\n'

	html_buffer += '<div class="w3-responsive w3-padding">\n'
	html_buffer += f'<h2>Transferred {title_str}:</h2>\n'
	html_buffer += '</div>\n'
	html_buffer += '<div class="w3-responsive">\n'
	html_buffer += '<table class="w3-table w3-hoverable responsive-text">\n'
	html_buffer += '<thead>\n'
	html_buffer += '<tr>\n'

	html_buffer += '<th>Player</th>\n'
	html_buffer += '<th class="w3-center">#Trans.</th>\n'
	# html_buffer += '<th>League Select.</th>\n'	
	html_buffer += '<th class="w3-center">Form</th>\n'

	now_gw = api._current_gw
	end_gw = min(38,now_gw+5)
	for i in range(now_gw,end_gw+1):
		html_buffer += f'<th class="w3-center">GW{i}</th>\n'

	# html_buffer += f'<th>Summary</th>\n'
	html_buffer += '</tr>\n'
	html_buffer += '</thead>\n'

	html_buffer += '<tbody>\n'

	counter = Counter(ids)

	for i,(id,count) in enumerate(counter.most_common(5)):

		if i == 0 and count == 1:
			return ""

		if count == 1:
			break

		p = Player(None,api,index=api.get_player_index(id))

		html_buffer += '<tr>\n'

		html_buffer += '<td style="vertical-align:middle;">'
		html_buffer += p.kit_name_html
		html_buffer += '</td>\n'
		
		html_buffer += '<td class="w3-center">'
		html_buffer += f'{count}'
		html_buffer += '</td>\n'

		form = p.form
		style_str = get_style_from_event_score(form).rstrip('"')+';vertical-align:middle;"'
		html_buffer += f'<td class="w3-center" style={style_str}>{form}</td>\n'

		html_buffer += player_summary_cell_modal(p,now_gw)

		for i in range(now_gw+1,end_gw+1):
			exp = p.expected_points(gw=i)
			style_str = get_style_from_event_score(exp).rstrip('"')+';vertical-align:middle;"'
			if style_str is None:
				html_buffer += f'<td class="w3-center" style="vertical-align:middle;">{p.get_fixture_str(i,short=True,lower_away=True)}</td>\n'
			else:
				html_buffer += f'<td class="w3-center" style={style_str}>{p.get_fixture_str(i,short=True,lower_away=True)} ({exp:.1f})</td>\n'

		html_buffer += '</tr>\n'

	html_buffer += '</tbody>\n'
	html_buffer += '</table>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'
	html_buffer += '</div>\n'

	return html_buffer

def preseason_table(league):

	html_buffer = ""
	html_buffer += '<table class="w3-table responsive-text">\n'
	html_buffer += '\t<tr>\n'
	html_buffer += '\t\t<th></th>\n'
	html_buffer += '\t\t<th>Team Name</th>\n'
	html_buffer += '\t\t<th>Manager</th>\n'
	html_buffer += '\t\t<th>Score</th>\n'
	html_buffer += '\t\t<th>Rank</th>\n'
	html_buffer += '\t</tr>\n'

	sorted_managers = sorted(league.managers, key=lambda x: x.last_season_score, reverse=True)
	for i,m in enumerate(sorted_managers):

		html_buffer += '\t<tr>\n'
		# if i+1 == len(sorted_managers):
			# html_buffer += f'\t\t<td style="text-align:right;">🥚</td>\n'
		# else:
		html_buffer += f'\t\t<td style="text-align:right;">{i+1}</td>\n'
		html_buffer += f'\t\t<td><img src="https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}?raw=true" alt="Kit Icon" width="22" height="29"></img>\n'

		html_buffer += f'\t\t<a href="{m.gui_url}">{m.team_name}</a></td>\n'
		
		if 'Tesco Bean Value' in league.name and m.is_diamond:
			html_buffer += f'\t\t<td>{m.name} 💎</td>\n'
		else:
			html_buffer += f'\t\t<td>{m.name}</td>\n'

		if len(m._past_points) < 1:
			html_buffer += f"<td>N/A</td><td>N/A</td>\n"
		else:
			html_buffer += f'<td>{m._past_points[-1]}</td>\n'
			html_buffer += f'<td>{api.big_number_format(m._past_ranks[-1])}</td>\n'

		html_buffer += '\t</tr>\n'

	html_buffer += '</table>\n'

	return html_buffer

	f.write(f"| # | Team Name | Manager | Last Season Score | Last Season Rank |\n")
	f.write(f"| --- | --- | --- | --- | ---: |\n")
	sorted_managers = sorted(league.managers, key=lambda x: x.last_season_score, reverse=True)
	for i,m in enumerate(sorted_managers):
		if i+1 == len(sorted_managers):
			f.write(f"| 🥚 ")
		else:
			f.write(f"| {i+1} ")

		f.write(f"| [[https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}]]")
		f.write(f" [{m.team_name}]({m.gui_url})")
		f.write(f"| [{m.name}]({m.gui_url}) ")

		if len(m._past_points) < 1:
			f.write(f"| N/A | N/A |\n")
		else:
			f.write(f"| {m._past_points[-1]} ")
			f.write(f"| {m._past_ranks[-1]} ")

		f.write(f"|\n")

def league_table_html(league,gw,awardkey=None):
	global api
	global json

	html_buffer = ""

	if awardkey == 'season':
		print(json[str(league.id)]['season'])

	create_key(json[str(league.id)][gw], 'positions')

	show_fix_played = api._live_gw
	show_avg_select = gw == 1
	# show_team_value = not api._live_gw
	show_team_value = False
	show_pos_delta = False
	show_tot_score = gw > 1
	show_gw_rank = gw > 1
	# show_transfers = gw > 1 and not api._live_gw
	show_transfers = gw > 1

	html_buffer += '<div class="w3-responsive">\n'
	html_buffer += '<table class="w3-table w3-hoverable responsive-text">\n'
	html_buffer += '<thead>\n'
	html_buffer += '<tr>\n'

	html_buffer += '<th class="w3-center">#</th>\n'
	html_buffer += '<th>Team Name</th>\n'
	html_buffer += '<th>Manager</th>\n'

	if show_tot_score:
		html_buffer += '<th style="text-align:center;">Score</th>\n'
	
	html_buffer += f'<th style="text-align:center;">(GW{gw})</th>\n'
	html_buffer += '<th style="text-align:right;">Rank</th>\n'

	if show_gw_rank:
		html_buffer += f'<th style="text-align:right;">(GW{gw})</th>\n'

	html_buffer += '<th>Captain</th>\n'

	if show_fix_played:
		html_buffer += '<th style="text-align:center;">Fix.</th>\n'

	if show_avg_select:
		html_buffer += '<th style="text-align:center;">Ownership</th>\n'

	if show_team_value:
		html_buffer += '<th style="text-align:center;">Team Value</th>\n'

	if show_transfers:
		html_buffer += '<th>Trans.</th>\n'

	html_buffer += '</tr>\n'
	html_buffer += '</thead>\n'
	
	html_buffer += '<tbody>\n'

	sorted_managers = sorted(league.managers, key=lambda x: x.total_livescore, reverse=True)

	diamond_count = 0

	for i,m in enumerate(sorted_managers):

		is_last = i+1 == len(sorted_managers)

		# print(i,m.id,4+diamond_count)

		if 'Toilet' in league.name and m.is_diamond and m.id != 3902717:
			diamond_count += 1
			# html_buffer += '<tr class="w3-pale-blue">\n'
		elif 'Toilet' in league.name and not m.is_diamond and m.id != 3902717 and i <= 3 + diamond_count:
			# print('dimiond')
			html_buffer += '<tr class="w3-pale-green">\n'
		elif 'Diamond' in league.name and i >= len(sorted_managers)-4:
			html_buffer += '<tr class="w3-pale-red">\n'
		elif i == 0:
			html_buffer += '<tr class="w3-pale-yellow">\n'
		# elif i == 1:
		# 	html_buffer += '<tr class="w3-gainsboro">\n'
		# elif i == 2:
		# 	html_buffer += '<tr class="w3-peru">\n'
		else:
			html_buffer += '<tr>\n'

		if is_last:
			pos_str = '🥚'
		else:
			pos_str = f'{i+1}'

		if show_pos_delta: 
			if league.name in m._league_positions.keys() and str(int(gw-1)) in m._league_positions[league.name].keys():
				delta = m._league_positions[league.name][str(int(gw-1))] - i
				if delta != 0:
					if delta < 0:
						color='red'
					else:
						color='green'
					html_buffer += f'<td class="w3-center"><span class="w3-tag w3-{color}">'
					html_buffer += f'{pos_str}</span></td>\n'
				else:
					html_buffer += f'<td class="w3-center">{pos_str}</td>\n'
			else:
				html_buffer += f'<td class="w3-center">{pos_str}</td>\n'
		else:
			html_buffer += f'<td class="w3-center">{pos_str}</td>\n'

		# team
		html_buffer += f'<td><img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}?raw=true" alt="Kit Icon" width="22" height="29"> <a href="{m.gui_url}">{m.team_name}</a></td>\n'

		# manager
		html_buffer += f'<td><a href="{m.gui_url}">{m.name}</a>'
		# if 'Toilet' in league.name:
			# print(m.name,m.is_diamond,m._league_positions)
		if 'Toilet' in league.name and m.is_diamond:
			html_buffer += " 💎"
		elif m.id == 3902717:
			html_buffer += " 🚫"
		
		if awardkey is None:
			awardkey = gw

		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['king']: html_buffer += " 👑"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['cock']: html_buffer += " 🐓"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['goals']: html_buffer += " ⚽️"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['scientist']: html_buffer += " 🧑‍🔬"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['boner']: html_buffer += " 🦴"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['smooth_brain']: html_buffer += " 🧠"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['chair']: html_buffer += " 🪑"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['asbo']: html_buffer += " 🥊"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['fortune']: html_buffer += " 🔮"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['clown']: html_buffer += " 🤡"
		except: pass
		
		try: 
			if m.id in json[str(league.id)][awardkey]['awards']['innovator']: html_buffer += " 🎓"
		except: pass

		html_buffer += '</td>\n'

		if show_tot_score:
			html_buffer += f'<td style="text-align:center;">{m.total_livescore:,}</td>\n'
		
		if m._bb_week == gw:
			html_buffer += f'<td class="w3-blue" style="text-align:center;"><strong>BB</strong> {m.livescore}</td>\n'
		elif m._fh_week == gw:
			html_buffer += f'<td class="w3-green" style="text-align:center;"><strong>FH</strong> {m.livescore}</td>\n'
		else:
			html_buffer += f'<td style="text-align:center;">{m.livescore}</td>\n'

		html_buffer += f'<td style="text-align:right;">{api.big_number_format(m.overall_rank)}</td>\n'

		if show_gw_rank:
			html_buffer += f'<td style="text-align:right;">{api.big_number_format(m.gw_rank)}</td>\n'

		if m._tc_week == gw:
			html_buffer += f'<td class="w3-amber"><strong>TC</strong> {m.captain} ({3*m.captain_points})'
			html_buffer += '</td>\n'
		else:
			html_buffer += f'<td>{m.captain} ({2*m.captain_points})'
			html_buffer += '</td>\n'

		if show_fix_played:
			html_buffer += f'<td style="text-align:center;">{m.fixtures_played}/{m.total_fixtures}</td>\n'

		if show_avg_select:
			html_buffer += f'<td style="text-align:center;">{m.avg_selection:.1f}%</td>\n'

		if show_team_value:
			html_buffer += f'<td style="text-align:center;">£{m.team_value:.1f}</td>\n'

		if show_transfers:
			if m.is_dead:
				html_buffer += f'<td class="w3-black" style="text-align:center;">💀</td>\n'
			else:
				transfer_str = m.get_transfer_str(short=True).rstrip().replace('\n','<br>')
				if '**WC**' in transfer_str:
					transfer_str = transfer_str.replace('**WC**','<strong>WC</strong>')
					html_buffer += f'<td class="w3-red" style="text-align:center;">{transfer_str}</td>\n'
				else:
					html_buffer += f'<td style="text-align:center;">{transfer_str}'
					hits = int(m.get_transfer_cost(gw)/4)
					if hits > 0:
						for i in range(hits):
							html_buffer += f' <span class="w3-tag"><strong>H</strong></span>'
					html_buffer += '</td>\n'

		html_buffer += f'</tr>\n'

		json[str(league.id)][gw]['positions'][m.id] = i

	html_buffer += '</tbody>\n'
	html_buffer += '</table>\n'
	html_buffer += '</div>\n'

	global _league_table_html
	_league_table_html[league.id] = html_buffer

	return html_buffer

# @mout.debug_log
def league_template(league,gw):

	html_buffer = ""

	html_buffer += position_template(league, league.captains, "Captain", gw)	
	html_buffer += position_template(league, league.starting_goalkeepers, "Goalkeeper", gw)
	html_buffer += position_template(league, league.starting_defenders, "Defence", gw)
	html_buffer += position_template(league, league.starting_midfielders, "Midfield", gw)
	html_buffer += position_template(league, league.starting_forwards, "Forwards", gw)
	
	html_buffer += ownership_template(league, "Effective Ownership", gw)
	
	html_buffer += f'</table>\n'

	return html_buffer

def ownership_template(league,title,gw):

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
			d = dict(shortteam=team.shortname,position='Attack',multiplier=mult_attacker/league.num_managers,kit_path=team._kit_path,points=sum_attacker/mult_attacker,started=started)
			data.append(d)
		
		if mult_defender > 0:
			d = dict(shortteam=team.shortname,position='Defence',multiplier=mult_defender/league.num_managers,kit_path=team._kit_path,points=sum_defender/mult_defender,started=started)
			data.append(d)

	data = sorted(data,key=lambda x: x['multiplier'],reverse=True)

	### STORE THE DATA
	create_key(json[str(league.id)][gw],'template')
	create_key(json[str(league.id)][gw]['template'],'ownership')
	json[str(league.id)][gw]['template']['ownership'] = data

	### DO THE HTML
	html_buffer = ""
	html_buffer += '<div class="w3-col s12 m6 l4">\n'

	html_buffer += f'<div class="w3-panel w3-white w3-center shadow89" style="padding:0px;padding-top:0px;padding-bottom:4px;">\n'
	html_buffer += f'<h2>{title}</h2>\n'

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

	for i,d in enumerate(data[:10]):
		html_buffer += f'<tr style="vertical-align:middle;">\n'
		
		html_buffer += f'<td style="vertical-align:middle;text-align:right;"><b>{ranks[i]}</b></td>'

		html_buffer += f'<td style="vertical-align:middle;">'
		html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{d["kit_path"]}?raw=true" alt="Kit Icon" width="22" height="29">'

		html_buffer += f' {d["shortteam"]} \n'
		html_buffer += f'{d["position"]}</td>\n'
		html_buffer += f'<td style="vertical-align:middle;text-align:right;">{d["multiplier"]:.0%}   </td>\n'

		html_buffer += f'<td style="text-align:center;">\n'

		if d["started"]:
			style_str = get_style_from_event_score(d["points"]).rstrip('"')+';text-align:right;vertical-align:middle;"'
			html_buffer += f'<span class="w3-tag" style={style_str}>{d["points"]:.1f}pts</span>\n'

		html_buffer += f'</td>\n'

		html_buffer += f'</tr>\n'

	html_buffer += f'</table>\n'
	html_buffer += f'</div>\n'
	html_buffer += f'</div>\n'

	return html_buffer

def position_template(league,players,pos_str,gw):
	global json

	html_buffer = ""

	html_buffer += '<div class="w3-col s12 m6 l4">\n'

	create_key(json[str(league.id)][gw],'template')
	create_key(json[str(league.id)][gw]['template'],pos_str.lower())

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
	for i,(name,count) in enumerate(data.most_common()[0:5]):

		if i == 0:
			p = Player(name,api)
			score = p.get_event_score()

			html_buffer += f'<div class="w3-panel w3-white shadow89" style="padding:0px;padding-top:0px;padding-bottom:4px;">\n'
			html_buffer += f'<div class="w3-center w3-{p.shortteam.lower()}-inv w3-{p.shortteam.lower()}-border-inv" style="padding:0px;padding-bottom:0px;">\n'

			html_buffer += f'<h2>{pos_str}</h2>\n'

			html_buffer += f'<img class="w3-image hide-if-narrow" style="width:30%" src="{p._photo_url}?raw=true"></img>\n'

			html_buffer += f'</div>\n'

			html_buffer += '<div class="w3-white">\n'
			
			html_buffer += f'<table class="w3-table w3-hoverable responsive-text">\n'

		html_buffer += f'<tr style="vertical-align:middle;">\n'
		if count > 1:
			p = Player(name,api)
			score = p.get_event_score()
			flag_str = ""
			if p.is_yellow_flagged:
				flag_str = f'⚠️ '
			elif p.is_yellow_flagged:
				flag_str = f'⛔️ '
			html_buffer += f'<td style="vertical-align:middle;text-align:left;">\n'
			html_buffer += f'<b>{ranks[i]}</b>\n'
			html_buffer += f'</td>\n'
			html_buffer += f'<td style="vertical-align:middle;text-align:right;">\n'
			html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{p.kit_path}?raw=true" alt="Kit Icon" width="22" height="29">'
			html_buffer += f'</td>\n'
			html_buffer += f'<td style="vertical-align:middle;">\n'
			html_buffer += f'<a href="{p._gui_url}">{p.name}</a>\n'
			html_buffer += f'</td>\n'
			html_buffer += f'<td style="vertical-align:middle;text-align:right;">\n'
			html_buffer += f'{count/league.num_managers:.1%}\n'
			html_buffer += f'</td>\n'
			if score is not None:
				style_str = get_style_from_event_score(score).rstrip('"')+';text-align:right;vertical-align:middle;"'
				# html_buffer += f'<td style={style_str}>\n'
				html_buffer += f'<td style="text-align:center;">\n'
				# html_buffer += f'{score}\n'
				html_buffer += f'<span class="w3-tag" style={style_str}>{score}pts</span>\n'
				html_buffer += f'</td>\n'
			else:
				html_buffer += f'<td>\n'
				html_buffer += f'</td>\n'
			# if i < 2:
			# 	html_buffer += f'<td>\n'
			# 	html_buffer += f'</td>\n'
			archive.append([p.id,count/league.num_managers,score])
		else:
			break
		html_buffer += f'</tr>\n'
	json[str(league.id)][gw]['template'][pos_str.lower()] = archive
	
	html_buffer += f'</table>\n'

	html_buffer += f'</div>\n'
	html_buffer += f'</div>\n'
	html_buffer += f'</div>\n'

	return html_buffer

def league_differentials(league,gw):
	global json

	html_buffer = ""

	players = league.get_starting_players(unique=False)

	sorted_players = sorted(players, key=lambda p: (p.multiplier*p.get_event_score(not_playing_is_none=False)/p.league_count, 1/p.league_count), reverse=True)

	html_buffer += f'<table class="w3-table responsive-text">\n'
	# html_buffer += f'<tr>\n'
	# html_buffer += f'<th>Player</th>\n'
	# html_buffer += f'<th>Points</th>\n'
	# html_buffer += f'<th>Team</th>\n'
	# html_buffer += f'<th>Summary</th>\n'
	# html_buffer += f'</tr>\n'

	archive = []

	for p in sorted_players[:5]:
		m = p._parent_manager
		score, summary = p.get_event_score(summary=True,not_playing_is_none=False,team_line=False)
		summary = summary.replace("\n","<br>")

		html_buffer += f'<tr>\n'
		html_buffer += f'<td style="vertical-align:middle;mid-width:25px;">\n'
		html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{p.kit_path}?raw=true" alt="Kit Icon" width="22" height="29">'
		html_buffer += f'</td>\n'
		html_buffer += f'<td style="vertical-align:middle;">\n'
		html_buffer += f'<a href="{p._gui_url}">{p.name}</a>\n'

		if p.is_yellow_flagged:
			html_buffer += f'⚠️ '
		elif p.is_yellow_flagged:
			html_buffer += f'⛔️ '
		if p.is_captain:
			html_buffer += f" (C) "

		html_buffer += f'</td>\n'

		html_buffer += f'<td style="vertical-align:middle;">\n'
		style_str = get_style_from_event_score(score).rstrip('"')+';text-align:right;vertical-align:middle;"'
		html_buffer += f'<span class="w3-tag" style={style_str}>{p.multiplier*score}pts</span>\n'
		html_buffer += f'</td>\n'

		html_buffer += f'<td style="vertical-align:middle;mid-width:25px;">\n'
		html_buffer += f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{m._kit_path}?raw=true" alt="Kit Icon" width="22" height="29">'
		html_buffer += f'</td>\n'
		html_buffer += f'<td style="vertical-align:middle;">\n'
		html_buffer += f'<a href="{m.gui_url}">{m.team_name}</a>\n'
		html_buffer += f'<br><a href="{m.gui_url}">{m.name}</a>\n'
		html_buffer += f'</td>\n'
		html_buffer += f'<td style="vertical-align:middle;">\n'
		html_buffer += f"{summary}\n"
		html_buffer += f'</td>\n'
		html_buffer += f'</tr>\n'
		archive.append([p.id,m.id,p.is_captain,p.multiplier*score])
		# print(p.name,p.league_count,p.multiplier*p.get_event_score(not_playing_is_none=False)/p.league_count)
	
	html_buffer += f'</table>\n'

	json[str(league.id)][gw]['differentials'] = archive

	return html_buffer

def launchd_plist(interval=3600):

	f = open("/Users/mw00368/Library/LaunchAgents/com.mwinokan.fpl.wiki.plist",'w')

	str_buffer = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
	<dict>
		<key>Label</key>
		<string>com.mwinokan.fpl.wiki</string>
		<key>RunAtLoad</key>
		<true/>
		<key>ProgramArguments</key>
		<array>
			<string>/Users/mw00368/miniconda3/bin/python3</string>
			<string>/Users/mw00368/Box/Python/FPL_GUI/wiki.py</string>
		</array>
		<key>EnvironmentVariables</key>
		<dict>
			<key>PATH</key>
			<string>/Users/mw00368/miniconda3/bin:/Users/mw00368/miniconda3/condabin:/Users/mw00368/bin:/Applications/Sublime Merge.app/Contents/SharedSupport/bin:/Applications/Sublime Text.app/Contents/SharedSupport/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/TeX/texbin:/usr/local/munki:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/Users/mw00368/MShTools:/Users/mw00368/MolParse:/Users/mw00368/MPyTools</string>
			<key>PYTHONPATH</key>
			<string>/Users/mw00368/MolParse:/Users/mw00368/MPyTools</string>
		</dict>
		<key>StandardInPath</key>
		<string>/Users/mw00368/Box/Python/FPL_GUI/daemon.stdin</string>
		<key>StandardOutPath</key>
		<string>/Users/mw00368/Box/Python/FPL_GUI/daemon.stdout</string>
		<key>StandardErrorPath</key>
		<string>/Users/mw00368/Box/Python/FPL_GUI/daemon.stderr</string>
		<key>WorkingDirectory</key>
		<string>/Users/mw00368/Box/Python/FPL_GUI</string>
		<key>StartInterval</key>"""
	str_buffer += f"		<integer>{interval}</integer>"
	str_buffer += """	</dict>
</plist>"""
		
		# <key>StartCalendarInterval</key>
		# <dict>
		#     <key>Hour</key>
		#     <integer>9</integer>
		#     <key>Minute</key>
		#     <integer>51</integer>
		# </dict>

	f.write(str_buffer)
	f.close()

	import os
	os.system("launchctl unload ~/Library/LaunchAgents/com.mwinokan.fpl.wiki.plist")
	os.system("launchctl load ~/Library/LaunchAgents/com.mwinokan.fpl.wiki.plist")

	print("/Users/mw00368/Library/LaunchAgents/com.mwinokan.fpl.wiki.plist")
	print("first time:")
	print("launchctl bootstrap gui/$(id -u) com.mwinokan.fpl.wiki.plist")
	print("start with:")
	print("launchctl start com.mwinokan.fpl.wiki")
	print("see details with:")
	print("launchctl print gui/$UID/com.mwinokan.fpl.wiki")

def clear_logs():
	mout.debugOut(f"clear_logs()")
	import os
	os.system("rm daemon.std*")

def push_changes():
	mout.debugOut(f"push_changes()")
	import os
	os.system(r'rm -v html/*\@*')
	num_changes = int(os.popen("git status | grep 'modified:' | grep -v '.pyc' | wc -l").read())
	if num_changes > 0:
	# os.system(f'cd {path}; git add *.md; git commit -m "auto-generated {timestamp}"; git push; cd {path.replace(".wiki","")}')
		os.system(f'rm kits/*.webp; git add *.py images/*.png go/*.html go/*.py graphs/*.png index.html html/*.html *.json kits/*.png ct_total_fit.json; git commit -m "auto-generated {timestamp}"; git push')
		os.system("terminal-notifier -title 'FPL_GUI' -message 'Completed Wiki Update' -open 'https://mwinokan.github.io/FPL_GUI/index.html'")
		exit(code=69)
	else:
		os.system("terminal-notifier -title 'FPL_GUI' -message 'No changes pushed' -open 'https://mwinokan.github.io/FPL_GUI/index.html'")
		exit(code=70)

def pull_changes():
	mout.debugOut(f"pull_changes()")
	import os
	os.system(f'git pull')

def create_key(json,key):
	if key not in json.keys():
		json[key] = {}

def load_json():
	from os.path import exists
	if exists(JSON_PATH):
		f = open(JSON_PATH,"rt")
		return js.load(f)
	else:
		return {}

def dump_json(data):

	new_dict = {}

	for pair in data.items():
		if pair[0] not in new_dict.keys():
			new_dict[pair[0]] = pair[1]
	
	f = open(JSON_PATH,"wt")
	js.dump(new_dict, f, indent="\t")

if __name__ == '__main__':
	main()

'''

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

	Pre-Season:

	- Position
	- Team Name
	- Manager
	* Previous Score
	* Previous Rank			

	GW1 Live:						GW1 not Live:
									
	- Position						- Position					
	- Team Name						- Team Name					
	- Manager						- Manager					
	- GW Score						- GW Score					
	- Rank							- Rank						
	- Captain (Points)				- Captain (Points)			
	* Fixtures Played				- Points/fixture						
	- Points/fixture				* Average Player Selection
	* Average Player Selection		* Team Value

	GW1 Live:						GW1 not Live:
									
	* Position (Delta)				* Position (Delta)
	- Team Name						- Team Name					
	- Manager						- Manager					
	* Total Score					* Total Score					
	- GW Score						- GW Score					
	- Rank							- Rank						
	* GW Rank						* GW Rank						
	- Captain (Points)				- Captain (Points)			
	* Fixtures Played				- Points/fixture						
	- Points/fixture 				* Team Value

'''