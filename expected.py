
# def multiplier(gw_diff):
# 	return 4 / ((gw_diff-1)/8.0 + 2.5) + 0.5

import numpy as np

def multiplier(gw_diff):
	return 5.5 * np.exp(-(gw_diff-1)/20.0) + 0.5

def weighted_average(this_season_by_gw,this_season_minutes_by_gw=None,last_season_total=None,last_season_minutes=None,plot=False,last_season_weight=1.0):

	"""

	this_season: [float]
	last_season_average: float

	"""

	total_multiplier = 0
	total_value = 0
	n = len(this_season_by_gw)

	if this_season_minutes_by_gw is None:
		this_season_minutes_by_gw = [1]*n

	for i,(value,mins) in enumerate(zip(this_season_by_gw,this_season_minutes_by_gw,strict=True)):
		if mins == 0:
			continue
		total_multiplier += multiplier(n-i) * mins
		total_value += value * multiplier(n-i)

	if last_season_total is not None:

		total_multiplier += last_season_weight * last_season_minutes
		total_value += last_season_weight * last_season_total

	if total_multiplier == 0:
		result = 0.0
	else:
		result = total_value / total_multiplier

	if plot:
		import plotly.graph_objects as go

		plot_x = []
		plot_y = []
		plot_mult = []
		
		for i,(value,mins) in enumerate(zip(this_season_by_gw,this_season_minutes_by_gw,strict=True)):
			if mins == 0:
				continue
			plot_x.append(n-i)
			plot_y.append(value/mins)
			plot_mult.append(multiplier(n-i))

		fig = go.Figure()

		trace = go.Scatter(name='values',x=plot_x,y=plot_y,mode='markers')
		fig.add_trace(trace)

		trace = go.Scatter(name='multiplier',x=plot_x,y=plot_mult,mode='lines')
		fig.add_trace(trace)

		if last_season_total is not None:
			trace = go.Scatter(name='last_season',x=[n,n+38],y=[last_season_total/last_season_minutes,last_season_total/last_season_minutes],mode='lines')
			fig.add_trace(trace)

		fig.add_hline(name='weighted_average',y=result)
		# fig.add_hline(name='average',y=sum(this_season_by_gw)/sum(this_season_minutes_by_gw))

		fig.show()

	return result


def scale_by_sample_size(value,samples,default=1.0,steepness=5):
	scaled =  value - np.exp((1.0-samples)/steepness)*(value-default)
	return scaled