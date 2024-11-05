def process_matches(api, matches):
    ms = set()
    for m in matches:
        pair = tuple(sorted([m["self"].id, m["opponent"].id]))
        ms.add(pair)
    ms = [(api.get_manager(id=a), api.get_manager(id=b)) for a, b in ms]
    return list(ms)


def bracket_table(final=None, semis=None, quarters=None):

    def quarter(i, flip=False):
        gw = 36
        loser, winner = sorted(quarters[i], key=lambda x: x.get_event_score(gw))
        cell(4, i * 3, winner, True, flip=flip, top=True, left=True, right=True, gw=gw)
        cell(5, i * 3, loser, flip=flip, bottom=True, left=True, right=True, gw=gw)

    def cell(
        y,
        x,
        m,
        winner=False,
        flip=False,
        top=False,
        bottom=False,
        left=False,
        right=False,
        gw=None,
    ):

        # flip = False

        if m is None:
            color = "w3-grey w3-border-black"
        elif winner:
            color = "w3-green w3-border-black"
        else:
            color = "w3-white w3-border-black"

        if flip:
            x1, x2 = x + 1, x
            x1_style = "w3-left-align"
            x2_style = "w3-center"
        else:
            x2, x1 = x + 1, x
            x1_style = "w3-right-align"
            x2_style = "w3-center"

        if top:
            x1_style += " w3-topbar"
            x2_style += " w3-topbar"

        if bottom:
            x1_style += " w3-bottombar"
            x2_style += " w3-bottombar"

        if left and not flip:
            x1_style += " w3-leftbar"
        if right and not flip:
            x2_style += " w3-rightbar"
        if left and flip:
            x2_style += " w3-leftbar"
        if right and flip:
            x1_style += " w3-rightbar"

        row = grid[y]

        if m is None:
            x1_style = x1_style.replace("right-align", "center").replace(
                "left-align", "center"
            )
            x2_style = x2_style.replace("right-align", "center").replace(
                "left-align", "center"
            )
            row[x1] = f'<td class="{color} {x1_style}">?</td>'
            row[x2] = f'<td class="{color} {x2_style}"></td>'
            return

        assert gw is not None
        row[x2] = f'<td class="{color} {x2_style}">{m.get_event_score(gw)}</td>'

        row[x1] = f'<td class="{color} {x1_style}"><a href="{m.gui_url}">{m.name}</a>'
        if m.is_diamond:
            row[x1] += "💎"
        # row[x1] += f'<br><a href="{m.gui_url}">{m.team_name}</a>'
        row[x1] += "</td>\n"

    def get_match(matches, manager):
        for m in matches:
            if manager in m:
                return m
        raise NotImplementedError

    r = 6
    c = 11

    grid = [["" for i in range(c)] for j in range(r)]

    if semis:
        grid[2][
            2
        ] = f'<td class="w3-white w3-topbar w3-bottombar w3-border-black">v</td>'
        grid[2][
            8
        ] = f'<td class="w3-white w3-topbar w3-bottombar w3-border-black">v</td>'

        # the order of the semi's will determine the quarters...
        new_quarters = [None, None, None, None]

        # s1
        loser1, winner1 = sorted(semis[0], key=lambda x: x.get_event_score(37))
        cell(2, 0, loser1, top=True, bottom=True, left=True, gw=37)  # S1-loser 1
        cell(
            2, 3, winner1, winner=True, top=True, bottom=True, right=True, gw=37
        )  # S1-winner 2

        new_quarters[0] = get_match(quarters, loser1)
        new_quarters[1] = get_match(quarters, winner1)

        loser2, winner2 = sorted(semis[1], key=lambda x: x.get_event_score(37))
        cell(
            2,
            6,
            winner2,
            winner=True,
            flip=True,
            top=True,
            bottom=True,
            left=True,
            gw=37,
        )  # S2-winner 3
        cell(
            2, 9, loser2, flip=True, top=True, bottom=True, right=True, gw=37
        )  # S2-loser 4

        new_quarters[2] = get_match(quarters, winner2)
        new_quarters[3] = get_match(quarters, loser2)

        quarters = new_quarters

        grid[3][0] = "|black"
        grid[3][3] = "|black"
        grid[3][6] = "|black"
        grid[3][9] = "|black"

    else:
        grid[2][
            2
        ] = f'<td class="w3-grey w3-topbar w3-bottombar w3-border-black">v</td>'
        grid[2][
            8
        ] = f'<td class="w3-grey w3-topbar w3-bottombar w3-border-black">v</td>'
        cell(2, 0, None, top=True, bottom=True, left=True)  # S1-loser 1
        cell(2, 3, None, top=True, bottom=True, right=True)  # S1-winner 2
        cell(2, 6, None, flip=True, top=True, bottom=True, left=True)  # S2-winner 3
        cell(2, 9, None, flip=True, top=True, bottom=True, right=True)  # S2-loser 4
        grid[3][0] = "|"
        grid[3][3] = "|"
        grid[3][6] = "|"
        grid[3][9] = "|"

    if final:
        grid[0][
            5
        ] = f'<td class="w3-white w3-topbar w3-bottombar w3-border-black">v</td>'
        grid[1][3] = "|black"
        grid[1][6] = "|black"
        cell(
            0,
            3,
            winner1,
            winner=winner1.get_event_score(38) > winner2.get_event_score(38),
            top=True,
            bottom=True,
            left=True,
            gw=38,
        )
        cell(
            0,
            6,
            winner2,
            winner=winner1.get_event_score(38) < winner2.get_event_score(38),
            flip=True,
            top=True,
            bottom=True,
            right=True,
            gw=38,
        )

    else:
        grid[0][
            5
        ] = f'<td class="w3-grey w3-topbar w3-bottombar w3-border-black">v</td>'
        cell(0, 3, None, top=True, bottom=True, left=True)
        cell(0, 6, None, flip=True, top=True, bottom=True, right=True)
        grid[1][3] = "|"
        grid[1][6] = "|"

    for i in range(4):
        quarter(i, flip=i > 1)

    # arrows

    # create the table

    html_buffer = '<div class="w3-col s12 m12 l12">\n'
    html_buffer += '<div class="w3-responsive w3-center">\n'
    html_buffer += '<div class="w3-panel" style="padding:4px;padding-bottom:4px;">\n'
    html_buffer += '<table class="w3-table responsive-text">\n'
    # html_buffer = '<table>\n'

    for i in range(r):
        html_buffer += "<tr>\n"
        for j in range(c):
            contents = f"{grid[i][j]}"
            if contents == "|":
                html_buffer += '<td class="w3-rightbar w3-border-black"></td>\n'
            elif contents == "|black":
                html_buffer += '<td class="w3-rightbar w3-border-black"></td>\n'
            elif contents:
                html_buffer += contents
                # html_buffer += '</td>\n'
            else:
                html_buffer += "<td></td>\n"
        html_buffer += "</tr>\n"
    html_buffer += "</table>\n"

    html_buffer += "</div>\n"
    html_buffer += "</div>\n"
    html_buffer += "</div>\n"

    return html_buffer
