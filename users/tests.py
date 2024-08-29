from django.test import TestCase
from django.utils import timezone
from .models import TINETUser, AppAPIKey, AllowedApp


class AppAPIKeyModelTests(TestCase):

    def setUp(self):
        self.user = TINETUser.objects.create(username='testuser', password='testpass')
        self.api_key = AppAPIKey.objects.create(
            user=self.user,
            name='Test API Key',
            description='A key for testing',
            key='testkey123'
        )

    def test_is_valid_with_expired_key(self):
        self.api_key.expired = True
        self.api_key.save()
        self.assertFalse(self.api_key.is_valid())

    def test_is_valid_with_valid_key(self):
        self.assertFalse(self.api_key.expired)
        self.assertTrue(self.api_key.is_valid())

    def test_mark_as_used_updates_last_used(self):
        old_last_used = self.api_key.last_used
        self.api_key.mark_as_used()
        self.api_key.refresh_from_db()
        self.assertNotEqual(old_last_used, self.api_key.last_used)
        self.assertLess(self.api_key.last_used, timezone.now())

    def test_update_expired_status_to_expired(self):
        self.assertFalse(self.api_key.expired)
        self.api_key.update_expired_status()
        self.api_key.refresh_from_db()
        self.assertTrue(self.api_key.expired)


class AllowedAppModelTests(TestCase):

    def setUp(self):
        self.user = TINETUser.objects.create(username='testuser2', password='testpass2')
        self.api_key = AppAPIKey.objects.create(
            user=self.user,
            name='Test API Key 2',
            description='A second key for testing',
            key='testkey456'
        )
        self.allowed_app = AllowedApp.objects.create(user=self.user, app=self.api_key)

    def test_allowed_app_creation(self):
        self.assertEqual(self.allowed_app.user, self.user)
        self.assertEqual(self.allowed_app.app, self.api_key)