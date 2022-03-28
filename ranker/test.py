import requests


def test_get_rank():
    url = "https://www.google.com/"
    response = requests.get(url)
    assert response.status_code == 200
    print(response.text)


if __name__ == '__main__':
    test_get_rank()
