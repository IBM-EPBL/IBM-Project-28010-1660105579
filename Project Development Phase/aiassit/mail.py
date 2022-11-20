from flask import Blueprint
import smtplib, os,ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


mail = Blueprint('mail', __name__)

sender_email = os.environ.get('MAIL_USERNAME')
password = os.environ.get('MAIL_PASSWORD')
host = "smtp.gmail.com"
port = 465

def send_email(to,otp):
    body = "Welcome! Thanks for signing up. Your code to activate your account: "+otp
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to
    message["Subject"] = "Verify Your Account - AIASSIST"
    message.attach(MIMEText(body, "plain"))
    text = message.as_string()
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host,port,context=context) as server:
        s=server.login(sender_email, password)
        server.sendmail(sender_email, to, text)
        server.close()


