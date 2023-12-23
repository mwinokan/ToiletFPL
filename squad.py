
class Squad():
	def __init__(self,gw=None,api=None):
		self._api = api
		self._players = []
		if gw is not None:
			self._gw = gw

	def add_player(self,player):
		if player is not None:
			self._players.append(player)

	@property
	def gw(self):
		return self._gw

	

	@property
	def players(self):
		return self._players

	@players.setter
	def players(self,arg):
		self._players = arg

	@property
	def num_players(self):
		return len(self._players)

	def is_valid(self,budget):
		if sum([p.price for p in self.players]) > budget:
			return False
		elif len(self.starting_players) > 15:
			return False
		elif len(self.goalkeepers) > 2:
			return False
		elif len(self.defenders) > 5:
			return False
		elif len(self.midfielders) > 5:
			return False
		elif len(self.forwards) > 3:
			return False
		return True

	# @property
	# def is_valid11(self):
	# 	if len(self.starting_players) != 11:
	# 		return False
	# 	elif len(self.goalkeepers) != 1:
	# 		return False
	# 	elif len(self.defenders) != 5:
	# 		return False
	# 	elif len(self.midfielders) != 5:
	# 		return False
	# 	elif len(self.forwards) != 3:
	# 		return False
	# 	return True

	def remove_last_player(self):
		self.players = self.players[:-2]
	
	@property
	def starting_players(self):
		return [p for p in self._players if p.multiplier > 0]

	@property
	def goalkeepers(self):
		return [p for p in self._players if p.position_id == 1]

	@property
	def defenders(self):
		return [p for p in self._players if p.position_id == 2]

	@property
	def midfielders(self):
		return [p for p in self._players if p.position_id == 3]

	@property
	def forwards(self):
		return [p for p in self._players if p.position_id == 4]

	@property
	def starting_goalkeepers(self):
		return [p for p in self._players if p.position_id == 1 and p.multiplier > 0]

	@property
	def starting_defenders(self):
		return [p for p in self._players if p.position_id == 2 and p.multiplier > 0]

	@property
	def starting_midfielders(self):
		return [p for p in self._players if p.position_id == 3 and p.multiplier > 0]

	@property
	def starting_forwards(self):
		return [p for p in self._players if p.position_id == 4 and p.multiplier > 0]

	@property
	def bench(self):
		return [p for p in self._players if p.multiplier == 0]

	@property
	def captain(self):
		return [p for p in self._players if p.is_captain][0]

	@property
	def vice_captain(self):
		return [p for p in self._players if p.is_vice_captain][0]

	@property
	def value(self):
		return sum([p.price for p in self._players])
	
	@property
	def sorted_players(self,key="position"):
		# position_ids = [p.position_id for p in self.players]
		# return [i for _,i in sorted(zip(position_ids,self.players))]
		return sorted(self.players,key=lambda p: (p.position_id,15-p.price))

	def set_best_multipliers(self,gw,use_official=False,summary=False,debug=False):

		sorted_goalkeepers = sorted(self.goalkeepers, key=lambda x: x.expected_points(gw=gw,debug=debug,use_official=use_official), reverse=True)
		sorted_goalkeepers[0].multiplier = 1
		sorted_goalkeepers[1].multiplier = 0
		
		rest = []

		sorted_defenders = sorted(self.defenders, key=lambda x: x.expected_points(gw=gw,debug=debug,use_official=use_official), reverse=True)
		for p in sorted_defenders[0:3]:
			p.multiplier = 1
		sorted_midfielders = sorted(self.midfielders, key=lambda x: x.expected_points(gw=gw,debug=debug,use_official=use_official), reverse=True)
		for p in sorted_midfielders[0:2]:
			p.multiplier = 1
		sorted_forwards = sorted(self.forwards, key=lambda x: x.expected_points(gw=gw,debug=debug,use_official=use_official), reverse=True)
		sorted_forwards[0].multiplier = 1

		rest += sorted_defenders[3:5]
		rest += sorted_midfielders[2:5]
		rest += sorted_forwards[1:3]
		sorted_rest = sorted(rest, key=lambda x: x.expected_points(gw=gw,debug=debug,use_official=use_official), reverse=True)
		for p in rest:
			p.multiplier = 0

		for p in sorted_rest[0:4]:
			p.multiplier = 1

		sorted_players = sorted(self.players, key=lambda x: x.expected_points(gw=gw,debug=debug,use_official=use_official), reverse=True)[0].multiplier = 2

		if summary:
			for p in self.players:
				print(f'{p.expected_points(gw=gw,debug=debug,use_official=use_official):5.1f}',p.multiplier,p.name)

	def expected_transfer_return(self,gw,player_out,player_in,assume_best_multipliers):

		if not assume_best_multipliers:
			self.set_best_multipliers(gw)

		copy = self.copy()

		copy.players[copy.players.index(player_out)] = player_in

		copy.set_best_multipliers(gw)

		return copy.expected_points(gw) - self.expected_points(gw)

	def next5_expected(self):

		gw = self._api._current_gw

		score = 0

		for i in range(gw,gw+6):

			self.set_best_multipliers(i)

			score += self.expected_points(gw=i)

		return score

		# self.defenders.index(max([p.expected_points(gw) for p in self.defenders]))
		# self.midfielders.index(max([p.expected_points(gw) for p in self.midfielders]))
		# self.forwards.index(max([p.expected_points(gw) for p in self.forwards]))

	def expected_points(self,gw):
		return sum([p.multiplier*p.expected_points(gw=gw) for p in self.players])

	def __str__(self):
		return str([p.name for p in self._players])

	def __len__(self):
		return len(self.players)

