#!/usr/bin/env python3

import api as fpl_api
from player import Player
import plotly.graph_objects as go
# import plotly.io as pio 
from plotly.offline import plot
import re
import mout

def create_vapm_figure(api,players,show=False, return_fig=False):

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

	gw = api._current_gw

	maximum = len(players)

	for i,p in enumerate(players):
		mout.progress(i,maximum)

		# next5_sum = 0
		# for i in range(gw,gw+6):
		# 	next5_sum += p.expected_points(gw=i,use_official=False)

		# next5_sum = float(f'{next5_sum:.1f}')

		size = p.selected_by/2+5

		if p.position_id == 1:
			xdata_gkp.append(p.price-4.0)
			# xdata_gkp.append(p.price)
			ydata_gkp.append(p.form)
			tdata_gkp.append(f'{p.name}, {p.team_obj.shortname}, {p.selected_by}%')
			sdata_gkp.append(size)
			udata_gkp.append(f'{p._gui_url}')
		elif p.position_id == 2:
			xdata_def.append(p.price-4.0)
			# xdata_def.append(p.price)
			ydata_def.append(p.form)
			tdata_def.append(f'{p.name}, {p.team_obj.shortname}, {p.selected_by}%')
			sdata_def.append(size)
			udata_def.append(f'{p._gui_url}')
		elif p.position_id == 3:
			xdata_mid.append(p.price-4.5)
			# xdata_mid.append(p.price)
			ydata_mid.append(p.form)
			tdata_mid.append(f'{p.name}, {p.team_obj.shortname}, {p.selected_by}%')
			sdata_mid.append(size)
			udata_mid.append(f'{p._gui_url}')
		elif p.position_id == 4:
			xdata_fwd.append(p.price-4.5)
			# xdata_fwd.append(p.price)
			ydata_fwd.append(p.form)
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
	# fig.update_xaxes(title_text="Price - ")
	fig.update_xaxes(title_text="Price (Relative to Fodder)")
	fig.update_yaxes(title_text="Form")

	if return_fig:
		return fig


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
