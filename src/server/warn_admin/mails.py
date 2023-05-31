import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.server.commands.path_functions import find_file
from src.server.config import Infos
from typing import TYPE_CHECKING

from src.server.environnement.server_logs import log_error, log

if TYPE_CHECKING:
    from src.server.data.computer import Computer
    from src.server.data.computer_database import ComputerDatabase

email: str
password: str


def load_email_infos() -> bool:
    global email, password
    if not does_email_json_file_exists():
        log_error(f"The file  '{Infos.email_infos_json}' was not found.\n"
                  f"\nTo fix it, create the file {Infos.email_infos_json} and fill it with the following informations :"
                  " \n{\n\t\"email\": \"\" \n\t\"password\": \"\"\n}")

        with open(Infos.email_infos_json, "w") as f:
            json.dump({"email": "", "password": ""}, f, indent=4)

        log(f"The file {Infos.email_infos_json} was created.")
        return False

    try:
        with open(find_file(Infos.email_infos_json), "r") as f:
            email_content = json.load(f)
    except FileNotFoundError:
        log_error(f"The file  '{Infos.email_infos_json}' was not found.\n"
                  f"\nTo fix it, create the file {Infos.email_infos_json} and fill it with the following informations :"
                  " \n{\n  \"email\": \"\" \n\"password\": \"\"\n}")
        return False

    email = email_content.get("email", "")
    password = email_content.get("password", "")
    if not are_credentials_valid(mail=email, password_to_test=password):
        email = ""
        password = ""
        return False

    return True


def does_email_json_file_exists() -> bool:
    res = find_file(Infos.email_infos_json)
    if res is None or res == "":
        return False
    return True


def are_credentials_valid(mail: str, password_to_test: str) -> bool:
    if mail == "" or password_to_test == "":
        log_error(f"The file {Infos.email_infos_json} is not correctly filled.\n"
                  f"To fix it, fill the file {Infos.email_infos_json} with the following informations : \n"
                  "{\n  \"email\": \"\" \n\"password\": \"\"\n}")
        return False

    if not test_credential(mail, password_to_test):
        log_error(f"The credentials in {Infos.email_infos_json} are not correct.\n")
        log_error(f"Here are the current credentials : \nEmail : {email}\nPassword : {password_to_test}")
        return False
    return True


def test_credential(mail: str, password_to_test: str) -> bool:
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(mail, password_to_test)
        return True
    except smtplib.SMTPAuthenticationError:
        return False


def send_error_email(computer: 'Computer', error: str, traceback: str) -> None:
    send_string = f"<h3>Error, {Infos.PROJECT_NAME} did not manage to update {computer.hostname} !</h3>" \
                  f"<h4>The main error is : {error}.</h4>" \
                  f"<p>The traceback : </b>{traceback}</p>"

    send_email(message=send_string, subject=f"Program crashed on computer {computer.hostname}!")


def send_result_email(database: "ComputerDatabase") -> None:
    n_updated_computers = database.get_successfully_number_of_updated_computers()
    total_updatable_computers = database.get_number_of_updatable_computers()
    total_failures = database.get_number_of_failed_computers()

    if total_updatable_computers == 0:
        send_string = f"<h3>{Infos.PROJECT_NAME} found no updates to install.</h3>"
        send_email(message=send_string, subject=f"{Infos.PROJECT_NAME} found no updates to install.")
        return

    if n_updated_computers == 0:
        send_string = f"<h3>{Infos.PROJECT_NAME} did not manage to update any computer !</h3>"
    else:
        send_string = f"<h3>{Infos.PROJECT_NAME} finished updating all/some computers !</h3>"

    if total_updatable_computers > 0 and n_updated_computers > 0:
        send_string += f"<h4>{n_updated_computers}/{total_updatable_computers} computers has been updated " \
                       f"successfully.</h4>"

    # TODO: End this feature. Lacks list of updates for each computer. Lack tests. Lack traceback support.
    for computer in database.get_updated_computers():
        if computer.updates_string is not None:
            send_string += f" {len(computer.updates_string)} updates"
            for update in computer.updates_string:
                send_string += f"<br>&nbsp;&nbsp;&nbsp;&nbsp;- {update}"
    if n_updated_computers != total_updatable_computers:
        send_string += f"<h4>{total_failures} of computers were not able to be updated. An error occurred.</h4>"
        send_string += "<p>Here is the list: </p>"
        for computer in database.get_not_updated_computers():
            send_string += f"<p>{computer.hostname}</p>"
            send_string += f"<p>Error : {computer.error}</p>"
            send_string += f"<p><br>Traceback : <br>{computer.traceback}</p>"
            send_string += "<br>"
    send_email(message=send_string, subject=f"{Infos.PROJECT_NAME} finished updating all computers !")


def send_email(message: str, subject="Unhandled subject, mail should not have been sent") -> None:
    global email, password
    load_email_infos()
    if email == "" or password == "":
        log_error(f"The file {Infos.email_infos_json} is not correctly filled.\nThe send_email function shall not "
                  f"have been called.\n")
        return
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = email
    receiver_email = email
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
