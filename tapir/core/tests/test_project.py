from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class TestProject(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@admin.de", password="admin"
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_model_admins(self):
        model_admin_urls = [
            f"/admin/{model._meta.app_label}/{model._meta.model_name}/"
            for model, model_admin in admin.site._registry.items()
        ]
        for url in model_admin_urls:
            response = self.client.get(url, follow=True)
            self.assertEqual(response.status_code, 200)
