import os
import qrcode
import urllib.request
from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from .models import *
from .encryption import encrypt
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import img2pdf

def make_qr_code(data):
    qr = qrcode.QRCode(
        version=5,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image()
    qr_img = qr_img.resize((225, 225))

    return qr_img

def make_pass(name, rdv_id, qr, template, font):
    cert = template.copy()
    cert.paste(qr, (184, 320))
    draw = ImageDraw.Draw(cert)

    n_list = name.split()
    name = n_list[0]
    if len(n_list[0]) < 2 and (len(n_list) > 1):
        name = n_list[1]
    
    draw.text((245, 577), name, (0, 0, 0), font=font)
    draw.text((250, 603), rdv_id, (0, 0, 0), font=font)

    io = BytesIO()
    cert.save(io, format='PNG')
    io.seek(0)
    pdfIo = BytesIO()
    pdfIo.write(img2pdf.convert(io))
    
    return pdfIo.getvalue()

def generate_pronite_pdf(name, rdv_id, pronite, enc_data):
    pronite_map = { "S": "Spectrum", "K": "Kaleidoscope", "M": "Melange", "D": "Dhoom" }
    template = Image.open(urllib.request.urlopen(f"https://rdv-bucket.s3.ap-south-1.amazonaws.com/Pronite/{pronite_map[pronite]}%20Pronite%20Pass%20Template.png"))
    font = ImageFont.truetype(urllib.request.urlopen("https://rdv-bucket.s3.ap-south-1.amazonaws.com/Pronite/Font.ttf"), 22)
    qr = make_qr_code(enc_data)
    pdf = make_pass(name, rdv_id, qr, template, font)
    return pdf
    

@shared_task()
def send_passes(pronite):
    pronite_map = { "S": "Spectrum", "K": "Kaleidoscope", "M": "Melange", "D": "Dhoom" }
    bookings = Booking.objects.filter(slot__pronite=pronite, pass_emailed=False)
    template = Image.open(urllib.request.urlopen(f"https://rdv-bucket.s3.ap-south-1.amazonaws.com/Pronite/{pronite_map[pronite]}%20Pronite%20Pass%20Template.png"))
    font = ImageFont.truetype(urllib.request.urlopen("https://rdv-bucket.s3.ap-south-1.amazonaws.com/Pronite/Font.ttf"), 22)
    for booking in bookings:
        profile = booking.user
        data = f"ticket_id={booking.ticket_id.replace('&', '')}"
        encrypted_data = encrypt(data, os.environ['ENCRYPTION_KEY'])

        qr = make_qr_code(encrypted_data)
        pdf = make_pass(profile.name, profile.rdv_id, qr, template, font)

        html_content = render_to_string('Email/pronite.html', {'pronite': pronite_map[pronite]})
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(
            subject=f"Your Pass to {pronite_map[pronite]} Pronite | RendezvousX",
            body=text_content,
            from_email="Rendezvous Pronites <pronites@rendezvousiitd.com>",
            to=[profile.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.attach("Pronite Pass.pdf", pdf, 'application/pdf')
        msg.send()

        booking.pass_emailed = True ; booking.save()

    return

@shared_task()
def send_pass(id):

    pronite_map = { "S": "Spectrum", "K": "Kaleidoscope", "M": "Melange", "D": "Dhoom" }
    booking = Booking.objects.get(id=id)
    data = f"ticket_id={booking.ticket_id.replace('&', '')}"
    encrypted_data = encrypt(data, os.environ['ENCRYPTION_KEY'])

    template = Image.open(urllib.request.urlopen(f"https://rdv-bucket.s3.ap-south-1.amazonaws.com/Pronite/{pronite_map[booking.slot.pronite]}%20Pronite%20Pass%20Template.png"))
    font = ImageFont.truetype(urllib.request.urlopen("https://rdv-bucket.s3.ap-south-1.amazonaws.com/Pronite/Font.ttf"), 22)

    qr = make_qr_code(encrypted_data)
    pdf = make_pass(booking.user.name, booking.user.rdv_id, qr, template, font)
    
    html_content = render_to_string('Email/pronite.html', {'pronite': pronite_map[booking.slot.pronite]})
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(
        subject=f"Your Pass to {pronite_map[booking.slot.pronite]} Pronite | RendezvousX",
        body=text_content,
        from_email="Rendezvous Pronites <pronites@rendezvousiitd.com>",
        to=[booking.user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.attach("Pronite Pass.pdf", pdf, 'application/pdf')
    msg.send()

    booking.pass_emailed = True ; booking.save()

    return