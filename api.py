import mout
import requests
import datetime
import json as js
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from team import Team
from player import Player
from os.path import exists
from manager import Manager
from plot import team_strength
from collections import Counter

from pprint import pprint
import mrich

url = "https://fantasy.premierleague.com/api/"

GC_DICT = {
    "MCI": 34,
    "ARS": 29,
    "MUN": 58,
    "NEW": 62,
    "LIV": 41,
    "BHA": 62,
    "AVL": 61,
    "TOT": 61,
    "BRE": 65,
    "FUL": 61,
    "CRY": 58,
    "CHE": 63,
    "WOL": 65,
    "WHU": 74,
    "BOU": 67,
    "NFO": 67,
    "EVE": 51,
    "IPS": 57 * 2 * 38 / 46,
    "LEI": 41 * 2 * 38 / 46,
    "SOU": 63 * 2 * 38 / 46,
}

GF_DICT = {
    "MCI": 96,
    "ARS": 91,
    "MUN": 57,
    "NEW": 85,
    "LIV": 86,
    "BHA": 55,
    "AVL": 76,
    "TOT": 74,
    "BRE": 56,
    "FUL": 55,
    "CRY": 57,
    "CHE": 77,
    "WOL": 50,
    "WHU": 60,
    "BOU": 54,
    "NFO": 49,
    "EVE": 40,
    "IPS": 92 / 2 * 38 / 46,
    "LEI": 89 / 2 * 38 / 46,
    "SOU": 87 / 2 * 38 / 46,
}


class Request404(Exception):
    pass


class FPL_API:

    _current_gw = 0

    _gw_stats = {}
    _element_histories = {}
    _element_summaries = {}

    _managers = {}
    _team_fixtures = {}
    _gw_fixtures = {}
    _loaded_players = []
    _exp_archive = {}
    _elements_by_team = None
    _element_indices_by_team = None
    _special_gws = {}

    _skip_gws = []
    _wc_cutoff = 16

    _season_str = 2425
    _season_str_fmt = "24/25"
    _last_season_str = 2324

    _prev_element_dict = None

    def __init__(
        self,
        offline=False,
        force_generate_kits=False,
        quick=True,
        write_offline_data=False,
    ):
        mout.debugOut(f"FPL_API.__init__(quick={quick})")

        self._init_time = datetime.datetime.now()
        self._request_log = []
        self._offline = offline
        self._write_offline_data = write_offline_data

        if offline:
            if exists(f"data_{self._season_str}.json"):
                f = open(f"data_{self._season_str}.json", "rt")
                self._request_data = js.load(f)
            else:
                mout.errorOut("No offline data found!", fatal=True)
        else:
            self._request_data = {}

        if exists(f"data_{self._last_season_str}.json"):
            f = open(f"data_{self._last_season_str}.json", "rt")
            self._prev_request_data = js.load(f)
        else:
            mout.errorOut("No previous season offline data found!", fatal=False)

        self._scrape_team_pairs = [
            [0, "Man Utd"],
            [1, "Leeds"],
            [2, "Arsenal"],
            [3, "Newcastle"],
            [5, "Spurs"],
            [6, "Aston Villa"],
            [7, "Chelsea"],
            [10, "Everton"],
            [12, "Leicester"],
            [13, "Liverpool"],
            [16, "Nott'm Forest"],
            [19, "Southampton"],
            [20, "West Ham"],
            [30, "Crystal Palace"],
            [35, "Brighton"],
            [38, "Wolves"],
            [40, "Ipswich"],
            [42, "Man City"],
            [48, "Sheffield Utd"],
            [53, "Fulham"],
            [89, "Burnley"],
            [90, "Bournemouth"],
            [93, "Brentford"],
            [101, "Luton"],
        ]

        self._short_team_pairs = {
            0: "MUN",
            1: "LEE",
            2: "ARS",
            3: "NEW",
            5: "TOT",
            6: "AVL",
            7: "CHE",
            10: "EVE",
            12: "LEI",
            13: "LIV",
            16: "NFO",
            19: "SOU",
            20: "WHY",
            30: "CRY",
            35: "BHA",
            38: "WOL",
            40: "IPS",
            42: "MCI",
            48: "SHU",
            53: "FUL",
            89: "BUR",
            90: "BOU",
            93: "BRE",
            101: "LUT",
        }

        self._team_styles = {
            "Arsenal": {
                "background-color": "#B7272E",
                "color": "white",
                "accent": "#E5D3B7",
            },
            "Aston Villa": {
                "background-color": "#5D1133",
                "color": "#91B6E4",
                "accent": "#F0D147",
            },
            "Brentford": {
                "background-color": "#A22621",
                "color": "white",
                "accent": "black",
            },
            "Bournemouth": {
                "background-color": "black",
                "color": "#BF3B33",
                "accent": "#B29460",
            },
            "Brighton": {
                "background-color": "white",
                "color": "#2253A0",
                "accent": "#1A2561",
            },
            "Burnley": {
                "background-color": "#9D3E45",
                "color": "#CCDCF3",
                "accent": "#FBEA88",
            },
            "Chelsea": {
                "background-color": "#051383",
                "color": "white",
                "accent": "PaleGoldenRod",
            },
            "Crystal Palace": {
                "background-color": "#BE2C2A",
                "color": "#2C67A9",
                "accent": "white",
            },
            "Everton": {
                "background-color": "#3A83E2",
                "color": "white",
                "accent": "#0F276C",
            },
            "Fulham": {
                "background-color": "white",
                "color": "black",
                "accent": "#A6271E",
            },
            "Ipswich": {
                "background-color": "#1E2F75",
                "color": "white",
                "accent": "#BA423A",
            },
            "Leicester": {
                "background-color": "SteelBlue",
                "color": "white",
                "accent": "GoldenRod",
            },
            "Leeds": {
                "background-color": "white",
                "color": "GoldenRod",
                "accent": "black",
            },
            "Liverpool": {
                "background-color": "#AF2532",
                "color": "white",
                "accent": "#75151A",
            },
            "Luton": {
                "background-color": "#E6552F",
                "color": "white",
                "accent": "#22355A",
            },
            "Man City": {
                "background-color": "#A1C2E7",
                "color": "#061736",
                "accent": "white",
            },
            "Man Utd": {
                "background-color": "#D1443F",
                "color": "black",
                "accent": "white",
            },
            "Newcastle": {
                "background-color": "WhiteSmoke",
                "color": "black",
                "accent": "#BEA679",
            },
            "Norwich": {"background-color": "limegreen", "color": "yellow"},
            "Nott'm Forest": {
                "background-color": "#DF4148",
                "color": "white",
                "accent": "black",
            },
            "Sheffield Utd": {
                "background-color": "white",
                "color": "#EA4D43",
                "accent": "black",
            },
            "Southampton": {
                "background-color": "white",
                "color": "FireBrick",
                "accent": "black",
            },
            "Spurs": {
                "background-color": "white",
                "color": "#212935",
                "accent": "#E1E752",
            },
            "Watford": {"background-color": "black", "color": "red"},
            "West Ham": {
                "background-color": "#7A2E3D",
                "color": "#95CDFA",
                "accent": "white",
            },
            "Wolves": {
                "background-color": "#F2BC44",
                "color": "black",
                "accent": "white",
            },
        }

        self._authenticated = False
        self._force_generate_kits = force_generate_kits
        self._skip_kits = False
        self._fixtures = None

        self._ct_total_fit_data = None
        if exists("ct_total_fit.json"):
            f = open("ct_total_fit.json", "rt")
            self._ct_total_fit_data = js.load(f)

        self.parse_bootstrap()
        if self._last_season_str:
            self.parse_bootstrap(last_season=True)

        for i, is_current in enumerate(self._events["is_current"]):
            if is_current:
                self._current_gw = i + 1
                self._previous_gw = i
                self._next_gw = i + 2

                if self._events["finished"][i]:
                    self._live_gw = False
                    self._wiki_gw = self._current_gw
                else:
                    self._live_gw = True
                    self._wiki_gw = self._current_gw
                break
        else:
            self._live_gw = False
            self._current_gw = 0
            self._wiki_gw = 0

        print(f"Current: GW{self._current_gw}")
        print(f"Wiki: GW{self._wiki_gw}")
        print(f"Live: {self._live_gw}")

        if offline:
            mout.warningOut("Offline mode!")

    def request(self, handle, last_season=False):

        if last_season:
            return self._prev_request_data[handle]

        if self._offline and handle in self._request_data.keys():
            return self._request_data[handle]
        else:
            try:
                r = requests.get(handle)
            except requests.exceptions.ConnectionError:
                mout.warningOut("ConnectionError, trying again...")
                return self.request(handle)

            if "502" in str(r):
                mout.warningOut("Error 502, trying again...")
                return self.request(handle)

            if "404" in str(r):
                print(handle)
                mout.errorOut("Request 404'd")
                raise Request404()
                return {}

            try:
                json = r.json()
                self._request_data[handle] = json
                self._request_log.append(handle)

                if "The game is being updated." in json:
                    mout.errorOut("The game is being updated.", fatal=True)

                return json
            except requests.exceptions.JSONDecodeError:
                print(r)
                mout.errorOut(f"Problem handling JSON from {handle}", fatal=True)

    def finish(self):

        if self._write_offline_data:
            js.dump(self._request_data, open(f"data_{self._season_str}.json", "wt"))
            # js.dump(self._request_data,open('data_2223.json','wt'), indent="\t")

        mout.varOut("#requests=", len(self._request_log))

        reqs = [x for x in self._request_log]
        data = Counter(reqs)
        for req in self._request_log:
            if data[req] > 1:
                mout.warningOut(f"Multiple requests ({data[req]}) to {req}")

        js.dump(self._request_log, open("requests.json", "wt"), indent="\t")

        self._finish_time = datetime.datetime.now()

        mout.varOut("Execution Time", str(self._finish_time - self._init_time))

    def create_team_styles_css(self):

        html_buffer = ""

        for team in self.teams:

            try:
                html_buffer += f".w3-{team.shortname.lower()}"
                html_buffer += "{"
                html_buffer += f'color:{team.style["color"]} !important; '
                html_buffer += f'background-color:{team.style["background-color"]} '
                html_buffer += "!important}\n"

                html_buffer += f".w3-{team.shortname.lower()}-inv"
                html_buffer += "{"
                html_buffer += f'color:{team.style["background-color"]} !important; '
                html_buffer += f'background-color:{team.style["color"]} !important'
                html_buffer += "}\n"

                html_buffer += f".w3-{team.shortname.lower()}-border-inv"
                html_buffer += "{"
                html_buffer += f'border: 1px {team.style["color"]} solid !important; '
                html_buffer += "}\n"
            except TypeError:
                mout.error(f"Missing style for {team}")

            # html_buffer += f'.w3-{team.shortname.lower()}-acc'
            # html_buffer += '{'
            # html_buffer += f'background-color:{team.style["accent"]} !important'
            # html_buffer += '}\n'

            # .w3-theme-l5 {color:#000 !important; background-color:#f0f4f8 !important}

        return html_buffer

    @property
    def fixtures(self):
        if self._fixtures is None:
            json = self.request(url + "fixtures/")
            self._fixtures = pd.DataFrame(json)

        return self._fixtures

    def get_gw_fixtures(self, gw=None):
        if gw is None:
            gw = self._current_gw

        if gw not in self._gw_fixtures.keys():

            json = self.request(url + f"fixtures/?event={gw}")

            if len(json) == 0:
                self._gw_fixtures[gw] = []
            else:
                f = pd.DataFrame(json)

                fixtures = []
                for i, c in enumerate(f["code"]):
                    this_fix = dict(
                        index=i,
                        finished=f["finished"][i],
                        started=f["started"][i],
                        team_a=f["team_a"][i],
                        team_h=f["team_h"][i],
                        team_a_score=f["team_a_score"][i],
                        team_h_score=f["team_h_score"][i],
                        kickoff=f["kickoff_time"][i],
                    )
                    fixtures.append(this_fix)
                self._gw_fixtures[gw] = fixtures

        return self._gw_fixtures[gw]

    def parse_bootstrap(self, last_season=False):
        if not last_season:
            self._bootstrapjson = self.request(url + "bootstrap-static/")
            self.__events = None
            self.__elements = None
            self.__element_types = None
            self.__teamdata = None
            self.__teams = None
        else:
            self._prev_bootstrapjson = self.request(
                url + "bootstrap-static/", last_season=True
            )

            self._prev_events = pd.DataFrame(self._prev_bootstrapjson["events"])
            self._prev_elements = pd.DataFrame(self._prev_bootstrapjson["elements"])

            self._prev_element_dict = self.build_element_dict(self._prev_elements)
            self._prev_element_types = pd.DataFrame(
                self._prev_bootstrapjson["element_types"]
            )
            self._prev_teamdata = pd.DataFrame(self._prev_bootstrapjson["teams"])

            self._prev_avg_gc_per_game = sum(GC_DICT.values()) / len(GC_DICT) / 38
            self._prev_avg_gf_per_game = sum(GF_DICT.values()) / len(GF_DICT) / 38

            self._prev_teams = []
            for id, name, shortname in zip(
                self._prev_teamdata["id"],
                self._prev_teamdata["name"],
                self._prev_teamdata["short_name"],
            ):
                team = Team(id, name, self, shortname=shortname)

                team._goals_conceded = GC_DICT[team.shortname]
                team._goals_scored = GF_DICT[team.shortname]

                matches = [t for t in self.teams if t.name == name]
                if matches:
                    matches[0]._prev_obj = team
                self._prev_teams.append(team)

    def build_element_dict(self, df):

        # print(df.columns)

        data = {}
        for i, key in enumerate(df["id"]):
            pd = df.iloc[i]
            # data[key] = {}
            data[f"{pd['first_name']} {pd['second_name']}"] = {}
            for col in df.columns:
                # data[key][col] = pd[col]
                data[f"{pd['first_name']} {pd['second_name']}"][col] = pd[col]

        return data

    @property
    def total_players(self):
        return int(self._bootstrapjson["total_players"])

    def get_manager(self, name=None, id=None, team_name=None, authenticate=False):
        id = int(id)
        if id not in self._managers.keys():
            if team_name is None or name is None:
                mout.warningOut(
                    f"Warning: Manager with id {id} was not found in dictionary and no details were passed!"
                )
            m = Manager(name, id, self, team_name=team_name, authenticate=authenticate)
            # if m.valid:
            self._managers[id] = m
        # else:
        # m = self._managers[id]
        return self._managers[id]

    @property
    def _element_types(self):
        if self.__element_types is None:
            self.__element_types = pd.DataFrame(self._bootstrapjson["element_types"])
        return self.__element_types

    @property
    def elements_by_team(self):
        # mout.debugOut(f"FPL_API.elements_by_team()")

        if not self._elements_by_team:

            self._elements_by_team = {}

            player_ids = self._elements["id"]

            for i, pid in enumerate(player_ids):

                # if self._elements['minutes'][i] < 90:
                # 	continue

                index = self.get_player_index(pid)

                p = Player(None, self, index=index)

                if p._shortteam not in self._elements_by_team.keys():
                    self._elements_by_team[p._shortteam] = []
                self._elements_by_team[p._shortteam].append(p)

        # print(self._elements_by_team.keys())

        return self._elements_by_team

    @property
    def element_indices_by_team(self):
        # mout.debugOut(f"FPL_API.element_indices_by_team()")

        if not self._element_indices_by_team:

            self._element_indices_by_team = {}

            player_ids = self._elements["id"]

            for i, pid in enumerate(player_ids):

                # if self._elements['minutes'][i] < 90:
                # 	continue

                index = self.get_player_index(pid)

                p = Player(None, self, index=index)

                if p._shortteam not in self._element_indices_by_team.keys():
                    self._element_indices_by_team[p._shortteam] = []
                self._element_indices_by_team[p._shortteam].append(index)

        # print(self._element_indices_by_team.keys())

        return self._element_indices_by_team

    @property
    def _elements(self):
        if self.__elements is None:
            self.__elements = pd.DataFrame(self._bootstrapjson["elements"])
        return self.__elements

    @property
    def _events(self):
        if self.__events is None:
            self.__events = pd.DataFrame(self._bootstrapjson["events"])
        return self.__events

    @property
    def _teamdata(self):
        if self.__teamdata is None:
            self.__teamdata = pd.DataFrame(self._bootstrapjson["teams"])
        return self.__teamdata

    @property
    def _teams(self):
        if self.__teams is None:
            self.__teams = []
            total_gc = 0
            for id, name, shortname in zip(
                self._teamdata["id"],
                self._teamdata["name"],
                self._teamdata["short_name"],
            ):
                team = Team(id, name, self, shortname=shortname)
                # self.__teams[-1].total_goals
                total_gc += team.goals_conceded

                self.__teams.append(team)
            self._avg_gc = total_gc / len(self.__teams)

            # team_strength(self.__teams)

        return self.__teams

    @property
    def elements(self):
        return self._elements

    @property
    def element_types(self):
        return self._element_types

    @property
    def teams(self):
        return self._teams

    @property
    def teamdata(self):
        return self._teamdata

    @property
    def current_gw(self):
        return self._current_gw

    @property
    def team_styles(self):
        return self._team_styles

    def authenticate_old(self):
        if not self._authenticated:

            print("Authenticating...")

            self._session = requests.session()

            url = "https://users.premierleague.com/accounts/login/"

            import json

            file = "_auth_payload"
            file = open(file, "r")
            payload = json.load(file)

            # print(payload)

            # payload = {
            # 	'password': 'password_goes_here',
            # 	'login': 'email@domain.com',
            # 	'redirect_uri': 'https://fantasy.premierleague.com/a/login',
            # 	'app': 'plfpl-web'
            # }
            # json.dump(payload,file)

            response = self._session.post(url, data=payload)

            if "<Response [403]>" in str(response):
                mout.errorOut("Could not authenticate", code=403, fatal=True)
                self._authenticated = False
                return

            self._authenticated = True

    def authenticate(self):
        mout.debugOut("FPL_API.authenticate()")
        if not self._authenticated:

            print("Authenticating...")

            self._session = requests.session()

            headers = {
                "authority": "users.premierleague.com",
                "method": "GET",
                "path": "/",
                "scheme": "https",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "cache-control": "max-age=0",
                "cookie": "csrftoken=3Ci7DiqxgqBVAFvchL7ROqqZ859ZT2tDagwUC2xGtaB3kVVDQFlr2xGZNXnz3d96; pl_euconsent-v2=CPk8z79Pk8z79FCABAENCxCsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}; datadome=lGOgjeg7LPkTRamk~wZby~Ifsq~eOLk--xqTwZyz7h3IolmlH8yFGoaapuAg091mkNR0wk7ccHd5J_-vEJt0NgB-LXRYL4gFW5mX7TJzBew3TIqvXTZ9jaQwNGIE3Oa",
                "referer": "https://users.premierleague.com/accounts/login/",
                "sec-ch-device-memory": "8",
                "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-full-version-list": '"Not?A_Brand";v="8.0.0.0", "Chromium";v="108.0.5359.124", "Google Chrome";v="108.0.5359.124"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            }

            headers = {
                "authority": "users.premierleague.com",
                "method": "POST",
                "path": "/accounts/login/",
                "scheme": "https",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                "cache-control": "max-age=0",
                "content-length": "224",
                "content-type": "application/x-www-form-urlencoded",
                "cookie": "csrftoken=3Ci7DiqxgqBVAFvchL7ROqqZ859ZT2tDagwUC2xGtaB3kVVDQFlr2xGZNXnz3d96; pl_euconsent-v2=CPk8z79Pk8z79FCABAENCxCsAP_AAH_AAAwIF5wAQF5gXnABAXmAAAAA.YAAAAAAAAAAA; pl_euconsent-v2-intent-confirmed={%22tcf%22:[755]%2C%22oob%22:[]}; pl_oob-vendors={}; datadome=7WQ3aBUJ-FOkg4azLJDLuyoIGNzyJqXpzM2aL9Q8kVcJWdRDVMG-50_YSLah1x_woJPe1qEe2GZjU1aJVvnw_gVfoktuHmJ-HlcpatZkvZ4gpGDYQub2MuCCeop8Glh-",
                "origin": "https://users.premierleague.com",
                "referer": "https://users.premierleague.com/?state=fail&reason=credentials",
                "sec-ch-device-memory": "8",
                "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-full-version-list": '"Not?A_Brand";v="8.0.0.0", "Chromium";v="108.0.5359.124", "Google Chrome";v="108.0.5359.124"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            }

            import json

            file = "_auth_payload"
            file = open(file, "r")
            data = json.load(file)

            # payload = {
            # 	'password': 'password_goes_here',
            # 	'login': 'email@domain.com',
            # 	'redirect_uri': 'https://fantasy.premierleague.com/a/login',
            # 	'app': 'plfpl-web'
            # }
            # json.dump(payload,file)

            url = "https://users.premierleague.com/accounts/login/"
            url = "https://users.premierleague.com"

            # print(data)
            # print(headers)

            response = self._session.post(url, data=data, headers=headers)
            # response = self._session.post(url,data=data)
            # print(response)

            if "<Response [403]>" in str(response):
                print(
                    "https://mkyong.com/computer-tips/how-to-view-http-headers-in-google-chrome/"
                )
                mout.errorOut(
                    "Could not authenticate. Refresh the headers? (datadome cookie)",
                    code=403,
                    fatal=True,
                )
                self._authenticated = False
                return

            self._authenticated = True

    def team_name(self, index, short=False):
        # print(index)
        if short:
            return self._teamdata["short_name"][index - 1]
        else:
            return self._teamdata["name"][index - 1]

    def get_player_team_obj(self, team_id):
        return self.teams[team_id - 1]

    def get_player_name(self, player_id):
        for i, id in enumerate(self.elements["id"]):
            if id == player_id:
                player_id = i
                break
        return (
            self.elements["first_name"][player_id]
            + " "
            + self.elements["web_name"][player_id]
        )

    def get_player_index(self, player_id):
        for i, id in enumerate(self.elements["id"]):
            if id == player_id:
                return i
        return False

    def get_player_fixtures(self, team, player_id):
        if team not in self._team_fixtures.keys():
            # r = requests.get(url+'element-summary/'+str(player_id)+'/')
            # self._request_log.append(url+'element-summary/'+str(player_id)+'/')
            json = self.get_player_summary(player_id)
            self._team_fixtures[team] = pd.DataFrame(json["fixtures"])
        return self._team_fixtures[team]

    def get_team_by_shortname(self, shortname):
        return [t for t in self.teams if t._shortname == shortname][0]

    def get_team_fixtures(self, team_id):

        # print(self.fixtures.keys())

        fix = []

        for event, team_a, team_h, team_a_score, team_h_score, started, finished in zip(
            self.fixtures["event"],
            self.fixtures["team_a"],
            self.fixtures["team_h"],
            self.fixtures["team_a_score"],
            self.fixtures["team_h_score"],
            self.fixtures["started"],
            self.fixtures["finished"],
        ):
            if int(team_id) == int(team_a) or int(team_id) == int(team_h):
                fix.append(
                    dict(
                        event=event,
                        team_a=team_a,
                        team_h=team_h,
                        team_a_score=team_a_score,
                        team_h_score=team_h_score,
                        started=started,
                        finished=finished,
                    )
                )

        return fix

        # if team_shortname not in self._team_fixtures.keys():

        # 	talismen = {
        # 	"ARS": "Ramsdale",
        # 	"AVL": "Bailey",
        # 	"BRE": "Mbeumo",
        # 	"BOU": "Billing",
        # 	"BHA": "Groß",
        # 	"CHE": "Havertz",
        # 	"CRY": "Zaha",
        # 	"EVE": "Gray",
        # 	"FUL": "Mitrović",
        # 	"LEI": "Vardy",
        # 	"LEE": "Bamford",
        # 	"LIV": "Salah",
        # 	"MCI": "De Bruyne",
        # 	"MUN": "Rashford",
        # 	"NEW": "Trippier",
        # 	"NFO": "Neco Williams",
        # 	"SOU": "Ward Prowse",
        # 	"TOT": "Kane",
        # 	"WHU": "Bowen",
        # 	"WOL": "Pedro Neto",
        # 	}

        # 	p = Player(talismen[team_shortname],self)
        # 	json = self.get_player_summary(p.id)
        # 	self._team_fixtures[team_shortname] = pd.DataFrame(json['fixtures'])
        # return self._team_fixtures[team_shortname]

    def get_player_summary(self, player_id):
        if player_id in self._element_summaries:
            return self._element_summaries[player_id]
        else:
            json = self.request(url + "element-summary/" + str(player_id) + "/")
            self._element_summaries[player_id] = json
            return json

    def get_player_history(self, player_id):
        if player_id in self._element_histories:
            return self._element_histories[player_id]
        else:
            json = self.get_player_summary(player_id)
            df = pd.DataFrame(json["history"])
            self._element_histories[player_id] = df
            return df

    def request_event_stats(self, gw):
        json = self.request(url + "event/" + str(gw) + "/live")

        # # adjust live bonus?

        # # if self._live_gw:

        # gw_fixtures = self.get_gw_fixtures(gw)

        # print(json['elements'][0])

        # # clear bonus
        # for element_stats in json['elements']:
        # 	element_stats['stats']['bonus'] = 0

        # # loop over fixtures
        # for fix in gw_fixtures:

        # 	pprint(fix)

        # 	fid = fix['index']

        # 	# get all player ids
        # 	team_h = self.get_player_team_obj(fix['team_h']).shortname
        # 	team_a = self.get_player_team_obj(fix['team_a']).shortname

        # 	pids = self.element_indices_by_team[team_h] + self.element_indices_by_team[team_a]

        # 	pid_bps_pairs = []

        # 	for pid in pids:
        # 		element_stats = json['elements'][pid-1]['stats']
        # 		bps = element_stats['bps']
        # 		pid_bps_pairs.append([pid-1,bps])

        # 	pid_bps_pairs = sorted(pid_bps_pairs, key=lambda x: x[1], reverse=True)

        # 	# print(team_h,team_a)
        # 	# pprint(pid_bps_pairs)

        # 	scores = [p[1] for p in pid_bps_pairs]
        # 	counter = Counter(scores)

        # 	count = 0

        # 	award = {}

        # 	for i,bps in enumerate(sorted(list(set(scores)), reverse=True)[:3]):
        # 		num = counter[bps]

        # 		print(bps,num)

        # 		if count >= 3:
        # 			break

        # 		count += num

        # 		if i == 0:
        # 			award[bps] = 3
        # 		elif i == 1:
        # 			award[bps] = 2
        # 		elif i == 2:
        # 			award[bps] = 1

        # 	for element in json['elements']:
        # 		element_stats = element['stats']

        # 		# probably broken for DGWs

        # 		# print(fid,[e['fixture'] for e in element['explain']])

        # 		if fid not in [e['fixture'] for e in element['explain']]:
        # 			continue

        # 		if element_stats['bps'] in award:
        # 			element_stats['bonus'] += award[element_stats['bps']]
        # 			print('awarding:',element_stats['bps'],element_stats['bonus'])

        return json

    def get_player_event_stats(self, gw, player_id, dgw_index=0):
        if gw not in self._gw_stats.keys():
            json = self.request_event_stats(gw)
            df = pd.DataFrame(json["elements"])
            self._gw_stats[gw] = df

        df = self._gw_stats[gw]

        player_stats = df[df["id"] == player_id]["stats"].values

        if not len(player_stats):
            if gw == self._current_gw:
                mout.warningOut(
                    f"Could not retrieve stats for player {player_id} (GW:{gw}, {len(player_stats)=})"
                )
            return {
                "minutes": 0,
                "goals_scored": 0,
                "assists": 0,
                "clean_sheets": 0,
                "goals_conceded": 0,
                "own_goals": 0,
                "penalties_saved": 0,
                "penalties_missed": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "saves": 0,
                "bonus": 0,
                "bps": 0,
                "influence": 0,
                "creativity": 0,
                "threat": 0,
                "ict_index": 0,
                "total_points": 0,
                "in_dreamteam": 0,
            }

        return player_stats[0]

    def get_event_averages(self):
        # print(self._events['average_entry_score'][0:self._current_gw])
        return list(self._events["average_entry_score"][0 : self._current_gw])

    def get_manager_base(self, id):

        json = self.request(url + "entry/" + str(id) + "/")

        return json

    def get_manager_history(self, id):
        json = self.request(url + "entry/" + str(id) + "/history/")
        # try:
        # 	json = r.json()
        # except:
        # 	print(url+'entry/'+str(id)+'/history/')
        # 	mout.errorOut("Problem parsing manager stats JSON, trying again")
        # 	return self.get_manager_history(id)
        return json

    def get_manager_transfers(self, id):
        # try:
        json = self.request(
            f"https://fantasy.premierleague.com/api/entry/{id}/transfers/"
        )
        # print(id,json)
        return list(json)
        # except:
        # 	return []

    def get_manager_team(self, id, gw=None, authenticate=True):

        if gw is None:
            gw = self._current_gw

        if authenticate:

            self.authenticate()

            r = self._session.get(url + "my-team/" + str(id) + "/")
            self._request_log.append(url + "my-team/" + str(id) + "/")

            json = r.json()

            # if "not provided" in json['detail']:
            # 	mout.errorOut("Authentication Failed.",fatal=False)
            # 	# json=dict({"picks":[{"element":559,"position":1,"selling_price":51,"multiplier":1,"purchase_price":51,"is_captain":False,"is_vice_captain":True},{"element":237,"position":2,"selling_price":80,"multiplier":1,"purchase_price":75,"is_captain":False,"is_vice_captain":False},{"element":256,"position":3,"selling_price":69,"multiplier":1,"purchase_price":66,"is_captain":False,"is_vice_captain":False},{"element":234,"position":4,"selling_price":70,"multiplier":1,"purchase_price":70,"is_captain":False,"is_vice_captain":False},{"element":370,"position":5,"selling_price":53,"multiplier":1,"purchase_price":53,"is_captain":False,"is_vice_captain":False},{"element":233,"position":6,"selling_price":130,"multiplier":2,"purchase_price":130,"is_captain":True,"is_vice_captain":False},{"element":359,"position":7,"selling_price":107,"multiplier":1,"purchase_price":107,"is_captain":False,"is_vice_captain":False},{"element":420,"position":8,"selling_price":68,"multiplier":1,"purchase_price":66,"is_captain":False,"is_vice_captain":False},{"element":578,"position":9,"selling_price":59,"multiplier":1,"purchase_price":59,"is_captain":False,"is_vice_captain":False},{"element":63,"position":10,"selling_price":65,"multiplier":1,"purchase_price":65,"is_captain":False,"is_vice_captain":False},{"element":450,"position":11,"selling_price":58,"multiplier":1,"purchase_price":56,"is_captain":False,"is_vice_captain":False},{"element":448,"position":12,"selling_price":40,"multiplier":0,"purchase_price":40,"is_captain":False,"is_vice_captain":False},{"element":413,"position":13,"selling_price":77,"multiplier":0,"purchase_price":77,"is_captain":False,"is_vice_captain":False},{"element":51,"position":14,"selling_price":47,"multiplier":0,"purchase_price":47,"is_captain":False,"is_vice_captain":False},{"element":418,"position":15,"selling_price":47,"multiplier":0,"purchase_price":47,"is_captain":False,"is_vice_captain":False}],"chips":[{"status_for_entry":"available","played_by_entry":[],"name":"wildcard","number":1,"start_event":21,"stop_event":38,"chip_type":"transfer"},{"status_for_entry":"available","played_by_entry":[22],"name":"freehit","number":2,"start_event":2,"stop_event":38,"chip_type":"transfer"},{"status_for_entry":"available","played_by_entry":[],"name":"bboost","number":1,"start_event":1,"stop_event":38,"chip_type":"team"},{"status_for_entry":"available","played_by_entry":[],"name":"3xc","number":1,"start_event":1,"stop_event":38,"chip_type":"team"}],"transfers":{"cost":4,"status":"cost","limit":1,"made":4,"bank":0,"value":1039}})

            return pd.DataFrame(json["picks"])

        else:

            # https://fantasy.premierleague.com/entry/780664/event/1
            # https://fantasy.premierleague.com/api/entry/780664/event/1

            # print(f'{url}entry/{id}/event/{self._current_gw}')

            this_url = (
                f"https://fantasy.premierleague.com/api/entry/{id}/event/{gw}/picks/"
            )

            # print(this_url)
            # try:
            # 	r = requests.get(this_url)
            # except requests.exceptions.ConnectionError:
            # 	mout.warningOut(f"Connection error for {id}'s picks, retrying...")
            # 	return self.get_manager_team(id,authenticate)
            # self._request_log.append(this_url)
            # json = r.json()

            try:
                json = self.request(this_url)
            except Request404 as e:
                print(e)
                mout.error(f"Could not get GW{gw} picks for {id=}")
                raise

            if "picks" not in json.keys():
                print(this_url)
                mout.warningOut("No picks in json")

            return pd.DataFrame(json["picks"])

    def get_manager_auth_stats(self, id):

        self.authenticate()

        r = self._session.get(url + "my-team/" + str(id) + "/")
        self._request_log.append(url + "my-team/" + str(id) + "/")

        # print(url+'my-team/'+str(id)+'/')

        try:
            import json

            # json = r.json()
            json = json.loads(r.content)
        except json.decoder.JSONDecodeError:
            # print(r)
            mout.errorOut("Invalid server response.", fatal=True)

        if "detail" in json.keys() and "not provided." in json["detail"]:
            mout.errorOut("Authentication failed.", fatal=True)

        return dict(json["transfers"])

    def get_fixture_diff(self, opp_team, own_team, is_home, is_attacker, overall=False):

        # if is_home and is_attacker:
        # 	print(f'{self.team_name(own_team)} attacker at home against {self.team_name(opp_team)}')
        # if not is_home and is_attacker:
        # 	print(f'{self.team_name(own_team)} attacker at away to {self.team_name(opp_team)}')
        # if is_home and not is_attacker:
        # 	print(f'{self.team_name(own_team)} defender at home against {self.team_name(opp_team)}')
        # if not is_home and not is_attacker:
        # 	print(f'{self.team_name(own_team)} defender at away to {self.team_name(opp_team)}')

        # overall difference
        return self._teams[own_team - 1].strength(
            overall=overall, defence=not is_attacker, is_home=is_home
        ) - self._teams[opp_team - 1].strength(
            overall=overall, defence=is_attacker, is_home=not is_home
        )

        # # overall difference
        # overall = self._teams[own_team-1].strength(overall=True,defence=False,is_home=is_home) - self._teams[opp_team-1].strength(overall=True,defence=True,is_home=not is_home)

        # # special difference
        # special = self._teams[own_team-1].strength(overall=False,defence=not is_attacker,is_home=is_home) - self._teams[opp_team-1].strength(overall=False,defence=is_attacker,is_home=not is_home)

        # if overall:
        # 	return overall

        # return special

    def get_manager_team_shirt(self, id):
        import json as js

        mout.debugOut(f"get_manager_team_shirt({id})")

        json = self.request(url + "entry/" + str(id) + "/")

        # r = requests.get(url+'entry/'+str(id)+'/')
        # self._request_log.append(url+'entry/'+str(id)+'/')
        # try:
        # 	json = r.json()
        # except:
        # 	print(url+'entry/'+str(id)+'/')
        # 	mout.errorOut("Problem parsing JSON")

        if json["kit"] is None:
            return None

        return js.loads(json["kit"])

    def generate_kit_png(self, kit_json, path):
        mout.debugOut(f"generate_kit_png({path})")

        from cairosvg import svg2png

        # svg_buffer = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="29" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        # svg_buffer = '<svg xmlns="http://www.w3.org/2000/svg" width="91" height="156" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'

        svg_buffer = '<svg xmlns="http://www.w3.org/2000/svg" id="ism-team-kit" data-name="ism-team-kit" viewBox="0 0 405 530" role="img" aria-labelledby="ism-kit-title ism-kit-desc">'

        svg_buffer += f'<path id="shirt_colour" d="M228.2 2c-16.8 7.2-42.7 14.1-66.3 11.8-6.9-.7-13.2-3.8-18.9-3.6-9.6.5-15.7 19.7-24.9 21.3-10.3 6.6-22.9 11-33.1 17.7h-1.2c-4.9 1.8-10.1 3.4-13 7.1h-1.2c-11.1 5.1-17.5 7.3-26 15-.6-3.8-12.1 48.4-8.4 91.6 4.3 49.9 23 95.8 23.3 95.8.6 6.4-.6 20 .5 29.5v124.4c-1.5 36.5-.7 57.8-5.9 82.8 31.3 16 142.8 29.6 143.2 29.6 37.4 3 72.6 7.3 99.1-3.4 10-3.3 18.4-24.3 13.4-34.5-5.5-51-31.2-86.4-24.9-145.5 1.1-10.1.4-11.4 1.2-16.6-.3-24.3 13.9-79.1 14.9-84.9 1.6 3.8 46.1-159.2 42.9-165-19.7-24-57.7-30.2-85-51.8-3.7-1.1-6.5-2.9-9.5-4.7A144.4 144.4 0 0 1 229.3 2h-1.2z" fill="{kit_json["kit_shirt_base"]}"></path>'

        # print(kit_json)
        # print(kit_json["kit_shirt_base"])

        if kit_json["kit_shirt_type"] not in ["plain", "stripes", "hoops"]:
            mout.warningOut(f"Not implemented: {kit_json['kit_shirt_type']}")

        if kit_json["kit_shirt_type"] == "stripes":

            svg_buffer += f'<g id="stripes_group" data-name="stripes group"><path id="stripe_1" data-name="stripe 1" d="M68 58c-6 33.3-3.5 115.6-1.9 203.6 2.3 95.9 3.7 196.2 2.5 239.3 5.8 1.4 12.1 2.2 17.5 4 7.5.5 12.7 3.3 19.7 4.4.3-65.4-2.1-168.6-3.8-264.1-1.3-88.2-1.9-168.8 5.6-207.9C99.9 41.1 68.5 57.7 68 58z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path><path id="stripe_2" data-name="stripe 2" d="M184.6 62.6c-14.4 4.9-29 6.4-40.3 2.3-6.9 89.5-.8 344.7.2 452.9q10.7 1.6 22.1 2.5c6.6 1.2 14 1.7 21 2.5-6.3-151.9-11.1-397.4-3-460.2z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path><path id="stripe_3" data-name="stripe 3" d="M276.6 526.2c-13-92.1-15.8-186.3-15.6-279.2.1-43.7 1-87.7 5.2-131.3 2.3-24 2.8-57.3 16.9-78.1-12-6-25.6-13.4-36.3-21.4C205.2 70.4 225 431.4 233.6 528c13.9 2.3 42.1-1.8 43-1.8z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path></g>'

        if kit_json["kit_shirt_type"] == "hoops":
            svg_buffer += f'<g id="hoops_group" data-name="hoops group"><path id="hoop_1" data-name="hoop 1" d="M54.2 64.3a79.8 79.8 0 0 0-10.4 6.9c-1 9.8-1.5 20.3-1.6 30.9 81.1 13.1 180.9 12.5 256.4 9.2a385.4 385.4 0 0 1 15.8-43.1c-68.3 2.3-153.3 8.2-260.2-3.9z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path><path id="hoop_2" data-name="hoop 2" d="M287.4 181.6a174.6 174.6 0 0 1 1.2-23.5c-60.9 4.1-145.8 4.4-244.9-10.1 1.2 17.2 2.8 32.7 4.2 43.5 74.1 15.3 171.1 16.5 244 13.6a78.2 78.2 0 0 1-4.5-23.5z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path><path id="hoop_3" data-name="hoop 3" d="M55.4 240.5l3 18.3c-1.1-.1-.1 15.2.1 24.1 71.1 9.8 159.7 18 229.5 12 2.2-10.7 10.1-42 10.4-44.7-61.5 5.8-161-1.2-243-9.7z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path><path id="hoop_4" data-name="hoop 4" d="M284.9 386.8a171.9 171.9 0 0 1-1.2-44.9c-59.8 5.9-136.9-1.7-224.8-13.5v44.4c71.2 12.1 151.3 20.5 226 14z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path><path id="hoop_5" data-name="hoop 5" d="M275.4 479.2c13.8-1.6 22.8-3.4 31.2-5.9-2.7-14.7-6.7-28.3-10.8-41.9-5.5 1.2-13.2 3.4-23.9 4.2-56.7 4.3-131.6-1.3-213.1-20.4-.6 15.9-.8 28.9-1.3 40.6 57 16 145.8 31.9 217.9 23.4z" fill="{kit_json["kit_shirt_secondary"]}" display="inline"></path></g>'

        # <g id="hoops_group" data-name="hoops group"><path id="hoop_1" data-name="hoop 1" d="M54.2 64.3a79.8 79.8 0 0 0-10.4 6.9c-1 9.8-1.5 20.3-1.6 30.9 81.1 13.1 180.9 12.5 256.4 9.2a385.4 385.4 0 0 1 15.8-43.1c-68.3 2.3-153.3 8.2-260.2-3.9z" fill="#E1E1E1" display="none"></path><path id="hoop_2" data-name="hoop 2" d="M287.4 181.6a174.6 174.6 0 0 1 1.2-23.5c-60.9 4.1-145.8 4.4-244.9-10.1 1.2 17.2 2.8 32.7 4.2 43.5 74.1 15.3 171.1 16.5 244 13.6a78.2 78.2 0 0 1-4.5-23.5z" fill="#E1E1E1" display="none"></path><path id="hoop_3" data-name="hoop 3" d="M55.4 240.5l3 18.3c-1.1-.1-.1 15.2.1 24.1 71.1 9.8 159.7 18 229.5 12 2.2-10.7 10.1-42 10.4-44.7-61.5 5.8-161-1.2-243-9.7z" fill="#E1E1E1" display="none"></path><path id="hoop_4" data-name="hoop 4" d="M284.9 386.8a171.9 171.9 0 0 1-1.2-44.9c-59.8 5.9-136.9-1.7-224.8-13.5v44.4c71.2 12.1 151.3 20.5 226 14z" fill="#E1E1E1" display="none"></path><path id="hoop_5" data-name="hoop 5" d="M275.4 479.2c13.8-1.6 22.8-3.4 31.2-5.9-2.7-14.7-6.7-28.3-10.8-41.9-5.5 1.2-13.2 3.4-23.9 4.2-56.7 4.3-131.6-1.3-213.1-20.4-.6 15.9-.8 28.9-1.3 40.6 57 16 145.8 31.9 217.9 23.4z" fill="#E1E1E1" display="none"></path></g>

        svg_buffer += f'<path id="shirt_sleeve_left_colour" data-name="shirt sleeve left colour" d="M50 208s-12.2-79.6-6.2-136.8c-.6.5-19.5 21.1-22.7 33.7-1 7.2-4.2 12.3-4.7 20.1v1.2c-3.9 8.8-4 21.2-7.1 30.8v5.9c-2.7 9.1 1 18.6 1.2 28.4C5 204 8.1 225.4.9 236.3v1.2c3.1 4.8 8.3 7.4 13 10.6 6.3 2.3 12.5 4.9 20.1 5.9 5.6 3 16.8 3.8 24.4 4.8z" fill="{kit_json["kit_shirt_sleeves"]}"></path><path id="shirt_sleeve_right_colour" data-name="shirt sleeve right colour" d="M319.6 56.7c-17.1 36-33.1 84.4-32.2 124.9.4 18.8 9 34.2 15.4 51.3 3.5 9-.7 21.2 5.8 28.1 8.8 9.2 78.3-18.6 92.8-26.6-5.4-7.3-21.9-80.6-39.5-125.2-15.7-39.5-39.5-50.9-42.3-52.5z" fill="{kit_json["kit_shirt_sleeves"]}"></path>'

        svg_buffer += '<path id="shirt_grey_tint_fill" data-name="shirt grey tint fill" opacity="0.2" d="M137.5 12.6s-13.7 43.2 25 43.2C230.7 40.2 230.7 2 230.7 2h-2.6c-16.8 7.2-42.7 14.1-66.3 11.8-6.9-.7-13.2-3.8-18.9-3.6a10.3 10.3 0 0 0-6.1 2.8z"></path>'

        svg_buffer += '<path id="Main_shirt_outline" data-name="Main shirt outline" d="M54 494.8s8.9-123.3 6.7-162.6-2.5-73.8-2.5-73.8-31.5-3.7-40.5-7.4S2 238.9 2 238.9s4.6-23.1 7.1-49.8c.6-6.2-.5-15.7 0-22.2 2.5-29.6 8.9-54.1 12-62.1C28.8 84.8 43.3 71 43.3 71s78-39.8 81.7-44.6 11-17.6 15.9-17 22.8 5.8 38.7 5.8S220 2 229 2c5.4 0 11 10.6 25.8 20.2 10.8 7 64.7 34.5 64.7 34.5s14.1 7 28 26.7c9 12.8 18 34.5 22.7 50.7 6.8 23.3 14 49.7 20.5 69.6 4.6 14.1 9.6 24.5 10.2 30.2S341 258.4 331.5 261s-22.8 3.7-23.4.5-6.4-29.2-6.4-29.2-21.7 72.9-19 128.2c2.2 45.1 27.7 121.3 27.4 134.9s-5.8 33.4-58.3 33.4-198.4-23.4-197.8-34z" style="fill: none; stroke: rgb(148, 148, 141); stroke-linecap: round; stroke-linejoin: round; stroke-width: 4px;"></path>'

        svg_buffer += '<path d="M232.6 8.5l3.6 2.4c-1.1 10.8-10.6 23.4-25.9 34.1s-35.7 18.2-51.2 18.2c-10.1 0-17.9-2.8-23.2-8.3s-8.4-14.7-8.3-26.4l6-8.4c-1.6 13.2.3 23.1 5.6 29.8s11.7 8.8 20.5 8.8c13.4 0 30.7-7 46.3-18.6 13.3-9.9 22.8-21.3 26.5-31.7M230.2 2c-3.1 22.8-43.8 52.8-70.3 52.8-16.8 0-27.9-11.9-20.2-45.1a21.7 21.7 0 0 0-8.4 7.1l-7.5 10.6c-.9 29 15.1 39.9 35.4 39.9 34.3 0 81.2-31 81.2-58.3l-10.2-7z" id="Collar_Outline" data-name="Collar Outline" style="fill: rgb(148, 148, 141);"></path>'

        svg_buffer += "</svg>"

        path = path.removeprefix("../")

        try:
            svg2png(bytestring=svg_buffer, write_to=path)
            self.png2png(path, path, size=87)
        except Exception as e:
            mrich.error(e)
            mrich.error("Error generating kit", path)

        # exit()

        # return kit_path

    def scrape_team_kits(self):

        import urllib

        url = "https://fantasy.premierleague.com/dist/img/shirts/standard/"

        # not_found = [5,9,10,12,15,16,18,19,22]

        count = 0
        i = 1
        i = 89
        while True:
            print(i, count)
            try:
                urllib.request.urlretrieve(
                    f"{url}shirt_{i+1}-66.webp", f"kits/{i}.webp"
                )
                i += 1
                count += 1
            except urllib.error.HTTPError:
                i += 1
                if i > 200:
                    break
                continue

            # if count == 19:
            # break

        return

        for i, name in self._scrape_team_pairs:
            try:
                urllib.request.urlretrieve(
                    f"{url}shirt_{i+1}-66.webp", f"kits/{i}.webp"
                )
                self.webp2png(f"kits/{i}.webp", f"kits/{name}.png")
                urllib.request.urlretrieve(
                    f"{url}shirt_{i+1}_1-66.webp", f"kits/{i}_gkp.webp"
                )
                self.webp2png(f"kits/{i}_gkp.webp", f"kits/{name}_gkp.png")
            except urllib.error.HTTPError:
                # print(i+1,name)
                mout.errorOut(f"Problem accessing {url}shirt_{i+1}-66.webp")

        # print(f"{url}shirt_{i+1}-66.webp", f"kits/{i}.webp")

        # from glob import glob

        # files = glob("kits/*.webp")

        # for webp in files:
        # 	self.webp2png(webp,webp.replace(".webp",".png"))
        # 	# self.webp2jpg(webp,webp.replace(".webp",".jpg"))

    def png2png(self, path, new, size=87):
        from PIL import Image

        # im = Image.open(path).convert("RGB")
        im = Image.open(path)
        im.thumbnail((size, size))
        # im.thumbnail((size,size), Image.ANTIALIAS)
        im.save(new, "png")

    def webp2png(self, path, new, size=87):
        from PIL import Image

        # im = Image.open(path).convert("RGB")
        im = (
            Image.open(path)
            .convert("RGBA")
            .convert("P", palette=Image.ADAPTIVE, colors=255)
        )
        im.thumbnail((size, size), Image.ANTIALIAS)
        im.save(new, "png")

    def webp2jpg(self, path, new):
        from PIL import Image

        im = Image.open(path).convert("RGB")
        im.save(new, "jpeg")

    def get_league_stats(self, code):

        # standings?page_standings=2
        json2 = None
        json3 = None

        # # print(f"{url}leagues-classic/{code}/standings/")
        # r = requests.get(f"{url}leagues-classic/{code}/standings/")
        # self._request_log.append(f"{url}leagues-classic/{code}/standings/")
        # json = r.json()

        json = self.request(f"{url}leagues-classic/{code}/standings/")

        # print(f"{url}leagues-classic/{code}/standings/")

        # print(json.keys())

        if json["standings"]["has_next"]:
            # print(f'{json["standings"]["page"]=}')
            # # print(f"{url}leagues-classic/{code}/standings/?page_standings=2")
            # r = requests.get(f"{url}leagues-classic/{code}/standings/?page_standings=2")
            # self._request_log.append(f"{url}leagues-classic/{code}/standings/?page_standings=2")
            # json2 = r.json()

            json2 = self.request(
                f"{url}leagues-classic/{code}/standings/?page_standings=2"
            )

            if json2["standings"]["has_next"]:
                # print(f'{json2["standings"]["page"]=}')
                json3 = self.request(
                    f"{url}leagues-classic/{code}/standings/?page_standings=3"
                )

        if isinstance(json, str):
            mout.errorOut(json)
            exit(code=1)

        # print(json.keys())

        # df = pd.DataFrame(json['new_entries']['results'])
        df = pd.DataFrame(json["standings"]["results"])

        if json2 is not None:
            df2 = pd.DataFrame(json2["standings"]["results"])
            # print(df.columns,df2.columns)
            df = pd.concat([df, df2])

        if json3 is not None:
            df3 = pd.DataFrame(json3["standings"]["results"])
            # print(df.columns,df2.columns)
            df = pd.concat([df, df3])

        # PRESEASON
        if len(df) == 0:

            df = pd.DataFrame(json["new_entries"]["results"])

            # if self.current_gw < 1:
            # from pprint import pprint
            # # # print(f"{url}leagues-classic/{code}/standings/")
            # # pprint(json)

            # mout.header("json['new_entries']")
            # pprint(json['new_entries'])

            json2 = None
            if json["new_entries"]["has_next"]:
                json2 = self.request(
                    f"{url}leagues-classic/{code}/standings/?page_new_entries=2"
                )

                if json2["new_entries"]["has_next"]:
                    json3 = self.request(
                        f"{url}leagues-classic/{code}/standings/?page_new_entries=3"
                    )

            if json2 is not None:
                df2 = pd.DataFrame(json2["new_entries"]["results"])
                # print(len(df),len(df2))
                df = pd.concat([df, df2])

            if json3 is not None:
                df3 = pd.DataFrame(json3["new_entries"]["results"])
                # print(len(df),len(df3))
                df = pd.concat([df, df3])

        # print(df['player_last_name'].values)

        name = json["league"]["name"]
        # print(name)
        # print(df)

        # print(f'Finished getting stats for {name}')

        return name, df

    def big_number_format(self, number):
        # print(type(number),number)
        if isinstance(number, int):
            if abs(number) < 10000:
                return str(number)
            elif abs(number) < 1000000:
                return f"{int(number/1000):d}k"
            else:
                return f"{number/1000000:.1f}M"
        else:
            return "N/A"
