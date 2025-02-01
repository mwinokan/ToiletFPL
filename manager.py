import mout
from player import Player
from squad import Squad
import pandas as pd
import mrich


class Manager:

    def __init__(self, name, id, api, team_name=None, authenticate=False):
        mout.debugOut(f"Manager.__init__({name},{id})")
        self._name = name.title()
        self._team_name = team_name
        self._id = id
        self._api = api

        self._entry_json = None

        self._authenticate = authenticate

        self._league_positions = {}
        self._awards = []

        self._squad = None
        self._kit_json = None
        self._livescore = None
        self._transfer_history = None
        self._transfer_gain = {}
        self._transfer_count = {}
        self._leagues = []

        self._best_gwrank = None
        self._best_orrank = None
        self._worst_gwrank = None
        self._worst_orrank = None

        self._graph_paths = []

        self._active_gws = None
        self._nonwc_transfers = None

        self._kit_path = f"../kits/man_{self.id}.png"
        self._gui_url = f"man_{self.id}.html"
        self._gui_path = f"man_{self.id}.html"

        self.get_stats()
        self.get_chips()
        self.get_team_shirt()

    @property
    def projected_points(self):
        return self.squad.projected_points

    @property
    def leagues(self):
        return self._leagues

    @property
    def gui_url(self):
        return self._gui_url

    @property
    def is_diamond(self):
        return "The RBS Diamond Invitational" in [l.name for l in self.leagues]

    @property
    def is_dead(self):
        if len(self._history_current) < 5:
            return False
        return not any(
            [
                len(self.get_gw_transfers(gw)) > 0
                for gw in range(
                    max(self._api._current_gw - 4, 2), self._api._current_gw + 1
                )
            ]
        )

    @property
    def gui_path(self):
        return self._gui_path

    @property
    def fpl_event_url(self):
        gw = self._api._current_gw
        return f"https://fantasy.premierleague.com/entry/{self.id}/event/{gw}"

    @property
    def fpl_history_url(self):
        return f"https://fantasy.premierleague.com/entry/{self.id}/history"

    @property
    def valid(self):
        if self._api._current_gw > 0 and self._event_points is None:
            return False
        if self.name is None:
            mout.errorOut(f"Manager with id {self.id} has no name!")
        return True

    def assign_league(self, league):
        if league.name not in [l.name for l in self._leagues]:
            self._leagues.append(league)

    @property
    def entry_json(self):
        if not self._entry_json:
            self._entry_json = self._api.get_manager_base(self.id)
        return self._entry_json

    def get_cup_matches(self, league):

        # get manager leagues
        leagues = self.entry_json["leagues"]["classic"]

        # get all cup_matches
        cup_matches = self.entry_json["leagues"]["cup_matches"]

        # get cup league associated to the league
        for l in leagues:
            if l["id"] == league.id:
                cup_league_id = l["cup_league"]
                break
        else:
            # mout.errorOut(f"{self} not in {league}'s Cup")
            return []

        league_matches = [m for m in cup_matches if m["league"] == cup_league_id]

        matches = []

        for match in league_matches:

            # print(match)

            # print(match['winner'])

            # print(match['event'])

            # print(self.name)
            # print(self.team_name)
            # print(self.get_event_score(self._api._current_gw))
            # print(self.fixtures_played)
            # print(self.total_fixtures)

            # print(match['entry_2_entry'])

            if match["is_bye"]:
                opponent = None
            else:

                if self.id == match["entry_1_entry"]:
                    opponent = self._api.get_manager(id=match["entry_2_entry"])
                else:
                    opponent = self._api.get_manager(id=match["entry_1_entry"])

                if opponent.id == self.id:
                    mout.warningOut(
                        f"{self}'s GW{match['event']} oppenent is themselves!"
                    )
                    continue

            # print(self,self.id,opponent)

            # print(opponent.name)
            # print(opponent.team_name)
            # print(opponent.get_event_score(self._api._current_gw))
            # print(opponent.fixtures_played)
            # print(opponent.total_fixtures)

            matches.append(
                {
                    "gw": match["event"],
                    "title": match["knockout_name"],
                    "winner": match["winner"],
                    "self": self,
                    "bye": match["is_bye"],
                    "opponent": opponent,
                }
            )

            # print(match['id'])
            # print(match['league'])

        return matches

        # print(self.entry_json['leagues']['cup_matches'])

    def get_stats(self):

        raw_history = self._api.get_manager_history(self._id)

        self._history_current = pd.DataFrame(raw_history["current"])
        self._history_past = pd.DataFrame(raw_history["past"])
        self._history_chips = list(raw_history["chips"])

        if len(self._history_current) != 0:

            self._event_points = list(self._history_current["points"])
            self._total_points = list(self._history_current["total_points"])
            self._overall_rank = list(self._history_current["overall_rank"])
            self._points_on_bench = list(self._history_current["points_on_bench"])
            self._event_rank = list(self._history_current["rank"])
            self._event_transfers = list(self._history_current["event_transfers"])
            self._event_transfers_cost = list(
                self._history_current["event_transfers_cost"]
            )

            self._squad_value = list(self._history_current["value"])
            self._bank_balance = list(self._history_current["bank"])

            self._squad_value = [v / 10.0 for v in self._squad_value]
            self._bank_balance = [v / 10.0 for v in self._bank_balance]

        else:

            self._event_points = None
            self._total_points = None
            self._overall_rank = None
            self._event_rank = None
            self._points_on_bench = None

            self._squad_value = [1000]
            self._bank_balance = [0]

        if self._authenticate:
            df = self._api.get_manager_auth_stats(self._id)

            self._transfers_available = df["limit"]
            self._transfers_made = df["made"]
            self._bank_balance[-1] = df["bank"] / 10.0
            self._squad_value[-1] = df["value"] / 10.0

        if len(self._history_past) > 0:
            self._past_seasons = list(self._history_past["season_name"])
            self._past_points = list(self._history_past["total_points"])
            self._past_ranks = list(self._history_past["rank"])
        else:
            self._past_seasons = []
            self._past_points = []
            self._past_ranks = []

    def get_team_shirt(self):
        from pathlib import Path

        if self._api._skip_kits:
            if not Path(self._kit_path).is_file():
                self._kit_path = f"../kits/blank_kit.png"
            return

        force_generate = self._api._force_generate_kits
        # force_generate = True

        mout.debug(f"get_team_shirt({self})")

        path = Path(self._kit_path)
        if not path.is_file() or force_generate:

            if self._kit_json is None:
                self._kit_json = self._api.get_manager_team_shirt(self._id)

            if self._kit_json is None:
                self._kit_path = f"../kits/blank_kit.png"
                # self._kit_json = {'kit_shirt_type': 'plain', 'kit_shirt_base': '#E1E1E1', 'kit_shirt_sleeves': '#E1E1E1', 'kit_shirt_secondary': '#E1E1E1'}
            else:
                if not path.is_file() or force_generate:
                    # from os.path import exists
                    # if not exists(self._kit_path):

                    self._api.generate_kit_png(self._kit_json, self._kit_path)

    def get_chips(self):

        self._tc_week = None
        self._bb_week = None
        self._fh_week = None
        self._wc1_week = None
        self._wc2_week = None
        self._am1_week = None
        self._am2_week = None
        self._am3_week = None

        self.__bb_ptsgain = None
        # self._bb_total = None
        # self._bb_rank = None

        self.__tc_ptsgain = None
        self._tc_name = None

        names = []
        events = []

        for chip in self._history_chips:

            if chip["name"] == "3xc":
                self._tc_week = chip["event"]
                # self._tc_name = self.get_current_squad(gw = self._tc_week).captain
                # self._squad = None
                self._tc_ptsgain

            elif chip["name"] == "bboost":
                self._bb_week = chip["event"]
                # rel_gw = self.active_gws.index(self._bb_week)
                # self._bb_total = self._event_points[rel_gw]
                # self._bb_rank = self._event_rank[rel_gw]
            elif chip["name"] == "freehit":
                self._fh_week = chip["event"]
                rel_gw = self.active_gws.index(self._fh_week)
                self._fh_total = self._event_points[rel_gw]
                self._fh_gwrank = self._event_rank[rel_gw]
                self._fh_or = self._overall_rank[rel_gw]
                self._fh_orprev = self._overall_rank[rel_gw - 1]
            elif chip["name"] == "wildcard":
                if self._wc1_week is None:
                    self._wc1_week = chip["event"]
                    cutoff = min(
                        min(self._api._wc_cutoff, self._wc1_week + 5),
                        self._api._current_gw,
                    )
                    rel_gw1 = self.active_gws.index(self._wc1_week - 1)
                    rel_gw2 = self.active_gws.index(cutoff)
                    self._wc1_ordelta = (
                        self._overall_rank[rel_gw1] - self._overall_rank[rel_gw2]
                    )
                    self._wc1_ordelta_percent = (
                        100 * self._wc1_ordelta / self._overall_rank[rel_gw1]
                    )

                    # self._fh_total = self._event_points[rel_gw]
                    # self._fh_gwrank = self._event_rank[rel_gw]
                    # self._fh_or = self._overall_rank[rel_gw]
                    # self._fh_orprev = self._overall_rank[rel_gw-1]

                else:
                    self._wc2_week = chip["event"]
                    cutoff = min(38, self._wc2_week + 5, self._api._current_gw)
                    rel_gw1 = self.active_gws.index(self._wc2_week - 1)
                    rel_gw2 = self.active_gws.index(cutoff)
                    self._wc2_ordelta = (
                        self._overall_rank[rel_gw1] - self._overall_rank[rel_gw2]
                    )
                    self._wc2_ordelta_percent = (
                        100 * self._wc2_ordelta / self._overall_rank[rel_gw1]
                    )

            elif chip["name"] == "manager":
                self._am1_week = chip["event"]
                self._am2_week = chip["event"] + 1
                self._am3_week = chip["event"] + 2

            else:
                print("Unrecognised chip: " + chip["name"])

        self._chip_dict = dict(
            tc=self._tc_week,
            bb=self._bb_week,
            fh=self._fh_week,
            wc1=self._wc1_week,
            wc2=self._wc2_week,
            am1=self._am1_week,
            am2=self._am2_week,
            am3=self._am3_week,
        )
        self._chip_names = dict(
            tc="Triple Captain",
            bb="Bench Boost",
            fh="Free Hit",
            wc1="First Wildcard",
            wc2="Second Wildcard",
            am1="Ass. Man. 1",
            am2="Ass. Man. 2",
            am3="Ass. Man. 3",
        )

    @property
    def _bb_ptsgain(self):
        if self.__bb_ptsgain is None:
            self.get_current_squad(gw=self._bb_week, force=True)
            self.__bb_ptsgain = sum(
                [
                    p.get_event_score(gw=self._bb_week, not_playing_is_none=False)
                    for p in self._squad.players[-4:]
                ]
            )
            self._squad = None
        return self.__bb_ptsgain

    @property
    def gw_rank_gain(self):
        try:
            this_gw = self.active_gws.index(self._api._current_gw)
            last_gw = self.active_gws.index(self._api._current_gw - 1)

            # 1M - 2M / 1M = -100%
            # 2M - 500k / 2M = +75%
            # 464 - 27 / 464 = +94%

            return (
                100
                * (self._overall_rank[last_gw] - self._overall_rank[this_gw])
                / self._overall_rank[last_gw]
            )
        except ValueError:
            return 0

    @property
    def _tc_ptsgain(self):
        if self.__tc_ptsgain is None:
            self.get_current_squad(gw=self._tc_week, force=True)
            self.__tc_ptsgain = self._squad.captain.get_event_score(gw=self._tc_week)
            self._tc_name = self._squad.captain.name
            # mout.out(f"{self} {self._squad.captain} {self._tc_week}")
            self._squad = None
        return self.__tc_ptsgain

    def get_event_chip(self, gw):
        if self._tc_week == gw:
            return "TC"
        elif self._bb_week == gw:
            return "BB"
        elif self._fh_week == gw:
            return "FH"
        elif self._wc1_week == gw:
            return "WC1"
        elif self._wc2_week == gw:
            return "WC2"
        elif self._am1_week == gw:
            return "AM1"
        elif self._am2_week == gw:
            return "AM2"
        elif self._am3_week == gw:
            return "AM3"
        else:
            return None

    def chip_text_list(self, with_name=True):

        # text = [None for i in range(len(self._event_points))]

        data = dict()

        gws = [i for i in self.active_gws if i not in self._api._skip_gws]

        for gw in gws:
            data[gw] = None

        # text = [None for i in self.active_gws if i not in self._api._skip_gws]

        if self._tc_week is not None:
            if with_name:
                data[self._tc_week] = f"TC {self._name}"
            else:
                data[self._tc_week] = "TC"
        if self._bb_week is not None:
            if with_name:
                data[self._bb_week] = f"BB {self._name}"
            else:
                data[self._bb_week] = "BB"
        if self._fh_week is not None:
            if with_name:
                data[self._fh_week] = f"FH {self._name}"
            else:
                data[self._fh_week] = "FH"
        if self._wc1_week is not None:
            if with_name:
                data[self._wc1_week] = f"C1 {self._name}"
            else:
                data[self._wc1_week] = "WC1"
        if self._wc2_week is not None:
            if with_name:
                data[self._wc2_week] = f"C2 {self._name}"
            else:
                data[self._wc2_week] = "WC2"

        text = list(data.values())

        return text

    def get_current_squad(self, gw=None, force=False):
        if self._squad is None or force:

            # mout.debugOut(f"man_{self.id}.get_current_squad()")

            response = self._api.get_manager_team(
                self._id, gw=gw, authenticate=self._authenticate
            )

            player_ids = list(response["element"].values)

            self._squad = Squad(api=self._api)

            for i, id in enumerate(player_ids):
                index = self._api.get_player_index(id)
                # elements = self._api.elements
                # player = Player(elements['web_name'][id],self._api,index)
                player = Player(None, self._api, index=index)
                if self._authenticate:
                    player.purchase_price = response["purchase_price"][i] / 10.0
                    player.selling_price = response["selling_price"][i] / 10.0
                else:
                    player.multiplier = response["multiplier"][i]

                player.is_captain = response["is_captain"][i]
                player.is_vice_captain = response["is_vice_captain"][i]
                player._parent_manager = self
                self._squad.add_player(player)

            if gw is None:
                gw = self._api._current_gw

            if gw == self._api._current_gw and self._api._live_gw:
                self.make_autosubs()
            else:
                old_cap = self._squad.captain
                old_cap.fetch_event_stats(gw)
                # print(f"Captain: {old_cap.name}")
                # print(f"Captain: {old_cap.multiplier}")
                # print(f"Captain: {old_cap.is_captain}")
                # print(f"Captain: {old_cap.is_vice_captain}")
                if old_cap.event_minutes == 0:
                    new_cap = self._squad.vice_captain
                    # print(f"GW{gw} Captain: {old_cap.name} --> {new_cap.name}")
                    new_cap.multiplier = 2
                    new_cap.is_captain = True
                    old_cap.multiplier = 0
                    old_cap.is_captain = False

            if self._tc_week is not None:
                if gw == self._tc_week:
                    self.captain.multiplier = 3

        return self._squad

    def get_squad_history(self):

        gw_squads = {}
        for gw in self.active_gws:
            gw_squads[gw] = self.get_current_squad(gw, force=True)

        all_players = list(
            set(sum([squad.players for squad in gw_squads.values()], []))
        )

        for p in all_players:
            owned = []
            started = []
            benched = []
            captained = []
            multipliers = []
            for gw, squad in gw_squads.items():
                if p in squad.players:
                    p2 = squad.players[squad.players.index(p)]
                    owned.append(gw)
                    # print(p2,gw,p2.multiplier)
                    if p2.multiplier > 0:
                        started.append(gw)
                    if p2.multiplier > 1:
                        captained.append(gw)
                    if p2.multiplier == 0 and p2.event_minutes > 0:
                        benched.append(gw)
                    multipliers.append(p2.multiplier)
            p._weeks_owned = owned
            p._weeks_started = started
            p._weeks_benched = benched
            p._weeks_captained = captained
            p._num_weeks_owned = len(owned)
            p._num_weeks_started = len(started)
            p._num_weeks_captained = len(captained)
            p._num_weeks_benched = len(benched)
            p._multiplier_history = multipliers

            for gw, multiplier in zip(p._weeks_owned, p._multiplier_history):
                pts = p.get_event_score(gw, not_playing_is_none=False)
                p._points_while_owned += pts
                if multiplier > 1:
                    p._points_while_captained += pts
                if multiplier > 0:
                    p._points_while_started += pts
                if multiplier == 0 and p2.event_minutes > 0:
                    p._points_while_benched += pts

            p._avg_pts_owned = (
                round(p._points_while_owned / len(owned), 1) if owned else None
            )
            p._avg_pts_started = (
                round(p._points_while_started / len(started), 1) if started else None
            )
            p._avg_pts_benched = (
                round(p._points_while_benched / len(benched), 1) if benched else None
            )
            p._avg_pts_captained = (
                round(p._points_while_captained / len(captained), 1)
                if captained
                else None
            )
            p._avg_pts_total = (
                round(p.total_points / p.appearances, 1) if p.appearances else None
            )

        all_players = sorted(
            all_players, key=lambda x: x._num_weeks_owned, reverse=True
        )

        self._squad_history = Squad(gw=self.active_gws)
        for p in all_players:
            self._squad_history.add_player(p)

        return self._squad_history

    @property
    def name(self):
        return self._name

    @property
    def score(self):
        if self._total_points is None:
            mout.warningOut(f"No total_points! {self.name}")
            return 0
        return self._total_points[-1]

    @property
    def livescore(self):
        if self._api._live_gw:
            if self._livescore is None:

                score = 0
                for player in self.players:
                    this_score = player.get_event_score()
                    if this_score is not None:
                        score += this_score * player.multiplier
                self._this_transfer_cost = self.get_transfer_cost(self._api.current_gw)
                self._livescore = score - self._this_transfer_cost

            return self._livescore

        else:
            return self.gw_score - self.get_transfer_cost(self._api.current_gw)

    @property
    def total_livescore(self):
        if self._api._current_gw == 1:
            return self.livescore
        else:
            if self._api._live_gw:
                if len(self._total_points) < 2:
                    return self.livescore
                else:
                    # print(self.name,self.id,self._total_points,self.livescore)
                    return self._total_points[-2] + self.livescore

            else:
                return self._total_points[-1]

    @property
    def livescore_nohits(self):
        if self._api._live_gw:
            return self.livescore + self._this_transfer_cost
        else:
            return self.gw_score

    @property
    def gw_score(self):
        return self._event_points[-1]
        # if len(self._history) < 1:
        # 	return 0
        # else:
        # 	return list(self._history['points'])[-1]

    @property
    def last_season_score(self):
        if len(self._past_points) < 1:
            return 0
        else:
            return self._past_points[-1]

    @property
    def overall_rank(self):
        if len(self._history_current) < 1:
            return None
        else:
            return list(self._history_current["overall_rank"])[-1]

    @property
    def gw_rank(self):
        if len(self._history_current) < 1:
            return None
        else:
            return list(self._history_current["rank"])[-1]

    @property
    def team_name(self):
        return self._team_name

    @property
    def squad(self):
        return self.get_current_squad()

    @property
    def players(self):
        return self.get_current_squad().players

    @property
    def id(self):
        return self._id

    def __repr__(self):
        return self._name

    @property
    def captain(self):
        # print(self.squad,self.players)
        return [p for p in self.players if p.is_captain][0]
        # return "N/A"

    @property
    def captain_points(self):
        score = self.captain.get_event_score()
        if score is None:
            return 0
        else:
            return score

    @property
    def purchase_power(self):
        return sum([p.selling_price for p in self.players])

    @property
    def fixtures_played(self):
        count = 0
        for player in self.players:
            if player.get_event_score() is not None:
                count += player.multiplier
        return count

    @property
    def total_fixtures(self):
        count = 0
        for player in self.players:
            count += player.num_gwfix(self._api._current_gw) * player.multiplier
        return count

    @property
    def gw_score(self):
        return self._event_points[-1]

    @property
    def avg_selection(self):
        return sum([p.selected_by for p in self.players if p.multiplier > 0]) / len(
            self.players
        )

    @property
    def team_value(self):
        return self._squad_value[-1]  # + self._bank_balance[-1]
        # return self.squad.value + self._bank_balance[-1]

    @property
    def best_gwrank(self):
        if self._best_gwrank is None:
            best_rank = 100000000
            if len(self._history_current) == 0:
                return best_rank
            for gw, rank in zip(self.active_gws, self._event_rank):
                if gw in self._api._skip_gws:
                    continue
                if rank < best_rank:
                    best_rank = rank
                self._best_gwrank = best_rank
        return self._best_gwrank

    @property
    def best_orrank(self):
        if self._best_orrank is None:
            best_rank = 100000000
            if len(self._history_current) == 0:
                return best_rank
            for gw, rank in zip(self.active_gws, self._overall_rank):
                if gw in self._api._skip_gws:
                    continue
                if rank < best_rank:
                    best_rank = rank
                self._best_orrank = best_rank
        return self._best_orrank

    @property
    def worst_gwrank(self):
        if self._worst_gwrank is None:
            best_rank = 1
            if len(self._history_current) == 0:
                return best_rank
            for gw, rank in zip(self.active_gws, sself._event_rank):
                if gw in self._api._skip_gws:
                    continue
                if rank > best_rank:
                    best_rank = rank
                self._worst_gwrank = best_rank
        return self._worst_gwrank

    @property
    def worst_orrank(self):
        if self._worst_orrank is None:
            best_rank = 1
            if len(self._history_current) == 0:
                return best_rank
            for gw, rank in zip(self.active_gws, self._overall_rank):
                if gw in self._api._skip_gws:
                    continue
                if rank > best_rank:
                    best_rank = rank
                self._worst_orrank = best_rank
        return self._worst_orrank

    @property
    def yellows(self):
        return sum([p.event_yellows * p.multiplier for p in self.players])

    @property
    def reds(self):
        return sum([p.event_reds * p.multiplier for p in self.players])

    @property
    def minutes(self):
        return sum([p.event_minutes * p.multiplier for p in self.players])

    @property
    def minutes_per_player(self):
        ms = [p.event_minutes for p in self.players if p.multiplier]
        return sum(ms) / len(ms)

    @property
    def bench_points(self):
        return sum(
            [
                p.get_event_score(not_playing_is_none=False)
                for p in self.players
                if p.multiplier == 0
            ]
        )

    @property
    def bps(self):
        return sum([p.event_bps * p.multiplier for p in self.players])

    @property
    def goals(self):
        return sum([p.event_goals * p.multiplier for p in self.players])

    @property
    def bonus(self):
        return sum([p.event_bonus * p.multiplier for p in self.players])

    def get_card_count(self, red_mult=2.1):
        return self.yellows + red_mult * self.reds

    @property
    def card_emojis(self):
        str_buffer = ""
        for i in range(self.reds):
            str_buffer += "🟥 "
        for i in range(self.yellows):
            str_buffer += "🟨 "
        return str_buffer.strip()

    @property
    def transfer_history(self):
        if self._transfer_history is None:
            self._transfer_history = self._api.get_manager_transfers(self.id)
        return self._transfer_history

    @property
    def num_nonwc_transfers(self):
        if self._nonwc_transfers is None:
            self._nonwc_transfers = len(
                [
                    t
                    for t in self.transfer_history
                    if t["event"] != self._wc1_week
                    and t["event"] != self._wc2_week
                    and t["event"] != 17
                    and t["event"] != 7
                    and t["event"] != self._fh_week
                ]
            )
        return self._nonwc_transfers

    @property
    def num_hits(self):
        hits = 0
        for gw in self.active_gws:
            hits += int(self.get_transfer_cost(gw) / 4)
        return hits

    def get_gw_transfers(self, gw=None, simplify=False):
        if gw == None:
            gw = self._api.current_gw
        if len(self.transfer_history) > 0:
            transfers = []
            for d in self.transfer_history:
                if d["event"] == gw:
                    transfers.append(d)

            transfers = sorted(transfers, key=lambda x: x["time"])

            if simplify:

                # BROKEN!x

                new_transfers = {}

                for transfer in transfers:

                    if transfer["element_out"] in new_transfers.values():
                        for key, val in new_transfers.items():
                            if val == transfer["element_out"]:
                                # val = transfer['element_in']
                                new_transfers[key] == transfer["element_in"]
                            break
                    else:
                        new_transfers[transfer["element_out"]] = transfer["element_in"]

                print(gw, new_transfers)

                transfers = []

                for key, val in new_transfers.items():
                    print(key, val)
                    transfers.append(dict(element_out=key, element_in=val))

            return transfers
        else:
            return []

    @property
    def total_transfer_gain(self):
        total = 0
        for i in self.active_gws:
            total += self.calculate_transfer_gain(gw=i)
        return total

    def calculate_transfer_gain(self, gw=None, debug=False):

        if gw is None:
            gw = self._api.current_gw

        transfers = self.get_gw_transfers(gw=gw)

        score = 0

        self._transfer_count[gw] = len(transfers)

        if len(transfers) == 0:
            self._transfer_gain[gw] = 0
            self._transfer_uniqueness = 0
            return 0

        wc_active = False
        if self._wc1_week is not None and gw == self._wc1_week:
            wc_active = True
        elif self._wc2_week is not None and gw == self._wc2_week:
            wc_active = True

        transfer_uniqueness = 0.0

        if debug:
            print(self)

        for d in transfers:
            p_out = Player(
                None, self._api, index=self._api.get_player_index(d["element_out"])
            )
            p_in = Player(
                None, self._api, index=self._api.get_player_index(d["element_in"])
            )

            p_in_score = p_in.get_event_score(gw=gw)
            p_out_score = p_out.get_event_score(gw=gw)

            transfer_uniqueness -= p_in.transfer_percent
            transfer_uniqueness += p_out.transfer_percent

            if p_in_score is None:
                p_in_score = 0
            if p_out_score is None:
                p_out_score = 0

            if debug:
                print(p_out, p_in, p_in_score, p_out_score)

            score += -p_out_score
            score += p_in_score

        if not wc_active:
            score -= self.get_transfer_cost(gw)

        self._transfer_gain[gw] = score
        self._transfer_uniqueness = transfer_uniqueness

        return score

    def get_transfer_str(self, gw=None, short=False):

        if gw is None:
            gw = self._api.current_gw

        str_buff = ""
        score = 0

        wc_active = False
        if self._wc1_week is not None and gw == self._wc1_week:
            wc_active = True
        elif self._wc2_week is not None and gw == self._wc2_week:
            wc_active = True
        fh_active = False
        if self._fh_week is not None and gw == self._fh_week:
            fh_active = True

        # transfers = self.get_gw_transfers(gw=gw,simplify=True)
        transfers = self.get_gw_transfers(gw=gw, simplify=False)

        self._transfer_count[gw] = len(transfers)

        if len(transfers) == 0:
            self._transfer_gain[gw] = 0
            return ""

        if wc_active:
            str_buff += f"**WC** "
        elif wc_active:
            str_buff += f"**FH** "
        if not short:
            str_buff += f"\n"

        for i, d in enumerate(transfers):
            p_out = Player(
                None, self._api, index=self._api.get_player_index(d["element_out"])
            )
            p_in = Player(
                None, self._api, index=self._api.get_player_index(d["element_in"])
            )
            p_in_score = p_in.get_event_score(gw=gw)
            p_out_score = p_out.get_event_score(gw=gw)
            if p_in_score is None:
                p_in_score = 0
            if p_out_score is None:
                p_out_score = 0
            score += -p_out_score
            score += p_in_score
            if not short:
                str_buff += (
                    f"{p_out.name} ({p_out_score}) → {p_in.name} ({p_in_score})\n"
                )

        score -= self.get_transfer_cost(gw)

        if short:
            str_buff += f"{len(transfers)} "
            str_buff += f"({score})\n"
        else:
            str_buff += f"gain= {score}\n"

        self._transfer_gain[gw] = score

        return str_buff

    def get_specific_overall_rank(self, gw=None):
        i = self._active_gws.index(gw)
        return self._overall_rank[i]

    def get_specific_event_rank(self, gw=None):
        i = self._active_gws.index(gw)
        return self._event_rank[i]

    def get_transfer_cost(self, gw):

        if gw == 1:
            return 0

        now_gw = self._api._current_gw
        start_gw = 0

        if len(self._overall_rank) < now_gw:
            start_gw = now_gw - len(self._overall_rank)

        j = gw - start_gw

        return self._event_transfers_cost[j - 1]

    def get_event_score(self, gw):

        now_gw = self._api._current_gw

        if self._api._live_gw and gw == now_gw:
            return self.livescore

        start_gw = 0

        if len(self._overall_rank) < now_gw:
            start_gw = now_gw - len(self._overall_rank)

        j = gw - start_gw

        try:
            return self._event_points[j - 1]
        except IndexError:
            mout.error(f"Can't index {self}'s _event_points[{j-1}] {gw=}")
            return 0.0

    def get_event_performed_xpts(self, gw):
        # for p in self.players:
        # 	print(p,p.get_event_score(),p.get_performed_xpts(gw),p.multiplier)
        return float(
            sum([p.get_performed_xpts(gw) * p.multiplier for p in self.players])
        )

    @property
    def gw_xg(self):
        gw = self._api._current_gw
        return float(sum([p.get_gw_xg(gw) * p.multiplier for p in self.players]))

    @property
    def gw_xa(self):
        gw = self._api._current_gw
        return float(sum([p.get_gw_xa(gw) * p.multiplier for p in self.players]))

    @property
    def gw_performed_xpts(self):
        gw = self._api._current_gw
        return self.get_event_performed_xpts(gw)

    @property
    def active_gws(self):
        if self._api._current_gw == 0:
            return []
        if self._active_gws is None:
            start_gw = 0
            now_gw = self._api.current_gw
            if len(self._overall_rank) < now_gw:
                start_gw = now_gw - len(self._overall_rank)
            self._active_gws = []
            for i in range(start_gw, now_gw):
                # if int(i+1) not in self._api._skip_gws:
                self._active_gws.append(int(i + 1))
        return self._active_gws

    def create_rank_graph(self, plot=True, show=False):

        if plot:
            mout.debugOut("create_rank_graph()")

            import matplotlib.pyplot as plt
            from matplotlib.ticker import ScalarFormatter, MaxNLocator

            with plt.style.context("seaborn-v0_8-white"):

                plt.rcParams["axes.linewidth"] = 2.0
                plt.rcParams["axes.edgecolor"] = "k"

                """
				
				Logarithmic y-axis

				Plot league positions from self._league_positions as lines
				Plot gw rank from self._event_rank as scatter
				Plot OR from self._overall_rank as lines
				Add chips

				"""

                # fig,axs = plt.subplots(nrows=2,sharex=True,figsize=[5,8])
                fig, ax = plt.subplots(figsize=[5, 5])

                #### Rank Axis

                # set up axes
                ax.set_yscale("log")
                ax.invert_yaxis()
                ax.set_ylabel("Rank")
                ax.set_xlabel("Gameweek")
                ax.grid(
                    which="both", axis="both", zorder=-1, color="white", linewidth=2
                )

                # plots

                x = [i for i in self.active_gws if i not in self._api._skip_gws]

                y = [
                    r
                    for i, r in zip(self.active_gws, self._event_rank)
                    if i not in self._api._skip_gws
                ]
                ax.scatter(x, y, label="GW Rank", marker="o", color="r", zorder=2)

                y = [
                    r
                    for i, r in zip(self.active_gws, self._overall_rank)
                    if i not in self._api._skip_gws
                ]
                ax.plot(
                    x,
                    y,
                    linestyle="-",
                    marker=None,
                    color="b",
                    label="Overall Rank",
                    zorder=1,
                )

                # axis ticks
                ax.set_axisbelow(True)
                max_rank = max([max(self._event_rank), max(self._overall_rank)])
                min_rank = min([min(self._event_rank), min(self._overall_rank)])
                tick_nums, tick_strs = self.graph_ticks(min_rank, max_rank)
                ax.set_yticks(tick_nums, tick_strs)
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))

                plt.legend(bbox_to_anchor=(0.5, 1.25), loc="upper center", ncol=2)
                plt.tight_layout(pad=0.5)

                plt.savefig(f"graphs/{self.id}_ranks.png", dpi=150)

                plt.close()

        self._graph_paths.append(f"graphs/{self.id}_ranks.png")

    def create_leaguepos_graph(self, plot=True, show=False):

        if plot:
            mout.debugOut("create_leaguepos_graph()")

            import matplotlib.pyplot as plt
            from matplotlib.ticker import ScalarFormatter, MaxNLocator

            with plt.style.context("seaborn-v0_8-white"):

                plt.rcParams["axes.linewidth"] = 2.0
                plt.rcParams["axes.edgecolor"] = "k"

                """
				
				Add chips

				"""

                # fig,axs = plt.subplots(nrows=2,sharex=True,figsize=[5,8])
                fig, ax = plt.subplots(figsize=[5, 5])

                #### Rank Axis

                # set up axes
                ax.invert_yaxis()
                ax.set_ylabel("League Position")
                ax.set_xlabel("Gameweek")
                ax.grid(
                    which="both", axis="both", zorder=-1, color="white", linewidth=2
                )

                if len(self._leagues) > 0:

                    for pair in self._league_positions.items():
                        x = []
                        y = []

                        try:
                            league = [l for l in self._leagues if l.name == pair[0]][0]
                        except IndexError:
                            continue

                        for pos_pair in pair[1].items():
                            if int(pos_pair[0]) in self._api._skip_gws:
                                continue
                            x.append(int(pos_pair[0]))
                            y.append(pos_pair[1] + 1)
                        ax.plot(x, y, label=league.shortname, color=league.colour_str)

                    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

                else:

                    mout.errorOut(
                        f"Manager {self.name} ({self.id}) has no league data."
                    )

                plt.legend(bbox_to_anchor=(0.5, 1.25), loc="upper center", ncol=2)
                plt.tight_layout(pad=0.5)

                # if show:
                # 	plt.show()

                plt.savefig(f"graphs/{self.id}_leaguepos.png", dpi=150)

                plt.close()

        self._graph_paths.append(f"graphs/{self.id}_leaguepos.png")

    def graph_ticks(self, min_y, max_y):

        tick_nums = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]
        tick_strs = ["1", "10", "100", "1k", "10k", "100k", "1M", "10M"]

        new_nums = []
        new_strs = []
        for i in range(len(tick_nums)):
            new_nums.append(tick_nums[i])
            new_strs.append(tick_strs[i])
            if tick_nums[i] > max_y:
                break

        tick_nums = new_nums
        tick_strs = new_strs

        n = len(tick_nums) - 1

        new_nums = []
        new_strs = []
        for i in range(len(tick_nums)):
            new_nums.append(tick_nums[n - i])
            new_strs.append(tick_strs[n - i])
            if tick_nums[n - i] < min_y:
                break

        return new_nums, new_strs

    def create_points_graph(self, plot=True, show=False):
        """

        Plot transfer gain
        Add chips

        """

        if plot:
            mout.debugOut("create_points_graph()")

            import matplotlib.pyplot as plt
            from matplotlib.ticker import ScalarFormatter, MaxNLocator

            with plt.style.context("seaborn-v0_8-white"):

                plt.rcParams["axes.linewidth"] = 2.0
                plt.rcParams["axes.edgecolor"] = "k"

                fig, ax = plt.subplots(figsize=[5, 5])

                #### Rank Axis

                # set up axes
                ax.set_ylabel("Points")
                ax.set_xlabel("Gameweek")
                ax.grid(
                    which="both", axis="both", zorder=-1, color="white", linewidth=2
                )

                avgs = self._api.get_event_averages()

                pts = self._event_points
                if self._api._live_gw:
                    pts[-1] = self.livescore

                # plots

                x = [i for i in self.active_gws if i not in self._api._skip_gws]

                # x = [i for i in range(1,self._api._current_gw+1) if i not in self._api._skip_gws]
                y = [
                    p if i not in self._api._skip_gws else None
                    for i, p in zip(range(1, self._api._current_gw + 1), avgs)
                ]
                ax.plot(
                    range(1, self._api._current_gw + 1),
                    y,
                    linestyle="-",
                    marker=None,
                    color="b",
                    label="Global Average",
                    zorder=3,
                )

                y = [
                    p
                    for i, p in zip(self.active_gws, pts)
                    if i not in self._api._skip_gws
                ]
                ax.scatter(x, y, label="GW Points", marker="o", color="r", zorder=4)

                hit_cost = [
                    self.get_transfer_cost(w)
                    for w in self.active_gws
                    if w not in self._api._skip_gws
                ]
                hit_yerrs = [[h for h in hit_cost], [0 for h in hit_cost]]
                ax.errorbar(
                    x,
                    y,
                    yerr=hit_yerrs,
                    label="Transfer Cost",
                    marker="o",
                    color="k",
                    zorder=2,
                    linewidth=0,
                    elinewidth=2,
                    fmt="none",
                    capsize=3,
                    capthick=2,
                )

                # for league in self._leagues:
                # 	# x = [i for i in range(1,self._api._current_gw+1) if i not in self._api._skip_gws]
                # 	# y = [p if i not in self._api._skip_gws else None for i,p in zip(range(1,self._api._current_gw+1),league.average_event_points)]

                # 	x = []
                # 	y = []

                # 	for gw,pts in zip(range(1,self._api._current_gw+1),league.average_event_points):
                # 		if gw in self._api._skip_gws:
                # 			continue
                # 		x.append(gw)
                # 		y.append(pts)

                # 	# ax.plot(range(1,self._api._current_gw+1),league.average_event_points,linestyle='--',marker=None,label=f"{league.shortname} Average",zorder=1,color=league.colour_str)
                # 	ax.plot(x,y,linestyle='--',marker=None,label=f"{league.shortname} Average",zorder=1,color=league.colour_str)

                # axis ticks
                ax.set_axisbelow(True)
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))

                plt.legend(bbox_to_anchor=(0.5, 1.25), loc="upper center", ncol=2)
                plt.tight_layout(pad=0.5)

                # if show:
                # 	plt.show()

                plt.savefig(f"graphs/{self.id}_points.png", dpi=150)

                plt.close()

        self._graph_paths.append(f"graphs/{self.id}_points.png")

    def make_autosubs(self):
        # mout.debugOut(f"man_{self.id}.make_autosubs()")

        bench = [p for p in self.players if p.multiplier == 0]

        if len(bench) != 4:
            if self._bb_week != self._api._current_gw:
                mout.warningOut(
                    f"Bench has wrong number of players ({self.name}). And no BB played!"
                )
                print("before:", bench)
                bench = self.players[-4:]
                print("after:", bench)
                for p in bench:
                    if p.is_captain:
                        self.squad.vice_captain.multiplier = 2
                    p.multiplier = 0
            else:
                bench = self.players[-4:]

        if all([p.needs_autosub for p in bench[1:]]):
            # mout.warningOut(f'No one on the bench is playing ({self.name})')
            return

        # goalkeeper
        for player in self.squad.starting_goalkeepers:
            if player.needs_autosub:
                # mout.out(f'{player.name} did not play ({self.name})',end=' ')
                # mout.varOut("bench",bench)
                replacement = bench[0]
                # mout.varOut('replacement',replacement)
            else:
                break
            if replacement.needs_autosub:
                # mout.warningOut(f'{replacement.name} also did not play. No change made')
                break
            else:
                # make the change
                player.multiplier = 0
                replacement.multiplier = 1
                replacement.was_subbed = True
                bench[0] = player
                # mout.varOut("new bench",bench)
                break

        n_defenders = len(self.squad.starting_defenders)
        n_changes = 0

        # outfield
        for player in self.players:

            if player.multiplier == 0:
                continue

            if player.position_id == 1:
                continue

            if player.needs_autosub:
                # mout.out(f'{player.name} did not play ({self.name}).',end=' ')
                # mout.varOut("bench",bench)
                # mout.varOut("squad",self.players)

                # select replacement
                replacement = bench[1]
                if replacement.needs_autosub:
                    # mout.warningOut(f'{replacement.name} also did not play.')
                    replacement = bench[2]
                    if replacement.needs_autosub:
                        # mout.warningOut(f'{replacement.name} also did not play.')
                        replacement = bench[3]
                        if replacement.needs_autosub:
                            # mout.errorOut(f'No one on the bench is playing.')
                            break

                # check for formation validity
                if (
                    n_defenders == 3
                    and player.position_id == 2
                    and replacement.position_id != 2
                ):
                    # mout.warningOut('Replacement must be a defender')
                    if bench[2].position_id == 2 and not bench[2].needs_autosub:
                        replacement = bench[2]
                    elif bench[3].position_id == 2 and not bench[3].needs_autosub:
                        replacement = bench[3]
                    else:
                        # mout.warningOut(f'Could not find replacement defender. {self.name}, {self.id}')
                        continue

                # mout.varOut('replacement',replacement)

                # check for captaincy
                if player.is_captain:
                    new_cap = self.squad.vice_captain
                    player.is_captain = False
                    player.is_vice_captain = True
                    # mout.warningOut(f'cap {player.name}')
                    # mout.warningOut(f'new_cap {new_cap.name}')
                    new_cap.is_captain = True
                    new_cap.is_vice_captain = False
                    new_cap.multiplier = 2
                    # mout.warningOut(f'{new_cap.name} is now captain!')

                # make the change
                player.multiplier = 0
                replacement.multiplier = 1
                replacement.was_subbed = True
                n_changes += 1
                bench[1] = bench[2]
                try:
                    bench[2] = bench[3]
                except IndexError:
                    print(self.name)
                    print(bench)

                bench[3] = player

                # mout.varOut("new bench",bench)

                if n_changes == 3:
                    break
