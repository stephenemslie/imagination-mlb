from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    mobile_number = PhoneNumberField()


class Game(models.Model):
    user = models.ForeignKey(User)
    date = models.DateField(auto_now_add=True)
    total_distance = models.IntegerField()
    num_homeruns = models.IntegerField()
