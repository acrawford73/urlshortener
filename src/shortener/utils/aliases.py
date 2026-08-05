import random
import string

from shortener.models import ShortURL


ALIAS_LENGTH = 6

# First-path segments from urlpatterns where len(segment) == ALIAS_LENGTH only.
RESERVED_ALIASES = frozenset({
	'create',
	'topics',
})


def generate_unique_alias(max_attempts=30) -> str:
	for _ in range(max_attempts):
		alias = ''.join(random.choices(string.ascii_letters + string.digits, k=ALIAS_LENGTH))
		if alias.lower() in RESERVED_ALIASES:
			continue
		if not ShortURL.objects.filter(short_alias=alias).exists():
			return alias
	raise RuntimeError("Failed to generate unique alias")
