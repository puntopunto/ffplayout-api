from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..serializers import UserSerializer


class CreateUserTest(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('john',
                                                       'john@snow.com',
                                                       'johnpassword')
        self.client.login(username='john', password='johnpassword')
        self.data = {
            'username': 'mike',
            'first_name': 'Mike',
            'last_name': 'Tyson',
            'password': 'password1234',
            'email': 'mike@tyson.com'
            }

    def test_can_create_user(self):
        response = self.client.post(reverse('api_player:user-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ReadUserTest(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('john',
                                                       'john@snow.com',
                                                       'johnpassword')
        self.client.login(username='john', password='johnpassword')
        self.user = User.objects.create(username="mike")

    def test_can_read_user_list(self):
        response = self.client.get(reverse('api_player:user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_read_user_detail(self):
        response = self.client.get(
            reverse('api_player:user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UpdateUserTest(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('john',
                                                       'john@snow.com',
                                                       'johnpassword')
        self.client.login(username='john', password='johnpassword')
        self.user = User.objects.create(username="mike", first_name="Tyson")
        self.data = UserSerializer(self.user).data
        self.data.update({'first_name': 'Changed'})

    def test_can_update_user(self):
        response = self.client.put(
            reverse('api_player:user-detail', args=[self.user.id]), self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DeleteUserTest(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('john',
                                                       'john@snow.com',
                                                       'johnpassword')
        self.client.login(username='john', password='johnpassword')
        self.user = User.objects.create(username="mikey")

    def test_can_delete_user(self):
        response = self.client.delete(
            reverse('api_player:user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
