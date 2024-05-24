import smtplib
from email.message import EmailMessage

from config.config import SMTP_PASSWORD, SMTP_USER, SERVER_DOMEN


SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 465


async def get_approval_email_template(name: str, user_email: str) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Заявка'
    email['From'] = SMTP_USER
    email['To'] = user_email

    email.set_content(
        '<div>'
        f'<h1>Здравствуйте, {name}</h1>'
        '<p>Мы получили Вашу заявку! В ближайшее время администратор её проверит, и Вы получите ответ.</p>'
        '</div>',
        subtype='html'
    )
    return email


async def get_accepted_request_email_template(name: str, user_email: str, token: str) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Заявка'
    email['From'] = SMTP_USER
    email['To'] = user_email

    email.set_content(
        '<div>'
        f'<h1>Здравствуйте, {name}</h1>'
        '<p>Ваша заявка одобрена! Чтобы верифицировать аккаунт, перейдите по <b>ссылке</b></p>'
        f'<p>https://localhost/logIn?token={token}</p>'
        '</div>',
        subtype='html'
    )
    return email


async def get_rejected_request_email_template(name: str, user_email: str,) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Заявка'
    email['From'] = SMTP_USER
    email['To'] = user_email

    email.set_content(
        '<div>'
        f'<h1>Здравствуйте, {name}</h1>'
        '<p>Ваша заявка отклонена.</p>'
        '</div>',
        subtype='html'
    )
    return email


async def get_forgot_email_template(name: str, user_email: str, token: str) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Сброс пароля'
    email['From'] = SMTP_USER
    email['To'] = user_email

    email.set_content(
        '<div>'
        f'<h1>Здравствуйте, {name}</h1>'
        '<p>Чтобы сбросить пароль, перейдите по <b>ссылке</b></p>'
        f'<p>https://{SERVER_DOMEN}/reset_password?token={token}</p>'
        '</div>',
        subtype='html'
    )
    return email


async def send_email(name: str, user_email: str,  token: str | None, destiny: str):
    if destiny == 'approval':
        email = await get_approval_email_template(name, user_email)
    elif destiny == 'accept':
        email = await get_accepted_request_email_template(name, user_email, token)
    elif destiny == 'forgot':
        email = await get_forgot_email_template(name, user_email, token)
    elif destiny == 'reject':
        email = await get_rejected_request_email_template(name, user_email)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(email)
    return {
         "status_code": 200,
         "data": "Письмо отправлено",
         "details": None
    }
