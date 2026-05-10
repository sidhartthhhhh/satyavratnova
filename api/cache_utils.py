import json

import redis
from django.conf import settings


def get_redis():
    try:
        return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


def cache_get_json(key):
    try:
        r = get_redis()
        if not r:
            return None
        val = r.get(key)
        if not val:
            return None
        return json.loads(val)
    except Exception:
        return None


def cache_set_json(key, value, ttl=60):
    try:
        r = get_redis()
        if not r:
            return False
        r.setex(key, ttl, json.dumps(value))
        return True
    except Exception:
        return False
