"""Smoke test for the fluke -> TWO selective port (Bicycle + Maintenance + dashboard)."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Bicycle


class CorePortSmokeTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="smoke", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def test_pages_render(self):
        for name in ["core:home", "core:dashboard", "core:bicycles",
                     "core:bicycle_create", "core:maintenance", "core:maintenance_create"]:
            with self.subTest(page=name):
                resp = self.client.get(reverse(name))
                self.assertEqual(resp.status_code, 200)

    def test_bicycle_crud_and_maintenance_flow(self):
        # create bicycle
        resp = self.client.post(reverse("core:bicycle_create"), {
            "bike_code": "BK-001", "brand": "Test", "model": "M1",
            "color": "Red", "status": "available", "current_location": "Station A",
            "total_rides": 0,
        })
        self.assertEqual(resp.status_code, 302)
        bike = Bicycle.objects.get(bike_code="BK-001")
        # report maintenance -> bike goes under_maintenance
        resp = self.client.post(reverse("core:maintenance_create"), {
            "bicycle": bike.id, "reported_by": self.user.id,
            "type": "repair", "description": "flat tire", "status": "pending", "cost": 0,
        })
        self.assertEqual(resp.status_code, 302)
        bike.refresh_from_db()
        self.assertEqual(bike.status, "under_maintenance")
        # complete maintenance -> bike back to available
        record = bike.maintenances.get()
        resp = self.client.post(
            reverse("core:maintenance_update_status", args=[record.id, "completed"]))
        self.assertEqual(resp.status_code, 302)
        bike.refresh_from_db()
        self.assertEqual(bike.status, "available")

