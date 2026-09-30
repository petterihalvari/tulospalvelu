import json
from pathlib import Path

ROSTER_DIR = Path("data/rosters")
OUTPUT_DIR = Path("output/games")
GAME_DIR = Path("data/games")
PLAYER_DATA_DIR = Path("data/players")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_player_row(player):

    captain = player.get("Captain", "")

    captain_text = ""
    if captain:
        captain_text = f" ({captain})"

    return f"""
    <tr>
        <td>{player.get("JerseyNr", "")}</td>
        <td>{player.get("LastName", "")} {player.get("FirstName", "")}</td>
        <td>{player.get("RoleAbbrv", "")}{captain_text}</td>
    </tr>
    """

def get_event_count(player):
    person_id = player.get("PersonID")

    if not person_id:
        return 0

    player_file = PLAYER_DATA_DIR / f"{person_id}.json"

    if not player_file.exists():
        return 0

    with open(player_file, "r", encoding="utf-8") as f:
        player_data = json.load(f)

    return len(player_data.get("events", []))

def jersey_sort_key(player):
    jersey = player.get("JerseyNr")

    try:
        return int(jersey)
    except (TypeError, ValueError):
        return 999

for roster_file in ROSTER_DIR.glob("*.json"):

    with open(roster_file, "r", encoding="utf-8") as f:
        data = json.load(f)




    home_players = sorted(
        data["HomeTeamGameRoster"]["Players"],
        key=jersey_sort_key
    )

    away_players = sorted(
        data["AwayTeamGameRoster"]["Players"],
        key=jersey_sort_key
    )

    game_file = GAME_DIR / roster_file.name

    with open(game_file, "r", encoding="utf-8") as f:
        game_data = json.load(f)

    game = game_data["GamesUpdate"][0]

    home_team = game["HomeTeam"]["Name"]
    away_team = game["AwayTeam"]["Name"]

    game_date = (
        game.get("StartDate")
        or game.get("GameDate")
        or game.get("GameDateDB")
        or ""
    )

    html = """
<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">

<style>

body{
    font-family: Arial, sans-serif;
    margin:20px;
}

.container{
    display:flex;
    gap:40px;
}

.team{
    flex:1;
}

table{
    width:100%;
    border-collapse:collapse;
}

th{
    background:#f3f3f3;
    text-align:left;
}

th,td{
    padding:6px;
    border-bottom:1px solid #ddd;
}

.player-link{
    text-decoration:none;
    color:#0066cc;
}

.player-link:hover{
    text-decoration:underline;
}

</style>
</head>
<body>
"""

    html += f"<h1>{home_team} - {away_team}</h1>"
    html += f"<p>{game_date}</p>"

    html += """
<div class="container">
"""

    # kotijoukkue

    html += f"""
    <div class="team">
    <h2>{home_team}</h2>
    

<table>
<tr>
    <th>#</th>
    <th>Pelaaja</th>
    <th>Rooli</th>
    <th>Tapahtumat</th>
</tr>
"""

    for player in home_players:

        player_id = player.get("PlayerID")
        event_count = get_event_count(player)
        captain = player.get("Captain", "")

        captain_text = ""
        if captain:
            captain_text = f" ({captain})"

        html += f"""
<tr>
    <td>{player.get("JerseyNr","")}</td>

<td>
    <a class="player-link"
    href="../players/{player.get('PersonID')}.html">
    {player.get("LastName","")} {player.get("FirstName","")}
    </a>
</td>

    <td>
        {player.get("RoleAbbrv","")}
        {captain_text}
    </td>
    <td>{event_count}</td>

</tr>
"""

    html += """
</table>
</div>
"""

    # vierasjoukkue

    
    html += f"""
<div class="team">
<h2>{away_team}</h2>


<table>
<tr>
    <th>#</th>
    <th>Pelaaja</th>
    <th>Rooli</th>
    <th>Tapahtumat</th>
</tr>
"""

    for player in away_players:

        player_id = player.get("PlayerID")
        event_count = get_event_count(player)
        captain = player.get("Captain", "")
        captain_text = ""
        if captain:
            captain_text = f" ({captain})"

        html += f"""
       
<tr>

    <td>{player.get("JerseyNr","")}</td>

    
<td>
    <a class="player-link"
    href="../players/{player.get('PersonID')}.html">
    {player.get("LastName","")} {player.get("FirstName","")}
    </a>
</td>

    <td>
        {player.get("RoleAbbrv","")}
        {captain_text}
    </td>
    <td>{event_count}</td>

</tr>
"""

    html += """
</table>
</div>
"""

    html += """
</div>
</body>
</html>
"""

    outfile = OUTPUT_DIR / f"{roster_file.stem}.html"

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Luotu {outfile}")

print("Valmis")