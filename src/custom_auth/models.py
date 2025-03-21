import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class CustomUserManager(UserManager):
	def _create_user(self, email, password, **extra_fields):
		if not email:
			raise ValueError("Email must be set")
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", False)
		extra_fields.setdefault("is_superuser", False)
		return self._create_user(email, password, **extra_fields)

	def create_superuser(self, email, password, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)
		if extra_fields.get("is_staff") is not True:
			raise ValueError("Superuser must have is_staff=True.")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True.")
		return self._create_user(email, password, **extra_fields)


# All users are stored here
class User(AbstractUser):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	username = None
	email = models.EmailField(_("email address"), unique=True,)
	objects = CustomUserManager()
	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = []
	def __str__(self):
		return self.email


class UserProfile(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
	bio = models.TextField()
	def __str__(self):
		return f"{self.__class__.__name__} object for {self.user}"
