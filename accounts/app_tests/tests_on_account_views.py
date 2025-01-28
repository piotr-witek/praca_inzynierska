from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class AccountViewsTest(TestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpassword123"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )

    def test_loginaccount_get(self):

        response = self.client.get(reverse("loginaccount"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loginaccount.html")

    def test_loginaccount_post_valid(self):

        response = self.client.post(
            reverse("loginaccount"),
            {"username": self.username, "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_loginaccount_post_invalid(self):

        response = self.client.post(
            reverse("loginaccount"),
            {"username": "wronguser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logoutaccount(self):

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse("logoutaccount"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("loginaccount"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
