import mout
import json
import datetime
import pytz

local_tz = pytz.timezone("Europe/London")

from expected import weighted_average, scale_by_sample_size
import numpy as np
from pprint import pprint

"""
To-Do's

	+ Improve speed of data access by only 
	  looking up element data if requested 
	  by @property getter call


"""


# import api


class Player:

    _league_count = {}
    _league_multiplier_count = {}

    def __init__(self, name, api, index=None, shortname=None):

        self._api = api

        if name is None:
            self._name = None
            # self._league_count = 1
            # print("player.name=None")
            # if index is None:
            # 	print("player.index=None")
            if not self.get_stats(api, index=index):
                mout.errorOut(
                    "Problem accessing player stats (" + name + ")", fatal=False
                )
                return None
        else:
            # print("player.name!=None")

            if name.isnumeric():
                print("Getting name from index = " + name)
                name = api.get_player_name(int(name))

            self._first_name = ""
            self._name = name
            self._shortname = name
            self._team_id = ""
            self._team = ""
            self._shortteam = ""
            self._price = ""
            self._purchase_price = "-"
            self._selling_price = "-"
            self._position = ""
            self._id = ""
            self._team_obj = None

            if not self.get_stats(api):
                mout.errorOut(
                    "Problem accessing player stats (" + name + ")", fatal=False
                )
                return None

        self._xG_no_opponent = None
        self._xA_no_opponent = None
        self._xC_no_opponent = None
        self._xBpts = None

        self._A_per_xA = None
        self._G_per_xG = None

        self._parent_manager = None
        self._league_count[self._id] = 1
        self._league_multiplier_count[self._id] = None
        self._is_captain = False
        self._multiplier = 1

        self._was_subbed = False
        self._appearances = None
        self._total_minutes = None
        self._attacking_returns_per90 = None
        self._next5_expected = None

        self._weeks_owned = []
        self._weeks_started = []
        self._weeks_benched = []
        self._weeks_captained = []
        self._num_weeks_owned = 0
        self._num_weeks_started = 0
        self._num_weeks_benched = 0
        self._num_weeks_captained = 0
        self._multiplier_history = None

        self._points_while_owned = 0
        self._points_while_started = 0
        self._points_while_captained = 0
        self._points_while_benched = 0

        self.__minutes = None
        self.__goals_scored = None
        self.__assists = None
        self.__clean_sheets = None
        self.__goals_conceded = None
        self.__own_goals = None
        self.__penalties_saved = None
        self.__penalties_missed = None
        self.__yellow_cards = None
        self.__red_cards = None
        self.__saves = None
        self.__bonus = None
        self.__bps = None
        self.__fix_started = None
        self.__fix_finished = None
        self.__total_points = None

        self._gui_url = f"player_{self.id}.html"

        if int(self.id) not in self._api._loaded_players:
            self._api._loaded_players.append(int(self.id))

    def get_stats(self, api, index=None):

        elements = api.elements

        # print(self._name,index)

        if self._name is not None and index is None:

            # print(f"Looking for {self._name}")

            matches = []
            for i, name in enumerate(elements["web_name"]):
                if self._name == elements["first_name"][i] + " " + name:
                    matches = [i]
                    break
                if self._name in elements["first_name"][i] + " " + name:
                    matches.append(i)
        else:
            matches = [index]
            # print(matches)

        if len(matches) == 1:
            i = matches[0]

            # print(elements.keys())

            self._name = elements["web_name"][i]
            self._first_name = elements["first_name"][i]
            self._last_name = elements["second_name"][i]
            self._full_name = f"{self._first_name} {self._last_name}"
            self._team_id = elements["team"][i]
            self._team = api.team_name(elements["team"][i])
            self._shortteam = api.team_name(elements["team"][i], short=True)
            self._price = float(elements["now_cost"][i] / 10)
            self._id = elements["id"][i]

            try:
                self._chance_of_playing_next_round = (
                    int(elements["chance_of_playing_next_round"][i]) / 100
                )
            except ValueError:
                self._chance_of_playing_next_round = 1.0
            try:
                chance = elements["chance_of_playing_this_round"][i]
                # print(f'{chance=}')
                if chance is None:
                    # self._chance_of_playing_this_round = 0
                    self._chance_of_playing_this_round = 1.0
                else:
                    self._chance_of_playing_this_round = int(chance) / 100
            except ValueError:
                self._chance_of_playing_this_round = 1.0

            if self._api._current_gw > 0:
                self._exp_this_round = float(elements["ep_this"][i] or 0.0)
                self._exp_next_round = float(elements["ep_next"][i] or 0.0)
            else:
                self._exp_this_round = 0.0
                self._exp_next_round = 0.0

            self._playing_chance = {}
            # print(f'{self._chance_of_playing_this_round=}')
            self._playing_chance[self._api._current_gw] = (
                self._chance_of_playing_this_round
            )
            self._playing_chance[self._api._current_gw + 1] = (
                self._chance_of_playing_this_round
            )

            self._returndate = None
            self._news = elements["news"][i]
            if self._news:
                if "Expected back" in self._news:
                    date = self._news.split("Expected back")[-1]
                    # print(self.name,self._news,date)
                    try:
                        nowtime = datetime.datetime.now(local_tz)
                        nowtime = datetime.datetime.now()
                        returndate = datetime.datetime.strptime(date, " %d %b")
                        returndate = returndate.replace(tzinfo=pytz.utc).astimezone(
                            local_tz
                        )
                        returnmonth = returndate.month
                        nowmonth = nowtime.month
                        if returnmonth < nowmonth:
                            year = nowtime.year + 1
                        else:
                            year = nowtime.year
                        self._returndate = returndate.replace(year=year)
                    except ValueError:
                        self._returndate = None
                        mout.errorOut(f"Could not parse date: {date}")

            else:
                self._news = None

            self._position_id = elements["element_type"][i]

            assert self._position_id in [1, 2, 3, 4, 5]

            if self.is_manager:
                # https://resources.premierleague.com/premierleague/photos/players/110x140/man85.png
                self._photo_url = f'https://resources.premierleague.com/premierleague/photos/players/110x140/{elements["opta_code"][i]}.png'
            else:
                self._photo_url = f'https://resources.premierleague.com/premierleague/photos/players/110x140/p{elements["photo"][i].replace(".jpg",".png")}'

            self._transfers_in = elements["transfers_in_event"][i]
            self._transfers_out = elements["transfers_out_event"][i]

            self._total_goals = elements["goals_scored"][i]
            self._total_expected_goals = float(elements["expected_goals"][i])
            self._total_expected_assists = float(elements["expected_assists"][i])
            self._total_bps = elements["bps"][i]
            self._total_goals_conceded = elements["goals_conceded"][i]
            self._total_assists = elements["assists"][i]
            self._total_bonus = elements["bonus"][i]
            self._total_clean_sheets = elements["clean_sheets"][i]
            self._total_yellows = elements["yellow_cards"][i]
            self._total_reds = elements["red_cards"][i]
            self._total_own_goals = elements["own_goals"][i]
            self._total_saves = elements["saves"][i]
            self._total_penalties_saved = elements["penalties_saved"][i]

            self._total_points = elements["total_points"][i]
            self._elements_id = i

            self._form = elements["form"][i]
            self._selected_by = float(elements["selected_by_percent"][i])

            self._fixtures = None
            self._history = None

            self._team_obj = self._api.get_player_team_obj(self._team_id)

            # print(api._prev_element_dict.keys())
            # exit()

            if api._prev_element_dict and self._full_name in api._prev_element_dict:

                pd = api._prev_element_dict[self._full_name]
                self._prev_dreamteam_count = pd["dreamteam_count"]
                self._prev_now_cost = pd["now_cost"]
                self._prev_points_per_game = pd["points_per_game"]
                self._prev_total_points = pd["total_points"]
                self._prev_minutes = pd["minutes"]
                self._prev_goals_scored = pd["goals_scored"]
                self._prev_assists = pd["assists"]
                self._prev_clean_sheets = pd["clean_sheets"]
                self._prev_goals_conceded = pd["goals_conceded"]
                self._prev_own_goals = pd["own_goals"]
                self._prev_penalties_saved = pd["penalties_saved"]
                self._prev_penalties_missed = pd["penalties_missed"]
                self._prev_yellow_cards = pd["yellow_cards"]
                self._prev_red_cards = pd["red_cards"]
                self._prev_saves = pd["saves"]
                self._prev_bonus = pd["bonus"]
                self._prev_bps = pd["bps"]
                self._prev_influence = pd["influence"]
                self._prev_creativity = pd["creativity"]
                self._prev_threat = pd["threat"]
                self._prev_starts = pd["starts"]
                self._prev_expected_goals = float(pd["expected_goals"])
                self._prev_expected_assists = float(pd["expected_assists"])
                self._prev_expected_goal_involvements = pd["expected_goal_involvements"]
                self._prev_expected_goals_conceded = pd["expected_goals_conceded"]
                self._prev_expected_goals_per_90 = pd["expected_goals_per_90"]
                self._prev_saves_per_90 = pd["saves_per_90"]
                self._prev_expected_assists_per_90 = pd["expected_assists_per_90"]
                self._prev_expected_goal_involvements_per_90 = pd[
                    "expected_goal_involvements_per_90"
                ]
                self._prev_expected_goals_conceded_per_90 = pd[
                    "expected_goals_conceded_per_90"
                ]
                self._prev_goals_conceded_per_90 = pd["goals_conceded_per_90"]
                self._prev_starts_per_90 = pd["starts_per_90"]
                self._prev_clean_sheets_per_90 = pd["clean_sheets_per_90"]
                self._prev_appearances = (
                    self._prev_minutes / 90 * self._prev_starts_per_90
                )
                if self._prev_appearances:
                    self._prev_mins_per_start = (
                        self._prev_minutes / self._prev_appearances
                    )
                else:
                    self._prev_mins_per_start = 0

                return True
                # print(pd['web_name'],self._name)

            # else:

            import difflib

            close_matches = difflib.get_close_matches(
                self._full_name, api._prev_element_dict.keys()
            )

            if len(close_matches) == 1:
                self._full_name = close_matches[0]

                pd = api._prev_element_dict[self._full_name]
                self._prev_dreamteam_count = pd["dreamteam_count"]
                self._prev_now_cost = pd["now_cost"]
                self._prev_points_per_game = pd["points_per_game"]
                self._prev_total_points = pd["total_points"]
                self._prev_minutes = pd["minutes"]
                self._prev_goals_scored = pd["goals_scored"]
                self._prev_assists = pd["assists"]
                self._prev_clean_sheets = pd["clean_sheets"]
                self._prev_goals_conceded = pd["goals_conceded"]
                self._prev_own_goals = pd["own_goals"]
                self._prev_penalties_saved = pd["penalties_saved"]
                self._prev_penalties_missed = pd["penalties_missed"]
                self._prev_yellow_cards = pd["yellow_cards"]
                self._prev_red_cards = pd["red_cards"]
                self._prev_saves = pd["saves"]
                self._prev_bonus = pd["bonus"]
                self._prev_bps = pd["bps"]
                self._prev_influence = pd["influence"]
                self._prev_creativity = pd["creativity"]
                self._prev_threat = pd["threat"]
                self._prev_starts = pd["starts"]
                self._prev_expected_goals = float(pd["expected_goals"])
                self._prev_expected_assists = float(pd["expected_assists"])
                self._prev_expected_goal_involvements = pd["expected_goal_involvements"]
                self._prev_expected_goals_conceded = pd["expected_goals_conceded"]
                self._prev_expected_goals_per_90 = pd["expected_goals_per_90"]
                self._prev_saves_per_90 = pd["saves_per_90"]
                self._prev_expected_assists_per_90 = pd["expected_assists_per_90"]
                self._prev_expected_goal_involvements_per_90 = pd[
                    "expected_goal_involvements_per_90"
                ]
                self._prev_expected_goals_conceded_per_90 = pd[
                    "expected_goals_conceded_per_90"
                ]
                self._prev_goals_conceded_per_90 = pd["goals_conceded_per_90"]
                self._prev_starts_per_90 = pd["starts_per_90"]
                self._prev_clean_sheets_per_90 = pd["clean_sheets_per_90"]
                self._prev_appearances = (
                    self._prev_minutes / 90 * self._prev_starts_per_90
                )
                if self._prev_appearances:
                    self._prev_mins_per_start = (
                        self._prev_minutes / self._prev_appearances
                    )
                else:
                    self._prev_mins_per_start = 0

            else:

                # mout.warning(f'No previous data for {self._full_name}')
                # mout.out(close_matches)

                self._prev_dreamteam_count = 0.0
                self._prev_now_cost = 0.0
                self._prev_points_per_game = 0.0
                self._prev_total_points = 0.0
                self._prev_minutes = 0.0
                self._prev_goals_scored = 0.0
                self._prev_assists = 0.0
                self._prev_clean_sheets = 0.0
                self._prev_goals_conceded = 0.0
                self._prev_own_goals = 0.0
                self._prev_penalties_saved = 0.0
                self._prev_penalties_missed = 0.0
                self._prev_yellow_cards = 0.0
                self._prev_red_cards = 0.0
                self._prev_saves = 0.0
                self._prev_bonus = 0.0
                self._prev_bps = 0.0
                self._prev_influence = 0.0
                self._prev_creativity = 0.0
                self._prev_threat = 0.0
                self._prev_starts = 0.0
                self._prev_expected_goals = 0.0
                self._prev_expected_assists = 0.0
                self._prev_expected_goal_involvements = 0.0
                self._prev_expected_goals_conceded = 0.0
                self._prev_expected_goals_per_90 = 0.0
                self._prev_saves_per_90 = 0.0
                self._prev_expected_assists_per_90 = 0.0
                self._prev_expected_goal_involvements_per_90 = 0.0
                self._prev_expected_goals_conceded_per_90 = 0.0
                self._prev_goals_conceded_per_90 = 0.0
                self._prev_starts_per_90 = 0.0
                self._prev_clean_sheets_per_90 = 0.0
                self._prev_appearances = 0.0
                self._prev_mins_per_start = 0.0

            return True

        elif len(matches) < 1:
            mout.errorOut(f"Could not find player {self._name}. Close matches:")

            import difflib

            for p in difflib.get_close_matches(self._name, elements["web_name"]):
                print(p)

        else:

            mout.errorOut("Multiple player matches:")

            for i in matches:
                mout.out(elements["first_name"][i] + " " + elements["web_name"][i])

        return False

    def get_playing_chance(self, gw, debug=False):
        if debug:
            mout.debug(f"{self.name}.get_playing_chance({gw=})")
        if gw in self._playing_chance.keys():
            if debug:
                mout.debug(f"Using cached playing chance {self._playing_chance[gw]=}")
            return self._playing_chance[gw]
        elif gw > self._api._current_gw + 1:
            if self._returndate is not None:
                # future gw
                fixs = self._team_obj.get_gw_fixtures(gw)
                if debug:
                    print(f"{fixs=}")
                if isinstance(fixs, list):
                    if len(fixs) < 1:
                        return 0.0
                    else:
                        # mout.warningOut(f"{self.name} has DGW{gw} and is flagged! Player::get_playing_chance()")

                        all_fixtures = self._api.get_gw_fixtures(gw)

                        probs = []

                        for player_fix in fixs:

                            team_a = player_fix["team_a"]
                            team_h = player_fix["team_h"]

                            fix = [
                                f
                                for f in all_fixtures
                                if f["team_a"] == team_a and f["team_h"] == team_h
                            ][0]

                            kickoff = datetime.datetime.strptime(
                                fix["kickoff"], "%Y-%m-%dT%H:%M:%SZ"
                            )
                            kickoff = kickoff.replace(tzinfo=pytz.utc).astimezone(
                                local_tz
                            )

                            if kickoff < self._returndate:
                                probs.append(self._chance_of_playing_next_round)
                            else:
                                probs.append(1.0)

                        gw_prob = sum(probs) / len(probs)

                        if gw_prob < 1:
                            # mout.warningOut(f"{self.name} has DGW{gw} and is flagged! Player::get_playing_chance()")
                            # print(probs,gw_prob)
                            return gw_prob
                        else:
                            return 1.0

                else:
                    fixtures = self._api.get_gw_fixtures(gw)
                    fix = [f for f in fixtures if f["team_a"] == fixs["team_a"]][0]
                    kickoff = datetime.datetime.strptime(
                        fix["kickoff"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    kickoff = kickoff.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    if kickoff < self._returndate:
                        return self._chance_of_playing_next_round
                    else:
                        return 1.0
            else:
                return 1.0
        else:
            return 1.0
        # if gw == self._api._current_gw:
        # 	return self._chance_of_playing_this_round
        # elif gw == self._api._current_gw + 1:
        # 	return self._chance_of_playing_next_round
        # else:
        # 	return 1.0

    @property
    def is_yellow_flagged(self):
        if self.is_red_flagged:
            return False
        if self._chance_of_playing_this_round < 1.0:
            return True
        elif self._chance_of_playing_next_round < 1.0:
            return True
        else:
            return False

    @property
    def is_red_flagged(self):
        if self._chance_of_playing_this_round < 0.25:
            return True
        elif self._chance_of_playing_next_round < 0.25:
            return True
        else:
            return False

    @property
    def fixtures(self):
        if self._fixtures is not None:
            return self._fixtures
        self._fixtures = self._api.get_player_fixtures(self.shortteam, self.id)
        return self._fixtures

    @property
    def team_obj(self):
        return self._team_obj

    @property
    def history(self):
        if self._history is None:
            self._history = self._api.get_player_history(self._id)
        return self._history

    @property
    def total_goals(self):
        return self._total_goals

    # @property
    # def total_gi_wPrev(self):
    # 	return self.total_goals + self.total_assists + self._prev_goals_scored + self._prev_assists

    # @property
    # def total_xgi_wPrev(self):
    # 	return self + self.total_assists + self._prev_expected_goals + self._prev_expected_assists

    @property
    def total_bps(self):
        return self._total_bps

    @property
    def total_assists(self):
        return self._total_assists

    @property
    def total_bonus(self):
        return self._total_bonus

    @property
    def total_clean_sheets(self):
        return self._total_clean_sheets

    @property
    def selected_by(self):
        return self._selected_by

    @property
    def name(self):
        return self._name

    @property
    def full_name(self):
        return f"{self._first_name} {self._name}"

    @property
    def price(self):
        return self._price

    @property
    def purchase_price(self):
        return self._purchase_price

    @property
    def selling_price(self):
        return self._selling_price

    @purchase_price.setter
    def purchase_price(self, a):
        self._purchase_price = a

    @property
    def is_captain(self):
        return bool(self._is_captain)

    @is_captain.setter
    def is_captain(self, a):
        a = bool(a)
        if a:
            self.multiplier = 2
        self._is_captain = a

    @property
    def is_vice_captain(self):
        return bool(self._is_vice_captain)

    @is_vice_captain.setter
    def is_vice_captain(self, a):
        self._is_vice_captain = bool(a)

    @property
    def was_subbed(self):
        return bool(self._was_subbed)

    @was_subbed.setter
    def was_subbed(self, a):
        self._was_subbed = bool(a)

    @property
    def needs_autosub(self):
        fixs = self.team_obj.get_gw_fixtures(self._api._current_gw)
        if isinstance(fixs, list):
            if len(fixs) < 1:
                return True
        if self.has_fixture_finished and self.event_minutes == 0:
            return True
        elif self._chance_of_playing_this_round == 0.0:
            return True
        else:
            return False

    @property
    def multiplier(self):
        return int(self._multiplier)

    @multiplier.setter
    def multiplier(self, a):
        self._multiplier = int(a)

    @selling_price.setter
    def selling_price(self, a):
        self._selling_price = a

    @property
    def shortteam(self):
        return self.team_obj._shortname

    @property
    def total_points(self):
        return self._total_points

    @property
    def team(self):
        return self._team

    @property
    def form(self):
        return float(self._form)

    @property
    def id(self):
        return int(self._id)

    @property
    def position_id(self):
        return self._position_id

    @property
    def is_manager(self) -> bool:
        return self.position_id == 5

    def get_fixture_str(self, gw, short=False, old=False, lower_away=False):

        relative_gw = self.get_relative_gw(gw, allow_dwg=True)

        if isinstance(relative_gw, list):

            # dgw or tgw

            strs = []

            for rgw in relative_gw:

                if self.fixtures["is_home"][rgw]:
                    strs.append(
                        self._api.team_name(self.fixtures["team_a"][rgw], short=short)
                    )
                else:
                    if lower_away:
                        # try:
                        strs.append(
                            self._api.team_name(
                                self.fixtures["team_h"][rgw], short=short
                            ).lower()
                        )
                        # except AttributeError:
                        # mout.errorOut(self.fixtures['team_h'][rgw])
                        # mout.errorOut(self._api.team_name(self.fixtures['team_h'][rgw],short=short))
                    else:
                        strs.append(
                            self._api.team_name(
                                self.fixtures["team_h"][rgw], short=short
                            )
                        )

            # return strs
            return " + ".join(strs)

        if relative_gw is None:
            return " - "

        if relative_gw < 0:
            print("previous GW")
            return None
            # fixs = self.team_obj.get_gw_fixtures(gw)
            # print(fixs)

        if self.fixtures["is_home"][relative_gw]:
            return self._api.team_name(
                self.fixtures["team_a"][relative_gw], short=short
            )
        else:
            if lower_away:
                return self._api.team_name(
                    self.fixtures["team_h"][relative_gw], short=short
                ).lower()
            else:
                return self._api.team_name(
                    self.fixtures["team_h"][relative_gw], short=short
                )

    def get_fixture_diff(self, gw, relative=True, old=False, overall=True):

        if not old:
            relative_gw = self.get_relative_gw(gw, allow_dwg=True)

            if relative_gw is None:
                return " - "

            if isinstance(relative_gw, list):

                # dgw or tgw

                diffs = []

                for rgw in relative_gw:

                    is_home = self.fixtures["is_home"][rgw]
                    if is_home:
                        opp_index = self.fixtures["team_a"][rgw]
                        own_index = self.fixtures["team_h"][rgw]
                    else:
                        opp_index = self.fixtures["team_h"][rgw]
                        own_index = self.fixtures["team_a"][rgw]

                    is_attacker = self.position_id > 2

                    diffs.append(
                        self._api.get_fixture_diff(
                            opp_index, own_index, is_home, is_attacker, overall=overall
                        )
                    )

                return diffs

            is_home = self.fixtures["is_home"][relative_gw]
            if is_home:
                opp_index = self.fixtures["team_a"][relative_gw]
                own_index = self.fixtures["team_h"][relative_gw]
            else:
                opp_index = self.fixtures["team_h"][relative_gw]
                own_index = self.fixtures["team_a"][relative_gw]

            is_attacker = self.position_id > 2

            # print(self._name)
            # print(overall)
            # print(self._api.get_fixture_diff(opp_index,own_index,is_home,True,overall=overall))
            # print(self._api.get_fixture_diff(opp_index,own_index,is_home,False,overall=overall))

            return self._api.get_fixture_diff(
                opp_index, own_index, is_home, is_attacker, overall=overall
            )

        else:

            # old method:

            if relative:
                relative_gw = self.get_relative_gw(gw)
                return int(self.fixtures["difficulty"][relative_gw])
            else:
                return int(self.fixtures["difficulty"][gw])

    def get_event_score(
        self,
        gw=None,
        summary=False,
        not_playing_is_none=True,
        md_bold=True,
        return_str=False,
        pts_line=False,
        team_line=True,
        html_highlight=True,
        debug=False,
    ):
        if gw is None:
            gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None

        if debug:
            mout.debug(f'Player("{self}",{self.id=}).get_event_score({gw=})')

        event_stats = self._api.get_player_event_stats(gw, self._id)

        self.extract_event_stats(event_stats)

        if debug:
            pprint(event_stats)

        score = int(self.__total_points)

        if debug:
            print(f"{score=}")

        if debug:
            print(f"{self.__minutes=}")

        if not_playing_is_none and self.__minutes == 0:
            if not return_str:
                score = None
            else:
                if self.has_fixture_finished:
                    score = "Did not play"
                elif self.has_fixture_started:
                    score = "Bench"
                else:
                    score = "Yet to play"

        if summary:
            return score, self.get_event_summary(
                gw,
                event_stats,
                md_bold=md_bold,
                pts_line=pts_line,
                team_line=team_line,
                html_highlight=html_highlight,
            )
        else:
            return score

    def event_stat_emojis(self, gw):
        stats = self._api.get_player_event_stats(gw, self._id)

        emoji_str = ""

        if self.is_yellow_flagged:
            emoji_str += f"⚠️"
        elif self.is_red_flagged:
            emoji_str += f"⛔️"

        # if self.multiplier > 1:
        # 	emoji_str += '©️'

        if self.multiplier < 0:
            emoji_str += "🪑"

        for i in range(stats["goals_scored"]):
            emoji_str += "⚽️"

        for i in range(stats["assists"]):
            emoji_str += "🅰️"

        for i in range(stats["penalties_saved"]):
            emoji_str += "✋"

        for i in range(stats["penalties_missed"]):
            emoji_str += "🚫"

        for i in range(stats["own_goals"]):
            emoji_str += "🫥"

        if self.position_id < 4 and stats["clean_sheets"]:
            emoji_str += "🛡️"

        for i in range(stats["saves"] // 3):
            emoji_str += "🧤"

        if stats["bonus"] == 1:
            emoji_str += "1️⃣"
        elif stats["bonus"] == 2:
            emoji_str += "2️⃣"
        elif stats["bonus"] == 3:
            emoji_str += "3️⃣"

        for i in range(stats["red_cards"]):
            emoji_str += "🟥"

        for i in range(stats["yellow_cards"]):
            emoji_str += "🟨"

        if self.was_subbed:
            emoji_str += f"🔄"

        return emoji_str

    def get_gw_xg(self, gw=None):
        if gw is None:
            gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None

        indices = [i for i, r in enumerate(self.history["round"]) if r == gw]
        xg = sum([float(self.history["expected_goals"][i]) for i in indices])
        return xg

    def get_gw_xa(self, gw=None):
        if gw is None:
            gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None

        indices = [i for i, r in enumerate(self.history["round"]) if r == gw]
        xa = sum([float(self.history["expected_assists"][i]) for i in indices])
        return xa

    def get_gw_xgi(self, gw=None):
        return self.get_gw_xg(gw=gw) + self.get_gw_xa(gw=gw)

    def get_performed_xpts(self, gw=None):
        if gw is None:
            gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None

        if "round" not in self.history:
            return None

        indices = [i for i, r in enumerate(self.history["round"]) if r == gw]

        minutes = [float(self.history["minutes"][i]) for i in indices]
        xgc = [float(self.history["expected_goals_conceded"][i]) for i in indices]

        xpts = 0

        for gc, mins in zip(xgc, minutes):
            if mins > 0:
                xpts += 1
            if mins > 59:
                xpts += 1
            if mins > 59 and gc < 0.5:
                if self.position_id < 3:
                    xpts += 4
                if self.position_id == 3:
                    xpts += 1
            if self.position_id < 3:
                xpts -= 0.5 * gc

        xg = sum([float(self.history["expected_goals"][i]) for i in indices])
        xa = sum([float(self.history["expected_assists"][i]) for i in indices])

        if self.position_id < 3:
            xpts += xg * 6 + xa * 3
        elif self.position_id == 3:
            xpts += xg * 5 + xa * 3
        elif self.position_id == 4:
            xpts += xg * 4 + xa * 3

        return xpts

    @property
    def attacking_history(self):
        pts = []
        for goals, assists in zip(
            self.history["goals_scored"], self.history["assists"]
        ):
            if self.position_id < 3:
                pts.append(goals * 6 + assists * 3)
            elif self.position_id == 3:
                pts.append(goals * 5 + assists * 3)
            elif self.position_id == 4:
                pts.append(goals * 4 + assists * 3)
        return pts

    @property
    def attacking_points(self):
        if self.position_id < 3:
            return self.total_goals * 6 + self.total_assists * 3
        elif self.position_id == 3:
            return self.total_goals * 5 + self.total_assists * 3
        elif self.position_id == 4:
            return self.total_goals * 4 + self.total_assists * 3

    @property
    def attacking_points_per90(self):
        if self.appearances == 0:
            return 0
            # self._attacking_returns_per90 = 0
        if self.total_minutes == 0:
            return 0
        return self.attacking_points / self.total_minutes * 90

    @property
    def attacking_points_per90_wPrev(self):
        if self._prev_minutes == 0:
            return self.attacking_points_per90
        return (
            self.attacking_points_per90
            + 90
            * (
                self._prev_goals_scored * self.goal_multiplier
                + self.assist_multiplier * self._prev_assists
            )
            / self._prev_minutes
        )

    @property
    def attacking_returns_per90(self):
        return (
            self.total_goals
            + self.total_assists
            + self._prev_goals_scored
            + self._prev_assists
        )

    @property
    def attacking_points_wPrev(self):
        # print('att. pts',self.name,self.attacking_points + self._prev_goals_scored*self.goal_multiplier + self.assist_multiplier*self._prev_assists)
        return (
            self.attacking_points
            + self._prev_goals_scored * self.goal_multiplier
            + self.assist_multiplier * self._prev_assists
        )

    @property
    def goal_multiplier(self):
        return [6, 6, 5, 4, 1][self.position_id - 1]

    @property
    def clean_sheet_multiplier(self):
        return [4, 4, 1, 0, 2][self.position_id - 1]

    @property
    def assist_multiplier(self):
        return [3, 3, 3, 3, 0][self.position_id - 1]

    @property
    def performed_expected_attacking_points(self):
        return (
            self._total_expected_goals * self.goal_multiplier
            + self.assist_multiplier * self._total_expected_assists
        )

    @property
    def performed_expected_attacking_points_wPrev(self):
        # print('att. xpts',self.name,self.performed_expected_attacking_points + self._prev_expected_goals*self.goal_multiplier + self.assist_multiplier*self._prev_expected_assists)
        return (
            self.performed_expected_attacking_points
            + self._prev_expected_goals * self.goal_multiplier
            + self.assist_multiplier * self._prev_expected_assists
        )

    @property
    def bonus_points_per90(self):
        if self.appearances == 0:
            return 0
        if self.total_minutes == 0:
            return 0
        pts = 0
        for bonus in self.history["bonus"]:
            pts += bonus
        return pts / self.total_minutes * 90

    @property
    def total_minutes(self):
        if self._total_minutes is None:
            self._total_minutes = sum(int(x) for x in self.history["minutes"])
        return self._total_minutes

    @property
    def appearances(self):
        if self._appearances is None:
            if self.history.empty:
                self._appearances = 0
            else:
                self._appearances = len([m for m in self.history["minutes"] if m > 0])
        return self._appearances

    @property
    def xG_no_opponent(self):
        if self._xG_no_opponent is None:
            self.expected_points()
        return self._xG_no_opponent

    @property
    def xA_no_opponent(self):
        if self._xA_no_opponent is None:
            self.expected_points()
        return self._xA_no_opponent

    @property
    def xC_no_opponent(self):
        if self._xC_no_opponent is None:
            self.expected_points()
        return self._xC_no_opponent

    @property
    def xBpts(self):
        if self._xBpts is None:
            self.expected_points()
        return self._xBpts

    def expected_minutes(self, gw=None, Ms=None):

        if gw is None:
            gw = self._api._current_gw + 1
        if gw > 38:
            return None

        if self.is_manager:
            return 90 * self.num_gwfix(gw)

        if "minutes" not in self.history:
            if self._prev_mins_per_start:
                # return prev_minutes
                return self._prev_mins_per_start
            else:
                return None

        Ms = Ms or [float(x) for x in self.history["minutes"]]

        if self.num_gwfix(gw) > 0 and not self.has_fixture_finished:
            Ms = Ms[:-1]

        return weighted_average(Ms) * self.get_playing_chance(gw)

    @property
    def A_per_xA(self):
        if self._A_per_xA is None:
            if (self._total_expected_assists + self._prev_expected_assists) == 0:
                self._A_per_xA = 1.0
            else:
                self._A_per_xA = (self.total_assists + self._prev_assists) / (
                    self._total_expected_assists + self._prev_expected_assists
                )
            # mout.out(f'A/xA {self} {self._A_per_xA:.2f}')
        return self._A_per_xA

    @property
    def G_per_xG(self):
        if self._G_per_xG is None:
            if (self._total_expected_goals + self._prev_expected_goals) == 0:
                self._G_per_xG = 1.0
            else:
                self._G_per_xG = (self.total_goals + self._prev_goals_scored) / (
                    self._total_expected_goals + self._prev_expected_goals
                )
            # mout.out(f'G/xG {self} {self._G_per_xG:.2f}')
        return self._G_per_xG

    @property
    def no_history(self) -> bool:
        if not len(self.history):
            return True
        if self._api._current_gw == 0:
            return True
        if self._api._current_gw == 1 and self._api._live_gw:
            return True
        return False

    """

	New xPts Approach
	=================

	Weight recent returns higher
	----------------------------

	* Define some sort of weighted average function?

	sigma(f(gw))

	Expected goals
	--------------

	xG_GW = sigma(xGs) * sum(Gs)/sum(xGs)
	xA_GW = sigma(xGs) * sum(As)/sum(xAs)

	Scale by Opponent
	-----------------

	xG_GW *= sigma(xGCs) / league_average(xGCs)
	xA_GW *= sigma(xGCs) / league_average(xGCs)

	SCALE CS PROBABILITY BY OPPONENT STRENGTH

	xMinutes
	--------

	* Injuries
	* Weighted average of recent minutes per game

	xCleans
	-------

	* sigma(GC < 1)

	xBonus
	------

	* sigma(bonus)

	"""

    def expected_points(
        self,
        opponent=None,
        gw=None,
        debug=False,
        use_official=False,
        force=False,
        not_started_only=False,
        summary=False,
    ):
        """not_started_only: for gameweeks with multiple matches only return expected points for games that have not started yet"""

        if gw is None:
            gw = self._api._current_gw

        if not not_started_only:
            if self.id in self._api._exp_archive.keys():
                if gw in self._api._exp_archive[self.id].keys():
                    if not force:
                        return self._api._exp_archive[self.id][gw]
                else:
                    self._api._exp_archive[self.id] = {}
            else:
                self._api._exp_archive[self.id] = {}

        if opponent is None:
            opponent = self.team_obj.get_opponent(gw, not_started_only=not_started_only)
            if opponent is None:
                self._api._exp_archive[self.id][gw] = 0
                return 0

        if debug:
            mout.debug(
                f"{self.name}.expected_points({opponent=},{gw=},{use_official=})"
            )

        if isinstance(opponent, list):
            total = 0
            for opp in opponent:
                total += self.expected_points(
                    opponent=opp,
                    gw=gw,
                    debug=debug,
                    use_official=use_official,
                    force=force,
                )
            return total

        if opponent is None:
            if debug:
                mout.out(f"no opponent (gw={gw})")
            if not not_started_only:
                self._api._exp_archive[self.id][gw] = 0
            return 0

        if debug:
            mout.varOut("opponent", str(opponent))

        # use flag status for prediction
        chance = self.get_playing_chance(gw)
        if debug:
            mout.varOut("playing_chance", chance)
        if chance == 0.0:
            if not not_started_only:
                self._api._exp_archive[self.id][gw] = 0
            return 0

        if use_official and gw == self._api._current_gw:
            if debug:
                mout.varOut("expected_points (official)", chance * self._exp_next_round)
            if not not_started_only:
                self._api._exp_archive[self.id][gw] = (
                    x := chance * self._exp_this_round
                )
            return x
        elif use_official and gw == self._api._current_gw + 1:
            if debug:
                mout.varOut("expected_points (official)", chance * self._exp_next_round)
            if not not_started_only:
                self._api._exp_archive[self.id][gw] = (
                    x := chance * self._exp_next_round
                )
            return x
        else:

            expected_points = 0

            # weighted_average(this_season_by_gw,this_season_minutes_by_gw,last_season_value,last_season_minutes)

            if debug:
                mout.varOut("self._prev_expected_goals", self._prev_expected_goals)
            if debug:
                mout.varOut("self._prev_expected_assists", self._prev_expected_assists)
            if debug:
                mout.varOut("self._prev_minutes", self._prev_minutes)
            if debug:
                mout.varOut(
                    "self._prev_clean_sheets_per_90", self._prev_clean_sheets_per_90
                )
            if debug:
                mout.varOut("self._prev_bonus", self._prev_bonus)

            ### MINUTES

            if "minutes" not in self.history:
                if debug:
                    mout.error(f"{self} has no minutes in self.history")
                if not self._prev_minutes:
                    if not not_started_only:
                        self._api._exp_archive[self.id][gw] = 0
                    return 0
                else:
                    Ms = []
            else:
                Ms = [float(x) for x in self.history["minutes"]]

            if debug:
                mout.varOut("Ms", Ms)

            if self._api._live_gw:
                Ms.pop()

            xM = self.expected_minutes(gw, Ms=Ms)  # or 0.0

            if not xM:
                if debug:
                    mout.error(f"{self} has no xM < 1")
                xMPts = 0.0

                if not not_started_only:
                    self._api._exp_archive[self.id][gw] = 0
                return 0
            else:
                xMPts = 1 + min([1, xM / 60])

            if debug:
                mout.varOut("xM", xM)
            if debug:
                mout.varOut("xMPts", xMPts)

            ### OPPONENT GOALS CONCEDED

            if opponent._prev_obj is None:
                if self.no_history:
                    from api import GC_DICT, GF_DICT

                    # mout.error(f"{opponent} has no prev_obj and the game hasn't started yet (assuming promoted)")
                    opp_GF_per_game = GF_DICT[opponent.shortname] / 46
                    opp_GC_per_game = GC_DICT[opponent.shortname] / 46
                else:
                    opp_GF_per_game = opponent.goals_scored / opponent.games_played
                    opp_GC_per_game = opponent.goals_conceded / opponent.games_played

            elif self.no_history:
                opp_GF_per_game = (opponent._prev_obj.goals_scored / 38) / 2
                opp_GC_per_game = (opponent._prev_obj.goals_conceded / 38) / 2

            else:
                opp_GF_per_game = (
                    opponent.goals_scored / opponent.games_played
                    + opponent._prev_obj.goals_scored / 38
                ) / 2
                opp_GC_per_game = (
                    opponent.goals_conceded / opponent.games_played
                    + opponent._prev_obj.goals_conceded / 38
                ) / 2

            if debug:
                mout.varOut("opp_GC_per_game", opp_GC_per_game)
            if debug:
                mout.varOut("opp_GF_per_game", opp_GF_per_game)

            if self.no_history:
                avg_GC_per_game = self._api._prev_avg_gc_per_game
            else:
                avg_GC_per_game = (
                    sum([t.goals_conceded / t.games_played for t in self._api.teams])
                    / 20
                    + self._api._prev_avg_gc_per_game
                ) / 2

            if debug:
                mout.varOut("avg_GC_per_game", avg_GC_per_game)

            opp_GC_ratio = opp_GC_per_game / avg_GC_per_game
            opp_GC_ratio = opp_GC_ratio or 1.0
            # opp_GC_ratio = scale_by_sample_size(opp_GC_ratio,opponent.games_played)

            if debug:
                mout.varOut("opp_GC_ratio", opp_GC_ratio)

            ### OPPONENT GOALS THREAT

            if self.no_history:
                avg_GF_per_game = self._api._prev_avg_gf_per_game
            else:
                avg_GF_per_game = (
                    sum([t.goals_scored / t.games_played for t in self._api.teams]) / 20
                    + self._api._prev_avg_gf_per_game
                ) / 2

            if debug:
                mout.varOut("avg_GF_per_game", avg_GF_per_game)

            opp_GF_ratio = opp_GF_per_game / avg_GF_per_game
            opp_GF_ratio = opp_GF_ratio or 1.0
            # opp_GF_ratio = scale_by_sample_size(opp_GF_ratio,opponent.games_played)

            if debug:
                mout.varOut("opp_GF_ratio", opp_GF_ratio)

            ### CLEAN SHEETS

            # xCSs = [int(int(x) < 1) for x in self.history['goals_conceded']]
            # xGCs = [float(x) for x in self.history['expected_goals_conceded']]
            if self.no_history:
                xCSs = []
            else:
                if "expected_goals_conceded" not in self.history:
                    print(len(self.history))
                xCSs = [
                    int(float(x) < 0.5) for x in self.history["expected_goals_conceded"]
                ]
                if self._api._live_gw:
                    xCSs.pop()

            if debug:
                mout.var("xCSs", xCSs)

            self._xC_no_opponent = weighted_average(
                xCSs,
                None,
                last_season_total=self._prev_clean_sheets_per_90
                * self._prev_minutes
                / 90,
                last_season_minutes=self._prev_minutes / 90,
            )

            if debug:
                mout.var("self._xC_no_opponent", self._xC_no_opponent)

            xCSPts = self._xC_no_opponent * self.clean_sheet_multiplier / opp_GF_ratio

            xCSPts *= min([1, xM / 60])

            if debug:
                mout.var("xCSPts", xCSPts)

            ### GOALS

            if self.no_history:
                xGs = []
            else:
                xGs = [float(x) for x in self.history["expected_goals"]]
                if self._api._live_gw:
                    xGs.pop()

            if debug:
                mout.varOut("xGs", xGs)
            # weighted average xG per game
            xG_per_minute = weighted_average(
                xGs, Ms, self._prev_expected_goals, self._prev_minutes
            )

            if debug:
                mout.varOut("xG_per_minute", xG_per_minute)

            ### ASSISTS

            if self.no_history:
                xAs = []
            else:
                xAs = [float(x) for x in self.history["expected_assists"]]
                if self._api._live_gw:
                    xAs.pop()

            if debug:
                mout.varOut("xAs", xAs)

            # weighted average xA per game
            xA_per_minute = weighted_average(
                xAs, Ms, self._prev_expected_assists, self._prev_minutes
            )

            if debug:
                mout.varOut("xA_per_minute", xA_per_minute)

            ### ATTACKING POINTS

            n = self.appearances + self._prev_appearances

            self._xG_no_opponent = (
                xG_per_minute * xM * scale_by_sample_size(self.G_per_xG, n)
            )
            self._xA_no_opponent = (
                xA_per_minute * xM * scale_by_sample_size(self.A_per_xA, n)
            )

            if debug:
                mout.varOut("_xG_no_opponent", self._xG_no_opponent)
            if debug:
                mout.varOut("_xA_no_opponent", self._xA_no_opponent)

            if debug:
                mout.varOut("G_per_xG", self.G_per_xG)
            if debug:
                mout.varOut("A_per_xA", self.A_per_xA)

            xG = self._xG_no_opponent * opp_GC_ratio
            xA = self._xA_no_opponent * opp_GC_ratio
            xGIPts = self.goal_multiplier * xG + 3 * xA

            if debug:
                mout.varOut("xGIPts", xGIPts)
            if debug:
                mout.varOut("xG", xG)
            if debug:
                mout.varOut("xA", xA)

            ### BONUS POINTS

            if self.no_history:
                Bs = []
            else:
                Bs = [float(x) for x in self.history["bonus"]]
                if self._api._live_gw:
                    Bs.pop()

            if debug:
                mout.varOut("Bs", Bs)

            self._xBpts = weighted_average(
                Bs, None, self._prev_bonus, self._prev_minutes / 90
            )

            if debug:
                mout.varOut("xBPts", self._xBpts)

            ### YELLOW CARDS

            if self.no_history:
                YCs = []
            else:
                YCs = [int(x) for x in self.history["yellow_cards"]]
                if self._api._live_gw:
                    YCs.pop()

            xYCPts = -weighted_average(
                YCs, None, self._prev_yellow_cards, self._prev_minutes / 90
            )

            ### RED CARDS

            if self.no_history:
                RCs = []
            else:
                RCs = [int(x) for x in self.history["red_cards"]]
                if self._api._live_gw:
                    RCs.pop()

            xRCPts = -3 * weighted_average(
                RCs, None, self._prev_red_cards, self._prev_minutes / 90
            )

            ### OWN GOALS

            if self.no_history:
                OGs = []
            else:
                OGs = [int(x) for x in self.history["own_goals"]]
                if self._api._live_gw:
                    OGs.pop()

            xOGPts = -2 * weighted_average(
                OGs, None, self._prev_own_goals, self._prev_minutes / 90
            )

            ### PENALTY MISS

            if self.no_history:
                PMs = []
            else:
                PMs = [int(x) for x in self.history["penalties_missed"]]
                if self._api._live_gw:
                    PMs.pop()

            xPMPts = -2 * weighted_average(
                PMs, None, self._prev_penalties_missed, self._prev_minutes / 90
            )

            if self.position_id == 1:

                ### PENALTY SAVE

                if self.no_history:
                    PSs = []
                else:
                    PSs = [int(x) for x in self.history["penalties_saved"]]
                    if self._api._live_gw:
                        PSs.pop()

                xPSPts = 5 * weighted_average(
                    PSs, None, self._prev_penalties_saved, self._prev_minutes / 90
                )

                if debug:
                    mout.varOut("xPSPts", xPSPts)

                ### SAVES

                if self.no_history:
                    Ss = []
                else:
                    Ss = [int(x) for x in self.history["saves"]]
                    if self._api._live_gw:
                        Ss.pop()

                xSPts = (
                    1
                    / 3
                    * weighted_average(
                        Ss, None, self._prev_saves, self._prev_minutes / 90
                    )
                )

                if debug:
                    mout.varOut("xSPts", xSPts)

            else:

                xPSPts = 0.0
                xSPts = 0.0

            ### COMBINE

            expected_points = (
                xMPts
                + xCSPts
                + xGIPts
                + self._xBpts
                + xYCPts
                + xRCPts
                + xOGPts
                + xPMPts
                + xPSPts
                + xSPts
            )

            # if debug:
            # 	mout.varOut('opponent',str(opponent))
            # 	mout.varOut('opp_GC_per_game',opp_GC_per_game)
            # 	mout.varOut('avg_GC_per_game',avg_GC_per_game)
            # 	mout.varOut('opp_GC_ratio',opp_GC_ratio)

            # 	mout.varOut('opp_GF_per_game',opp_GF_per_game)
            # 	mout.varOut('avg_GF_per_game',avg_GF_per_game)
            # 	mout.varOut('opp_GF_ratio',opp_GF_ratio)

            # 	mout.var('xCSs',xCSs)
            # 	mout.var('self._xC_no_opponent',self._xC_no_opponent)
            # 	mout.var('xCSPts',xCSPts)

            # 	mout.varOut('xGs',xGs)
            # 	mout.varOut('_prev_expected_goals',self._prev_expected_goals)
            # 	mout.varOut('_xG_no_opponent',self._xG_no_opponent)

            # 	mout.varOut('xAs',xAs)
            # 	mout.varOut('_prev_expected_assists',self._prev_expected_goals)
            # 	mout.varOut('self._xA_no_opponent',self._xA_no_opponent)

            # 	mout.varOut('Bs',Bs)

            # 	mout.varOut('Ms',Ms)
            # 	mout.varOut('xM',xM)

            # 	mout.varOut('xG_per_minute',xG_per_minute)
            # 	mout.varOut('xA_per_minute',xA_per_minute)

            # 	mout.varOut('G_per_xG',self.G_per_xG)
            # 	mout.varOut('A_per_xA',self.A_per_xA)

            # 	mout.varOut('xG',xG)
            # 	mout.varOut('xA',xA)

            if summary:
                mout.varOut("xMPts", xMPts)
                mout.varOut("xCSPts", xCSPts)
                mout.varOut("xGIPts", xGIPts)
                mout.varOut("xBPts", self._xBpts)
                mout.varOut("xYCPts", xYCPts)
                mout.varOut("xRCPts", xRCPts)
                mout.varOut("xOGPts", xOGPts)
                mout.varOut("xPMPts", xPMPts)
                mout.varOut("xPSPts", xPSPts)
                mout.varOut("xSPts", xSPts)

            if debug:
                mout.varOut("expected_points", expected_points)

            if not not_started_only:
                self._api._exp_archive[self.id][gw] = expected_points
            return expected_points

    # @mout.debug_log
    def old_expected_points(
        self,
        opponent=None,
        gw=None,
        fit_ratio=0.8,
        debug=False,
        use_official=False,
        force=False,
    ):

        if gw is None:
            gw = self._api._current_gw

        if self.id in self._api._exp_archive.keys():
            if gw in self._api._exp_archive[self.id].keys():
                if not force:
                    return self._api._exp_archive[self.id][gw]
            else:
                self._api._exp_archive[self.id] = {}
        else:
            self._api._exp_archive[self.id] = {}
            # self._api._exp_archive[self.id][gw] = {}

        if opponent is None:
            opponent = self.team_obj.get_opponent(gw)

        if debug:
            mout.debug(
                f"{self.name}.expected_points({opponent=},{gw=},{fit_ratio=},{use_official=})"
            )

        if isinstance(opponent, list):
            total = 0
            for opp in opponent:
                total += self.expected_points(
                    opponent=opp,
                    gw=gw,
                    fit_ratio=fit_ratio,
                    debug=debug,
                    use_official=use_official,
                    force=force,
                )
            return total

        if opponent is None:
            if debug:
                mout.out(f"no opponent (gw={gw})")
            return 0

        # use flag status for prediction
        chance = self.get_playing_chance(gw)
        if debug:
            mout.varOut("playing_chance", chance)
        if chance == 0.0:
            self._api._exp_archive[self.id][gw] = 0
            return self._api._exp_archive[self.id][gw]

        if use_official and gw == self._api._current_gw:
            if debug:
                mout.varOut("expected_points (official)", chance * self._exp_next_round)
            self._api._exp_archive[self.id][gw] = chance * self._exp_this_round
            return self._api._exp_archive[self.id][gw]
        elif use_official and gw == self._api._current_gw + 1:
            if debug:
                mout.varOut("expected_points (official)", chance * self._exp_next_round)
            self._api._exp_archive[self.id][gw] = chance * self._exp_next_round
            return self._api._exp_archive[self.id][gw]
        else:
            expected_points = 0

            # get expected attacking_points_per90 from CT index and fit_data
            if fit_ratio == 0.0 or self.position_id == 1:
                # print('Not using fitting')
                attacking_points_per90 = self.attacking_points_per90_wPrev
            else:
                if self.position_id == 2:
                    from_fit = (
                        self._api._ct_total_fit_data["def"]["intercept"]
                        + self._api._ct_total_fit_data["def"]["slope"]
                        * self.ct_total_scaled
                    )
                    attacking_points_per90 = (
                        self.attacking_points_per90_wPrev * (1.0 - fit_ratio)
                        + fit_ratio * from_fit
                    )
                elif self.position_id == 3:
                    from_fit = (
                        self._api._ct_total_fit_data["mid"]["intercept"]
                        + self._api._ct_total_fit_data["mid"]["slope"]
                        * self.ct_total_scaled
                    )
                    attacking_points_per90 = (
                        self.attacking_points_per90_wPrev * (1.0 - fit_ratio)
                        + fit_ratio * from_fit
                    )
                elif self.position_id == 4:
                    from_fit = (
                        self._api._ct_total_fit_data["fwd"]["intercept"]
                        + self._api._ct_total_fit_data["fwd"]["slope"]
                        * self.ct_total_scaled
                    )
                    attacking_points_per90 = (
                        self.attacking_points_per90_wPrev * (1.0 - fit_ratio)
                        + fit_ratio * from_fit
                    )
                if debug:
                    mout.varOut("attacking_points_per90 (fit)", from_fit)
            if debug:
                mout.varOut("attacking_points_per90", attacking_points_per90)

            # compensate for difficult opponent
            expected_goals_scored = (
                self.team_obj.goals_scored_per_game + opponent.goals_conceded_per_game
            ) / 2
            if debug:
                mout.varOut("expected_goals_scored", expected_goals_scored)
            if debug:
                mout.varOut(
                    "self._attacking_returns_per90", self.attacking_returns_per90
                )
            if self.attacking_points_per90 is None:
                boost = 1
            elif self.attacking_returns_per90 == 0:
                boost = 1
            else:
                boost = (
                    expected_goals_scored - self.attacking_returns_per90
                ) / self.attacking_returns_per90 + 1
            if debug:
                mout.varOut("boost", boost)
            boost = max(0.7, boost)
            boost = min(1.3, boost)
            attacking_points_per90 *= boost

            # get expected minutes from average minutes
            if self.appearances > 0:
                mins_per_appearance = self.total_minutes / self.appearances
                if debug:
                    mout.varOut("mins_per_appearance", mins_per_appearance)
            else:
                self._api._exp_archive[self.id][gw] = 0
                return self._api._exp_archive[self.id][gw]

            # calculated clean sheet probability
            clean_sheet_probability = self.team_obj.expected_clean_sheet(opponent)
            if debug:
                mout.varOut("clean_sheet_probability", clean_sheet_probability)

            # calculate points lost due to conceding multiple goals
            expected_goals_conceded = (
                self.team_obj.goals_conceded_per_game + opponent.goals_scored_per_game
            ) / 2
            if debug:
                mout.varOut("expected_goals_conceded", expected_goals_conceded)

            goals_conceded_loss = 0
            if self.position_id == 3:
                clean_sheet_value = 1
            elif self.position_id < 3:
                clean_sheet_value = 4
                goals_conceded_loss = -expected_goals_conceded / 2
            else:
                clean_sheet_value = 0

            if debug:
                mout.varOut("goals_conceded_loss", goals_conceded_loss)

            # use get team on team scoring data to build up defensive and offensive ratings for all the teams

            # add points due to expected minutes
            if mins_per_appearance == 0:
                self._api._exp_archive[self.id][gw] = 0
                return self._api._exp_archive[self.id][gw]
            elif mins_per_appearance < 60:
                expected_points += (
                    1
                    + (attacking_points_per90 + self.bonus_points_per90)
                    * mins_per_appearance
                    / 90
                )
            else:
                expected_points += (
                    2
                    + (attacking_points_per90 + self.bonus_points_per90)
                    * mins_per_appearance
                    / 90
                    + clean_sheet_probability * clean_sheet_value
                )

            expected_points += goals_conceded_loss

            expected_points *= chance

            if debug:
                mout.varOut("expected_points", expected_points)

            self._api._exp_archive[self.id][gw] = expected_points
            return self._api._exp_archive[self.id][gw]

    # def performed_xpts(self,gw):

    def expected_total_points(
        self, debug=False, return_actual=False, fit_ratio=0.5, use_official=True
    ):

        if self.appearances == 0:
            if return_actual:
                return 0, 0
            else:
                return 0

        actual_total = 0
        expected_total = 0
        diff_list = []

        for gw, actual in zip(self.history["round"], self.history["total_points"]):
            expected = self.expected_points(
                gw=gw, fit_ratio=fit_ratio, use_official=use_official
            )
            expected_total += expected
            actual_total += actual
            # if actual > 20:
            # 	print(self.name,gw,actual)
            diff_list.append(expected - actual)

        if debug:
            mout.headerOut(self.name)
            mout.varOut("actual_total", actual_total)
            mout.varOut("expected_total", expected_total)
            mout.varOut("error", sum(diff_list) / len(diff_list))

        if return_actual:
            return expected_total, actual_total
        else:
            return expected_total

    @property
    def ct_history(self):
        pts = []
        if len(self.history) < 1:
            return pts
        for creativity, threat in zip(
            self.history["creativity"], self.history["threat"]
        ):
            pts.append(creativity + threat)
        return pts

    @property
    def ct_history_scaled(self):
        pts = []
        if len(self.history) < 1:
            return pts
        for creativity, threat in zip(
            self.history["creativity"], self.history["threat"]
        ):
            creativity = float(creativity)
            threat = float(threat)
            if self.position_id < 3:
                pts.append(threat * 1.5 + creativity)
            elif self.position_id == 3:
                pts.append(threat * 1.25 + creativity)
            elif self.position_id == 4:
                pts.append(threat * 4 + creativity)
            # pts.append(creativity+threat)
        return pts

    @property
    def ct_total_scaled(self):
        pts = 0
        if len(self.history) < 1:
            return pts
        for creativity, threat in zip(
            self.history["creativity"], self.history["threat"]
        ):
            creativity = float(creativity)
            threat = float(threat)
            if self.position_id < 3:
                pts += threat * 1.5 + creativity
            elif self.position_id == 3:
                pts += threat * 1.25 + creativity
            elif self.position_id == 4:
                pts += threat * 1 + creativity
            # pts.append(creativity+threat)
        return pts

    @property
    def ct_total_scaled_wPrev(self):
        multiplier = [1.5, 1.5, 1.25, 1][self.position_id]
        return (
            self.ct_total_scaled
            + multiplier * self._prev_threat
            + self._prev_creativity
        )

    # def build_ict_lists(self):
    # 	print(self.history)

    def get_event_ict(self, gw):
        event_stats = self._api.get_player_event_stats(gw, self._id)
        self.extract_event_stats(event_stats)
        return self.__influence, self.__creativity, self.__threat, self.__ict_index

    @property
    def has_fixture_started(self):
        gw = self._api._current_gw
        fixs = self.team_obj.get_gw_fixtures(gw)
        if isinstance(fixs, list):
            if len(fixs) < 1:
                return False
            else:
                return bool(fixs[0]["started"])
        else:
            return bool(fixs["started"])

    @property
    def has_fixture_finished(self):
        gw = self._api._current_gw
        fixs = self.team_obj.get_gw_fixtures(gw)
        if isinstance(fixs, list):
            if len(fixs) < 1:
                return False
            if bool(fixs[-1]["finished"]):
                return True
            else:
                # kickoff = datetime.strptime(fixs[-1]['kickoff'], '%Y-%m-%dT%H:%M:%SZ')
                # kickoff = kickoff.replace(tzinfo=pytz.utc).astimezone(local_tz)
                # # kickoff.replace(tzinfo=None)
                # nowtime = datetime.datetime.now()
                # difference = nowtime - kickoff
                # print(difference)
                return False
        else:
            if bool(fixs["finished"]):
                return True
            else:
                if self.has_fixture_started:
                    fixtures = self._api.get_gw_fixtures(gw)
                    fixs = [f for f in fixtures if f["team_a"] == fixs["team_a"]][0]
                    kickoff = datetime.datetime.strptime(
                        fixs["kickoff"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    kickoff = kickoff.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    nowtime = datetime.datetime.now(local_tz)
                    difference = nowtime - kickoff
                    if difference.total_seconds() > 6000:
                        return True
                    else:
                        return False
                else:
                    return False

    def extract_event_stats(self, event_stats):

        if self.is_manager:
            self.__clean_sheets = event_stats.get("mng_clean_sheets")
            self.__goals_scored = event_stats.get("mng_goals_scored")
            self.__manager_draw = event_stats.get("mng_draw")
            self.__manager_loss = event_stats.get("mng_loss")
            self.__manager_win = event_stats.get("mng_win")
            self.__manager_underdog_draw = event_stats.get("mng_underdog_draw")
            self.__manager_underdog_win = event_stats.get("mng_underdog_win")
            if self.__manager_draw is None:
                self.__minutes = 0
            else:
                self.__minutes = 90

        else:
            self.__goals_scored = event_stats["goals_scored"]
            self.__clean_sheets = event_stats["clean_sheets"]
            self.__minutes = event_stats["minutes"]

        # print(event_stats.keys())
        self.__assists = event_stats["assists"]
        self.__goals_conceded = event_stats["goals_conceded"]
        self.__own_goals = event_stats["own_goals"]
        self.__penalties_saved = event_stats["penalties_saved"]
        self.__penalties_missed = event_stats["penalties_missed"]
        self.__yellow_cards = event_stats["yellow_cards"]
        self.__red_cards = event_stats["red_cards"]
        self.__saves = event_stats["saves"]
        self.__bonus = event_stats["bonus"]
        self.__bps = event_stats["bps"]
        self.__creativity = event_stats["creativity"]
        self.__influence = event_stats["influence"]
        self.__threat = event_stats["threat"]
        self.__ict_index = event_stats["ict_index"]
        self.__total_points = event_stats["total_points"]

    def fetch_event_stats(self, gw):
        gw = gw or self._api.current_gw
        event_stats = self._api.get_player_event_stats(gw, self._id)
        self.extract_event_stats(event_stats)

    @property
    def event_yellows(self):
        gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None
        if self.__yellow_cards is None:
            self.fetch_event_stats(gw)
        return self.__yellow_cards

    @property
    def event_reds(self):
        gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None
        if self.__red_cards is None:
            self.fetch_event_stats(gw)
        return self.__red_cards

    @property
    def event_minutes(self):
        gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None
        if self.__minutes is None:
            self.fetch_event_stats(gw)
        return self.__minutes

    @property
    def event_bps(self):
        gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None
        if self.__bps is None:
            self.fetch_event_stats(gw)
        return self.__bps

    @property
    def event_bonus(self):
        gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None
        if self.__bonus is None:
            self.fetch_event_stats(gw)
        return self.__bonus

    @property
    def event_goals(self):
        gw = self._api.current_gw
        if gw > self._api.current_gw:
            mout.errorOut("Gameweek has not happened yet")
            return None
        if self.__goals_scored is None:
            self.fetch_event_stats(gw)
        return self.__goals_scored

    def get_event_summary(
        self,
        gw,
        event_stats=None,
        md_bold=True,
        pts_line=True,
        team_line=True,
        html_highlight=True,
    ):

        if event_stats is None:
            event_stats = self._api.get_player_event_stats(gw, self._id)

        self.extract_event_stats(event_stats)

        ### fixture

        # print(self.name,list(self.history['round']))

        if "round" not in self.history:
            # mout.error(f'{self} has no round in self.history')
            return "No data."

        # if the player was added to the game late, their history is weird
        h_indices = []
        for i, r in enumerate(self.history["round"]):
            if gw == r:
                h_indices.append(i)

        if len(h_indices) > 1:
            event_stats = None

        kwargs = dict(
            md_bold=md_bold,
            event_stats=event_stats,
            pts_line=pts_line,
            team_line=team_line,
            html_highlight=html_highlight,
        )

        if len(h_indices) == 1:
            return self.get_event_strbuff(h_indices[0], gw, 0, **kwargs)

        elif len(h_indices) == 2:
            return (
                self.get_event_strbuff(h_indices[0], gw, 0, **kwargs)
                + "\n\n"
                + self.get_event_strbuff(h_indices[1], gw, 1, **kwargs)
            )
        elif len(h_indices) == 3:
            return (
                self.get_event_strbuff(h_indices[0], gw, 0**kwargs)
                + "\n\n"
                + self.get_event_strbuff(h_indices[1], gw, 1, **kwargs)
                + "\n\n"
                + self.get_event_strbuff(h_indices[2], gw, 2, **kwargs)
            )
        else:

            str_buffer = "No fixture."
            return str_buffer

    def get_event_strbuff(
        self,
        h_index,
        gw,
        dgw_index,
        event_stats=None,
        md_bold=True,
        pts_line=True,
        html_highlight=True,
        team_line=True,
        player_lines=True,
    ):

        if event_stats is None:
            event_stats = self._api.get_player_event_stats(gw, self._id, dgw_index)

        # print(h_index,gw,dgw_index,player_lines)

        self.extract_event_stats(event_stats)

        if team_line:
            was_home = self.history["was_home"][h_index]
            try:
                home_score = int(self.history["team_h_score"][h_index])
                away_score = int(self.history["team_a_score"][h_index])
            except:
                home_score = None
                away_score = None

            opp_team = self._api.team_name(
                self.history["opponent_team"][h_index], short=False
            )
            score_str = f"{home_score}-{away_score}"

            if home_score is not None:

                if home_score == away_score:
                    result_str = (
                        f"Drew {score_str} at home"
                        if was_home
                        else f"Drew {score_str} away"
                    )
                elif home_score > away_score:
                    result_str = (
                        f"Won {score_str} at home"
                        if was_home
                        else f"Lost {score_str} away"
                    )
                else:
                    result_str = (
                        f"Lost {score_str} at home"
                        if was_home
                        else f"Won {score_str} away"
                    )

                if md_bold:
                    str_buffer = f"<b>{self.team}</b>: {result_str} to {opp_team}.\n"
                else:
                    str_buffer = f"{self.team}: {result_str} to {opp_team}.\n"

            else:

                result_str = "Home" if was_home else "Away"

                if md_bold:
                    str_buffer = f"<b>{self.team}</b>: {result_str} to {opp_team}.\n"
                else:
                    str_buffer = f"{self.team}: {result_str} to {opp_team}.\n"

            if not player_lines:
                return str_buffer

            if md_bold:
                str_buffer += f"<b>{self.name}</b>: "
            else:
                str_buffer += f"{self.name}: "

        else:
            str_buffer = ""

        ### general

        if self.is_manager:

            ### MANAGER STUFF

            if html_highlight:
                if self.__manager_draw:
                    text = "Draw"
                    color = "pale-blue"
                elif self.__manager_win:
                    text = "Win"
                    color = "pale-green"
                elif self.__manager_loss:
                    text = "Loss"
                    color = "dark-grey"
                elif self.__manager_underdog_win:
                    text = "Underdog Win"
                    color = "green"
                elif self.__manager_underdog_draw:
                    text = "Underdog Draw"
                    color = "blue"
                else:
                    text = None

                if text:
                    str_buffer += f'<span class="w3-tag w3-{color}">{text}</span> '

            else:
                if self.__manager_draw:
                    str_buffer += "Draw, "
                elif self.__manager_win:
                    str_buffer += "Win, "
                elif self.__manager_loss:
                    str_buffer += "Loss, "
                elif self.__manager_underdog_win:
                    str_buffer += "Underdog Win, "
                elif self.__manager_underdog_draw:
                    str_buffer += "Underdog Draw, "

        elif self.__minutes > 0:
            if html_highlight:
                str_buffer += (
                    f'<span class="w3-tag w3-dark-grey">{self.__minutes} mins</span> '
                )
            else:
                str_buffer += f"{self.__minutes} Minutes, "

        else:
            if self.has_fixture_finished:
                str_buffer += "Did not play."
            elif self.has_fixture_started:
                str_buffer += "Benched."
            else:
                str_buffer += "Upcoming fixture."

        if self.__goals_scored == 1:
            if html_highlight:
                str_buffer += f'<span class="w3-tag w3-green">Goal</span> '
            else:
                str_buffer += f"Goal, "
        elif self.__goals_scored > 1:
            if html_highlight:
                str_buffer += (
                    f'<span class="w3-tag w3-green">{self.__goals_scored} Goals</span> '
                )
            else:
                str_buffer += f"{self.__goals_scored} Goals, "
        if self.__assists == 1:
            if html_highlight:
                str_buffer += f'<span class="w3-tag w3-blue">Assist</span> '
            else:
                str_buffer += f"Assist, "
        elif self.__assists > 1:
            if html_highlight:
                str_buffer += (
                    f'<span class="w3-tag w3-blue">{self.__assists} Assists</span> '
                )
            else:
                str_buffer += f"{self.__assists} Assists, "
        if self.__own_goals == 1:
            if html_highlight:
                str_buffer += f'<span class="w3-tag">Own Goal</span> '
            else:
                str_buffer += "Own Goal, "
        elif self.__own_goals > 1:
            if html_highlight:
                str_buffer += (
                    f'<span class="w3-tag">{self.__own_goals} Own Goals</span> '
                )
            else:
                str_buffer += f"{self.__own_goals} Own Goals, "
        if self.__penalties_missed == 1:
            if html_highlight:
                str_buffer += f'<span class="w3-tag">Penalty Miss</span> '
            else:
                str_buffer += "Penalty Miss, "
        elif self.__penalties_missed > 1:
            if html_highlight:
                str_buffer += f'<span class="w3-tag">{self.__penalties_missed} Penalties Missed</span> '
            else:
                str_buffer += f"{self.__penalties_missed} Penalties Missed, "
        if self.__yellow_cards > 0:
            if html_highlight:
                str_buffer += f'<span class="w3-tag w3-yellow">Yellow Card</span> '
            else:
                str_buffer += "Yellow Card, "
        if self.__red_cards > 0:
            if html_highlight:
                str_buffer += f'<span class="w3-tag w3-red">Red Card</span> '
            else:
                str_buffer += "Red Card, "
        if self.__bonus > 0:
            if html_highlight:
                str_buffer += (
                    f'<span class="w3-tag w3-aqua">{self.__bonus} Bonus</span> '
                )
            else:
                str_buffer += f"{self.__bonus} Bonus, "

        ### non-attackers

        if self.position_id != 4 and self.__clean_sheets > 0:
            if html_highlight:
                str_buffer += f'<span class="w3-tag w3-purple">Clean Sheet</span> '
            else:
                str_buffer += "Clean Sheet, "

        ### defenders

        if self.position_id < 3 and self.__goals_conceded > 1:
            if html_highlight:
                str_buffer += f'<span class="w3-tag w3-orange">{self.__goals_conceded} Goals Conceded</span> '
            else:
                str_buffer += f"{self.__goals_conceded} Goals Conceded, "

        ### goal keepers

        if self.position_id == 1:

            if self.__penalties_saved == 1:
                if html_highlight:
                    str_buffer += f'<span class="w3-tag w3-green">Penalty Saved</span> '
                else:
                    str_buffer += f"Penalty Saved, "
            elif self.__penalties_saved > 1:
                if html_highlight:
                    str_buffer += f'<span class="w3-tag w3-green">{self.__penalties_saved} Penalties Saved</span> '
                else:
                    str_buffer += f"{self.__penalties_saved} Penalties Saved, "

            if self.__saves > 2:
                if html_highlight:
                    str_buffer += (
                        f'<span class="w3-tag w3-blue">{self.__saves} Saves</span> '
                    )
                else:
                    str_buffer += f"{self.__saves} Saves, "

        if str_buffer.endswith(", "):
            str_buffer = str_buffer[: -len(", ")]

        # print(f'{self.name}, GW{gw}')
        # print(str_buffer)

        if pts_line:
            str_buffer += f"\nPoints: {self.get_event_score(gw)}, Expected: {self.expected_points(gw=gw):.1f}\n"

        return str_buffer

        # fixture = self.get_fixture(gw)
        # print(event_stats.keys())
        # print(f'bps={event_stats["bps"]}')
        # print(f'minutes={event_stats['influe']}')

    def get_relative_gw(self, gw, allow_dwg=False):

        events = list(self.fixtures["event"])

        try:
            index = events.index(gw)
        except:
            return None

        if allow_dwg:

            if events.count(gw) == 2:
                return [index, index + 1]
            elif events.count(gw) == 3:
                return [index, index + 1, index + 3]
            elif events.count(gw) == 0:
                return None

            return index

        else:
            return index

        # relative_gw = gw - self._api.current_gw

        # if self.fixtures['event'][relative_gw-1] > gw:
        # 	events = [int(w) for w in self.fixtures['event'] if w <= 38.0]
        # 	if gw not in events:
        # 		# print(self.name,gw,"no fix")
        # 		return None

        # 	return events.index(gw) + 1

        # return relative_gw

    @property
    def projected_points(self):

        gw = self._api._current_gw

        # team fixtures
        team_fixs = self.team_obj.get_gw_fixtures(gw)
        if not isinstance(team_fixs, list):
            team_fixs = [team_fixs]
        team_fixs = [f for f in team_fixs if not f["finished"]]

        # player fixtures
        df = self.fixtures

        score = self.get_event_score(not_playing_is_none=False)

        try:
            # print(self_fixs)

            # start with achieved score
            # print(f'starting with {score=}')

            self_fixs = df[df["event"] == gw]
            if len(team_fixs) > len(self_fixs):
                return score

            assert len(self_fixs) == len(team_fixs), (
                self,
                gw,
                len(self_fixs),
                len(team_fixs),
            )

            # add outstanding fixtures
            for (i, p_fix), t_fix in zip(self_fixs.iterrows(), team_fixs):
                if not t_fix["started"]:
                    # print(f'{self} adding expected {p_fix["id"]}')

                    # expected points
                    is_home = p_fix["is_home"]
                    opp = t_fix["team_a"] if is_home else t_fix["team_h"]
                    opp = self._api.get_player_team_obj(opp)
                    score += self.expected_points(
                        opponent=opp, debug=False, force=False
                    )

        except Exception as e:
            mout.error(
                f"something went wrong with calculating projected points for {self} {gw=}"
            )
            mout.error(str(e))

        return score

    @property
    def net_transfers(self):
        net = self._transfers_in - self._transfers_out
        return self._api.big_number_format(net)

    @property
    def transfer_percent(self):
        net = int(self._transfers_in - self._transfers_out)
        new_count = float(self.selected_by) * int(self._api.total_players) / 100.0
        old_count = new_count - net
        try:
            result = float(net / old_count * 100)
        except:
            result = 0.0
        return result

    def __str__(self):
        return self.name
        # return self.name + ", " + str(self.price)

    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.id == other.id

    @property
    def outstanding_gwfix(self):
        return list(self.fixtures["event"]).count(self._api.current_gw)

    def num_gwfix(self, gw):

        if gw > self._api.current_gw:
            # outstanding fixtures
            events = list(self.fixtures["event"])
            return events.count(gw)

        elif gw < self._api.current_gw:
            # print(list(self.history['round']))
            return list(self.history["round"]).count(gw)

        else:
            # print(list(self.history['round']).count(gw),self.outstanding_gwfix)
            return list(self.history["round"]).count(gw)
            # return list(self.history['round']).count(gw) + self.outstanding_gwfix

        # add together previous fixtures which match GW
        # with current/live fixture
        # with outstanding gwfix?

        # or go via Team class.

        return None

    @property
    def league_count(self):
        return self._league_count[self._id]

    @league_count.setter
    def league_count(self, arg):
        self._league_count[self._id] = arg

    @property
    def league_multiplier_count(self):
        return self._league_multiplier_count[self._id]

    @league_multiplier_count.setter
    def league_multiplier_count(self, arg):
        self._league_multiplier_count[self._id] = arg

    @property
    def kit_path(self):
        if self._position_id == 1:
            return self._team_obj._kit_path_gkp
        else:
            return self._team_obj._kit_path

    @property
    def kit_name_html(self):
        # html_buffer = f'<img class="w3-image" src="https://github.com/mwinokan/FPL_GUI/blob/main/{self.kit_path}?raw=true" alt="Kit Icon" width="22" height="29">'
        html_buffer = f'<img class="w3-image" src="{self.kit_path}" alt="Kit Icon" width="22" height="29">'
        html_buffer += f' <a href="{self._gui_url}">{self.name}</a> '
        if self.is_yellow_flagged:
            html_buffer += f"⚠️"
        elif self.is_yellow_flagged:
            html_buffer += f"⛔️"
        return html_buffer

    @property
    def next5_expected(self):
        if self._next5_expected is None:
            self._next5_expected = sum(
                [
                    self.expected_points(gw=gw)
                    for gw in range(self._api._current_gw, self._api._current_gw + 6)
                ]
            )
        return self._next5_expected

    def next_expected(self, n, use_official=False):
        return sum(
            [
                self.expected_points(gw=gw, use_official=use_official)
                for gw in range(
                    self._api._current_gw + 1, self._api._current_gw + 1 + n
                )
            ]
        )
