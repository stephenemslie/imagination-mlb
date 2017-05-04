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
    state = FSMField(default='registered')
    team = models.ForeignKey(Team, null=True, blank=True)


class Game(models.Model):
    user = models.ForeignKey(User, related_name='games')
    date = models.DateField(auto_now_add=True)
    total_distance = models.IntegerField()
    num_homeruns = models.IntegerField()
