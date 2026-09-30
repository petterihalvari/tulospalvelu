import json
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path

ROSTER_DIR = Path("data/rosters")
GAME_DIR = Path("data/games")
PLAYER_DIR = Path("data/players")

# False = vanhat pelaajatiedostot poistetaan ennen uudelleenrakennusta.
# Pelaajadata on johdettua dataa, joten se voidaan aina rakentaa uudelleen.
KEEP_OLD_PLAYER_FILES = False


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def first_value(data, *keys, default=None):
    if not isinstance(data, dict):
        return default
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return default


def normalize_name(value):
    """Normalisoi nimet vain tapahtumien yhdistämistä varten."""
    if not value:
        return ""
    value = unicodedata.normalize("NFKC", str(value))
    value = value.replace(",", " ")
    value = re.sub(r"\s+", " ", value).strip().casefold()
    return value


def player_name(player):
    last_name = str(player.get("LastName") or "").strip()
    first_name = str(player.get("FirstName") or "").strip()
    return " ".join(part for part in (last_name, first_name) if part)


def parse_int(value, default=0):
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        match = re.search(r"-?\d+", str(value))
        return int(match.group()) if match else default


def format_game_time(value):
    """Muuttaa sekunnit muotoon MM:SS. Valmis kellonaika säilytetään."""
    if value in (None, ""):
        return ""
    if isinstance(value, str) and ":" in value:
        return value
    seconds = parse_int(value, default=-1)
    if seconds < 0:
        return str(value)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def get_game_info(game_data, game_id):
    games = game_data.get("GamesUpdate") or []
    game = games[0] if games else {}

    home = game.get("HomeTeam") or {}
    away = game.get("AwayTeam") or {}

    return {
        "game_id": parse_int(first_value(game, "Id", "GameID", default=game_id), game_id),
        "date": first_value(game, "StartDate", "GameDate", "GameDateDB", default=""),
        "season": first_value(game, "Season", default=None),
        "level_id": first_value(game, "LevelID", "LevelId", default=None),
        "level_name": first_value(game, "LevelName", default=""),
        "subserie_id": first_value(game, "SubSerieID", "SubSerieId", default=None),
        "subserie_name": first_value(game, "SubSerieName", default=""),
        "home_team_id": first_value(home, "Id", "TeamID", "TeamId", default=None),
        "home_team": first_value(home, "Name", "TeamName", default="Kotijoukkue"),
        "away_team_id": first_value(away, "Id", "TeamID", "TeamId", default=None),
        "away_team": first_value(away, "Name", "TeamName", default="Vierasjoukkue"),
        "home_goals": first_value(home, "Goals", default=None),
        "away_goals": first_value(away, "Goals", default=None),
    }


def create_player_record(player):
    person_id = player.get("PersonID")
    player_id = player.get("PlayerID")
    key = str(person_id or player_id)

    return key, {
        "person_id": person_id,
        "name": player_name(player),
        "first_name": player.get("FirstName") or "",
        "last_name": player.get("LastName") or "",
        "player_ids": [],
        "link_ids": [],
        "summary": {
            "games": 0,
            "goals": 0,
            "assists": 0,
            "points": 0,
            "penalties": 0,
            "penalty_minutes": 0,
        },
        "appearances": [],
        "events": [],
    }


def ensure_player(players, player):
    person_id = player.get("PersonID")
    player_id = player.get("PlayerID")
    if person_id is None and player_id is None:
        return None

    key = str(person_id or player_id)
    if key not in players:
        _, record = create_player_record(player)
        players[key] = record

    record = players[key]

    if player_id is not None and player_id not in record["player_ids"]:
        record["player_ids"].append(player_id)

    link_id = player.get("LinkID")
    if link_id and link_id not in record["link_ids"]:
        record["link_ids"].append(link_id)

    if not record["name"]:
        record["name"] = player_name(player)
        record["first_name"] = player.get("FirstName") or ""
        record["last_name"] = player.get("LastName") or ""

    return key


def event_base(game_info, team_id, team_name, event, raw_event_index):
    period = first_value(event, "Period", "PeriodNumber", "GamePeriod", default=None)
    raw_time = first_value(
        event,
        "GameTime",
        "EventTime",
        "Time",
        "GameTimeSeconds",
        default="",
    )

    return {
        "game_id": game_info["game_id"],
        "date": game_info["date"],
        "season": game_info["season"],
        "level_id": game_info["level_id"],
        "series": game_info["level_name"],
        "subserie_id": game_info["subserie_id"],
        "subserie": game_info["subserie_name"],
        "team_id": team_id,
        "team": team_name,
        "opponent": (
            game_info["away_team"]
            if team_id == game_info["home_team_id"]
            else game_info["home_team"]
        ),
        "game_label": f'{game_info["home_team"]} - {game_info["away_team"]}',
        "period": period,
        "game_time": format_game_time(raw_time),
        "raw_event_index": raw_event_index,
    }


def resolve_team(game_info, raw_team_id, fallback_team_id=None, fallback_team_name=""):
    team_id = raw_team_id if raw_team_id not in (None, "") else fallback_team_id
    if team_id == game_info["home_team_id"]:
        return team_id, game_info["home_team"]
    if team_id == game_info["away_team_id"]:
        return team_id, game_info["away_team"]
    return team_id, fallback_team_name


def add_event(record, event):
    record["events"].append(event)

    event_type = event["event_type"]
    role = event.get("role")

    if event_type == "goal" and role == "scorer":
        record["summary"]["goals"] += 1
    elif event_type == "assist":
        record["summary"]["assists"] += 1
    elif event_type == "penalty":
        record["summary"]["penalties"] += 1
        record["summary"]["penalty_minutes"] += event.get("penalty_minutes", 0)


def build_roster_maps(players, roster_data, game_info):
    """Lisää kokoonpanoesiintymiset ja palauttaa tapahtumien yhdistämiskartat."""
    by_link_id = {}
    by_player_id = {}
    by_name_and_team = defaultdict(list)
    by_name = defaultdict(list)

    roster_sets = (
        (
            "home",
            roster_data.get("HomeTeamGameRoster", {}).get("Players", []),
            game_info["home_team_id"],
            game_info["home_team"],
            game_info["away_team_id"],
            game_info["away_team"],
        ),
        (
            "away",
            roster_data.get("AwayTeamGameRoster", {}).get("Players", []),
            game_info["away_team_id"],
            game_info["away_team"],
            game_info["home_team_id"],
            game_info["home_team"],
        ),
    )

    for home_away, roster_players, team_id, team_name, opponent_id, opponent_name in roster_sets:
        for player in roster_players:
            key = ensure_player(players, player)
            if not key:
                continue

            record = players[key]
            appearance = {
                "game_id": game_info["game_id"],
                "date": game_info["date"],
                "season": game_info["season"],
                "level_id": game_info["level_id"],
                "series": game_info["level_name"],
                "subserie_id": game_info["subserie_id"],
                "subserie": game_info["subserie_name"],
                "team_id": team_id,
                "team": team_name,
                "opponent_id": opponent_id,
                "opponent": opponent_name,
                "home_away": home_away,
                "jersey_number": player.get("JerseyNr") or "",
                "role": player.get("RoleName") or "",
                "role_abbrv": player.get("RoleAbbrv") or "",
                "captain": player.get("Captain") or "",
            }
            record["appearances"].append(appearance)
            record["summary"]["games"] += 1

            link_id = player.get("LinkID")
            player_id = player.get("PlayerID")
            normalized = normalize_name(player_name(player))

            if link_id:
                by_link_id[str(link_id)] = key
            if player_id is not None:
                by_player_id[str(player_id)] = key
            if normalized:
                by_name_and_team[(normalized, str(team_id))].append(key)
                by_name[normalized].append(key)

    return {
        "by_link_id": by_link_id,
        "by_player_id": by_player_id,
        "by_name_and_team": by_name_and_team,
        "by_name": by_name,
    }


def resolve_player_key(maps, name, team_id, link_id=None, player_id=None):
    if link_id and str(link_id) in maps["by_link_id"]:
        return maps["by_link_id"][str(link_id)]

    if player_id is not None and str(player_id) in maps["by_player_id"]:
        return maps["by_player_id"][str(player_id)]

    normalized = normalize_name(name)
    if not normalized:
        return None

    team_matches = maps["by_name_and_team"].get((normalized, str(team_id)), [])
    if len(team_matches) == 1:
        return team_matches[0]

    name_matches = list(dict.fromkeys(maps["by_name"].get(normalized, [])))
    if len(name_matches) == 1:
        return name_matches[0]

    return None


def participant_specs(event):
    """Palauttaa tapahtuman pelaajaroolit. Kenttänimiä on mukana useita versioita."""
    event_type = str(first_value(event, "Type", "EventType", default="")).casefold()

    if event_type == "goal" or "goal" in event_type or "maali" in event_type:
        return [
            {
                "event_type": "goal",
                "event_label": "Maali",
                "role": "scorer",
                "role_label": "Maalintekijä",
                "name": first_value(event, "ScorerName", "GoalScorerName", default=""),
                "link_id": first_value(event, "ScorerLinkID", "ScorerLinkId", default=None),
                "player_id": first_value(event, "ScorerPlayerID", "ScorerPlayerId", default=None),
            },
            {
                "event_type": "assist",
                "event_label": "Syöttö",
                "role": "first_assist",
                "role_label": "1. syöttäjä",
                "name": first_value(event, "FirstAssistName", "Ass1Name", default=""),
                "link_id": first_value(event, "Ass1LinkID", "FirstAssistLinkID", default=None),
                "player_id": first_value(event, "Ass1PlayerID", "FirstAssistPlayerID", default=None),
            },
            {
                "event_type": "assist",
                "event_label": "Syöttö",
                "role": "second_assist",
                "role_label": "2. syöttäjä",
                "name": first_value(event, "SecondAssistName", "Ass2Name", default=""),
                "link_id": first_value(event, "Ass2LinkID", "SecondAssistLinkID", default=None),
                "player_id": first_value(event, "Ass2PlayerID", "SecondAssistPlayerID", default=None),
            },
        ]

    if event_type == "penalty" or "penalty" in event_type or "rangaistus" in event_type:
        return [
            {
                "event_type": "penalty",
                "event_label": "Rangaistus",
                "role": "penalized_player",
                "role_label": "Rangaistu pelaaja",
                "name": first_value(event, "Name", "PlayerName", "PenaltyPlayerName", default=""),
                "link_id": first_value(event, "PlayerLinkID", "PenaltyPlayerLinkID", default=None),
                "player_id": first_value(event, "PlayerID", "PenaltyPlayerID", default=None),
            }
        ]

    return []


def process_game_events(players, maps, game_data, game_info, unmatched_events):
    events = game_data.get("GameLogsUpdate") or []

    for raw_index, raw_event in enumerate(events):
        raw_team_id = first_value(raw_event, "TeamId", "TeamID", "Team", default=None)
        team_id, team_name = resolve_team(game_info, raw_team_id)

        for spec in participant_specs(raw_event):
            if not spec["name"]:
                continue

            key = resolve_player_key(
                maps,
                spec["name"],
                team_id,
                link_id=spec["link_id"],
                player_id=spec["player_id"],
            )

            if not key:
                unmatched_events.append(
                    {
                        "game_id": game_info["game_id"],
                        "team_id": team_id,
                        "player_name": spec["name"],
                        "event_type": spec["event_type"],
                        "raw_event_index": raw_index,
                    }
                )
                continue

            event = event_base(game_info, team_id, team_name, raw_event, raw_index)
            event.update(
                {
                    "event_type": spec["event_type"],
                    "event_label": spec["event_label"],
                    "role": spec["role"],
                    "role_label": spec["role_label"],
                    "score": first_value(
                        raw_event,
                        "Score",
                        "GameScore",
                        "ScoreAfter",
                        default="",
                    ),
                    "penalty_minutes": 0,
                    "penalty_reason": "",
                }
            )

            if spec["event_type"] == "penalty":
                event["penalty_minutes"] = parse_int(
                    first_value(
                        raw_event,
                        "PenaltyMinutes",
                        "PenaltyMinute",
                        "Minutes",
                        "PenaltyTime",
                        default=0,
                    )
                )
                event["penalty_reason"] = first_value(
                    raw_event,
                    "PenaltyReasonsFI",
                    "Reason",
                    "PenaltyName",
                    "Cause",
                    default="",
                )

            add_event(players[key], event)


def finalize_players(players):
    for record in players.values():
        record["summary"]["points"] = (
            record["summary"]["goals"] + record["summary"]["assists"]
        )
        record["player_ids"] = sorted(record["player_ids"], key=str)
        record["link_ids"] = sorted(record["link_ids"], key=str)
        record["appearances"].sort(
            key=lambda row: (row.get("date", ""), row.get("game_id", 0))
        )
        record["events"].sort(
            key=lambda row: (
                row.get("date", ""),
                row.get("game_id", 0),
                row.get("period") or 0,
                row.get("game_time", ""),
                row.get("raw_event_index", 0),
            )
        )


def main():
    if not ROSTER_DIR.exists():
        raise FileNotFoundError(f"Kokoonpanokansiota ei löytynyt: {ROSTER_DIR}")

    PLAYER_DIR.mkdir(parents=True, exist_ok=True)
    if not KEEP_OLD_PLAYER_FILES:
        for old_file in PLAYER_DIR.glob("*.json"):
            old_file.unlink()

    players = {}
    unmatched_events = []
    processed_games = 0
    skipped_games = []

    for roster_file in sorted(ROSTER_DIR.glob("*.json")):
        game_id = parse_int(roster_file.stem, default=0)
        game_file = GAME_DIR / roster_file.name

        if not game_file.exists():
            skipped_games.append({"game_id": game_id, "reason": "peliraportti puuttuu"})
            continue

        try:
            roster_data = load_json(roster_file)
            game_data = load_json(game_file)
            game_info = get_game_info(game_data, game_id)

            # Joissakin raporteissa Season ei ole GamesUpdate-osiossa.
            if game_info["season"] is None:
                game_info["season"] = first_value(roster_data, "Season", default=None)

            maps = build_roster_maps(players, roster_data, game_info)
            process_game_events(players, maps, game_data, game_info, unmatched_events)
            processed_games += 1

        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            skipped_games.append({"game_id": game_id, "reason": str(error)})

    finalize_players(players)

    for key, record in players.items():
        save_json(PLAYER_DIR / f"{key}.json", record)

    save_json(
        PLAYER_DIR / "_build_report.json",
        {
            "processed_games": processed_games,
            "players": len(players),
            "unmatched_event_count": len(unmatched_events),
            "unmatched_events": unmatched_events,
            "skipped_games": skipped_games,
        },
    )

    print(f"Käsiteltyjä otteluita: {processed_games}")
    print(f"Pelaajia: {len(players)}")
    print(f"Yhdistämättömiä tapahtumia: {len(unmatched_events)}")
    print(f"Ohitettuja otteluita: {len(skipped_games)}")
    print(f"Pelaajatiedostot: {PLAYER_DIR}")
    print(f"Raportti: {PLAYER_DIR / '_build_report.json'}")


if __name__ == "__main__":
    main()
