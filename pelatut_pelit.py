import requests

url = "https://tulospalvelu.leijonat.fi/helpers/getgames"

params = {
    "dwl": 0,
    "season": 2027,
    "subSerieId": 5182,
    "teamid": 0,
    "districtid": 0,
    "gamedays": 1,
    "dog": "2026-09-12",
    "levelid": -1
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("content-type"))

data = response.json()

print("Otteluita:", len(data))
print(data[0])