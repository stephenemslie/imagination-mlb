from django.dispatch import receiver
from django.utils import timezone
from django_fsm.signals import post_transition
from django.db import transaction

from .models import Game
from .tasks import render_souvenir, send_souvenir_sms


@receiver(post_transition, sender=Game)
def recall_users(sender, instance, name, source, target, **kwargs):
    if target in ('completed', 'cancelled'):
        for game in Game.objects.next_recalls():
            game.recall()
            game.save()


@receiver(post_transition, sender=Game)
def send_souvenir(sender, instance, name, source, target, **kwargs):
    if target == 'completed' and instance.user.mobile_number:
        s = render_souvenir.s(instance.pk)
        s.link(send_souvenir_sms.s())
        transaction.on_commit(s.delay)


@receiver(post_transition, sender=Game)
def log_state_change(sender, instance, name, source, target, **kwargs):
    date_field = 'date_{}'.format(target)
    try:
        state_changed = getattr(instance, date_field)
        if state_changed is None:
            setattr(instance, date_field, timezone.now())
            instance.save()
    except AttributeError:
        pass
