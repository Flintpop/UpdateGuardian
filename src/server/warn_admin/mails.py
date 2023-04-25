import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.server.config import Infos
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.data.computer import Computer


def send_error_email(computer: 'Computer', error: str, traceback: str) -> None:
    send_string = f"<h3>Error, {Infos.PROJECT_NAME} did not manage to update {computer.hostname} !</h3>" \
                  f"<h4>The main error is : {error}.</h4>" \
                  f"<p>The traceback : </b>{traceback}<\\p>The close price is <b>"

    send_email(message=send_string, subject=f"Program crashed on computer {computer.hostname}!")


def send_email(message: str, subject="Unhandled subject, mail should not have been sent") -> None:
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = ''
    receiver_email = ''
    password = ""
    html = u"""\
    <html>
    <head>
    <meta charset="utf-8" />
    </head>
    <body>
    <div>
    {}
    </div>
    </body
    </html>
    """.format(message)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email
    part = MIMEText(html, 'html')

    msg.attach(part)
    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
