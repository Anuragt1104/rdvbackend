from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import auth
from .models import *
from .tasks import *

# Create your views here.

def mailer(request):
    if not request.user.is_authenticated:
        return redirect('mailer_login')
    if not request.user.is_staff:
        auth.logout(request)
        return redirect('mailer_login')
    if request.method == 'POST':
        subject = request.POST['subject']
        senderId = request.POST['senderId']
        message = request.POST['message']
        datafile = request.FILES['datafile']
        csv_file = datafile.read().decode('utf-8')
        csv_file = csv_file.split('\n')
        firstRow = csv_file[0].split(',')
        if 'Email' not in firstRow[0] or 'Name' not in firstRow[1]:
            return render(request, 'Mailer/mailer.html', {'error': 'Invalid CSV File. Please see the template and try again.'})
        csv_file = csv_file[1:]
        mailCount = len(csv_file)
        if senderId == "null": return render(request, 'Mailer/mailer.html', {'error': 'Please select a sender ID'})
        mail = Mail.objects.create(createdBy=request.user, subject=subject, message=message, mailCount=mailCount, data=datafile, senderId=senderId)
        if 'attachment' in request.FILES:
            mail.attachment = request.FILES['attachment']
            mail.save()
        return redirect('confirm_mail', id=mail.id)
    if 'sent' in request.GET:
        sent = request.GET['sent']
        return render(request, 'Mailer/mailer.html', {'sent': sent})
    return render(request, 'Mailer/mailer.html')

def login(request):
    if request.user.is_authenticated:
        return redirect('mailer')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request=request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('mailer')
        else:
            return render(request, 'Mailer/login.html', {'error': 'Invalid Credentials'})
    return render(request, 'Mailer/login.html')

def confirm_mail(request, id):
    if not request.user.is_authenticated:
        return redirect('mailer_login')
    if not request.user.is_staff:
        auth.logout(request)
        return redirect('mailer_login')
    if not Mail.objects.filter(id=id).exists():
        return redirect('mailer')
    mail = Mail.objects.get(id=id)
    if not mail.createdBy == request.user or mail.sent:
        return redirect('mailer')
    if request.method == 'POST':
        if "abort" in request.POST:
            mail.delete()
            return redirect('/mailer/?sent=False')
        else:
            mail.sent = True ; mail.save()
            mailerSendMail.delay(mail.id)
            return redirect('/mailer/?sent=True')
    return render(request, 'Mailer/confirm_mail.html', {'mail': mail})

def past_mails(request):
    if not request.user.is_authenticated:
        return redirect('mailer_login')
    if not request.user.is_staff:
        auth.logout(request)
        return redirect('mailer_login')
    mails = Mail.objects.all().order_by('-date')
    return render(request, 'Mailer/past_mails.html', {'mails': mails})