import datetime

from django.db import models
from django.db.models import Count
from django.db.models.functions import Trunc
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from django_fsm import FSMField, transition
from phonenumber_field.modelfields import PhoneNumberField

from .tasks import send_sms, render_souvenir, send_souvenir_sms


class Team(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

    @property
    def scores(self):
        query = Game.objects.filter(user__team=self, state='completed')\
                .annotate(day=Trunc('date_created', 'day', output_field=models.DateField()))\
                .values('day')\
                .annotate(score=models.Sum('score'))\
                .annotate(distance=models.Sum('distance'))\
                .annotate(homeruns=models.Sum('homeruns'))\
                .order_by('day')
        return list(query)


class User(AbstractUser):
    mobile_number = PhoneNumberField(unique=False)
    image = models.ImageField(null=True, blank=True)
    is_finalist = models.BooleanField(default=False)
    team = models.ForeignKey(Team, null=True, blank=True, related_name='members')
    active_game = models.OneToOneField('Game', related_name='+', null=True, blank=True)
    handedness = models.CharField(max_length=1,
                                  choices=(('L', 'Left'), ('R', 'Right')),
                                  null=True, blank=True)
    signed_waiver = models.BooleanField(default=False)

    def send_welcome_sms(self):
        message = ("Welcome to #mlbbattlegrounds. We’ll text you when it’s your "
                   "turn to bat. Enjoy Boston or L.A. food while you wait. Prepare "
                   "for beastmode!")
        send_sms.delay(self.mobile_number.as_e164, message)

    def send_recall_sms(self):
        message = ("Ready to smash it? Because it’s your turn to bat now! "
                   "Please head over to the batting cage where we’re waiting for "
                   "you. Do your team proud!")
        send_sms.delay(self.mobile_number.as_e164, message)


class GameQuerySet(models.QuerySet):

    def active_recalls(self, recall_expire=None, now=None):
        now = now or timezone.now()
        recall_expire = recall_expire or settings.RECALL_WINDOW_MINUTES
        expire_time = now - datetime.timedelta(minutes=recall_expire)
        query = self.filter(state='recalled', date_updated__gt=expire_time)
        return query

    def next_recalls(self, max_recalls=None):
        max_recalls = max_recalls or settings.RECALL_WINDOW_SIZE
        size = max(max_recalls - self.active_recalls().count(), 0)
        query = self.order_by('date_created').filter(state='queued')[:size]
        return query


class Game(models.Model):
    user = models.ForeignKey(User, related_name='games')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    distance = models.IntegerField(default=0)
    homeruns = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    state = FSMField(default='new')
    souvenir_image = models.ImageField(upload_to='souvenirs/', null=True, blank=True)

    objects = GameQuerySet.as_manager()

    @transition(field=state, source=['recalled', 'new'], target='queued')
    def queue(self):
        pass

    @transition(field=state, source=['new', 'queued', 'recalled'], target='confirmed')
    def confirm(self):
        if not self.user.team:
            query = Team.objects.annotate(member_count=Count('members')).order_by('member_count')
            self.user.team = query[0]
            self.user.save()

    @transition(field=state, source='queued', target='recalled')
    def recall(self):
        self.user.send_recall_sms()

    @transition(field=state, source='confirmed', target='playing')
    def play(self):
        pass

    @transition(field=state, source='playing', target='completed')
    def complete(self, score, distance, homeruns):
        self.score = score
        self.distance = distance
        self.homeruns = homeruns
        s = render_souvenir.s(self.pk)
        s.link(send_souvenir_sms.s())
        s.delay()

    @transition(field=state, source='*', target='cancelled')
    def cancel(self):
        pass
