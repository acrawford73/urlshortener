import asyncio
import logging
import re
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

SEARCH_PATTERNS = {
	"google": re.compile(r"google\.[^/]+/search\?"),
	"brave": re.compile(r"search\.brave\.[^/]+/search\?"),
	"duckduckgo": re.compile(r"duckduckgo\.[^/]+/\?"),
}

QUERY_PATTERN = re.compile(r"q=([^&]+)(?:&|$)")

DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.m4v'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a', '.wma'}
ALL_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

MEDIA_ROUTE_PATTERN = re.compile(
	r"\.(asx|m3u|m3u8|ts|qt|mov|mp4|mpg|m4v|m4a|mp3|ogg|jpeg|jpg|png|gif|svg|webp|wott|woff|otf|eot)$"
)


def extract_query_param(url, pattern):
	match = pattern.search(url)
	return unquote(match.group(1)).replace('+', ' ').strip()[:475] if match else None


def search_check(search_domain, search_url):
	if search_domain.search(search_url):
		return extract_query_param(search_url, QUERY_PATTERN)
	return None


def is_direct_file_link(url: str):
	path = urlparse(url).path.lower()
	for ext in ALL_EXTENSIONS:
		if path.endswith(ext):
			return ext
	return None


def _title_from_heuristics(url):
	ext = is_direct_file_link(url)
	if ext:
		return f"Direct link to {ext.split('.')[1].upper()} file! Please rename this Title field."

	for name, pattern in SEARCH_PATTERNS.items():
		if title := search_check(pattern, url):
			return f"{title} - {name.capitalize()} Search"

	if re.search(r'patents\.google\.[^/]+/\?', url):
		match = re.search(r'q=\(([^)]+)\)(?:&|$)', url)
		if match:
			title = unquote(match.group(1)).replace('\n', '').replace('+', ' ').strip()[:475]
			return f"{title} - Google Patents Search"

	return None


def fetch_title_from_html(url):
	server_host = urlparse(url).netloc
	headers = {
		'Host': server_host,
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-US;q=0.7,en;q=0.3',
		'Accept-Encoding': 'gzip, deflate, br, zstd',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
		'Connection': 'keep-alive',
		'Cache-Control': 'max-age=0',
		'Upgrade-Insecure-Requests': '1',
	}

	try:
		with requests.Session() as session:
			response = session.get(url, timeout=10, allow_redirects=True, headers=headers)
			response.raise_for_status()
			soup = BeautifulSoup(response.text, 'html.parser')
			title_tag = soup.select_one("title")
			if title_tag:
				return unquote(title_tag.text.strip())[:500]
	except requests.exceptions.RequestException as err:
		logger.warning("Request error fetching title for %s: %s", url, err)
	return None


async def async_get_title_playwright(url):
	try:
		async with async_playwright() as p:
			browser = await p.chromium.launch(headless=True)
			context = await browser.new_context()
			page = await context.new_page()
			page.set_default_navigation_timeout(30000)
			await page.route(MEDIA_ROUTE_PATTERN, lambda route: route.abort())
			await page.goto(url)
			title = await page.title()
			await browser.close()
			return unquote(title.strip())[:500]
	except Exception as e:
		logger.warning("Playwright error fetching title for %s: %s", url, e)
	return None


def fetch_title_fast(url):
	title = _title_from_heuristics(url)
	if title:
		return title
	return fetch_title_from_html(url)


def fetch_title_full(url):
	title = fetch_title_fast(url)
	if title:
		return title
	return asyncio.run(async_get_title_playwright(url))
