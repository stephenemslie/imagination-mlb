from django.conf import settings

import boto3
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
