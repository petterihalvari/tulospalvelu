import json
import requests
from pathlib import Path

# Seurattavat sarjat
SERIES_URLS = [
    #"alkusarjat"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=3587&teamid=0&districtid=0&gamedays=3&dog=2026-09-12&levelid=-1", #"U15 keltainen"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=5182&teamid=0&districtid=0&gamedays=3&dog=2026-09-26&levelid=-1", #"U15 valkoinen lohko1b"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=1925&teamid=0&districtid=0&gamedays=3&dog=2026-09-12&levelid=-1", #"U15 valkoinen lohkoa1a"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=1476&teamid=0&districtid=0&gamedays=3&dog=2026-09-23&levelid=-1", #"U15 sininen"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=3289&teamid=0&districtid=0&gamedays=3&dog=2026-09-24&levelid=-1", #"U16 suomisarja"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=1512&teamid=0&districtid=0&gamedays=3&dog=2026-09-26&levelid=-1", #"U14 sininen 1a"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=4906&teamid=0&districtid=0&gamedays=3&dog=2026-09-26&levelid=-1", #"U14 sininen 1b"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=1513&teamid=0&districtid=0&gamedays=3&dog=2026-09-26&levelid=-1", #"U14 valkoinen 1a"
    "https://tulospalvelu.leijonat.fi/helpers/getgames?dwl=0&season=2027&subSerieId=3959&teamid=0&districtid=0&gamedays=3&dog=2026-09-26&levelid=-1", #"U14 valkoinen 1b"
    # lisää tänne uusia sarjoja
    # "https://tulospalvelu.leijonat.fi/helpers/getgames?...",
]

OUTPUT_DIR = Path("data/schedules")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROSTER_DIR = Path("data/rosters")
ROSTER_DIR.mkdir(parents=True, exist_ok=True)

def extract_subserie_id(url):
    for part in url.split("&"):
        if part.startswith("subSerieId="):
            return part.split("=")[1]
    return "unknown"


def download_schedule(url):

    subserie_id = extract_subserie_id(url)

    print(f"Haetaan sarja {subserie_id}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    outfile = OUTPUT_DIR / f"{subserie_id}.json"

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Tallennettu: {outfile}")

    return data

GAME_DIR = Path("data/games")
GAME_DIR.mkdir(parents=True, exist_ok=True)

def download_game(game_id, season):

    outfile = GAME_DIR / f"{game_id}.json"

    if outfile.exists():
        return

    url = (
        "https://tulospalvelu.leijonat.fi/"
        f"gamereport/getgamereportdata"
        f"?gameid={game_id}&season={season}"
    )

    print(f"Haetaan peli {game_id}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f,
                 ensure_ascii=False,
                 indent=2)

    print(f"Tallennettu {outfile}")

def download_roster(game_id, season):

    outfile = ROSTER_DIR / f"{game_id}.json"

    if outfile.exists():
        return

    url = (
        "https://tulospalvelu.leijonat.fi/"
        f"game/helpers/getrosters"
        f"?gameid={game_id}&season={season}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(
            response.json(),
            f,
            ensure_ascii=False,
            indent=2
        )

for url in SERIES_URLS:

    try:

        data = download_schedule(url)

        for schedule in data:

            for game in schedule["Games"]:

                # vain pelatut ottelut
                if game["GameStatus"] != 2:
                    continue

                download_game(
                    game["GameID"],
                    game["Season"]
                )

                download_roster(
                    game["GameID"],
                    game["Season"]
                )

    except Exception as e:

        print(f"Virhe: {url}")
        print(e)

print("Valmis")