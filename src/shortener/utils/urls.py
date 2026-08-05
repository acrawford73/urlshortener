import ipaddress
import socket
from urllib.parse import urlparse

from django.core.exceptions import ValidationError


class URLValidationError(ValidationError):
	pass


def _is_blocked_ip(ip_str: str) -> bool:
	try:
		ip = ipaddress.ip_address(ip_str)
	except ValueError:
		return False
	return (
		ip.is_private
		or ip.is_loopback
		or ip.is_link_local
		or ip.is_reserved
		or ip.is_multicast
	)


def _resolve_host_ips(hostname: str) -> list[str]:
	ips = set()
	for family in (socket.AF_INET, socket.AF_INET6):
		try:
			for result in socket.getaddrinfo(hostname, None, family, socket.SOCK_STREAM):
				ips.add(result[4][0])
		except socket.gaierror:
			continue
	return list(ips)


def validate_url_safe(url: str) -> None:
	parsed = urlparse(url)

	if parsed.scheme != 'https':
		raise URLValidationError("URL must use https://")

	hostname = parsed.hostname
	if not hostname:
		raise URLValidationError("URL must include a valid hostname")

	if hostname.lower() in ('localhost', 'localhost.localdomain'):
		raise URLValidationError("URL hostname is not allowed")

	if _is_blocked_ip(hostname):
		raise URLValidationError("URL hostname is not allowed")

	resolved_ips = _resolve_host_ips(hostname)
	if not resolved_ips:
		raise URLValidationError("Could not resolve URL hostname")

	for ip in resolved_ips:
		if _is_blocked_ip(ip):
			raise URLValidationError("URL resolves to a disallowed address")
