from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

def is_email_valid(email):
    if len(email) <= 7:
        return False
    if '@' not in email:
        return False
    if '.' not in email:
        return False
    if email.count('@') > 1:
        return False
    eList = email.split('.')
    if len(eList[-1]) < 2:
        return False
    return True

@shared_task()
def send_otp(email, otp):
    if not is_email_valid(email):
        return
    html_content = render_to_string('Email/otp.html', {'otp': otp})
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(
        subject="Your OTP for Rendezvous'23",
        body=text_content,
        from_email="Rendezvous IIT Delhi <otp@rendezvousiitd.com>",
        to=[email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    return

@shared_task()
def send_welcome_email(email):
    if not is_email_valid(email):
        return
    html_content = render_to_string('Email/welcome.html')
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(
        subject="Welcome to Rendezvous'23",
        body=text_content,
        from_email="Rendezvous IIT Delhi <noreply@rendezvousiitd.com>",
        to=[email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    return