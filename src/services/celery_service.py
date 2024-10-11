from celery import Celery
import smtplib
from config.config import REDIS_PORT, SMTP_PASSWORD, SMTP_USER, SMTP_HOST, SMTP_PORT
from src.services.email_service import (get_approval_email_template, get_accepted_request_email_template,
                                        get_forgot_email_template, get_rejected_request_email_template,
                                        get_admin_approval_email_template, get_time_limit_qa_template,
                                        get_time_limit_test_template, get_token_limit_template)


celery_app = Celery(
    'tasks',
    broker=f'redis://redis:{REDIS_PORT}/1',
    result_backend=f'redis://redis:{REDIS_PORT}/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Yekaterinburg',
    enable_utc=True,
)


@celery_app.task
def send_email(**kwargs):
    destiny = kwargs.pop('destiny')
    if destiny == 'approval':
        email = get_approval_email_template(**kwargs)
    elif destiny == 'accept':
        email = get_accepted_request_email_template(**kwargs)
    elif destiny == 'forgot':
        email = get_forgot_email_template(**kwargs)
    elif destiny == 'reject':
        email = get_rejected_request_email_template(**kwargs)
    elif destiny == 'admin_approval':
        email = get_admin_approval_email_template(**kwargs)
    elif destiny == 'qa_time_limit':
        email = get_time_limit_qa_template(**kwargs)
    elif destiny == 'test_time_limit':
        email = get_time_limit_test_template(**kwargs)
    elif destiny == 'token_limit':
        email = get_token_limit_template(**kwargs)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(email)
    return f'{destiny} email was sent'