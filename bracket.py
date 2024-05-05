
def process_matches(matches):
    ms = set()
    for m in matches:
        pair = tuple(sorted([m['self'].id,m['opponent'].id]))
        ms.add(pair)
    ms = [(api.get_manager(id=a), api.get_manager(id=b)) for a,b in ms]
    return list(ms)

def bracket_table(final=None, semis=None, quarters=None):
    
    r = 6
    c = 7
    
    grid = [[' ' for i in range(c)] for j in range(r)]

    grid[0][3] = 'v'
    if final:
        grid[0][2] = final[0]
        grid[0][4] = final[1]
    else:
        grid[0][2] = '?'
        grid[0][4] = '?'
        
    grid[2][1] = 'v'
    grid[2][5] = 'v'
    if semis:
        grid[2][2] = 'S1-winner'
        grid[2][4] = 'S2-winner'
        grid[2][0] = 'S1-loser'
        grid[2][6] = 'S2-loser'
    else:
        grid[2][2] = '?'
        grid[2][4] = '?'
        grid[2][0] = '?'
        grid[2][6] = '?'
        
    def quarter(i):
        loser, winner = sorted(quarters[i], key=lambda x: x.livescore)
        grid[4][i*2] = cell(winner)
        grid[5][i*2] = cell(loser)
        
    def cell(m):
        return f'{m.name} {m.livescore} {m.projected_points:.1f}'
    
    for i in range(4):
        quarter(i)
    
    # arrows
    grid[1][2] = '|'
    grid[1][4] = '|'
    grid[3][0] = '|'
    grid[3][2] = '|'
    grid[3][4] = '|'
    grid[3][6] = '|'

    # create the table
    html_buffer = '<table>\n'
    for i in range(r):
        html_buffer += '<tr>\n'
        for j in range(c):
            html_buffer += '<td>\n'
            html_buffer += f'{grid[i][j]}'
            html_buffer += '</td>\n'
        html_buffer += '</tr>\n'
    html_buffer += '</table>\n'
    return html_buffer