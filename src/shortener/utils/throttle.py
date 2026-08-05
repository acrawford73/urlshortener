from django.core.cache import cache
from ipware import get_client_ip


def check_rate_limit(request, key_prefix, rate, per_seconds):
	"""Return True if the request is within the rate limit, False if exceeded."""
	ip, _ = get_client_ip(request)
	if not ip:
		ip = 'unknown'
	key = f"{key_prefix}:{ip}"
	try:
		count = cache.incr(key)
	except ValueError:
		cache.set(key, 1, timeout=per_seconds)
		count = 1
	return count <= rate
