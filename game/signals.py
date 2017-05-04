from django.dispatch import receiver
from django_fsm.signals import post_transition

from .models import Game


@receiver(post_transition, sender=Game)
def recall_user(sender, instance, name, source, target, **kwargs):
    if target == 'completed':
        instance.send_recall_sms()
