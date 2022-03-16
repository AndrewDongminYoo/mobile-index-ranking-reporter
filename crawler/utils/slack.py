from slacker import Slacker


def slack_notify(text=None, channel='#test', username='알림봇', attachments=None):
    token = "xoxb-272240507447-3112130236450-7EkTIhNzhZecqfoLKk1lHIvD"
    slack = Slacker(token)
    slack.chat.post_message(text=text, channel=channel, username=username, attachments=attachments)


if __name__ == '__main__':
    slack_notify(text='test', channel='#ranker-test', username='알림봇')
