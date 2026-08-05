import uuid
import time
import random
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from shortener.models import ShortURL
from shortener.utils.aliases import generate_unique_alias
from shortener.utils.titles import fetch_title_full
from shortener.utils.urls import validate_url_safe, URLValidationError


logging.basicConfig(
	filename='import_errors.log',
	level=logging.ERROR,
	format="%(asctime)s - %(levelname)s - %(message)s"
)

User = get_user_model()


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
			if not url.startswith('https://'):
				continue

			try:
				validate_url_safe(url)
			except URLValidationError as e:
				logging.error(f'Unsafe URL skipped: {url} ({e})')
				self.stdout.write(self.style.WARNING(f'{count_url}: Unsafe URL skipped: {url}'))
				count_url += 1
				continue

			existing = ShortURL.objects.filter(long_url=url).first()
			if existing:
				logging.warning(f'URL already shortened: {url}')
				self.stdout.write(self.style.WARNING(f'{count_url}: URL already shortened: {url}'))
				count_url += 1
				continue

			try:
				short_alias = generate_unique_alias()
			except RuntimeError:
				logging.error(f"Failed unique alias generation for URL: {url}")
				self.stdout.write(self.style.ERROR(f'{count_url}: Failed unique alias generation: {url}'))
				count_url += 1
				continue

			try:
				title = fetch_title_full(url)
				private = True

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
			self.stdout.write(self.style.SUCCESS('No URLs were imported.'))
		else:
			self.stdout.write(self.style.SUCCESS(f'Successfully imported {count_import} URLs with titles.'))
		print()
