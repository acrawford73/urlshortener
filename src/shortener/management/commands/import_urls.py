import uuid
import time
import random
import string
import re
import asyncio
from playwright.async_api import async_playwright, Error

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shortener.models import ShortURL


### Usage:  python manage.py import_urls path/to/urls.txt user_id


User = get_user_model()


def generate_short_alias(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# Precompile regex patterns for better performance
SEARCH_PATTERNS = {
    "google": re.compile(r"google\.[^/]+/search\?"),
    "brave": re.compile(r"search\.brave\.[^/]+/search\?"),
    "duckduckgo": re.compile(r"duckduckgo\.[^/]+/\?")
}

QUERY_PATTERN = re.compile(r"q=([^&]+)(?:&|$)")

def extract_query_param(url, pattern):
    match = pattern.search(url)
    return unquote(match.group(1)).replace('+',' ').strip()[:475] if match else None


# Check for specific search engines based on common regex
def search_check(search_domain, search_url):
    """Extracts the search query from a given search URL."""
    if search_domain.search(search_url):
        return extract_query_param(search_url, QUERY_PATTERN)
    return None


def fetch_page_title(url):
    """Fetches the title of a given webpage."""

    ## Level 1
    # Check search engines
    for name, pattern in SEARCH_PATTERNS.items():
        if title := search_check(pattern, url):
            return f"{title} - {name.capitalize()} Search"

    # Google Patents specific case
    if re.search(r'patents\.google\.[^/]+/\?', url):
        match = re.search(r'q=\(([^)]+)\)(?:&|$)', url)
        if match:
            title = unquote(match.group(1)).replace('+',' ').strip()[:475]
            return f"{title} - Google Patents Search"

    ## Level 2 or 3
    # Fallback: Try to fetch the page title
    return fetch_title_from_html(url) or asyncio.run(async_get_title_playwright(url))


## Level 2 - Requests & BS4
def fetch_title_from_html(url):
    host_url = url
    server_host = urlparse(host_url).netloc

    """Attempts to retrieve the title using requests and BeautifulSoup."""
    headers = {
        'Host': server_host,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
        'Connection':'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        with requests.Session() as session:
            response = session.get(url, timeout=10, allow_redirects=True, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            if title_tag := soup.select_one("title"):
                session.close()
                return unquote(title_tag.text.strip())[:500]
    except requests.exceptions.RequestException as err:
        print(f"Request error: {err}")
    finally:
        session.close()
    return None


## Level 3 - Browser Simulator
async def async_get_title_playwright(url):
    """Fetches the title using Playwright for JavaScript-rendered pages."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            page.set_default_navigation_timeout(30000)
            await page.route(re.compile(r"\.(asx|m3u|m3u8|ts|qt|mov|mp4|mpg|m4v|m4a|mp3|ogg|jpeg|jpg|png|gif|svg|webp|wott|woff|otf|eot)$"), lambda route: route.abort())
            await page.goto(url)
            title = await page.title()
            await browser.close()
            return unquote(title.strip())[:500]
    except Exception as e:
        print(f"Playwright error: {e}")
    return None


class Command(BaseCommand):
    help = 'Import URLs from a text file and insert them into the ShortURL model'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the text file containing URLs')
        parser.add_argument('user_id', type=int, help='ID of the user who owns the URLs')

    def handle(self, *args, **options):
        file_path = options['file_path']
        user_id = options['user_id']

        try:
            owner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} does not exist.'))
            return

        try:
            with open(file_path, 'r') as file:
                urls = [line.strip() for line in file.readlines() if line.strip()]
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        count = 0
        for url in urls:
            longurl = url
            if longurl.lower().endswith('.pdf'):
                continue
            else:
                short_alias = generate_short_alias()
                while ShortURL.objects.filter(short_alias=short_alias).exists():
                    short_alias = generate_short_alias()

                title = fetch_page_title(url)
                short_count = count
                short_count = str(short_count)
                print(f'{short_count}: {short_alias}, {title}')

                short_url = ShortURL(
                    id=uuid.uuid4(),
                    long_url=url,
                    short_alias=short_alias,
                    title=title,
                    owner=owner
                )
                short_url.save()
                count += 1
                time.sleep(random.uniform(0.05, 0.2))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} URLs with titles.'))
