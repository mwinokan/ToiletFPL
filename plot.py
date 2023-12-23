
import plotly.graph_objects as go

def event_points(managers,api,show=True,relative=False):

	traces = []
	
	avgs = api.get_event_averages()
	x = [i+1 for i in range(len(avgs))]

	if not relative:
		traces.append(go.Scatter(x=x,y=avgs,name="Average",mode="lines"))

	for manager in managers:

		text = manager.chip_text_list()

		if not relative:
			y = manager._event_points
		else:
			y = []
			for avg,pts in zip(avgs,manager._event_points):
				y.append(pts-avg)

		traces.append(go.Scatter(x=x,y=y,text=text,textposition="bottom center",
									name=manager.name,mode="lines+markers+text"))

	# api.get_event_averages()

	fig = go.Figure(data=traces)

	fig.update_xaxes(title=dict(text="Gameweek"))
	if not relative:
		# fig.update_yaxes(title=dict(text="Event Points"),range=[0,100])
		fig.update_yaxes(title=dict(text="Event Points"))
	else:
		fig.update_yaxes(title=dict(text="Event Points (Relative)"))

	if not relative:
		write_image(fig,"event_points.png")
	else:
		write_image(fig,"event_points_relative.png")

	if show:
		fig.show()

def total_points(managers,api,show=True,relative=False):

	traces = []

	avgs = api.get_event_averages()


	new_avgs = []
	for i,avg in enumerate(avgs):
		new_avgs.append(sum(avgs[0:i+1]))
	avgs = new_avgs

	x = [i+1 for i in range(len(avgs))]

	if not relative:
		traces.append(go.Scatter(x=x,y=avgs,name="Average",mode="lines"))

	for manager in managers:
		
		text = [None]+manager.chip_text_list()

		if not relative:
			y = manager._total_points
		else:
			y = []
			for avg,pts in zip(avgs,manager._total_points):
				y.append(pts-avg)

		traces.append(go.Scatter(x=[0]+x,y=[0]+y,text=text,textposition="bottom center",
									name=manager.name,mode="lines+markers+text"))

		# traces.append(go.Scatter(x=[0]+x,y=[0]+y,name=manager.name,mode="lines+markers"))

	fig = go.Figure(data=traces)

	fig.update_xaxes(title=dict(text="Gameweek"))
	if not relative:
		fig.update_yaxes(title=dict(text="Total Points"))
	else:
		fig.update_yaxes(title=dict(text="Total Points (Relative)"))

	if not relative:
		write_image(fig,"total_points.png")
	else:
		write_image(fig,"total_points_relative.png")

	if show:
		fig.show()

def overall_rank(managers,show=True):

	traces = []

	for manager in managers:

		text = manager.chip_text_list()

		y = manager._overall_rank
		x = [i+1 for i in range(len(y))]

		traces.append(go.Scatter(x=x,y=y,text=text,textposition="bottom center",
							name=manager.name,mode="lines+markers+text"))

		# traces.append(go.Scatter(x=x,y=y,name=manager.name,mode="lines+markers"))

	fig = go.Figure(data=traces)

	fig.update_xaxes(title=dict(text="Gameweek"))
	fig.update_yaxes(title=dict(text="Overall Rank"),type="log",autorange="reversed")

	write_image(fig,"overall_rank.png")

	if show:
		fig.show()

def gameweek_rank(managers,show=True):

	traces = []

	for manager in managers:

		text = manager.chip_text_list()

		y = manager._event_rank
		x = [i+1 for i in range(len(y))]

		traces.append(go.Scatter(x=x,y=y,text=text,textposition="bottom center",
							name=manager.name,mode="lines+markers+text"))

	fig = go.Figure(data=traces)

	fig.update_xaxes(title=dict(text="Gameweek"))
	fig.update_yaxes(title=dict(text="Gameweek Rank"),type="log",autorange="reversed")

	write_image(fig,"gameweek_rank.png")

	if show:
		fig.show()

def squad_value(managers,show=True):

	traces = []

	for manager in managers:

		text = manager.chip_text_list()

		y = manager._squad_value
		x = [i+1 for i in range(len(y))]

		traces.append(go.Scatter(x=x,y=y,text=text,textposition="bottom center",
							name=manager.name,mode="lines+markers+text"))

	fig = go.Figure(data=traces)

	fig.update_xaxes(title=dict(text="Gameweek"))
	fig.update_yaxes(title=dict(text="Squad Value"))

	write_image(fig,"squad_value.png")

	if show:
		fig.show()

def rank_history(managers,key,show=False):

	traces = []

	sorted_managers = sorted(managers, key=lambda x: x.last_season_score, reverse=True)

	for manager in sorted_managers:

		text = manager._past_points

		t = manager._past_seasons
		x = [int(T.split("/")[0]) for T in t]
		y = manager._past_ranks

		# traces.append(go.Scatter(x=x,y=y,text=text,textposition="bottom center",name=manager.name,mode="lines+markers+text"))
		traces.append(go.Scatter(x=x,y=y,name=manager.name,mode="lines+markers"))

		# traces.append(go.Scatter(x=x,y=y,name=manager.name,mode="lines+markers"))

	fig = go.Figure(data=traces)

	fig.update_xaxes(title=dict(text="Year"))
	fig.update_yaxes(title=dict(text="Rank History"),type="log",autorange="reversed")

	fig.update_layout(autosize=False,width=900,height=600)

	write_image(fig,f"{key}_rank_history.png")

	if show:
		fig.show()

	return f"{key}_rank_history.png"

def team_strength(teams):
	# print([t.strength(overall=True) for t in teams])

	names = [t._name for t in teams]

	traces = []

	traces.append(go.Scatter(x=names, y=[t.strength(overall=True) for t in teams],
							 name="Overall, Home"))

	traces.append(go.Scatter(x=names, y=[t.strength(overall=True,is_home=False) for t in teams],
							 name="Overall, Away"))

	traces.append(go.Scatter(x=names, y=[t.strength(defence=False,is_home=True) for t in teams],
							 name="Attack, Home"))

	traces.append(go.Scatter(x=names, y=[t.strength(defence=False,is_home=False) for t in teams],
							 name="Attack, Away"))

	traces.append(go.Scatter(x=names, y=[t.strength(defence=True,is_home=True) for t in teams],
							 name="Defence, Home"))

	traces.append(go.Scatter(x=names, y=[t.strength(defence=True,is_home=False) for t in teams],
							 name="Defence, Away"))

	fig = go.Figure(data=traces)
	write_image(fig,"team_strengths.png")
	# fig.show()

def write_image(figure,filename):
	import os
	if not os.path.exists("images"):
	    os.mkdir("images")

	figure.write_image("images/"+filename)
