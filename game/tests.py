from rest_framework.test import APITestCase
from .factories import AdminUserFactory, PlayerUserFactory, TeamFactory


class TestQueue(APITestCase):

    def setUp(self):
        self.user = AdminUserFactory()
        self.client.login(username=self.user.username, password=self.user.password)
        response = self.client.post('/token/', {'username': self.user.username, 'password': 'adm1n'})
        self.client.credentials(HTTP_AUTHORIZATION='JWT {}'.format(response.data['token']))
