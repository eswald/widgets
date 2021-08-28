def now():
    import datetime
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
