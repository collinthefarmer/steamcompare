import csv
import codecs
import requests
from steam.webapi import WebAPI

API_KEY = ""

STEAM_IDS = [
]


def get_prices(appids):
    resp = requests.get(
        f"https://store.steampowered.com/api/appdetails/?appids={','.join(appids)}&cc=us&filters=price_overview")
    return [
        v["data"]
            .get("price_overview", {})
            .get("final_formatted")
        for v in resp.json().values()
        if v["success"]
           and isinstance(v["data"], dict)
    ]


def get_user_summary(api: WebAPI, steamid: str):
    return api.call(
        "ISteamUser.GetPlayerSummaries",
        steamids=steamid
    )["response"]["players"][0]


def get_owned(api: WebAPI, steamid: str):
    return api.call(
        "IPlayerService.GetOwnedGames",
        steamid=steamid,
        include_appinfo=True,
        include_played_free_games=False,
        appids_filter=[],
        include_free_sub=False
    )["response"]["games"]


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main(writer, api_key, ids):
    api = WebAPI(api_key)

    users = [get_user_summary(api, id_) for id_ in ids]

    user_games = {user["steamid"]: [(g["appid"], g["name"]) for g in get_owned(api, user["steamid"])] for user in users}
    game_set = list(set(g for games in user_games.values() for g in games))
    game_prices = {}
    for game_chunk in chunks(game_set, 100):
        game_prices.update({game[0]: p for game, p in zip(game_chunk, get_prices([str(g[0]) for g in game_chunk]))})

    ownership = [[
        gid,
        [gid in user_games[user["steamid"]] for user in users]
    ] for gid in game_set]

    exportable = [
        [r[0][1], game_prices.get(r[0][0], "???"), *r[1]]
        for r in ownership
    ]

    writer.writerows([
        ["Game Name", "Current Price", *[f"{user['personaname']} ({user.get('realname', 'Mr. Mystery')}) owns" for user in users]]
    ])
    writer.writerows(exportable)


if __name__ == '__main__':
    with codecs.open("owned.csv", "w", "utf-8") as f:
        main(csv.writer(f), API_KEY, STEAM_IDS)
