import requests
from bs4 import BeautifulSoup


def ive_korea_internal_api():
    """
    아이브코리아 내부 API를 호출해 앱 정보를 등록한다.
    """
    API_KEY = 'wkoo4ko0g808s0kkossoo4o8ow0kwwg88gw004sg'
    url = f'http://dev.i-screen.kr/channel/rank_ads_list?apikey={API_KEY}'
    req = requests.get(url)
    url = "http://13.125.164.253/cron/new/following"
    url = "http://127.0.0.1:8000/cron/new/following"

    if req.status_code == 200:
        response = req.json()
        for adv_info in response["list"]:
            app = dict(
                market_appid=adv_info.get("ads_package"),
                address=adv_info.get("ads_join_url"),
                appname=adv_info.get("ads_name"),
                os_type=adv_info.get("ads_os_type"),
            )
            requests.post(url, data=app)


def following_one_crawl():
    url = "http://13.125.164.253/v2/follow/list"
    url = "http://127.0.0.1:8000/v2/follow/list"
    res = requests.get(url).json()["items"]
    url = "http://13.125.164.253/cron/new/downloads"
    url = "http://127.0.0.1:8000/cron/new/downloads"
    for obj in res:
        market_id = obj["market_id"]
        requests.post(url, data={"market_id": market_id})


if __name__ == '__main__':
    ive_korea_internal_api()
