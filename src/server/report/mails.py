import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jeepney.wrappers
import keyring

# Circular import, need the type checking thing to work, so import type_checking

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.server.core.remote_computer_manager import RemoteComputerManager
    from src.server.update_management.network_update_manager import UpdateManager
from src.server.logs_management.server_logger import log, log_error
from src.server.infrastructure.paths import ServerPath
from src.server.infrastructure.config import Infos


email: str
password: str


def setup_email_config(already_asked: bool = False) -> None:
    """
    Sets up the email feature.
    Checks if credentials are valid.
    """
    if not already_asked:
        log("Setting up email configuration...\n", print_formatted=False)
        log("This works with google mails, and with the \"application password\" feature. If you want to use another "
            "email provider, you may have to modify the code yourself.", print_formatted=False)
        log("Please enter the following information to set up the email configuration.", print_formatted=False)
        log("Note : If you don't want to set up the email configuration, just press enter for each field.\n",
            print_formatted=False)

    email = input("Email : ")
    password = input("Password : ")

    if email == "" and password == "":
        log("Skipping email configuration...", print_formatted=False)
        Infos.email_send = False
        write_email_infos("", False)

        return

    if email == "" or password == "":
        log_error("You must enter both email and password.", print_formatted=False)
        setup_email_config(True)
        return

    if not test_credential(mail=email, password_to_test=password):
        log_error("Invalid email or password. Please try again.", print_formatted=False)
        setup_email_config(True)
        return

    Infos.email_send = True

    try:
        keyring.set_password("UpdateGuardian", email, password)
    except (jeepney.wrappers.DBusErrorResponse, keyring.core.fail.NoKeyringError):
        log_error("Error while saving the password. The keyring service does not work."
                  "Please fix it before trying to use the email system.", print_formatted=False)
        write_email_infos("", False)
        return
    write_email_infos(email, True)

    log("Email configuration set up successfully !", print_formatted=False, new_lines=2)


def write_email_infos(email: str, send_mail: bool, password: str = None) -> None:
    """
    Writes the email infos to a file.
    """
    if password is None:
        with open(ServerPath.get_email_infos_json_file(), "w", encoding="utf-8") as f:
            json.dump({"email": email, "send_mail": send_mail}, f, indent=4)
    else:
        with open(ServerPath.get_email_infos_json_file(), "w", encoding="utf-8") as f:
            json.dump({"email": email, "password": password, "send_mail": send_mail}, f, indent=4)


def load_email_infos() -> bool:
    """
    Loads email info from a file.
    Returns true if it is a success, false otherwise.
    """
    global email, password
    string_email_not_found: str = f"The file  '{Infos.email_infos_json}' was not found.\n\nTo fix it, create the " \
                                  f"file {Infos.email_infos_json} and fill it with the following informations :" \
                                  " \n{\n\t\"email\": \"\"}"
    if not does_email_json_file_exists():
        setup_email_config()
        load_email_infos()

    try:
        email_info_json_path: str = ServerPath.get_email_infos_json_file()
        with open(email_info_json_path, "r") as f:
            email_content = json.load(f)
    except FileNotFoundError:
        log_error(string_email_not_found)
        return False

    mails_activated: bool = email_content.get("send_mail", "")
    if not mails_activated:
        return False

    email = email_content.get("email", "")

    if email == "" or not email:
        setup_email_config()
        load_email_infos()
    # Set credentials
    service_id = 'UpdateGuardian'
    username = email

    # Get credentials
    password = keyring.get_password(service_id, username)

    if password is None:
        log_error(f"The password for the email {email} was not found in the windows credential secure system.\n"
                  f"Please enter the password for the email {email} : ", print_formatted=False)
        return False
    if not are_credentials_valid(mail=email, password_to_test=password):
        email = ""
        password = ""
        log_error("The credentials are not valid. Make sure the password and the provided email are correct.",
                  print_formatted=False)
        return False

    return True


def does_email_json_file_exists() -> bool:
    email_json_path: str = ServerPath.get_email_infos_json_file()
    if not ServerPath.exists(email_json_path):
        return False
    return True


def are_credentials_valid(mail: str, password_to_test: str) -> bool:
    """
    Tests emails credentials
    """
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
    """Core credential test function. Depends on 'are_credentials_valid'"""
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


def send_error_email(computer: 'RemoteComputerManager', error: str, traceback: str) -> None:
    """
    Sends an email expressing an error message.
    """
    send_string = f"<h3>Error, {Infos.PROJECT_NAME} did not manage to update {computer.get_hostname()} !</h3>" \
                  f"<h4>The main error is : {error}.</h4>" \
                  f"<p>The traceback : </b>{traceback}</p>"

    send_email(message=send_string, subject=f"Program crashed on computer {computer.get_hostname()}!")


class EmailResults:
    def __init__(self, database: 'UpdateManager'):
        """
        Initialize EmailResults class with a database.

        Args:
            database (ComputerDatabase): the database to get computer update details from.
        """
        self.database = database
        self.n_updated_computers = database.get_successfully_number_of_updated_computers()
        self.total_updatable_computers = database.get_number_of_updatable_computers()
        self.total_failures = database.get_number_of_failed_computers()
        self.subject = ""
        self.send_string = ""
        self.list_string = "&nbsp;&nbsp;&nbsp;&nbsp;-"

    def get_subject(self):
        """
        Generate the email subject based on the number of updatable and updated computers.

        Returns:
            str: The email subject.
        """
        if self.total_updatable_computers == 0:
            self.subject += f"{Infos.PROJECT_NAME} found no updates to install."

        if self.n_updated_computers == 0:
            self.subject += f"{Infos.PROJECT_NAME} did not manage to update any computer !"
        else:
            self.subject += f"{Infos.PROJECT_NAME} finished updating all/some computers !"
        return self.subject

    def generate_updated_computers_string(self):
        """
        Generate a string detailing the computers that have been successfully updated.

        Returns:
            str: The details of the updated computers in HTML format.
        """
        if self.total_updatable_computers > 0 and self.n_updated_computers > 0:
            self.send_string += f"<h4>{self.n_updated_computers}/{self.total_updatable_computers} " \
                                f"computers have been updated successfully.</h4>"
            self.send_string += "<p>Here is the list: </p>"

            updated_computers = self.database.get_updated_computers()
            length_updated_computers = len(updated_computers)

            for idx, computer in enumerate(updated_computers):
                if computer.updates_string is not None:
                    self.send_string += f"The PC <b>{computer.hostname}</b> had {len(computer.updates_string)} updates:"
                    for update in computer.updates_string:
                        self.send_string += f"<br>{self.list_string} {update}"
                    if idx == length_updated_computers - 1:
                        self.send_string += "<br><br>"
                    self.send_string += "<br>"
        return self.send_string

    def generate_not_updated_computers_string(self):
        """
        Generate a string detailing the computers that failed to update.

        Returns:
            str: The details of the failed computers in HTML format.
        """
        if self.n_updated_computers != self.total_updatable_computers:
            self.send_string += f"<h4>{self.total_failures} of computers were not able to be updated." \
                                f" An error occurred.</h4>"
            self.send_string += "<p>Here is the list: </p>"
            for computer in self.database.get_not_updated_computers():
                self.send_string += f"<p>{self.list_string} <b>{computer.hostname}</b>: {computer.error}</p>"
                self.send_string += "<br>"
        return self.send_string

    def send_email_results(self):
        """
        Send an email with the results of the computer update process.

        This method gathers all the necessary information, formats the email body and finally sends the email.
        """
        self.get_subject()
        self.generate_updated_computers_string()
        self.generate_not_updated_computers_string()
        send_email(message=self.send_string, subject=self.subject)


def send_email(message: str, subject="Unhandled subject, mail should not have been sent") -> None:
    """
    Loads emails credentials.
    Send html formatted email to registered email settings.
    Email is sent to the **same email address** as the one used.
    :param message: The message to send
    :param subject: The subject of the email
    :return: None
    """
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
