from celery import shared_task
import pdfkit
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

def generate_offer_letter(name, date):
    html_content = render_to_string('PDF/offerletter.html', {'name': name, 'date': date})
    config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
    options = { 'page-size': 'A4', 'margin-top': '0in', 'margin-right': '0in', 'margin-bottom': '0in', 'margin-left': '0in', 'encoding': "UTF-8", 'no-outline': None }
    pdf = pdfkit.from_string(html_content, False, configuration=config, options=options)
    return pdf


@shared_task()
def send_ca_onboarding(data):
    email = data['email']
    if not is_email_valid(email):
        return
    offerletter = generate_offer_letter(data['name'], data['date'])
    html_content = render_to_string('Email/cap.html', {'name': data['name'], 'ca_id': data['ca_id'], 'email': data['email'], 'password': data['password']})
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(
        subject="You're In! Welcome to the Campus Ambassador Team |  Rendezvous'23-'24",
        body=text_content,
        from_email="Rendezvous IIT Delhi <noreply@rendezvousiitd.com>",
        to=[email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.attach('offerletter.pdf', offerletter, 'application/pdf')
    msg.send()
    return