from unittest import mock
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from .factories import AdminUserFactory, PlayerUserFactory, GameFactory
from .models import User, Game


class AuthenticatedTestMixin:

    def setUp(self):
        super().setUp()
        self.user = AdminUserFactory()
        self.client.login(username=self.user.username, password=self.user.password)
        response = self.client.post('/token/', {'username': self.user.username, 'password': 'adm1n'})
        self.client.credentials(HTTP_AUTHORIZATION='JWT {}'.format(response.data['token']))


class TestGameStateActions(AuthenticatedTestMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.player = PlayerUserFactory()
        self.player.active_game = GameFactory(user=self.player)

    def test_game_on_create(self):
        player = PlayerUserFactory.build()
        data = {'first_name': player.first_name, 'mobile_number': player.mobile_number}
        response = self.client.post(reverse('user-list'), data)
        user = User.objects.get(pk=response.data['id'])
        game = Game.objects.get(user=user)
        self.assertEqual(response.data['active_game']['id'], game.pk)
        self.assertEqual(game.state, 'new')

    def test_direct_confirm(self):
        response = self.client.post(reverse('game-confirm', args=(self.player.active_game.pk,)))
        game = Game.objects.get(pk=self.player.active_game.pk)
        self.assertEqual(game.state, 'confirmed')

    def test_queue(self):
        response = self.client.post(reverse('game-queue', args=(self.player.active_game.pk,)))
        game = Game.objects.get(pk=self.player.active_game.pk)
        self.assertEqual(game.state, 'queued')

    def test_play(self):
        self.player.active_game = GameFactory(user=self.player, state='confirmed')
        response = self.client.post(reverse('game-play', args=(self.player.active_game.pk,)))
        game = Game.objects.get(pk=self.player.active_game.pk)
        self.assertEqual(game.state, 'playing')


class TestCompleteGame(AuthenticatedTestMixin, APITestCase):

    @mock.patch.object(Game, 'send_recall_sms')
    def setUp(self, send_recall_sms):
        super().setUp()
        self.score_data = {'score': 100, 'homeruns': 3, 'distance': 100}
        self.player = PlayerUserFactory()
        self.player.active_game = GameFactory(user=self.player, state='playing')
        game_id = self.player.active_game.pk
        self.response = self.client.post(reverse('game-complete', args=(game_id,)), self.score_data)
        self.game = Game.objects.get(pk=game_id)
        self._send_recall_sms = send_recall_sms

    def test_state(self):
        self.assertEqual(self.game.state, 'completed')
        self.assertEqual(self.response.data['state'], 'completed')

    def test_score(self):
        self.assertEqual(self.game.score, self.score_data['score'])
        self.assertEqual(self.game.homeruns, self.score_data['homeruns'])
        self.assertEqual(self.game.distance, self.score_data['distance'])
        self.assertEqual(self.response.data['score'], self.score_data['score'])
        self.assertEqual(self.response.data['homeruns'], self.score_data['homeruns'])
        self.assertEqual(self.response.data['distance'], self.score_data['distance'])

    def test_send_recall(self):
        self._send_recall_sms.assert_called()
