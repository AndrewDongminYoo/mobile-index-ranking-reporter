from datetime import timedelta

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Min
from django.shortcuts import render
from django.utils import timezone

from crawler.models import TrackingApps, Ranked, OneStoreDL


def index(request: WSGIRequest):
    return render(request, "index.html")


def statistic(request: WSGIRequest, market=None, deal=None, app=None):
    # 전체 차트 (등록 하지 않은 애플리케이션) 무료/유료/매출 순위
    if deal == "market_rank":
        apps = Ranked.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
    elif deal == "realtime_rank":
        apps = Ranked.objects.filter(created_at__gte=timezone.now() - timedelta(hours=1))
    market_app = apps.filter(market=market, deal_type=deal, app_type=app).order_by("created_at")
    return render(request, "statistic.html", {"apps": market_app})


def my_rank(request: WSGIRequest):
    # 등록한 애플리케이션 최근 3일 차트
    apps = TrackingApps.objects.filter(created_at__gte=timezone.now() - timedelta(days=3))
    ratings = apps.values("created_at__date", "app_name", "market", "deal_type", "rank_type").annotate(
        rank=Min("rank")).values("created_at__date", "icon_url", "app_name", "market", "deal_type", "rank_type",
                                 "rank").order_by("-created_at__date")
    return render(request, "my_rank.html", {"apps": ratings})


def ranking(request: WSGIRequest):
    # 랭킹 변동 테이블 (및 분류)
    apps = OneStoreDL.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
    return render(request, "ranking.html", {"apps": apps})


def some_func(request):
    print(request.accepted_types)
    # [<MediaType: text/html>, <MediaType: application/xhtml+xml>,
    # <MediaType: application/xml; q=0.9>, <MediaType: image/avif>, <MediaType: image/webp>,
    # <MediaType: image/apng>, <MediaType: */*; q=0.8>, <MediaType: application/signed-exchange; v=b3; q=0.9>]
    print(request.body)  # b''
    print(request.COOKIES)
    # {'csrftoken': 'P6PiYHAreI9zJuZGbJdMyqwxKR6MMw6mDNIT7sO8ZFqanw2C7BxOrQUdJwF8diGt',
    # 'sessionid': 'qv5v699xcbn86e7y1jx60774mlsjbtdn'}
    print(request.encoding)  # None
    print(request.headers)
    # {'Content-Length': '', 'Content-Type': 'text/plain', 'Host': '127.0.0.1:8000', 'Connection': 'keep-alive',
    # 'Cache-Control': 'max-age=0', 'Sec-Ch-Ua': '" Not A;Brand";v="99", "Chromium";v="98",
    # "Google Chrome";v="98"', 'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': '"Windows"',
    # 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)
    # AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36',
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;
    # q=0.8,application/signed-exchange;v=b3;q=0.9', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-Mode': 'navigate',
    # 'Sec-Fetch-User': '?1', 'Sec-Fetch-Dest': 'document', 'Accept-Encoding': 'gzip, deflate, br',
    # 'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    # 'Cookie': 'csrftoken=P6PiYHAreI9zJuZGbJdMyqwxKR6MMw6mDNIT7sO8ZFqanw2C7BxOrQUdJwF8diGt;
    # sessionid=qv5v699xcbn86e7y1jx60774mlsjbtdn'}
    print(request.scheme)  # http
    print(request.upload_handlers)
    # [<django.core.files.uploadhandler.MemoryFileUploadHandler object at 0x000001B7E7128490>,
    # <django.core.files.uploadhandler.TemporaryFileUploadHandler object at 0x000001B7E7128D60>]
    print(request.environ == request.META)
    # {'ALLUSERSPROFILE': 'C:\\ProgramData', 'APPDATA': 'C:\\Users\\User\\AppData\\Roaming',
    # 'COMMONPROGRAMFILES': 'C:\\Program Files\\Common Files',
    # 'COMMONPROGRAMFILES(X86)': 'C:\\Program Files (x86)\\Common Files',
    # 'COMMONPROGRAMW6432': 'C:\\Program Files\\Common Files',
    # 'COMPUTERNAME': 'LAPTOP-NJ38A8SC', 'COMSPEC': 'C:\\Windows\\system32\\cmd.exe',
    # 'DJANGO_SETTINGS_MODULE': 'ranker.settings', 'DRIVERDATA': 'C:\\Windows\\System32\\Drivers\\DriverData',
    # 'FPS_BROWSER_APP_PROFILE_STRING': 'Internet Explorer',
    # 'FPS_BROWSER_USER_PROFILE_STRING': 'Default', 'HOMEDRIVE': 'C:',
    # 'HOMEPATH': '\\Users\\User', 'IDEA_INITIAL_DIRECTORY': 'C:\\Program Files\\JetBrains\\PyCharm 2021.3.2\\bin',
    # 'LOCALAPPDATA': 'C:\\Users\\User\\AppData\\Local', 'LOGONSERVER': '\\\\LAPTOP-NJ38A8SC',
    # 'NUMBER_OF_PROCESSORS': '8', 'ONEDRIVE': 'C:\\Users\\User\\OneDrive', 'OS': 'Windows_NT',
    # 'PATH': 'C:\\Users\\User\\PycharmProjects\\ranker\\venv\\Scripts;C:\\Windows\\system32;
    # C:\\Windows;C:\\Windows\\System32\\Wbem;C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\;
    # C:\\Windows\\System32\\OpenSSH\\;C:\\Program Files\\Git\\cmd;C:\\Program Files\\Bandizip\\;
    # C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python310\\Scripts\\;
    # C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python310\\;
    # C:\\Users\\User\\AppData\\Local\\Microsoft\\WindowsApps;
    # C:\\Program Files\\JetBrains\\PyCharm 2021.3.2\\bin;
    # C:\\Users\\User\\AppData\\Local\\Programs\\Microsoft VS Code\\bin',
    # 'PATHEXT': '.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC',
    # 'PROCESSOR_ARCHITECTURE': 'AMD64', 'PROCESSOR_IDENTIFIER': 'Intel64 Family 6 Model 140 Stepping 1, GenuineIntel',
    # 'PROCESSOR_LEVEL': '6', 'PROCESSOR_REVISION': '8c01', 'PROGRAMDATA': 'C:\\ProgramData',
    # 'PROGRAMFILES': 'C:\\Program Files', 'PROGRAMFILES(X86)': 'C:\\Program Files (x86)',
    # 'PROGRAMW6432': 'C:\\Program Files', 'PROMPT': '(venv) $P$G',
    # 'PSMODULEPATH': 'C:\\Program Files\\WindowsPowerShell\\Modules;C:\\Windows\\system32\\WindowsPowerShell\\v1.0\\Modules',
    # 'PUBLIC': 'C:\\Users\\Public', 'PYCHARM': 'C:\\Program Files\\JetBrains\\PyCharm 2021.3.2\\bin;',
    # 'PYCHARM_DISPLAY_PORT': '63342', 'PYCHARM_HOSTED': '1', 'PYTHONIOENCODING': 'UTF-8', 'PYTHONPATH':
    # 'C:\\Users\\User\\PycharmProjects\\ranker;
    # C:\\Program Files\\JetBrains\\PyCharm 2021.3.2\\plugins\\python\\helpers\\pycharm_matplotlib_backend;
    # C:\\Program Files\\JetBrains\\PyCharm 2021.3.2\\plugins\\python\\helpers\\pycharm_display',
    # 'PYTHONUNBUFFERED': '1', 'SESSIONNAME': 'Console', 'SYSTEMDRIVE': 'C:',
    # 'SYSTEMROOT': 'C:\\Windows', 'TEMP': 'C:\\Users\\User\\AppData\\Local\\Temp',
    # 'TMP': 'C:\\Users\\User\\AppData\\Local\\Temp', 'USERDOMAIN': 'LAPTOP-NJ38A8SC',
    # 'USERDOMAIN_ROAMINGPROFILE': 'LAPTOP-NJ38A8SC', 'USERNAME': 'User', 'USERPROFILE':
    # 'C:\\Users\\User', 'VIRTUAL_ENV': 'C:\\Users\\User\\PycharmProjects\\ranker\\venv',
    # 'WINDIR': 'C:\\Windows', 'ZES_ENABLE_SYSMAN': '1', '_OLD_VIRTUAL_PATH':
    # 'C:\\Windows\\system32;C:\\Windows;C:\\Windows\\System32\\Wbem;C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\;
    # C:\\Windows\\System32\\OpenSSH\\;C:\\Program Files\\Git\\cmd;C:\\Program Files\\Bandizip\\;
    # C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python310\\Scripts\\;
    # C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python310\\;
    # C:\\Users\\User\\AppData\\Local\\Microsoft\\WindowsApps;;
    # C:\\Program Files\\JetBrains\\PyCharm 2021.3.2\\bin;;
    # C:\\Users\\User\\AppData\\Local\\Programs\\Microsoft VS Code\\bin',
    # '_OLD_VIRTUAL_PROMPT': '$P$G', 'RUN_MAIN': 'true', 'SERVER_NAME': 'LAPTOP-NJ38A8SC',
    # 'GATEWAY_INTERFACE': 'CGI/1.1', 'SERVER_PORT': '8000', 'REMOTE_HOST': '',
    # 'CONTENT_LENGTH': '', 'SCRIPT_NAME': '', 'SERVER_PROTOCOL': 'HTTP/1.1',
    # 'SERVER_SOFTWARE': 'WSGIServer/0.2', 'REQUEST_METHOD': 'GET', 'PATH_INFO': '/statistic/google/realtime_rank/app',
    # 'QUERY_STRING': '', 'REMOTE_ADDR': '127.0.0.1', 'CONTENT_TYPE': 'text/plain', 'HTTP_HOST': '127.0.0.1:8000',
    # 'HTTP_CONNECTION': 'keep-alive', 'HTTP_SEC_CH_UA': '" Not A;Brand";v="99", "Chromium";v="98",
    # "Google Chrome";v="98"', 'HTTP_SEC_CH_UA_MOBILE': '?0', 'HTTP_SEC_CH_UA_PLATFORM': '"Windows"',
    # 'HTTP_UPGRADE_INSECURE_REQUESTS': '1', 'HTTP_USER_AGENT':
    # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)
    # AppleWebKit/537.36 (KHTML, like Gecko)
    # Chrome/98.0.4758.82 Safari/537.36',
    # 'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;
    # q=0.8,application/signed-exchange;v=b3;q=0.9',
    # 'HTTP_SEC_FETCH_SITE': 'none', 'HTTP_SEC_FETCH_MODE': 'navigate', 'HTTP_SEC_FETCH_USER': '?1',
    # 'HTTP_SEC_FETCH_DEST': 'document', 'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br',
    # 'HTTP_ACCEPT_LANGUAGE': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7', 'HTTP_COOKIE':
    # 'csrftoken=P6PiYHAreI9zJuZGbJdMyqwxKR6MMw6mDNIT7sO8ZFqanw2C7BxOrQUdJwF8diGt;
    # sessionid=qv5v699xcbn86e7y1jx60774mlsjbtdn', 'wsgi.input':
    # <django.core.handlers.wsgi.LimitedStream object at 0x0000022791A8EDD0>, 'wsgi.errors':
    # <_io.TextIOWrapper name='<stderr>' mode='w' encoding='utf-8'>, 'wsgi.version': (1, 0),
    # 'wsgi.run_once': False, 'wsgi.url_scheme': 'http', 'wsgi.multithread': True, 'wsgi.multiprocess': False,
    # 'wsgi.file_wrapper': <class 'wsgiref.util.FileWrapper'>, 'CSRF_COOKIE':
    # 'P6PiYHAreI9zJuZGbJdMyqwxKR6MMw6mDNIT7sO8ZFqanw2C7BxOrQUdJwF8diGt'}
    print(request.method)  # GET, POST, PATCH, DELETE, PUT
    print(request.path == request.path_info)  # /statistic/google/realtime_rank/app
    print(request.resolver_match)
    # ResolverMatch(func=crawler.rank.views.statistic, args=(),
    # kwargs={'market': 'google', 'deal': 'realtime_rank', 'app': 'app'},
    # url_name=None, app_names=[], namespaces=[], route=statistic/<str:market>/<str:deal>/<str:app>)
