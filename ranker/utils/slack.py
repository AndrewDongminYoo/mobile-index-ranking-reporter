from slacker import Slacker


def slack_notify(text=None, channel='#test', username='알림봇', attachments=None):
    token = "xoxb-272240507447-3112130236450-7EkTIhNzhZecqfoLKk1lHIvD"
    slack = Slacker(token)
    slack.chat.post_message(text=text, channel=channel, username=username, attachments=attachments)


def post_to_slack(text=None):
    import requests
    import json
    url = 'https://hooks.slack.com/services/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'
    headers = {'Content-type': 'application/json'}
    body = json.dumps({"text": text})
    req = requests.post(url, headers=headers, data=body)