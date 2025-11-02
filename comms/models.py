from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import Role


class AnnouncementStatus(models.TextChoices):
	DRAFT = "DRAFT", "Draft"
	PUBLISHED = "PUBLISHED", "Published"
	ARCHIVED = "ARCHIVED", "Archived"


class AnnouncementQuerySet(models.QuerySet):
	def published(self):
		return self.filter(status=AnnouncementStatus.PUBLISHED)

	def active(self):
		now = timezone.now()
		return (
			self.published()
			.filter(models.Q(publish_at__isnull=True) | models.Q(publish_at__lte=now))
			.filter(models.Q(expire_at__isnull=True) | models.Q(expire_at__gt=now))
		)

	def for_departments(self, dept_ids):
		"""
		Filter announcements visible to any of the provided department IDs,
		including global announcements (with no departments specified).
		"""
		if not dept_ids:
			return self.filter(departments__isnull=True)
		return self.filter(models.Q(departments__isnull=True) | models.Q(departments__in=dept_ids)).distinct()


class Announcement(models.Model):
	"""Company announcements with optional department targeting and scheduling."""

	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=220, unique=True)
	content = models.TextField()

	status = models.CharField(max_length=12, choices=AnnouncementStatus.choices, default=AnnouncementStatus.DRAFT)
	pinned = models.BooleanField(default=False, help_text="Pin to top in lists")

	publish_at = models.DateTimeField(null=True, blank=True, help_text="Start showing at this time (optional)")
	expire_at = models.DateTimeField(null=True, blank=True, help_text="Stop showing after this time (optional)")

	# Targeting: if empty => global announcement (all departments)
	departments = models.ManyToManyField('departments.Department', related_name='announcements', blank=True)

	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	objects = AnnouncementQuerySet.as_manager()

	class Meta:
		ordering = ['-pinned', '-publish_at', '-created_at']
		indexes = [
			models.Index(fields=["status", "publish_at"]),
			models.Index(fields=["pinned"]),
			models.Index(fields=["slug"], name="announcement_slug_idx"),
		]

	def __str__(self):
		return self.title

	# Business logic helpers
	@property
	def is_published(self) -> bool:
		return self.status == AnnouncementStatus.PUBLISHED

	@property
	def is_live(self) -> bool:
		"""Published and within schedule window."""
		if not self.is_published:
			return False
		now = timezone.now()
		if self.publish_at and self.publish_at > now:
			return False
		if self.expire_at and self.expire_at <= now:
			return False
		return True

	def publish(self, when: timezone.datetime | None = None):
		"""Publish now (or at a specific datetime)."""
		if when is None:
			when = timezone.now()
		# Enforce role-based publish rules
		from django.core.exceptions import ValidationError
		if not self.author:
			raise ValidationError({"author": "Author is required to publish an announcement."})
		if self.author.role == Role.EMPLOYEE:
			raise ValidationError({"author": "Employees cannot publish announcements."})
		if self.author.role == Role.MANAGER:
			# Managers must target only their managed departments and cannot publish globally
			managed_ids = list(self.author.managed_departments.values_list("id", flat=True))
			if not self.departments.exists():
				raise ValidationError({"departments": "Managers must select one or more of their managed departments to publish."})
			invalid_target = self.departments.exclude(id__in=managed_ids).exists()
			if invalid_target:
				raise ValidationError({"departments": "Managers can only publish to their managed departments."})
		self.status = AnnouncementStatus.PUBLISHED
		if self.publish_at is None:
			self.publish_at = when
		self.save(update_fields=["status", "publish_at", "updated_at"])

	def archive(self):
		self.status = AnnouncementStatus.ARCHIVED
		self.save(update_fields=["status", "updated_at"])

	def mark_read(self, user):
		"""Mark this announcement as read by the given user (idempotent)."""
		obj, _ = AnnouncementRead.objects.get_or_create(announcement=self, user=user)
		return obj

	def is_read_by(self, user) -> bool:
		"""Return True if the user has read this announcement."""
		return AnnouncementRead.objects.filter(announcement=self, user=user).exists()

	def read_count(self) -> int:
		"""Number of read receipts for this announcement."""
		return self.reads.count()

	def clean(self):
		super().clean()
		if self.publish_at and self.expire_at and self.publish_at >= self.expire_at:
			from django.core.exceptions import ValidationError

			raise ValidationError({
				"expire_at": "Expire time must be after publish time.",
			})


class AnnouncementRead(models.Model):
	"""Tracks when a user has read an announcement."""

	announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="reads")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="announcement_reads")
	read_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("announcement", "user")
		ordering = ["-read_at"]
		indexes = [
			models.Index(fields=["announcement", "user"]),
		]

	def __str__(self) -> str:
		return f"{self.user} read {self.announcement} at {self.read_at:%Y-%m-%d %H:%M}"
 


