import requests

from crawler.models import Ranked


def crawl_app_store_rank(market: int, rank: int, app: int):
    market_type = ["google", "apple", "one"]
    rank_type = ["realtime_rank", "market_rank"]
    app_type = ["game", "app"]
    USER_AGENT = " ".join(
        ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
         "AppleWebKit/537.36 (KHTML, like Gecko)",
         "Chrome/98.0.4758.80 Safari/537.36"])
    url = f'https://proxy-insight.mobileindex.com/chart/{rank_type[rank]}'
    headers = {'origin': 'https://www.mobileindex.com',
               'user-agent': USER_AGENT}
    data = {
        "market": market_type[market],
        "appType": app_type[app],
        "dateType": "d",
        "date": 20220202,
        "startRank": 0,
        "endRank": 200,
    }

    req = requests.post(url, data=data, headers=headers)
    obj = req.json()
    print(obj.items())
    for i in obj["data"]:
        item = Ranked()
        item.rank_type = i.get('rank_type')
        item.rank = i.get('rank')
        item.app_name = i.get('app_name')
        item.publisher_name = i.get('publisher_name')
        item.icon_url = i.get('icon_url')
        item.market_appid = i.get('market_appid')
        item.package_name = i.get('package_name')
        item.save()


if __name__ == '__main__':
    for market in range(0, 3):
        for rank in range(0, 2):
            for app in range(0, 2):
                crawl_app_store_rank(market, rank, app)

