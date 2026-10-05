from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from announcements.models import CampusAnnouncement, AnnouncementCategory, AnnouncementRead
from audit.models import SystemAuditLog
from staff.models import StaffProfile
from django.core.management import call_command

User = get_user_model()

class AnnouncementSystemTest(TestCase):
    def setUp(self):
        # Create Users
        self.admin_user = User.objects.create_user(username='admin', password='password', is_superuser=True)
        
        self.staff_user = User.objects.create_user(username='staff', password='password')
        self.staff_profile = StaffProfile.objects.create(user=self.staff_user, position='Officer', access_level='MANAGER')
        
        self.basic_user = User.objects.create_user(username='basic', password='password')
        
        self.category = AnnouncementCategory.objects.create(name='General')

    def test_announcement_creation_and_soft_delete(self):
        ann = CampusAnnouncement.objects.create(
            title='New Policy',
            content='Details here',
            category=self.category,
            created_by=self.staff_user
        )
        self.assertEqual(ann.status, CampusAnnouncement.Status.DRAFT)
        self.assertFalse(ann.is_deleted)
        
        # Soft delete
        ann.soft_delete(self.admin_user)
        self.assertTrue(ann.is_deleted)
        self.assertEqual(ann.deleted_by, self.admin_user)
        
        # Restore
        ann.restore(self.admin_user)
        self.assertFalse(ann.is_deleted)

    def test_process_announcements_command(self):
        now = timezone.now()
        
        # Create a scheduled announcement
        scheduled_ann = CampusAnnouncement.objects.create(
            title='Scheduled',
            content='Content',
            category=self.category,
            status=CampusAnnouncement.Status.SCHEDULED,
            publish_at=now - timedelta(minutes=5) # In the past, should publish now
        )
        
        # Create an expired announcement
        published_ann = CampusAnnouncement.objects.create(
            title='Published',
            content='Content',
            category=self.category,
            status=CampusAnnouncement.Status.PUBLISHED,
            expire_at=now - timedelta(minutes=5) # In the past, should expire now
        )
        
        # Run command
        call_command('process_announcements')
        
        scheduled_ann.refresh_from_db()
        published_ann.refresh_from_db()
        
        self.assertEqual(scheduled_ann.status, CampusAnnouncement.Status.PUBLISHED)
        self.assertEqual(published_ann.status, CampusAnnouncement.Status.EXPIRED)

    def test_permissions(self):
        # Admin can view manage page
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('announcements:manage_list'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        
        # Basic user cannot view manage page
        self.client.login(username='basic', password='password')
        response = self.client.get(reverse('announcements:manage_list'))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

    def test_read_tracking(self):
        ann = CampusAnnouncement.objects.create(
            title='Public Ann',
            content='Content',
            category=self.category,
            created_by=self.admin_user,
            status=CampusAnnouncement.Status.PUBLISHED
        )
        
        self.client.login(username='basic', password='password')
        response = self.client.get(reverse('announcements:detail', args=[ann.id]))
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(AnnouncementRead.objects.filter(announcement=ann, user=self.basic_user).exists())
