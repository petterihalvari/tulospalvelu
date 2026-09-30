import json
from pathlib import Path

SCHEDULE_DIR = Path("data/schedules")
OUTPUT_DIR = Path("output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_schedule_html(data):

    level = data[0]

    title = level["LevelName"]

    games = level.get("Games", [])

    if games:
        subserie = games[0].get("SubSerieName", "")
    else:
        subserie = ""

    html = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">
<title>{title}</title>

<style>
body {{
    font-family: Arial, sans-serif;
    margin: 20px;
}}

h1 {{
    margin-bottom: 20px;
}}

table {{
    border-collapse: collapse;
    width: 100%;
}}

th, td {{
    border-bottom: 1px solid #ddd;
    padding: 8px;
}}

th {{
    background: #f5f5f5;
    text-align: left;
}}

.result {{
    font-weight: bold;
    text-align: center;
}}

.finished {{
    color: #000;
}}

.future {{
    color: #888;
}}

</style>
</head>
<body>

<h1>{title}</h1>
<p class="subserie">{subserie}</p>

<table>
<thead>
<tr>
    <th>Päivä</th>
    <th>Kotijoukkue</th>
    <th>Tulos</th>
    <th>Vierasjoukkue</th>
</tr>
</thead>

<tbody>
"""

    for game in level["Games"]:

        if game["GameStatus"] == 2:
            result = f'{game["HomeGoals"]} - {game["AwayGoals"]}'
            css_class = "finished"
        else:
            result = "-"
            css_class = "future"



        html += f"""
        <tr onclick="window.location='games/{game['GameID']}.html'"
        style="cursor:pointer">
            
            <td>{game["GameDate"]}</td>
            <td>{game["HomeTeamAbbrv"]}</td>
            <td class="result">{result}</td>
            <td>{game["AwayTeamAbbrv"]}</td>
            
        </tr>
        """
    html +=f"""


    </tbody>
    </table>

    </body>
    </html>
    """

    return html


index_links = []

for schedule_file in SCHEDULE_DIR.glob("*.json"):

    with open(schedule_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    level = data[0]

    title = level["LevelName"]
    subserie = level["Games"][0]["SubSerieName"]

    output_file = OUTPUT_DIR / f"{schedule_file.stem}.html"

    html = build_schedule_html(data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    index_links.append(
        f'''
        <a class="series-card" href="{output_file.name}">
            <div class="series-name">{title}</div>
            <div class="subserie-name">{subserie}</div>
        </a>
        '''
    )

    print(f"Luotu: {output_file}")


# etusivu

index_html = f"""
<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="utf-8">
<title>Jääkiekkosarjat</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin: 20px;
}}

h1 {{
    margin-bottom: 5px;
}}

.intro {{
    color: #666;
    margin-bottom: 25px;
}}

.series-grid {{
    display: grid;
    grid-template-columns: repeat(
        auto-fill,
        minmax(280px, 1fr)
    );
    gap: 16px;
    max-width: 1200px;
}}

.series-card {{
    display: block;
    padding: 18px;
    background: #f5f5f5;
    border-radius: 7px;
    text-decoration: none;
    color: #000;
}}

.series-card:hover {{
    background: #eaeaea;
}}

.series-name {{
    font-size: 1.2em;
    font-weight: bold;
    margin-bottom: 6px;
}}

.subserie-name {{
    color: #555;
    font-size: 0.95em;
}}

</style>
</head>

<body>

<h1>Sarjat</h1>

<p class="intro">
Valitse sarja nähdäksesi ottelut ja kokoonpanot.
</p>

<div class="series-grid">
{''.join(index_links)}
</div>

</body>
</html>
"""

with open(
    OUTPUT_DIR / "index.html",
    "w",
    encoding="utf-8"
) as f:
    f.write(index_html)

print("Valmis")