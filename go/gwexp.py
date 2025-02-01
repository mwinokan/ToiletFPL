#!/usr/bin/env python3

import api as fpl_api
from player import Player
import plotly.graph_objects as go
# import plotly.io as pio 
from plotly.offline import plot
import re
import mout

def main():

	api = fpl_api.FPL_API()

	players = []

	player_ids = api._elements['id']
	for i,pid in enumerate(player_ids):
		if i%50 == 0:
			print(i)

		if api._elements['minutes'][i] < minutes:
			continue

		index = api.get_player_index(pid)
		p = Player(None, api, index=index)
		players.append(p)

	create_gwexp_figure(api,players,show=True)

def create_gwexp_figure(api,players,show=False):
	gw = api._current_gw
	mout.debugOut(f"create_gwexp_figure(gw={gw+1})")

	budget = None
	position = None
	minutes = 90

	xdata_gkp = []
	ydata_gkp = []
	tdata_gkp = []
	sdata_gkp = []
	udata_gkp = []
	xdata_def = []
	ydata_def = []
	tdata_def = []
	sdata_def = []
	udata_def = []
	xdata_mid = []
	ydata_mid = []
	tdata_mid = []
	sdata_mid = []
	udata_mid = []
	xdata_fwd = []
	ydata_fwd = []
	tdata_fwd = []
	sdata_fwd = []
	udata_fwd = []


	maximum = len(players)

	for i,p in enumerate(players):
		mout.progress(i,maximum)

		# official_gwexp = p.expected_points(gw=gw+1,fit_ratio=0.8,use_official=True,debug=False)
		gwexp = p.expected_points(gw=gw+1,use_official=True,debug=False,force=True)
		
		form = p.form

		if gwexp == 0:
			continue

		size = p.selected_by/2+5

		if p.position_id == 1:
			xdata_gkp.append(form)
			ydata_gkp.append(gwexp)
			tdata_gkp.append(f'{p.name}, {p.team_obj.shortname}, {p.selected_by}%')
			sdata_gkp.append(size)
			udata_gkp.append(f'{p._gui_url}')
		elif p.position_id == 2:
			xdata_def.append(form)
			ydata_def.append(gwexp)
			tdata_def.append(f'{p.name}, {p.team_obj.shortname}, {p.selected_by}%')
			sdata_def.append(size)
			udata_def.append(f'{p._gui_url}')
		elif p.position_id == 3:
			xdata_mid.append(form)
			ydata_mid.append(gwexp)
			tdata_mid.append(f'{p.name}, {p.team_obj.shortname}, {p.selected_by}%')
			sdata_mid.append(size)
			udata_mid.append(f'{p._gui_url}')
		elif p.position_id == 4:
			xdata_fwd.append(form)
			ydata_fwd.append(gwexp)
			tdata_fwd.append(f'{p.name}, {p.team_obj.shortname}, {p.selected_by}%')
			sdata_fwd.append(size)
			udata_fwd.append(f'{p._gui_url}')

	mout.progress(maximum,maximum)

	fig = go.Figure()
	fig.add_trace(go.Scatter(name="Goalkeepers",opacity=0.8,x=xdata_gkp, y=ydata_gkp, text=tdata_gkp, marker_size=sdata_gkp, customdata=udata_gkp, textposition='middle right', mode='markers'))
	fig.add_trace(go.Scatter(name="Defenders",opacity=0.8,x=xdata_def, y=ydata_def, text=tdata_def, marker_size=sdata_def, customdata=udata_def, textposition='middle right', mode='markers'))
	fig.add_trace(go.Scatter(name="Midfielders",opacity=0.8,x=xdata_mid, y=ydata_mid, text=tdata_mid, marker_size=sdata_mid, customdata=udata_mid, textposition='middle right', mode='markers'))
	fig.add_trace(go.Scatter(name="Forwards",opacity=0.8,x=xdata_fwd, y=ydata_fwd, text=tdata_fwd, marker_size=sdata_fwd, customdata=udata_fwd, textposition='middle right', mode='markers'))

	fig.update_traces(marker=dict(line=dict(width=1,color='Black')),selector=dict(mode='markers'))

	fig.update_layout(legend_title_text = "Position",autosize=True,margin=dict(l=20, r=20, t=20, b=20))
	fig.update_xaxes(title_text=f"Form")
	# fig.update_xaxes(title_text=f"Official GW{gw} xPts")
	fig.update_yaxes(title_text=f"GW{gw+1} xPts")

	# Get HTML representation of plotly.js and this figure
	plot_div = plot(fig, output_type='div', include_plotlyjs=False)

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
	""".format(div_id=div_id)

	# Build HTML string
	html_str = """{plot_div}
	{js_callback}
	""".format(plot_div=plot_div, js_callback=js_callback)

	# # Write out HTML file
	# with open('go/value.html', 'w') as f:
	#     f.write(html_str)

	return html_str

	# pio.write_html(fig, file='go/value.html', auto_open=show)
	# fig.show()

if __name__ == '__main__':
	main()
