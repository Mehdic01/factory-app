from django.contrib import admin
from .models import Announcement, AnnouncementStatus, AnnouncementRead
from core.models import Role


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
	list_display = (
		"title",
		"status",
		"pinned",
		"publish_at",
		"expire_at",
		"author",
		"created_at",
	)
	list_filter = ("status", "pinned", "publish_at", "expire_at", "departments")
	search_fields = ("title", "slug", "content")
	prepopulated_fields = {"slug": ("title",)}
	filter_horizontal = ("departments",)

	actions = ("make_published", "make_archived")

	@admin.action(description="Publish selected announcements")
	def make_published(self, request, queryset):
		for obj in queryset:
			# Ensure author exists (needed for role checks)
			if obj.author is None:
				obj.author = request.user
				obj.save(update_fields=["author"])
			# Only allow GM or MANAGER to publish
			if getattr(request.user, "role", None) not in (Role.GM, Role.MANAGER):
				# skip publishing for unauthorized users
				continue
			try:
				obj.publish()
			except Exception:
				# Silently skip invalid ones in bulk action; admins can open the object for details
				continue

	@admin.action(description="Archive selected announcements")
	def make_archived(self, request, queryset):
		queryset.update(status=AnnouncementStatus.ARCHIVED)


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
	list_display = ("announcement", "user", "read_at")
	list_select_related = ("announcement", "user")
	search_fields = ("announcement__title", "user__username", "user__first_name", "user__last_name")
	date_hierarchy = "read_at"

