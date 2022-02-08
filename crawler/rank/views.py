from datetime import datetime, timedelta


def get_kst():
    return datetime.utcnow() + timedelta(hours=9)
