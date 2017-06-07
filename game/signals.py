from django.dispatch import receiver
from django_fsm.signals import post_transition

from .models import Game


@receiver(post_transition, sender=Game)
def recall_users(sender, instance, name, source, target, **kwargs):
    if target == 'completed':
        for game in Game.objects.next_recalls():
            game.user.send_recall_sms()
