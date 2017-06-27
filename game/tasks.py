from celery import shared_task

@shared_task
def send_sms(recipient, message):
    pass
