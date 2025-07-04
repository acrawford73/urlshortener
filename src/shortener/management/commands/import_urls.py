import uuid
import time
import random
import string
import re
import logging

import asyncio
from playwright.async_api import async_playwright, Error

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shortener.models import ShortURL


# Purpose: Import a list of URLs to shorten.
# The urls text file is prepared by placing one URL per line.
# Usage:  python manage.py import_urls path/to/urls.txt user_id

# Logging
logging.basicConfig(
    filename='import_errors.log', 
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


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


DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.m4v'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a', '.wma'}
ALL_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

def is_direct_file_link(url: str) -> bool:
    path = urlparse(url).path.lower()
    for ext in ALL_EXTENSIONS:
        if path.endswith(ext):
            return ext
    return None


def fetch_page_title(url):
    """Fetches the title of a given webpage."""

    ## Level 1
    # Check direct links to files
    ext = is_direct_file_link(url)
    if ext:
        return f"Direct link to {ext.split('.')[1].upper()} file! Please rename this Title field."

    ## Level 2
    # Check search engines
    for name, pattern in SEARCH_PATTERNS.items():
        if title := search_check(pattern, url):
            return f"{title} - {name.capitalize()} Search"

    # Google Patents specific case
    if re.search(r'patents\.google\.[^/]+/\?', url):
        match = re.search(r'q=\(([^)]+)\)(?:&|$)', url)
        if match:
            title = unquote(match.group(1)).replace('\n','').replace('+',' ').strip()[:475]
            return f"{title} - Google Patents Search"

    ## Level 3 or 4
    # Fallback: Try to fetch the page title
    return fetch_title_from_html(url) or asyncio.run(async_get_title_playwright(url))


## Level 3 - BS4
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
            title_tag = soup.select_one("title")
            if title_tag:
                return unquote(title_tag.text.strip())[:500]
    except requests.exceptions.RequestException as err:
        logging.error(f"Requests error: {err} | URL: {url}")
    finally:
        session.close()
    return None


## Level 4 - Browser Simulator
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
        logging.error(f"Playwright error: {e} | URL: {url}")
    return None


# python manage.py import_url ~/path/to/file.txt user_id
class Command(BaseCommand):
    help = 'Import URLs from a text file and insert them into the ShortURL model'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the text file containing URLs')
        parser.add_argument('user_id', type=uuid.UUID, help='ID of the user who owns the URLs')

    def handle(self, *args, **options):
        file_path = options['file_path']
        user_id = options['user_id']

        try:
            owner = User.objects.get(id=str(user_id))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} does not exist.'))
            return

        try:
            with open(file_path, 'r') as file:
                urls = [line.strip() for line in file.readlines() if line.strip()]
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        count_url = 0
        count_import = 0

        for url in urls:

            # If line is not a URL then skip it
            if url.startswith('https://') or url.startswith('http://'):
                
                # Check if link is shortened already
                existing = ShortURL.objects.filter(long_url=url).first()
                if existing:
                    logging.warning(f'URL already shortened: {url}')
                    self.stdout.write(self.style.WARNING(f'{count_url}: URL already shortened: {url}'))
                    count_url += 1
                    continue

                MAX_ATTEMPTS = 20
                attempts = 0
                short_alias = generate_short_alias()
                while ShortURL.objects.filter(short_alias=short_alias).exists():
                    attempts += 1
                    if attempts >= MAX_ATTEMPTS:
                        logging.error(f"Failed unique alias generation for URL: {url}")
                        self.stdout.write(self.style.ERROR(f'{count_url}: Failed unique alias generation: {url}'))
                        count_url += 1
                        continue
                    short_alias = generate_short_alias()

                try:
                    title = fetch_page_title(url)

                    # Changed all imported links set to private, review first
                    private = True

                    # if title != None:
                    #     private = False
                    #     if title.startswith("Direct link to"):
                    #         private = True

                    short_url = ShortURL(
                        id=uuid.uuid4(),
                        long_url=url,
                        short_alias=short_alias,
                        title=title,
                        owner=owner,
                        private=private
                    )
                    short_url.save()
                    print(f'{count_url}: {short_alias}, {title}, {url}')
                    count_url += 1
                    count_import += 1
                    time.sleep(random.uniform(0.05, 0.25))
                except Exception as e:
                    logging.error(f"Error saving URL: {e}", extra={'dcount': count_url, 'alias': short_alias, 'url': url})

        if count_url == 0:
            self.stdout.write(self.style.SUCCESS(f'No URLs were imported.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {count_import} URLs with titles.'))
        print()
