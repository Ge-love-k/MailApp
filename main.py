import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
import os
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtGui import QIcon
import sys
from plyer import notification

load_dotenv('credentials.env')

class MailClient:
    def __init__(self):
        self.mail = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL("imap.mail.ru", 993)
            self.mail.login(os.getenv("EMAIL"), os.getenv("PASSWORD"))
            self.mail.select("INBOX")
            print("Connected to mail server")
        except Exception as e:
            print(f"Error connecting to mail server: {e}")

    def fetch_emails(self, count):
        try:
            status, messages = self.mail.search(None, "ALL")
            mail_ids = messages[0].split()
            last_ids = mail_ids[-count:]
            emails = []

            for mail_id in last_ids:
                status, msg_data = self.mail.fetch(mail_id, "(RFC822)")
                for response in msg_data:
                    if isinstance(response, tuple):
                        msg = email.message_from_bytes(response[1])

                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        if not subject:
                            subject = "<Без темы>"

                        from_ = msg.get("From")
                        name, addr = parseaddr(from_)

                        body = self.get_body(msg)

                        emails.append({
                            "subject": subject,
                            "from": f"{name} <{addr}>",
                            "body": body
                        })

            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def get_body(self, msg):
        body = None
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                    break
        else:
            if msg.get_content_type() == "text/plain":
                body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")

        return body if body else "No content available in this email."

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mail App")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon("icon.png"))

        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        self.count_label = QLabel("Enter the number of emails to display:", self)
        self.layout.addWidget(self.count_label)

        self.count_input = QLineEdit(self)
        self.layout.addWidget(self.count_input)

        self.refresh_button = QPushButton("Refresh Emails", self)
        self.layout.addWidget(self.refresh_button)

        self.email_list = QListWidget(self)
        self.layout.addWidget(self.email_list)

        self.email_body = QTextEdit(self)
        self.email_body.setReadOnly(True)
        self.layout.addWidget(self.email_body)

        self.mail_client = MailClient()
        self.mail_client.connect()

        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        self.email_list.itemClicked.connect(self.display_email_body)

        self.setCentralWidget(self.main_widget)

    def on_refresh_clicked(self):
        try:
            count = int(self.count_input.text())
            self.display_emails(count)
        except ValueError:
            self.email_list.clear()
            self.email_list.addItem("Invalid input! Please enter a valid number.")

    def display_emails(self, count):
        emails = self.mail_client.fetch_emails(count)
        self.emails_data = emails

        self.email_list.clear()
        for email_data in emails:
            self.email_list.addItem(email_data['subject'])

    def display_email_body(self, item):
        subject = item.text()
        for email_data in self.emails_data:
            if email_data['subject'] == subject:
                self.email_body.setText(email_data['body'])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
