from django.core.management.base import BaseCommand
from django.utils import timezone
from announcements.models import CampusAnnouncement
from audit.models import SystemAuditLog
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Processes scheduled announcements to PUBLISHED and expired announcements to EXPIRED.'

    def handle(self, *args, **options):
        now = timezone.now()
        User = get_user_model()
        system_user = User.objects.filter(is_superuser=True).first()

        # 1. SCHEDULED -> PUBLISHED
        scheduled_qs = CampusAnnouncement.objects.filter(
            status=CampusAnnouncement.Status.SCHEDULED,
            is_deleted=False,
            publish_at__lte=now
        )
        
        published_count = 0
        for ann in scheduled_qs:
            old_status = ann.status
            ann.status = CampusAnnouncement.Status.PUBLISHED
            ann.save(update_fields=['status'])
            published_count += 1
            if system_user:
                SystemAuditLog.log_action(
                    user=system_user,
                    action_type="PUBLISH_ANNOUNCEMENT_AUTO",
                    entity=ann,
                    old_values={'status': old_status},
                    new_values={'status': ann.status}
                )

        # 2. PUBLISHED -> EXPIRED
        expired_qs = CampusAnnouncement.objects.filter(
            status=CampusAnnouncement.Status.PUBLISHED,
            is_deleted=False,
            expire_at__lte=now
        )

        expired_count = 0
        for ann in expired_qs:
            old_status = ann.status
            ann.status = CampusAnnouncement.Status.EXPIRED
            ann.save(update_fields=['status'])
            expired_count += 1
            if system_user:
                SystemAuditLog.log_action(
                    user=system_user,
                    action_type="EXPIRE_ANNOUNCEMENT_AUTO",
                    entity=ann,
                    old_values={'status': old_status},
                    new_values={'status': ann.status}
                )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed announcements: {published_count} published, {expired_count} expired.'
        ))
