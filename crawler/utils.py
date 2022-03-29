import requests
from bs4 import BeautifulSoup


def post_to_slack(text=None, URL=""):
    requests.post(URL, headers={'Content-Type': 'application/json'}, data=f'{"text": "{text}"}')


def get_date(date_string: str) -> int:
    url = "http://13.125.164.253/cron/new/date"
    url = "http://127.0.0.1:8000/cron/new/date"
    res = requests.post(url, data={"date": date_string})
    return res.json()["id"]


def get_soup(market_id, back=True):
    one_url = "https://m.onestore.co.kr/mobilepoc/"
    if back:
        one_url += f"web/apps/appsDetail/spec.omp?prodId={market_id}"
    else:
        one_url += f"apps/appsDetail.omp?prodId={market_id}"
    response = requests.get(one_url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")


def create_app(app_data: dict) -> dict:
    url = "http://13.125.164.253/cron/new/app"
    url = "http://127.0.0.1:8000/cron/new/app"
    res = requests.post(url, data=app_data)
    return res.json()
