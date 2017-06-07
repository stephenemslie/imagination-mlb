from io import BytesIO
import logging
import datetime
from unittest import mock

from django.conf import settings
from django.utils.timezone import now
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from PIL import Image

from .factories import AdminUserFactory, PlayerUserFactory, GameFactory, TeamFactory
from .models import User, Game


logging.disable(logging.CRITICAL)


class AuthenticatedTestMixin:

    def setUp(self):
        super().setUp()
        self.user = AdminUserFactory()
        self.client.login(username=self.user.username, password=self.user.password)
        response = self.client.post('/token/', {'username': self.user.username, 'password': 'adm1n'})
        self.client.credentials(HTTP_AUTHORIZATION='JWT {}'.format(response.data['token']))


class TestPlayerFields(AuthenticatedTestMixin, APITestCase):

    def setUp(self):
        super().setUp()
        player = PlayerUserFactory.build()
        team = TeamFactory()
        self.data = {'first_name': player.first_name,
                     'last_name': player.last_name,
                     'mobile_number': player.mobile_number,
                     'team': team.name,
                     'handedness': player.handedness,
                     'signed_waiver': True}

    def test_create(self):
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 201)

    def test_handedness(self):
        self.data.pop('handedness')
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('handedness', response.json())

    def test_signed_waiver(self):
        self.data.pop('signed_waiver')
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 201)

    def test_first_name(self):
        self.data.pop('first_name')
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('first_name', response.json())

    def test_last_name(self):
        self.data.pop('last_name')
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 201)

    def test_mobile_number(self):
        self.data.pop('mobile_number')
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('mobile_number', response.json())

    def test_team(self):
        self.data.pop('team')
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 201)


class TestGame(APITestCase):
    
    def test_confirm_sets_team(self):
        team1 = TeamFactory()
        team2 = TeamFactory()
        user1 = PlayerUserFactory(team=team2)
        user2 = PlayerUserFactory(team=team1)
        user3 = PlayerUserFactory(team=team1)
        user4 = PlayerUserFactory(team=None)
        game = GameFactory(user=user4)
        self.assertEqual(game.user.team, None)
        game.confirm()
        game.save()
        self.assertEqual(game.user.team, team2)
        PlayerUserFactory(team=team2)
        user = PlayerUserFactory(team=None)
        game = GameFactory(user=user)
        game.confirm()
        self.assertEqual(game.user.team, team1)

    def test_confirm_existing_team(self):
        team1 = TeamFactory()
        team2 = TeamFactory()
        for i in range(5):
            PlayerUserFactory(team=team2)
        user = PlayerUserFactory(team=team2)
        game = GameFactory(user=user)
        self.assertEqual(user.team, team2)
        game.confirm()
        game.save()
        game = Game.objects.get(pk=game.pk)
        self.assertEqual(user.team, team2)



class TestGameStateActions(AuthenticatedTestMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.player = PlayerUserFactory()
        self.player.active_game = GameFactory(user=self.player)
        self.team = TeamFactory()

    def test_game_on_create(self):
        player = PlayerUserFactory.build()
        data = {'first_name': player.first_name,
                'mobile_number': player.mobile_number,
                'team': self.team.name,
                'handedness': player.handedness}
        response = self.client.post(reverse('user-list'), data)
        user = User.objects.get(pk=response.data['id'])
        game = Game.objects.get(user=user)
        self.assertEqual(response.data['active_game']['id'], game.pk)
        self.assertEqual(game.state, 'new')

    def test_second_game(self):
        data = {'user': self.player.pk}
        response = self.client.post(reverse('game-list'), data)
        player = User.objects.get(pk=self.player.pk)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(player.active_game.pk, response.json()['id'])

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
        with self.settings(RECALL_DISABLE=False):
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


class TestIllegalGameStateChanges(AuthenticatedTestMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.player = PlayerUserFactory()
        self.player.active_game = GameFactory(user=self.player)
        self.team = TeamFactory()

    def test_queue(self):
        for state in ('confirmed', 'playing', 'completed'):
            self.player.active_game = GameFactory(user=self.player, state=state)
            response = self.client.post(reverse('game-queue', args=(self.player.active_game.pk,)))
            self.assertEqual(response.status_code, 400)

    def test_recall(self):
        for state in ('new', 'confirmed', 'playing', 'completed'):
            self.player.active_game = GameFactory(user=self.player, state=state)
            response = self.client.post(reverse('game-recall', args=(self.player.active_game.pk,)))
            self.assertEqual(response.status_code, 400)

    def test_confirm(self):
        for state in ('queued', 'playing', 'complete'):
            self.player.active_game = GameFactory(user=self.player, state=state)
            response = self.client.post(reverse('game-confirm', args=(self.player.active_game.pk,)))
            self.assertEqual(response.status_code, 400)

    def test_play(self):
        for state in ('new', 'queued', 'recalled', 'completed'):
            self.player.active_game = GameFactory(user=self.player, state=state)
            response = self.client.post(reverse('game-play', args=(self.player.active_game.pk,)))
            self.assertEqual(response.status_code, 400)

    def test_complete(self):
        for state in ('new', 'queued', 'recalled', 'confirmed'):
            self.player.active_game = GameFactory(user=self.player, state=state)
            response = self.client.post(reverse('game-complete', args=(self.player.active_game.pk,)))
            self.assertEqual(response.status_code, 400)


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


class TestGameView(AuthenticatedTestMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.team_1 = TeamFactory()
        self.team_2 = TeamFactory()
        for i in range(10):
            game = GameFactory(state='completed', score=10, distance=10, homeruns=10)
            game.user.team = self.team_1
            game.user.save()
        for i in range(10):
            game = GameFactory(state='completed', score=20, distance=20, homeruns=20)
            game.user.team = self.team_2
            game.user.save()
        yesterday = now() - datetime.timedelta(days=1)
        for i in range(20):
            game = GameFactory(state='completed', score=10, distance=10, homeruns=10)
            game.date_created = yesterday
            game.user.team = self.team_1
            game.user.save()
            game.save()
        for i in range(10):
            game = GameFactory(state='completed', score=10, distance=10, homeruns=10)
            game.date_created = yesterday
            game.user.team = self.team_2
            game.user.save()
            game.save()

    def test_scores(self):
        team1_response = self.client.get(reverse('team-detail', args=(self.team_1.pk,)))
        team2_response = self.client.get(reverse('team-detail', args=(self.team_2.pk,)))
        self.assertEqual(team1_response.json()['scores'][0]['score'], 200)
        self.assertEqual(team1_response.json()['scores'][0]['distance'], 200)
        self.assertEqual(team1_response.json()['scores'][0]['homeruns'], 200)
        self.assertEqual(team1_response.json()['scores'][1]['score'], 100)
        self.assertEqual(team1_response.json()['scores'][1]['distance'], 100)
        self.assertEqual(team1_response.json()['scores'][1]['homeruns'], 100)
        self.assertEqual(team2_response.json()['scores'][0]['score'], 100)
        self.assertEqual(team2_response.json()['scores'][0]['distance'], 100)
        self.assertEqual(team2_response.json()['scores'][0]['homeruns'], 100)
        self.assertEqual(team2_response.json()['scores'][1]['score'], 200)
        self.assertEqual(team2_response.json()['scores'][1]['distance'], 200)
        self.assertEqual(team2_response.json()['scores'][1]['homeruns'], 200)


class TestMethodOverrideMiddleware(AuthenticatedTestMixin, APITestCase):

    def test_image_upload(self):
        user = PlayerUserFactory()
        image = Image.new('RGBA', (100, 100), (255, 255, 255, 255))
        f = BytesIO()
        image.save(f, 'png')
        f.seek(0)
        f.name = 'test.png'
        url = reverse('user-detail', args=(user.pk,))
        data = {'image': f}
        response = self.client.post(url, data=data, HTTP_X_HTTP_METHOD_OVERRIDE='PATCH')
        user = User.objects.get(pk=user.pk)
        f.seek(0)
        self.assertIsNotNone(user.image)
        self.assertEqual(user.image.read(), f.read())

