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
from .views import set_lighting
from .signals import recall_users


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
        self.assertEqual(response.status_code, 201)
        self.data['mobile_number'] = ''
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 201)
        self.data['mobile_number'] = '+447786500944'
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(reverse('user-list'), self.data)
        self.assertEqual(response.status_code, 201)

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
        self.player.save()
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

    def test_second_game_requires_completion(self):
        data = {'user_id': self.player.pk}
        response = self.client.post(reverse('game-list'), data)
        self.assertEqual(response.status_code, 400)
        self.player.active_game = GameFactory(user=self.player, state='completed')
        self.player.save()
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

    def test_cancel(self):
        for state in ('new', 'queued', 'recalled', 'confirmed', 'playing'):
            game = GameFactory(state=state)
            response = self.client.post(reverse('game-cancel', args=(game.pk,)))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['state'], 'cancelled')
            self.assertEqual(Game.objects.get(pk=game.pk).state, 'cancelled')


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
        for state in ('playing', 'complete'):
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
        with mock.patch('game.tasks.render_souvenir.delay'):
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


class TestRecallUsersSignal(APITestCase):

    def setUp(self):
        super().setUp()
        for i in range(10):
            GameFactory(state='queued')

    def _recall_users(self, state):
        with mock.patch.object(User, 'send_recall_sms') as _send_recall_sms:
            with self.settings(RECALL_DISABLE=False):
                recall_users(sender=mock.Mock(),
                             instance=mock.Mock(),
                             name=mock.Mock(),
                             source=mock.Mock(),
                             target=state)
        return _send_recall_sms

    def test_send_recall_sms_completed(self):
        with self.settings(RECALL_WINDOW_SIZE=5):
            _send_recall_sms = self._recall_users('completed')
            self.assertEqual(_send_recall_sms.call_count, 5)

    def test_send_recall_sms_cancelled(self):
        with self.settings(RECALL_WINDOW_SIZE=5):
            _send_recall_sms = self._recall_users('cancelled')
            self.assertEqual(_send_recall_sms.call_count, 5)

    def test_recalled_state_completed(self):
        query = Game.objects.filter(state='recalled')
        self.assertEqual(query.count(), 0)
        with self.settings(RECALL_WINDOW_SIZE=5):
            self._recall_users('completed')
        self.assertEqual(query.count(), 5)

    def test_recalled_state_cancelled(self):
        query = Game.objects.filter(state='recalled')
        self.assertEqual(query.count(), 0)
        with self.settings(RECALL_WINDOW_SIZE=5):
            self._recall_users('cancelled')
        self.assertEqual(query.count(), 5)



class TestRecall(APITestCase):

    def setUp(self):
        self.expired_time = now() - datetime.timedelta(minutes=settings.RECALL_WINDOW_MINUTES + 1)
        GameFactory(state='new')

    def test_active_recalls(self):
        """Test active_recalls.

        Create 3 games in recalled state: 2 active, 1 expired. Test that games
        expire.
        """
        for state in ('new', 'confirmed', 'playing', 'completed', 'cancelled',
                      'recalled', 'recalled', 'recalled'):
            game = GameFactory(state=state)
        self.assertEqual(Game.objects.active_recalls().count(), 3)
        Game.objects.filter(pk=game.pk).update(date_updated=self.expired_time)
        self.assertEqual(Game.objects.active_recalls().count(), 2)

    def test_next_recalls(self):
        """Test next_recalls.

        Create 3 games in recalled state: 2 active, 1 expired. Adjust the
        recall window to test.
        """
        for state in ('new', 'confirmed', 'playing', 'completed', 'cancelled',
                      'recalled', 'recalled', 'recalled'):
            game = GameFactory(state=state)
        Game.objects.filter(pk=game.pk).update(date_updated=self.expired_time)
        for i in range(10):
            GameFactory(state='queued')
        with self.settings(RECALL_WINDOW_SIZE=1):
            self.assertEqual(Game.objects.next_recalls().count(), 0)
        with self.settings(RECALL_WINDOW_SIZE=2):
            self.assertEqual(Game.objects.next_recalls().count(), 0)
        with self.settings(RECALL_WINDOW_SIZE=3):
            self.assertEqual(Game.objects.next_recalls().count(), 1)
        with self.settings(RECALL_WINDOW_SIZE=4):
            self.assertEqual(Game.objects.next_recalls().count(), 2)

    def test_queue_order(self):
        games = []
        for i in reversed(range(10)):
            game = GameFactory(state='queued')
            game.date_created = now() - datetime.timedelta(minutes=i)
            games.append(game)
        with self.settings(RECALL_WINDOW_SIZE=3):
            self.assertEqual(list(Game.objects.next_recalls()), games[:3])


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


class TestSouvenirTask(APITestCase):

    def test_called_on_complete(self):
        user = PlayerUserFactory()
        user.active_game = GameFactory(user=user, state='playing')
        with mock.patch('game.tasks.render_souvenir.s') as _delay_partial:
            user.active_game.complete(10, 10, 10)
            _delay_partial().delay.assert_called()

    def test_screenshot_on_complete(self):
        user = PlayerUserFactory()
        user.active_game = GameFactory(user=user, state='playing')
        user.save()
        with mock.patch('chromote.Chromote') as _Chromote:
            _Chromote().tabs = mock.MagicMock()
            user.active_game.complete(10, 10, 10)
            _Chromote().tabs[0].screenshot.assert_called()
