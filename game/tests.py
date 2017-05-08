import datetime
from unittest import mock

from django.conf import settings
from django.utils.timezone import now
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from .factories import AdminUserFactory, PlayerUserFactory, GameFactory, TeamFactory
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
        self.team = TeamFactory()

    def test_game_on_create(self):
        player = PlayerUserFactory.build()
        data = {'first_name': player.first_name, 'mobile_number': player.mobile_number, 'team': self.team.name}
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

    @mock.patch.object(User, 'send_recall_sms')
    def test_recall(self, send_recall_sms):
        self.client.post(reverse('game-queue', args=(self.player.active_game.pk,)))
        self.client.post(reverse('game-recall', args=(self.player.active_game.pk,)))
        send_recall_sms.assert_called()

    @mock.patch.object(User, 'send_recall_sms')
    def test_requeue(self, _send_recall_sms):
        self.assertEqual(Game.objects.get(pk=self.player.active_game.pk).state, 'new')
        self.client.post(reverse('game-queue', args=(self.player.active_game.pk,)))
        self.client.post(reverse('game-recall', args=(self.player.active_game.pk,)))
        self.client.post(reverse('game-queue', args=(self.player.active_game.pk,)))
        self.assertEqual(Game.objects.get(pk=self.player.active_game.pk).state, 'queued')

    def test_play(self):
        self.player.active_game = GameFactory(user=self.player, state='confirmed')
        response = self.client.post(reverse('game-play', args=(self.player.active_game.pk,)))
        game = Game.objects.get(pk=self.player.active_game.pk)
        self.assertEqual(game.state, 'playing')


class TestCompleteGame(AuthenticatedTestMixin, APITestCase):

    @mock.patch('django_fsm.signals.post_transition.send')
    def setUp(self, send):
        super().setUp()
        self.score_data = {'score': 100, 'homeruns': 3, 'distance': 100}
        self.player = PlayerUserFactory()
        self.player.active_game = GameFactory(user=self.player, state='playing')
        game_id = self.player.active_game.pk
        self.response = self.client.post(reverse('game-complete', args=(game_id,)), self.score_data)
        self.game = Game.objects.get(pk=game_id)
        self._send = send

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

    def test_signal(self):
        self._send.assert_called()
        self.assertEqual(self._send.call_args[1]['target'], 'completed')


class TestRecall(APITestCase):

    def setUp(self):
        expired_time = now() - datetime.timedelta(minutes=settings.RECALL_WINDOW_MINUTES + 1)
        GameFactory(state='new')
        for i in range(10):
            GameFactory(state='queued')
        self.old_game = GameFactory(state='queued')
        self.old_game.date_created = now() - datetime.timedelta(days=10)
        self.old_game.save()
        GameFactory(state='confirmed')
        GameFactory(state='playing')
        GameFactory(state='completed')
        GameFactory(state='recalled')
        GameFactory(state='recalled')
        game = GameFactory(state='recalled')
        Game.objects.filter(pk=game.pk).update(date_updated=expired_time)

    def test_active_recalls(self):
        self.assertEqual(Game.objects.active_recalls().count(), 2)

    def test_next_recalls(self):
        with self.settings(RECALL_WINDOW_SIZE=3):
            self.assertEqual(Game.objects.next_recalls().count(), 1)
        with self.settings(RECALL_WINDOW_SIZE=4):
            self.assertEqual(Game.objects.next_recalls().count(), 2)
        with self.settings(RECALL_WINDOW_SIZE=1):
            self.assertEqual(Game.objects.next_recalls().count(), 0)

    def test_queue_order(self):
        with self.settings(RECALL_WINDOW_SIZE=3):
            self.assertEqual(list(Game.objects.next_recalls()), [self.old_game])
