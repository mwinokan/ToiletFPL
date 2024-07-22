
import mout

class Team():

	def __init__(self, id, name, api, shortname = None):

		self._api = api

		self._id = id
		self._name = name
		self._shortname = shortname

		self._badge_url = None
		for i,name in api._scrape_team_pairs:
			if name == self._name:
				# self._badge_url = f"https://resources.premierleague.com/premierleague/badges/25/t{i+1}@x2.png"
				self._badge_url = f"https://resources.premierleague.com/premierleague/badges/50/t{i+1}@x2.png"
				# https://resources.premierleague.com/premierleague/badges/50/t40@x2.png
				break

		if self._badge_url is None:
			mout.error(f'No badge url for Team: {self.name} {self.id}')

		self._fixtures = None

		self._style = self.get_style()

		# self._badge_path = f"kits/{self._name}.png"
		self._kit_path = f"kits/{self._name}.png"
		self._kit_path_gkp = f"kits/{self._name}_gkp.png"

		# print(id,name)

		# self._code = self._api._teamdata['code'][id]

		# print('code',self._api._teamdata['code'][id-1])
		# print('draw',self._api._teamdata['draw'][id-1])
		# print('form',self._api._teamdata['form'][id-1])
		# print('loss',self._api._teamdata['loss'][id-1])
		# print('name',self._api._teamdata['name'][id-1])
		# print('played',self._api._teamdata['played'][id-1])
		# print('points',self._api._teamdata['points'][id-1])
		# print('position',self._api._teamdata['position'][id-1])
		# print('strength',self._api._teamdata['strength'][id-1])
		# print('team_division',self._api._teamdata['team_division'][id-1])
		# print('unavailable',self._api._teamdata['unavailable'][id-1])
		# print('win',self._api._teamdata['win'][id-1])

		self._strength_overall_home = self.scale_strength(self._api._teamdata['strength_overall_home'][id-1])
		self._strength_overall_away = self.scale_strength(self._api._teamdata['strength_overall_away'][id-1])
		self._strength_attack_home = self.scale_strength(self._api._teamdata['strength_attack_home'][id-1])
		self._strength_attack_away = self.scale_strength(self._api._teamdata['strength_attack_away'][id-1])
		self._strength_defence_home = self.scale_strength(self._api._teamdata['strength_defence_home'][id-1])
		self._strength_defence_away = self.scale_strength(self._api._teamdata['strength_defence_away'][id-1])

		self._goals_scored = None
		self._goals_conceded = None
		self._clean_sheets = None
		self._clean_sheets_broken = None
		self._games_played = None
		self._difficulty_next5 = None

		self._prev_obj = None

		self._shortname = self._api._teamdata['short_name'][id-1]

		# print(self._api._prev_teamdata)
		# print(self._api._prev_teamdata.columns)

		# exit()

	def strength(self,is_home=True,overall=False,defence=False):
		if is_home:
			if overall:
				return self._strength_overall_home
			elif defence:
				return self._strength_defence_home
			else:
				return self._strength_attack_home
		else:
			if overall:
				return self._strength_overall_away
			elif defence:
				return self._strength_defence_away
			else:
				return self._strength_attack_away

	def scale_strength(self,input):
		output = (input - 1000)/100
		if output < 0:
			print("Warning: Strength underflow")
		if output > 400:
			print("Warning: Strength overflow")
		return output

	def get_style(self):

		try:
			return self._api.team_styles[self._name]
		except KeyError:
			print(f"No style found for {self.name}")
			return None

		# print(self._id)
		# print(self._name)

	@property
	def shortname(self):
		return self._shortname

	def get_gw_fixtures(self,gw):

		fixs = []

		for fix_d in self.fixtures:
			if fix_d['event'] == gw:
				fixs.append(fix_d)

		match len(fixs):
			case 3:
				self._api._special_gws[gw] = "TGW"
			case 2:
				if gw in self._api._special_gws.keys():
					if self._api._special_gws[gw] == "BGW":
						self._api._special_gws[gw] = "DGW"
				else:
					self._api._special_gws[gw] = "DGW"
			case 0:
				if gw not in self._api._special_gws.keys():
					self._api._special_gws[gw] = "BGW"

		if len(fixs) == 1:
			return fixs[0]
		else:
			return fixs

	def get_opponent(self, gw, not_started_only=False):

		# print(self, gw, not_started_only)

		opps = []

		for fix_d in self.fixtures:

			if not_started_only and fix_d['started']:
				continue

			if fix_d['event'] != gw:
				continue

			if fix_d['team_h'] == self.id:
				t = self._api.teams[fix_d['team_a']-1]
			elif fix_d['team_a'] == self.id:
				t = self._api.teams[fix_d['team_h']-1]
			opps.append(t)

		if len(opps) == 0:
			return None
		elif len(opps) == 1:
			return opps[0]
		else:
			return opps

	# def get_oppname(self,gw):

	# 	opp = self.get_opponent(gw)

	# 	opp.shortname

	@property
	def name(self):
		return self._name
	
	@property
	def id(self):
		return self._id
	
	@property
	def style(self):
		return self._style

	@property
	def goals_scored(self):
		if self._goals_scored is None:
			fix = self.fixtures
		return self._goals_scored

	# @property
	# def goals_scored_wprev(self):
	# 	return self.goals_scored + self._goals_scored_prev
	
	@property
	def goals_conceded(self):
		if self._goals_conceded is None:
			fix = self.fixtures
		return self._goals_conceded
	
	@property
	def clean_sheets(self):
		if self._clean_sheets is None:
			fix = self.fixtures
		return self._clean_sheets
	
	@property
	def clean_sheets_broken(self):
		if self._clean_sheets_broken is None:
			fix = self.fixtures
		return self._clean_sheets_broken
	
	@property
	def games_played(self):
		if self._games_played is None:
			fix = self.fixtures
		return self._games_played

	@property
	def clean_sheet_probability(self):
		if self.games_played == 0:
			return 0
		return self.clean_sheets/self.games_played

	def expected_clean_sheet(self,opponent):
		if isinstance(opponent, list):
			probs = []
			for opp in opponent:
				p = (self.clean_sheet_probability + 1 - opp.clean_sheet_breaking_probability)/2
				p = (p + 1 - min(1.0,self.expected_goals_conceded(opp)))/2
				probs.append(p)
			prob = sum(probs)/len(probs)
		else:
			prob = (self.clean_sheet_probability + 1 - opponent.clean_sheet_breaking_probability)/2
			prob = (prob + 1 - min(1.0,self.expected_goals_conceded(opponent)))/2
		return prob

	def expected_goals_conceded(self,opponent):
		return (self.goals_conceded_per_game + opponent.goals_scored_per_game)/2

	@property
	def clean_sheet_breaking_probability(self):
		if self.games_played == 0:
			return 0
		return self.clean_sheets_broken/self.games_played

	@property
	def goals_conceded_per_game(self):
		if self.games_played == 0:
			return 0
		return self.goals_conceded/self.games_played

	@property
	def goals_scored_per_game(self):
		if self.games_played == 0:
			return 0
		return self.goals_scored/self.games_played

	@property
	def goals_scored_per_game_wprev(self):
		if self.games_played == 0:
			return 0
		return self.goals_scored_wprev/self.games_played_wprev

	@property
	def difficulty_next5(self):
		if not self._difficulty_next5:

			if self._api._current_gw == 38:
				return 0.0

			total = 0
			count = 0

			for gw in range(self._api.current_gw+1,min(self._api.current_gw+5,38)):
				
				fixs = self.get_gw_fixtures(gw)
				
				if not fixs:
					continue
				
				opps = self.get_opponent(gw)

				if not isinstance(fixs, list):
					fixs = [fixs]
					opps = [opps]


				for fix,opp in zip(fixs,opps):

					is_home = fix['team_a'] == opp.id
					total += self.strength(is_home,overall=True) - opp.strength(not is_home,overall=True)
					# total += - opp.strength(not is_home,overall=True)
					count += 1
			if count:
				self._difficulty_next5 = total / count					
			else:
				self._difficulty_next5 = 0

		return self._difficulty_next5

	@property
	def fixtures(self):
		if self._fixtures is None:
			self._fixtures = self._api.get_team_fixtures(self.id)

			self._goals_scored = 0
			self._goals_conceded = 0
			self._clean_sheets = 0
			self._clean_sheets_broken = 0
			self._games_played = 0

			for fix_d in self._fixtures:
				if not fix_d['started']:
					continue
				
				self._games_played += 1

				if fix_d['team_h'] == self.id:
					if fix_d['team_h_score'] > 0:
						self._goals_scored += fix_d['team_h_score']
						self._clean_sheets_broken += 1
					if fix_d['team_a_score'] > 0:
						self._goals_conceded += fix_d['team_a_score']
					else:
						self._clean_sheets += 1
				elif fix_d['team_a'] == self.id:
					if fix_d['team_a_score'] > 0:
						self._goals_scored += fix_d['team_a_score']
						self._clean_sheets_broken += 1
					if fix_d['team_h_score'] > 0:
						self._goals_conceded += fix_d['team_h_score']
					else:
						self._clean_sheets += 1

			self._goals_scored = int(self._goals_scored)
			self._goals_conceded = int(self._goals_conceded)
			self._clean_sheets = int(self._clean_sheets)
			self._clean_sheets_broken = int(self._clean_sheets_broken)
			self._games_played = int(self._games_played)

		return self._fixtures
	
	def get_fixture_diff(self,gw,attacker):
		return 0.0

	def __repr__(self):
		return self._name