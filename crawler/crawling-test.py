from unittest import TestCase

from crawling import *


class Test(TestCase):
    def test_post_to_slack(self):
        try:
            post_to_slack("테스트 파일입니다!")
        except AttributeError:
            self.fail()

    def test_get_soup(self):
        market_id = "0000760513"
        back = True
        try:
            print(get_soup(market_id, back))
        except AttributeError:
            self.fail()

    def test_get_one_store_app_download_count(self):
        date = TimeIndex.objects.last()
        app = App.objects.last()
        try:
            get_one_store_app_download_count(date, app)
        except AttributeError:
            self.fail()

    def test_crawl_app_store_rank(self):
        term = "market_rank"
        market = "google"
        price = "free"
        game_or_app = "app"
        try:
            crawl_app_store_rank(term, market, price, game_or_app)
        except ValueError:
            self.fail()

    def test_tracking_rank_flushing(self):
        try:
            tracking_rank_flushing()
        except AttributeError:
            self.fail()

    def test_following_crawl(self):
        try:
            following_one_crawl()
        except AttributeError:
            self.fail()
