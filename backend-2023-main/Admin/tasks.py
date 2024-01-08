from celery import shared_task
from django.core.mail import send_mail
from CAP.models import Notification

@shared_task()
def send_notification(notif_id):
    try:
        notif = Notification.objects.get(id=notif_id)
    except: return
    send_mail(
        subject=notif.subject,
        message=notif.message,
        from_email="Rendezvous Notifications <notifications@rendezvousiitd.com>",
        recipient_list=["campus-ambassadors@rendezvousiitd.com"],
    )