from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse

import time
import boto3
import chromote
from celery import shared_task
from botocore.exceptions import EndpointConnectionError


@shared_task(bind=True)
def send_sms(self, recipient, message):
    client = boto3.client('sns',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          region_name=settings.AWS_REGION_NAME)
    try:
        client.publish(PhoneNumber=recipient,
                       Message=message,
                       MessageAttributes={
                           'AWS.SNS.SMS.SenderID': {
                               'DataType': 'String',
                               'StringValue': settings.RECALL_SENDER_ID},
                           'AWS.SNS.SMS.SMSType': {
                               'DataType': 'String',
                               'StringValue': 'Transactional'}
                       })
    except EndpointConnectionError as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True)
def render_souvenir(self, game_id):
    from .models import Game
    game = Game.objects.get(pk=game_id)
    path = reverse('game-souvenir', args=(game_id,))
    chrome = chromote.Chromote(host=settings.CHROME_REMOTE_HOST)
    tab = chrome.tabs[0]
    tab.set_url("http://{}{}".format(settings.DJANGO_HOST, path))
    time.sleep(2)
    screenshot = tab.screenshot()
    game.souvenir_image.save('souvenir.png', ContentFile(screenshot))
