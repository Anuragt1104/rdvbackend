from django.shortcuts import render, redirect
from django.contrib import auth
from Users.models import *
from CAP.models import PointsLedger
from Events.models import *
from Users.views import generate_rdv_id
from django.contrib.auth.models import User
import random
from .tasks import send_ca_onboarding

def generate_random_password():
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    password = ''
    for _ in range(8):
        password += random.choice(chars)
    return password

def generate_ca_id(name="X"):
    last_ca = Profile.objects.filter(is_ca=True).order_by('id').last()
    if not last_ca:
        return 'A001'
    id_ = int(last_ca.ca_id[2:], 16) % 256
    rand_ = random.randint(0, 15)
    rand2_ = random.randint(0, 15)
    ca_id = hex(rand2_)[2:].upper() + name[0].upper() + hex(rand_)[2:].upper() + hex(id_ + 1)[2:].upper().zfill(2)
    return ca_id

def norway(request):
    if not request.user.is_authenticated:
        return redirect('norway_login')
    if not request.user.is_staff:
        auth.logout(request)
        return redirect('norway_login')
    return render(request, 'Norway/services.html')

def norway_login(request):
    if request.user.is_authenticated:
        return redirect('norway')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request=request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('norway')
        else:
            return render(request, 'Norway/login.html', {'error': 'Invalid Credentials'})
    return render(request, 'Norway/login.html')

def add_ca(request):
    if not request.user.is_authenticated:
        return redirect('norway_login')
    if not request.user.is_staff:
        auth.logout(request)
        return redirect('norway_login')
    state_list = ["Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Delhi/U.T./Other","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Orissa","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal"]
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        college_id = request.POST['college_id']
        instagram = request.POST['instagram']
        linkedin = request.POST['linkedin']
        profile = None
        if not College.objects.filter(college_id=college_id).exists():
            return render(request, 'Norway/add_ca.html', {'error': 'Invalid College ID'})
        if Profile.objects.filter(email=email).exists():
            profile = Profile.objects.get(email=email)
            if profile.is_ca:
                return render(request, 'Norway/add_ca.html', {'error': 'CA already exists'})
            elif not profile.isVerified:
                user = User.objects.get(username=profile.rdv_id)
                profile.delete() ; user.delete() ; profile = None
        if Profile.objects.filter(mobile_number=phone).exists():
            profile = Profile.objects.get(mobile_number=phone)
            if profile.is_ca:
                return render(request, 'Norway/add_ca.html', {'error': 'CA already exists'})
            elif not profile.isVerified:
                user = User.objects.get(username=profile.rdv_id)
                profile.delete() ; user.delete() ; profile = None
        if profile is None:
            rdv_id = generate_rdv_id(name)
            ca_id = generate_ca_id(name)
            password = generate_random_password()
            user = User.objects.create_user(username=rdv_id, password=password, email=email)    
            profile = Profile.objects.create(rdv_id=rdv_id, name=name, email=email, mobile_number=phone, college_id=college_id, isVerified=True, is_ca=True, ca_id=ca_id, instagram_link=instagram, linkedin_link=linkedin)
        else:
            ca_id = generate_ca_id(name)
            password = generate_random_password()
            user = User.objects.get(username=profile.rdv_id)
            user.set_password(password) ; user.save()
            profile.name = name ; profile.college_id = college_id ; profile.email = email ; profile.mobile_number = phone ; profile.isVerified = True
            profile.is_ca = True ; profile.ca_id = ca_id ; profile.instagram_link = instagram ; profile.linkedin_link = linkedin ; profile.save()
        
        PointsLedger.objects.create(user=profile, points=0)

        data = {
            'name': name,
            'email': email,
            'password': password,
            'date': user.date_joined.strftime('%d %B, %Y'),
            'ca_id': ca_id
        }

        send_ca_onboarding.delay(data)
        
        success = 'CA Added Successfully'
    return render(request, 'Norway/add_ca.html', locals())

def add_event(request):
    if not request.user.is_authenticated:
        return redirect('norway_login')
    if not request.user.is_staff:
        auth.logout(request)
        return redirect('norway_login')

    if request.method == 'POST':
        name = request.POST['title']
        description = request.POST['description']
        prizes = request.POST['prizes']
        type = request.POST['type']
        location = request.POST['location']
        application_deadline = request.POST['deadline']
        event_date = request.POST['date']
        event_time = request.POST['time']
        team_size = request.POST['team-size']
        registration_link = request.POST['registration-link']
        rulebook_link = request.POST['rulebook']
        poster = request.FILES['poster']
        event_date_time = event_date + ' ' + event_time
        if Event.objects.filter(name=name).exists():
            Event.objects.get(name=name).delete()
        event = Event.objects.create(name=name, description=description, prizes=prizes, type=type, location=location, application_deadline=application_deadline, event_date_time=event_date_time, team_size=team_size, registration_link=registration_link, rulebook_link=rulebook_link, poster=poster)
        tags = request.POST['tags'].split(',')
        for tag in tags:
            if not Tag.objects.filter(name=tag).exists():
                Tag.objects.create(name=tag)
            event.tags.add(Tag.objects.get(name=tag))
        event.save()
        success = 'Event Added Successfully'

    tags = Tag.objects.all().order_by('name').values('name')

    return render(request, 'Norway/add_event.html', locals())