import mout
from manager import Manager
import pandas as pd
from tqdm import tqdm
import mrich


class League:

    def __init__(self, code, api, extra=None):
        self._code = int(code)
        self._name = None
        self._api = api
        self._managers = []
        self._extra_managers = extra
        self._icon = None
        self.get_stats()
        self._average_event_points = None
        self._graph_paths = []
        self._active_managers = None
        self._normal_transfers_managers = None
        self._all_players = None
        self._last_gw_position_dict = None
        self._position_change_dict = None
        self._skip_awards = []

    def get_stats(self):
        # mout.debug(f'{self.name}.get_stats()')
        name, manager_df = self._api.get_league_stats(self._code)

        if self._api._current_gw < 2:
            # manager_df = manager_df.drop(columns=['entry', 'entry_name', 'player_first_name', 'player_last_name'])
            pass
        else:
            # print(manager_df)
            manager_df = manager_df.drop(
                columns=["id", "event_total", "rank_sort", "total"]
            )

        # print(manager_df)
        # print(len(manager_df))

        if self._extra_managers is not None:
            data = []
            for d in self._extra_managers:
                if "player_name" in manager_df.keys():
                    data.append([d[1] + " " + d[2], d[0], d[3]])
                else:
                    data.append([d[1], d[2], d[0], d[3]])

            # print(manager_df.keys())
            # print(data)

            new_df = pd.DataFrame(data, columns=manager_df.keys())

            # manager_df = manager_df.append(new_df, ignore_index=True, verify_integrity=False, sort=False)
            manager_df = pd.concat(
                [manager_df, new_df],
                ignore_index=True,
                verify_integrity=False,
                sort=False,
            )

        self._name = name

        if len(manager_df) == 0:
            mout.errorOut("League stats dataframe is empty!")
            return

        mout.debugOut(f"League({self.name})::get_stats()::ManagerInits")
        mout.hideDebug()

        maximum = len(manager_df)

        if "rank" not in manager_df.keys():
            manager_df["rank"] = [None] * len(manager_df)
        if "last_rank" not in manager_df.keys():
            manager_df["last_rank"] = [None] * len(manager_df)

        count = 0
        if "player_name" in manager_df.keys():
            for c, n, t, rank, last_rank in zip(
                manager_df["entry"],
                manager_df["player_name"],
                manager_df["entry_name"],
                manager_df["rank"],
                manager_df["last_rank"],
            ):

                if last_rank == 0 or rank == 0:
                    mrich.warning(n, "has invalid current/last league rank")
                    continue

                mout.progress(count, maximum)

                m = self._api.get_manager(f"{n}", c, t, authenticate=False)
                # m = Manager(f"{n}",c,self._api,team_name=t)
                if m.valid:
                    self._managers.append(m)
                else:
                    mout.warningOut(
                        f"Skipping invalid manager '{m.name}' with ID: {m.id}"
                    )

                m._league_positions[self.id] = dict(rank=rank, last_rank=last_rank)

                # print(f'adding {m} [1]')
                count += 1

        else:

            for c, f, l, t, rank, last_rank in zip(
                manager_df["entry"],
                manager_df["player_first_name"],
                manager_df["player_last_name"],
                manager_df["entry_name"],
                manager_df["rank"],
                manager_df["last_rank"],
            ):
                mout.progress(count, maximum)

                m = self._api.get_manager(f"{f} {l}", c, t, authenticate=False)
                # m = Manager(f"{f} {l}",c,self._api,team_name=t)

                m._league_positions[self.id] = dict(rank=rank, last_rank=last_rank)

                if m.valid:
                    self._managers.append(m)
                else:
                    mout.warningOut(
                        f"Skipping invalid manager '{m.name}' with ID: {m.id}"
                    )

                # print(f'adding {m} [2]')
                count += 1
        mout.progress(maximum, maximum)
        mout.showDebug()

        for m in self._managers:
            m.assign_league(self)

        # print(self.managers)

    # def get_manager(self,id):
    # 	[m for m in self.managers if m.id == int(id)][0]

    @property
    def managers(self):
        return self._managers

    @property
    def active_managers(self):
        if self._active_managers is None:
            self._active_managers = [
                m
                for m in self.managers
                if not m.is_dead and not m.id in self._skip_awards
            ]
        return self._active_managers

    @property
    def normal_transfers_managers(self):
        if self._normal_transfers_managers is None:
            self._normal_transfers_managers = [
                m
                for m in self.active_managers
                if self._api._current_gw
                not in [m._bb1_week, m._bb2_week, m._fh1_week, m._fh2_week]
            ]
        return self._normal_transfers_managers

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return self.name

    @property
    def num_managers(self):
        return len(self.managers)

    @property
    def all_players(self):
        if self._all_players is None:
            self._all_players = []
            for m in self.managers:
                self._all_players += m.squad.players
        return self._all_players

    @property
    def goalkeepers(self):
        return [p for p in self.all_players if p.position_id == 1]

    @property
    def defenders(self):
        return [p for p in self.all_players if p.position_id == 2]

    @property
    def midfielders(self):
        return [p for p in self.all_players if p.position_id == 3]

    @property
    def forwards(self):
        return [p for p in self.all_players if p.position_id == 4]

    @property
    def captains(self):
        return [p for p in self.all_players if p.multiplier > 1]

    @property
    def starting_goalkeepers(self):
        return [p for p in self.all_players if p.position_id == 1 and p.multiplier > 0]

    @property
    def starting_defenders(self):
        return [p for p in self.all_players if p.position_id == 2 and p.multiplier > 0]

    @property
    def starting_midfielders(self):
        return [p for p in self.all_players if p.position_id == 3 and p.multiplier > 0]

    @property
    def starting_forwards(self):
        return [p for p in self.all_players if p.position_id == 4 and p.multiplier > 0]

    def get_starting_players(self, unique=False, active_only=True):
        lst = []
        if active_only:
            for m in self.active_managers:
                lst += m.squad.starting_players
        else:
            for m in self.managers:
                lst += m.squad.starting_players

        new_set = []
        ids = []
        for p in lst:
            if p.id not in ids:
                new_set.append(p)
                ids.append(p.id)
                p.league_multiplier_count = p.multiplier
            else:
                p.league_count += 1
                p.league_multiplier_count += p.multiplier
        if unique:
            return new_set
        else:
            return lst

    @property
    def last_gw_position_dict(self) -> dict[int, int]:
        """Returns a dictionary with:

        - key: manager ID
        - value: previous GW position

        """

        if not self._last_gw_position_dict:
            pairs = [(m.id, sum(m._event_points[:-1])) for m in self.managers]
            self._last_gw_position_dict = {
                id: i + 1
                for i, (id, pts) in enumerate(
                    sorted(pairs, key=lambda x: x[1], reverse=True)
                )
            }
        return self._last_gw_position_dict

    @property
    def position_change_dict(self) -> dict[int, int]:
        """Returns a dictionary with:

        - key: manager ID
        - value: change in position since last week

        """

        if not self._position_change_dict:
            pairs = [(m.id, m.total_livescore) for m in self.managers]
            position_dict = {
                id: i + 1
                for i, (id, pts) in enumerate(
                    sorted(pairs, key=lambda x: x[1], reverse=True)
                )
            }
            self._position_change_dict = {
                id: (self.last_gw_position_dict[id] - value)
                for id, value in position_dict.items()
            }
        return self._position_change_dict

    @property
    def id(self):
        return self._code

    @property
    def average_event_points(self):
        if self._average_event_points is None:
            self._average_event_points = []
            for i in range(1, self._api._current_gw + 1):
                this_sum = 0
                this_count = 0
                for man in self.managers:
                    if i in man.active_gws:
                        score = man.get_event_score(i)
                        if score is None:
                            continue
                        this_sum += man.get_event_score(i)
                        this_count += 1
                if this_count > 0:
                    self._average_event_points.append(int(this_sum / this_count))
                else:
                    self._average_event_points.append(0)

        return self._average_event_points

    @property
    def shortname(self):
        return self._shortname

    @property
    def colour_str(self):
        return self._colour_str

    def get_league_transfers(self, gw):

        element_ids_in = []
        element_ids_out = []

        for m in self.managers:

            transfers = m.get_gw_transfers()

            for d in transfers:
                element_ids_in.append(d["element_in"])
                element_ids_out.append(d["element_out"])

        return element_ids_in, element_ids_out

    def create_points_graph(self, plot=True, show=False):
        """

        Plot transfer gain
        Add chips

        """

        if plot:
            mout.debugOut(f"create_points_graph({self.shortname})")

            import matplotlib.pyplot as plt
            from matplotlib.ticker import ScalarFormatter, MaxNLocator

            with plt.style.context("seaborn-white"):

                plt.rcParams["axes.linewidth"] = 2.0
                plt.rcParams["axes.edgecolor"] = "k"

                fig, ax = plt.subplots(figsize=[6, 5])

                #### Rank Axis

                # set up axes
                ax.set_ylabel("Points")
                ax.set_xlabel("Gameweek")
                ax.grid(
                    which="both", axis="both", zorder=-1, color="white", linewidth=2
                )

                avgs = self._api.get_event_averages()

                # plots

                for man in self.managers:
                    ydata = []
                    for i in range(1, self._api._current_gw + 1):
                        ydata.append(man.get_event_score(i))
                    ax.scatter(
                        man.active_gws, ydata, label=man.name, marker="o", zorder=4
                    )

                # averages
                ax.plot(
                    range(1, self._api._current_gw + 1),
                    avgs,
                    linestyle="-",
                    marker=None,
                    color="b",
                    label="Global Average",
                    zorder=3,
                )
                ax.plot(
                    range(1, self._api._current_gw + 1),
                    self.average_event_points,
                    linestyle="--",
                    marker=None,
                    label=f"{self.shortname} Average",
                    zorder=1,
                    color=self.colour_str,
                )

                # hit_cost = [self.get_transfer_cost(w) for w in self.active_gws]
                # hit_yerrs = [[ h for h in hit_cost],[ 0 for h in hit_cost]]
                # ax.errorbar(self.active_gws,self._event_points,yerr=hit_yerrs,label="Transfer Cost",marker='o',color="k",zorder=2,linewidth=0,elinewidth=2,fmt='none',capsize=3,capthick=2)

                # axis ticks
                ax.set_axisbelow(True)
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))

                plt.legend(bbox_to_anchor=(0.5, 1.25), loc="upper center", ncol=3)
                plt.tight_layout(pad=0.5)

                if show:
                    plt.show()

                plt.savefig(f"graphs/{self.shortname}_points.png", dpi=150)

                plt.close()

        self._graph_paths.append(f"graphs/{self.shortname}_points.png")

    def get_cup_matches(self):
        all_matches = []
        mout.debugOut(f"Getting all cup matches in {self.name}...")
        for i, manager in tqdm(enumerate(self.managers)):
            matches = manager.get_cup_matches(self)
            # print(i,manager.name,len(matches))
            all_matches += manager.get_cup_matches(self)
        return all_matches
