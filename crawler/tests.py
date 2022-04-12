import unittest
from selenium import webdriver


class TestCrawler(unittest.TestCase):
    def setUp(self) -> None:
        self.browser = webdriver.Chrome()

    def tearDown(self) -> None:
        self.browser.quit()

    def test_can_start_without_permission(self):
        self.browser.get('http://127.0.0.1:8000/')
        self.assertIn('Django', self.browser.title)


if __name__ == '__main__':
    unittest.main()
