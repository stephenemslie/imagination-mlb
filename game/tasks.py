import time
import asyncio

from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse

import boto3
import requests
from pyppeteer import launch
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
    async def screenshot(url):
        browser = await launch(args=['--no-sandbox'])
        page = await browser.newPage()
        await page.goto(url)
        return await page.screenshot()
    loop = asyncio.get_event_loop()
    path = reverse('game-souvenir', args=(game_id,))
    url = "http://{}{}".format(settings.DJANGO_HOST, path)
    data = loop.run_until_complete(screenshot(url))
    game = Game.objects.get(pk=game_id)
    try:
        game.souvenir_image.save('souvenir.png', ContentFile(data))
    except EndpointConnectionError as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)
    return game.pk


@shared_task
def periodic_recall():
    from .models import Game
    for game in Game.objects.next_recalls():
        game.recall()
        game.save()


@shared_task(bind=True)
def shorten_url(self, url):
    try:
        payload = {'access_token': settings.BITLY_TOKEN, 'longUrl': url}
        response = requests.get('https://api-ssl.bitly.com/v3/shorten', params=payload)
    except requests.exceptions.ConnectionError as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)
    response.raise_for_status()
    return response.json()


@shared_task()
def send_souvenir_sms(game_id):
    from .models import Game
    game = Game.objects.get(pk=game_id)
    url = shorten_url(game.souvenir_image.url)['data']['url']
    message = game.show.souvenir_message.format(url)
    send_sms.delay(game.user.mobile_number.as_e164, message)
