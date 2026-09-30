import json
from pathlib import Path

PLAYER_DATA_DIR = Path("data/players")
OUTPUT_DIR = Path("output/players")

SUBSERIE_COLORS = {
    1925: "#4e79a7",
    5182: "#f28e2b",
    3587: "#59a14f",
    1476: "#e15759",
    3289: "#76b7b2",
    1512: "#edc948",
    4906: "#b07aa1",
    1513: "#ff9da7",
    3959: "#9c755f",
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for player_file in PLAYER_DATA_DIR.glob("*.json"):

    if player_file.name.startswith("_"):
        continue

    with open(player_file, encoding="utf-8") as f:
        data = json.load(f)

    summary = data["summary"]

    # Pelatut ottelut sarjoittain ja lohkoittain
    games_by_subserie = {}

    for appearance in data.get("appearances", []):
        series = appearance.get("series", "").strip()
        subserie = appearance.get("subserie", "").strip()
        game_id = appearance.get("game_id")

        key = (series, subserie)

        if key not in games_by_subserie:
            games_by_subserie[key] = set()

        if game_id:
            games_by_subserie[key].add(game_id)


    series_cards = ""

    for (series, subserie), game_ids in sorted(games_by_subserie.items()):

        # Estetään turha tuplaus, jos subserie sisältää jo sarjan nimen
        if subserie and series and subserie.startswith(series):
            label = subserie
        elif subserie:
            label = f"{series} – {subserie}"
        else:
            label = series

        series_cards += f"""
        <div class="card">
            {label}<br>
            <b>{len(game_ids)} peliä</b>
        </div>
        """

    html = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">

<title>{data["name"]}</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin: 20px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th, td {{
    padding: 6px;
    border-bottom: 1px solid #ddd;
}}

th {{
    background: #f3f3f3;
    text-align: left;
}}

.summary {{
    display: flex;
    gap: 25px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}

.card {{
    background: #f5f5f5;
    padding: 12px;
    border-radius: 5px;
    min-width: 120px;
}}

.card b {{
    font-size: 1.4em;
}}

a {{
    color: #0066cc;
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

.series-color-cell {{
    width: 20px;
    text-align: center;
}}

.series-dot {{
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
}}

</style>

</head>
<body>

<h1>{data["name"]}</h1>

<p>
PersonID: {data["person_id"]}
</p>

<div class="summary">

<div class="card">
Ottelut<br>
<b>{summary["games"]}</b>
</div>

<div class="card">
Maalit<br>
<b>{summary["goals"]}</b>
</div>

<div class="card">
Syötöt<br>
<b>{summary["assists"]}</b>
</div>

<div class="card">
Pisteet<br>
<b>{summary["points"]}</b>
</div>

<div class="card">
Jäähyt<br>
<b>{summary["penalties"]}</b>
</div>

<div class="card">
Jäähyminuutit<br>
<b>{summary["penalty_minutes"]}</b>
</div>



</div>

<h2>Sarjat</h2>

<div class="summary">
{series_cards}
</div>

<h2>Tapahtumat</h2>

<table>

<tr>
    <th></th>
    <th>Sarja</th>
    <th>Päivä</th>
    <th>Ottelu</th>
    <th>Tapahtuma</th>
    <th>Aika</th>
    <th>Lisätieto</th>
</tr>
"""

    for event in data["events"]:

        event_text = event["event_label"]
        extra = ""

        if event["event_type"] == "penalty":

            reason = event.get("penalty_reason", "").strip()

            if reason:
                event_text = f"R - {reason}"
            else:
                event_text = "R"

            extra = f'{event.get("penalty_minutes", 0)} min'
            # Sarjan väri
        subserie_id = event.get("subserie_id")

        series_color = SUBSERIE_COLORS.get(
            subserie_id,
            "#999999"
        )

        html += f"""
<tr>
        <td class="series-color-cell">
        <span
            class="series-dot"
            style="background-color: {series_color};">
        </span>
    </td>

    <td>
    {event["series"]}<br>
    <small>{event.get("subserie", "")}</small>
    </td>

    <td>{event["date"]}</td>

    <td>

            {event["game_label"]}
        </a>
    </td>

    <td>{event_text}</td>

    <td>{event["game_time"]}</td>

    <td>{extra}</td>

</tr>
"""

    html += """
</table>

</body>
</html>
"""

    outfile = OUTPUT_DIR / f"{player_file.stem}.html"

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Luotu {outfile}")

print("Valmis")