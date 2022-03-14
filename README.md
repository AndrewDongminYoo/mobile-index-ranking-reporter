# 모바일 애플리케이션마켓 크롤러

> 우리가 광고 중인 어플리케이션의 랭킹을 자동으로 수집하자

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/dwyl/esta/issues)

![프로젝트 예시 이미지.png](https://blog.kakaocdn.net/dn/bKX6NA/btrvyk8I42V/JBO2wP0IdwVSp1U1d5HsW0/img.png)

## Requirements  

```markdown
asgiref==3.5.0
beautifulsoup4==4.10.0
Django==4.0.3
django-crontab==0.7.1
django-environ==0.8.1
django-import-export==2.7.1
django-ninja==0.17.0
django-ratelimit==3.0.1
gunicorn==20.1.0
import-export==0.2.67.dev6
mysqlclient==2.1.0
pydantic==1.9.0
requests==2.27.1
```

## Installation

A step by step list of commands / guide that informs how to install an instance of this project.  

`git clone https://github.com/AndrewDongminYoo/ranker.git`

`pip install -r requirements.txt`

`python manage.py makemigrations`

`python manage.py migrate`

`python manage.py collectstatic`

`python manage.py runserver`

## Screenshots

Use this space to give a little demo of your project. Attach important screenshots if applicable. This section is optional and might not be applicable in some cases.

![Screenshots of the project](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FbQswyt%2FbtrvQgd2rUE%2F58kDZCmMFW2kIKgl2f29fk%2Fimg.png)

## Features

* 어플리케이션 순위 변화 표현 위해 lodash.js와 Chart.js 사용
* Django-Crontab 사용해 매일 12시마다, 매 시간 정각마다 특정 수집 동작
* Django-Import-Export 사용해 연관부서가 쉽게 데이터 외부 저장할 수 있도록 구성
* 슬랙 봇 연동해 앱 순위 변화 실시간 보고
* Django-Ninja 사용해 DRF보다 12배 빠른 API 생성
