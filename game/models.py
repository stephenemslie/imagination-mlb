from django.db import models
from django.contrib.auth.models import AbstractUser

from django_fsm import FSMField, transition
from phonenumber_field.modelfields import PhoneNumberField


class Team(models.Model):
    name = models.CharField(max_length=128)


class User(AbstractUser):
    mobile_number = PhoneNumberField(unique=True)
    image = models.ImageField(null=True, blank=True)
    is_finalist = models.BooleanField(default=False)
    team = models.ForeignKey(Team, null=True, blank=True)


class Game(models.Model):
    user = models.ForeignKey(User, related_name='games')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    distance = models.IntegerField(default=0)
    homeruns = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    state = FSMField(default='new')

    @transition(field=state, source='new', target='queued')
    def queue(self):
        pass

    @transition(field=state, source=['new', 'recalled'], target='confirmed')
    def confirm(self):
        pass

    @transition(field=state, source='new', target='recalled')
    def recall(self):
        pass

    @transition(field=state, source='confirmed', target='playing')
    def play(self):
        pass

    @transition(field=state, source='playing', target='completed')
    def complete(self, score, distance, homeruns):
        self.score = score
        self.distance = distance
        self.homeruns = homeruns

    def send_recall_sms(self):
        client = boto3.client('sns')
