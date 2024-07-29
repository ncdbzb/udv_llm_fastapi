import smtplib
from email.message import EmailMessage
from config.config import SMTP_USER, SERVER_DOMEN, admin_dict


def get_approval_email_template(name: str, user_email: str) -> EmailMessage:
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


def get_accepted_request_email_template(name: str, user_email: str, token: str) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Заявка'
    email['From'] = SMTP_USER
    email['To'] = user_email

    email.set_content(
        '<div>'
        f'<h1>Здравствуйте, {name}</h1>'
        '<p>Ваша заявка одобрена! Чтобы верифицировать аккаунт, перейдите по <b>ссылке</b><br>Ссылка будет доступна в течении 1 суток.</p>'
        f'<p>https://{SERVER_DOMEN}/logIn?token={token}</p>'
        '</div>',
        subtype='html'
    )
    return email


def get_rejected_request_email_template(name: str, user_email: str,) -> EmailMessage:
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


def get_forgot_email_template(name: str, user_email: str, token: str) -> EmailMessage:
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


def get_admin_approval_email_template(name: str, surname: str, user_email: str) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Новая заявка на регистрацию'
    email['From'] = SMTP_USER
    email['To'] = admin_dict['email']

    email.set_content(
    '<div>'
    '<h1>Уважаемый администратор,</h1>'
    '<p>Поступила новая заявка на регистрацию. Ниже приведены данные пользователя:</p>'
    '<table border="1" cellpadding="5" cellspacing="0">'
    '<tr>'
    '<th>Имя</th>'
    '<th>Фамилия</th>'
    '<th>Email</th>'
    '<th>Роль</th>'
    '</tr>'
    '<tr>'
    f'<td>{name}</td>'
    f'<td>{surname}</td>'
    f'<td>{user_email}</td>'
    '<td>Представитель организации</td>'
    '</tr>'
    '</table>'
    '</div>',
    subtype='html'
)
    return email


def get_time_limit_qa_template(
    filename: str, 
    tokens: int, 
    total_time: float, 
    gigachat_time: float, 
    question: str, 
    answer: str
) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Превышен временной лимит в вопросно-ответной системе!'
    email['From'] = SMTP_USER
    email['To'] = admin_dict['email']

    email.set_content(
    '<div>'
    '<h1>Уважаемый администратор,</h1>'
    '<p>Один из запросов в вопросно-ответной системе превысил временной лимит (15 секунд)</p>'
     '<table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%;">'
    '<tr>'
    '<th style="text-align: left; width: 30%;">Операция</th>'
    '<th style="text-align: left;">Вопросно-ответная система</th>'
    '</tr>'
    '<tr>'
    f'<td>Документация</td>'
    f'<td>{filename}</td>'
    '</tr>'
    '<tr>'
    f'<td>Потраченные токены</td>'
    f'<td>{tokens}</td>'
    '</tr>'
    '<tr>'
    f'<td>Общее время</td>'
    f'<td>{total_time}</td>'
    '</tr>'
    '<tr>'
    f'<td>Время работы GigaChat</td>'
    f'<td>{gigachat_time}</td>'
    '</tr>'
    '<tr>'
    f'<td>Вопрос</td>'
    f'<td style="word-break: break-word;">{question}</td>'
    '</tr>'
    '<tr>'
    f'<td>Ответ</td>'
    f'<td style="word-break: break-word;">{answer.replace(chr(10), "<br>")}</td>'
    '</tr>'
    '</table>'
    '</div>',
    subtype='html'
)
    return email


def get_time_limit_test_template(
    filename: str, 
    tokens: int, 
    total_time: float, 
    gigachat_time: float,
    generation_attemps: int,
    question: str, 
    options: str, 
    right_answer: str
) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Превышен временной лимит в тестовой системе!'
    email['From'] = SMTP_USER
    email['To'] = admin_dict['email']

    email.set_content(
    '<div>'
    '<h1>Уважаемый администратор,</h1>'
    '<p>Один из запросов в тестовой системе превысил временной лимит (15 секунд)</p>'
     '<table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%;">'
    '<tr>'
    '<th style="text-align: left; width: 30%;">Операция</th>'
    '<th style="text-align: left;">Тестовая система</th>'
    '</tr>'
    '<tr>'
    f'<td>Документация</td>'
    f'<td>{filename}</td>'
    '</tr>'
    '<tr>'
    f'<td>Потраченные токены</td>'
    f'<td>{tokens}</td>'
    '</tr>'
    '<tr>'
    f'<td>Общее время</td>'
    f'<td>{total_time}</td>'
    '</tr>'
    '<tr>'
    f'<td>Время работы GigaChat</td>'
    f'<td>{gigachat_time}</td>'
    '</tr>'
    '<tr>'
    f'<td>Кол-во попыток генерации</td>'
    f'<td style="word-break: break-word;">{generation_attemps}</td>'
    '</tr>'
    '<tr>'
    f'<td>Вопрос</td>'
    f'<td style="word-break: break-word;">{question}</td>'
    '</tr>'
    '<tr>'
    f'<td>Варианты ответа</td>'
    f'<td style="word-break: break-word;">{options}</td>'
    '</tr>'
    '<tr>'
    f'<td>Правильный ответ</td>'
    f'<td style="word-break: break-word;">{right_answer}</td>'
    '</tr>'
    '</table>'
    '</div>',
    subtype='html'
)
    return email


def get_token_limit_template(name: str, surname: str, user_email: str, tokens_by_doc: dict[str: int]) -> EmailMessage:
    email = EmailMessage()
    email['Subject'] = 'Превышен лимит затрат токенов одним пользователем!'
    email['From'] = SMTP_USER
    email['To'] = admin_dict['email']

    table_headers = ''.join([f'<th>{key}</th>' for key in tokens_by_doc.keys()])
    table_values = ''.join([f'<td>{value}</td>' for value in tokens_by_doc.values()])

    email.set_content(
    '<div>'
    '<h1>Уважаемый администратор,</h1>'
    '<p>Один из пользователей превысил лимити затрат токенов (63000)</p>'
    '<table border="1" cellpadding="5" cellspacing="0">'
    '<tr>'
    '<th>Имя</th>'
    '<th>Фамилия</th>'
    '<th>Email</th>'
    f'{table_headers}'
    '</tr>'
    '<tr>'
    f'<td>{name}</td>'
    f'<td>{surname}</td>'
    f'<td>{user_email}</td>'
    f'{table_values}'
    '</tr>'
    '</table>'
    '</div>',
    subtype='html'
)
    return email

