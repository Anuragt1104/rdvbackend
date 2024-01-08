from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Admin.permissions import *
from .models import *
from .serializers import *
from .tasks import *
from .permissions import *
from datetime import timedelta
from rest_framework.permissions import 	IsAuthenticated, IsAdminUser
from Users.models import Profile
from .encryption import *
from django.contrib.auth.models import User
from Users.views import generate_rdv_id
import re, os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

# Create your views here.

def generate_ticket_id(slot, profile):
    return f"{slot.pronite}-{profile.rdv_id}"

def is_eligible(profile, pronite):

    user_cat_map = {
        "S": "IITD Student",
        "F": "IITD Faculty and Staff",
        "E": "External",
        "T": "Team",
        "X": "Others"
    }

    pronite_map = {
        "S": "Spectrum",
        "K": "Kaleidoscope",
        "M": "Melange",
        "D": "Dhoom"
    }
    
    if not Slot.objects.filter(pronite=pronite, eligibility=profile.user_category, start_time__lte=timezone.now(), end_time__gte=timezone.now()).exists():
        return False, f"No active slot for user category {user_cat_map[profile.user_category]}."
    slot = Slot.objects.get(pronite=pronite, eligibility=profile.user_category, start_time__lte=timezone.now(), end_time__gte=timezone.now())
    if slot.booked >= slot.capacity:
        return False, f"Slot capacity exhausted."
    if Booking.objects.filter(user=profile, slot__pronite=pronite).exists():
        return False, f"Already booked for pronite {pronite_map[pronite]}."
    if profile.user_category not in 'FTX':
        if profile.user_category == 'S':
            connected_pronites = {"S": "K", "K": "S", "M": "D", "D": "M"}
            if Booking.objects.filter(user=profile, slot__pronite=connected_pronites[pronite]).exists():
                return False, f"Already booked for pronite {pronite_map[connected_pronites[pronite]]}."
        else:
            if Booking.objects.filter(user=profile).exists():
                return False, f"Only allowed 1 pronite in RendezvousX."
    if profile.BlockedFromPronite:
        return False, "User blocked from Pronite."
    return True, slot.id

class SlotView(APIView):

    permission_classes = [IsShashank]

    def get(self, request):
        upcomingSlots = Slot.objects.filter(end_time__gte=timezone.now()).order_by('start_time').values()
        pastSlots = Slot.objects.filter(end_time__lt=timezone.now()).order_by('-start_time').values()
        slots = []
        for slot in upcomingSlots:
            slot['date'] = slot['start_time'].strftime("%d %b %Y")
            slot['start_time'] = (slot['start_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slot['end_time'] = (slot['end_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            if slot['exhaust_time']:
                slot['exhaust_time'] = (slot['exhaust_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slots.append(slot)
        for slot in pastSlots:
            slot['date'] = slot['start_time'].strftime("%d %b %Y")
            slot['start_time'] = (slot['start_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slot['end_time'] = (slot['end_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            if slot['exhaust_time']:
                slot['exhaust_time'] = (slot['exhaust_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slot['past'] = True
            slots.append(slot)
        return Response(slots, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SlotSerializer(data={"pronite": request.data.get("pronite"), "start_time": request.data.get("start_time"), "end_time": request.data.get("end_time"), "capacity": request.data.get("capacity"), "eligibility": request.data.get("eligibility")})
        serializer.is_valid(raise_exception=True)

        pronite = serializer.data.get("pronite")
        start_time = serializer.data.get("start_time")
        end_time = serializer.data.get("end_time")
        capacity = serializer.data.get("capacity")
        eligibility = serializer.data.get("eligibility")

        slot = Slot.objects.create(pronite=pronite, start_time=start_time, end_time=end_time, capacity=capacity, eligibility=eligibility)
        slot.save()

        Log.objects.create(user=request.user, action=f"Created slot {slot.pronite}{slot.id}")

        return Response({'message': 'Slot created successfully.'}, status=status.HTTP_201_CREATED)
    
    def delete(self, request, id):
        if not Slot.objects.filter(id=id).exists():
            return Response({'detail': 'Slot does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        slot = Slot.objects.get(id=id)
        if slot.booked > 0:
            return Response({'detail': 'Slot has bookings.'}, status=status.HTTP_400_BAD_REQUEST)
        if slot.end_time < timezone.now():
            return Response({'detail': 'Slot has already ended.'}, status=status.HTTP_400_BAD_REQUEST)
        if slot.start_time < timezone.now():
            return Response({'detail': 'Slot has already started.'}, status=status.HTTP_400_BAD_REQUEST)
        slot.delete()

        Log.objects.create(user=request.user, action=f"Deleted slot {slot.pronite}{slot.id}")

        return Response({'message': 'Slot deleted successfully.'}, status=status.HTTP_200_OK)

class ProniteView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        res = { "S": False, "K": False, "M": False, "D": False }
        profile = get_object_or_404(Profile, rdv_id = request.user.username)
        active_slot = Slot.objects.filter(start_time__lte=timezone.now(), end_time__gte=timezone.now(), eligibility=profile.user_category)
        if not active_slot.exists():
            return Response(res, status=status.HTTP_200_OK)
        active_slot = active_slot[0]
        res[active_slot.pronite] = True
        return Response(res, status=status.HTTP_200_OK)

class ScanSlotView(APIView):

    permission_classes = [IsShashank]

    def get(self, request):
        upcomingSlots = ScanningSchedule.objects.filter(end_time__gte=timezone.now()).order_by('start_time').values()
        pastSlots = ScanningSchedule.objects.filter(end_time__lt=timezone.now()).order_by('-start_time').values()
        slots = []
        for slot in upcomingSlots:
            slot['date'] = slot['start_time'].strftime("%d %b %Y")
            slot['start_time'] = (slot['start_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slot['end_time'] = (slot['end_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slots.append(slot)
        for slot in pastSlots:
            slot['date'] = slot['start_time'].strftime("%d %b %Y")
            slot['start_time'] = (slot['start_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slot['end_time'] = (slot['end_time']+timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            slot['past'] = True
            slots.append(slot)
        return Response(slots, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ScanSlotSerializer(data={"pronite": request.data.get("pronite"), "start_time": request.data.get("start_time"), "end_time": request.data.get("end_time")})
        serializer.is_valid(raise_exception=True)

        pronite = serializer.data.get("pronite")
        start_time = serializer.data.get("start_time")
        end_time = serializer.data.get("end_time")

        slot = ScanningSchedule.objects.create(pronite=pronite, start_time=start_time, end_time=end_time)
        slot.save()

        Log.objects.create(user=request.user, action=f"Created scanning slot for pronite {slot.pronite}")

        return Response({'message': 'Slot created successfully.'}, status=status.HTTP_201_CREATED)
    
    def delete(self, request, id):
        if not ScanningSchedule.objects.filter(id=id).exists():
            return Response({'detail': 'Slot does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        slot = ScanningSchedule.objects.get(id=id)
        if slot.admissions > 0:
            return Response({'detail': 'Slot has admissions.'}, status=status.HTTP_400_BAD_REQUEST)
        if slot.end_time < timezone.now():
            return Response({'detail': 'Slot has already ended.'}, status=status.HTTP_400_BAD_REQUEST)
        if slot.start_time < timezone.now():
            return Response({'detail': 'Slot has already started.'}, status=status.HTTP_400_BAD_REQUEST)
        slot.delete()
        
        Log.objects.create(user=request.user, action=f"Deleted scanning slot for pronite {slot.pronite}")

        return Response({'message': 'Slot deleted successfully.'}, status=status.HTTP_200_OK)
    
class BookingView(APIView):

    permission_classes = [IsAuthenticated, IsCaptchaVerified]

    def post(self, request):
        try: profile = Profile.objects.get(rdv_id=request.user.username)
        except: return Response({'detail': 'User profile does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get("pronite"):
            return Response({'detail': 'Pronite not specified.'}, status=status.HTTP_400_BAD_REQUEST)
        pronite = request.data.get("pronite")
        if pronite not in "SKMD": return Response({'detail': 'Invalid pronite.'}, status=status.HTTP_400_BAD_REQUEST)
        eligible, response = is_eligible(profile, pronite)
        if not eligible:
            return Response({'detail': response}, status=status.HTTP_400_BAD_REQUEST)
        slot = Slot.objects.get(id=response)
        ticket_id = generate_ticket_id(slot, profile)
        Booking.objects.create(user=profile, slot=slot, ticket_id=ticket_id)
        slot.booked += 1 ; slot.save()
        return Response({'ticket_id': ticket_id, 'message': 'Congratulations! Your booking has been confirmed successfully. You can expect to receive your event pass via email approximately 6 hours prior to the start of the pronite.'}, status=status.HTTP_200_OK)

class SendPassView(APIView):

    permission_classes = [IsShashank]

    def post(self, request):
        pronite = request.data.get("pronite")
        if pronite not in "SKMD": return Response({'detail': 'Invalid pronite.'}, status=status.HTTP_400_BAD_REQUEST)

        if not Booking.objects.filter(slot__pronite=pronite, pass_emailed=False).exists():
            return Response({'detail': 'No unsent passes for this pronite.'}, status=status.HTTP_400_BAD_REQUEST)
        
        send_passes.delay(pronite)

        Log.objects.create(user=request.user, action=f"Sent passes for pronite {pronite}")

        return Response({'detail': 'Passes are being sent to attendees.'}, status=status.HTTP_200_OK)

class CreatePassbyIDView(APIView):
    
    permission_classes = [IsShashank]
    
    def post(self, request):
        rdv_id = request.data.get('rdv_id')

        if not request.data.get("pronite"):
            return Response({'detail': 'Pronite not specified.'}, status=status.HTTP_400_BAD_REQUEST)
        
        pronite = request.data.get('pronite')
        if pronite not in "SKMD": return Response({'detail': 'Invalid pronite.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_profile = Profile.objects.get(rdv_id=rdv_id)
        except Profile.DoesNotExist:
            return Response({'detail': 'User profile does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        
        existing_booking = Booking.objects.filter(user=user_profile, slot__pronite=pronite).first()
        if existing_booking:
            return Response({'detail': "Already Booked"}, status=status.HTTP_208_ALREADY_REPORTED)

        slot = Slot.objects.filter(eligibility="X", pronite=pronite)
        if not slot: slot = Slot.objects.create(eligibility="X", pronite=pronite, start_time=timezone.now(), end_time=timezone.now(), capacity=10000)
        else: slot = slot[0]

        ticket_id = generate_ticket_id(slot, user_profile)
        booking = Booking.objects.create(user=user_profile, ticket_id=ticket_id, slot=slot)
        slot.booked += 1 ; slot.save()

        send_pass.delay(booking.id)

        Log.objects.create(user=request.user, action=f"Created pass for user {user_profile.rdv_id} for pronite {pronite}")
        
        return Response({'detail': 'Pass Sent Successfully!'}, status=status.HTTP_200_OK)
    
class CreatePassbyEmailView(APIView):

    permission_classes = [IsShashank]
    
    def post(self, request):
        email = request.data.get('email')

        if not request.data.get("pronite"):
            return Response({'detail': 'Pronite not specified.'}, status=status.HTTP_400_BAD_REQUEST)
        
        pronite = request.data.get('pronite')
        if pronite not in "SKMD": return Response({'detail': 'Invalid pronite.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_profile = Profile.objects.get(email=email)
        except Profile.DoesNotExist:
            user_profile = Profile.objects.create(
                    rdv_id=generate_rdv_id(),
                    email=email,
                    name='RDV User',
                    college_id='34350',
                    user_category='X',
                    isVerified=True
                )
            User.objects.create(username=user_profile.rdv_id, email=email)   
        
        existing_booking = Booking.objects.filter(user=user_profile, slot__pronite=pronite).first()
        if existing_booking:
            return Response({'detail': "Already Booked"}, status=status.HTTP_208_ALREADY_REPORTED)

        slot = Slot.objects.filter(eligibility="X", pronite=pronite)
        if not slot: slot = Slot.objects.create(eligibility="X", pronite=pronite, start_time=timezone.now(), end_time=timezone.now(), capacity=10000)
        else: slot = slot[0]

        ticket_id = generate_ticket_id(slot, user_profile)
        booking = Booking.objects.create(user=user_profile, ticket_id=ticket_id, slot=slot)
        slot.booked += 1 ; slot.save()
        
        send_pass.delay(booking.id)

        Log.objects.create(user=request.user, action=f"Created pass for user {user_profile.email} for pronite {pronite}")
        
        return Response({'detail': 'Pass Sent Successfully!'}, status=status.HTTP_200_OK)
    
class CancelPassView(APIView):

    permission_classes = [IsShashank]
    
    def post(self, request):
        ticket_id = request.data.get('ticket_id')
        if not ticket_id:
            return Response({'detail': 'Ticket ID not specified.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            booking = Booking.objects.get(ticket_id=ticket_id)
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if booking.cancelled:
            return Response({'detail': 'Booking already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if booking.admitted:
            return Response({'detail': 'Participant already admitted.'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.cancelled = True
        booking.save()

        Log.objects.create(user=request.user, action=f"Cancelled pass for user {booking.user.rdv_id} for pronite {booking.slot.pronite}")

        return Response({'detail': 'Booking cancelled successfully.'}, status=status.HTTP_200_OK)
    
class BlockUserView(APIView):

    permission_classes = [IsShashank]
    
    def post(self, request):
        email = request.data.get('email')

        try:
            user_profile = Profile.objects.get(email=email)
        except Profile.DoesNotExist:
            user_profile = Profile.objects.create(
                    rdv_id=generate_rdv_id(),
                    email=email,
                    name='RDV User',
                    college_id='34350',
                    user_category='X',
                    isVerified=True
                )
            User.objects.create(username=user_profile.rdv_id, email=email) 
        
        user_profile.BlockedFromPronite = True
        user_profile.save()

        unadmitted_bookings = Booking.objects.filter(user=user_profile, admitted=False)
        for booking in unadmitted_bookings:
            booking.cancelled = True ; booking.save()

        Log.objects.create(user=request.user, action=f"Blocked user {user_profile.email} from pronite")
        
        return Response({'detail': 'User blocked successfully.'}, status=status.HTTP_200_OK)
    
class ScanPassView(APIView):

    permission_classes = [IsAdminUser]

    def post(self, request):
        pass_data = request.data.get('pass_data')

        try: decrypted_pass_data = decrypt(pass_data, os.environ['ENCRYPTION_KEY'])
        except: return Response({'success': False, 'detail': 'Invalid Pass'}, status=status.HTTP_400_BAD_REQUEST)

        ticket_id = re.search(r'ticket_id=([^&]+)', decrypted_pass_data).group(1)

        try:
            booking = Booking.objects.get(ticket_id=ticket_id)
        except Booking.DoesNotExist:
            return Response({
                'success': False,
                'detail': 'Invalid Pass'
            }, status=status.HTTP_400_BAD_REQUEST)

        pronite = booking.slot.pronite
        scanning_schedules = ScanningSchedule.objects.filter(pronite=pronite)
        if not scanning_schedules.exists():
            return Response({
                'success': False,
                'detail': f'Scanning not allowed for Pronite `{pronite}` at the moment.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        for scanning_schedule in scanning_schedules:
            if scanning_schedule.start_time <= timezone.now() <= scanning_schedule.end_time:
                break
        else:
            return Response({
                'success': False,
                'detail': f'Scanning not allowed for Pronite `{pronite}` at the moment.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if booking.cancelled:
            return Response({'detail': 'Pass cancelled by admin.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if booking.admitted:
            return Response({'success': False, 'detail': f'Participant already admitted at {(booking.admission_time + timedelta(hours=5, minutes=30)).strftime("%I:%M %p")}'}, status=status.HTTP_400_BAD_REQUEST)

        booking.admission_time = timezone.now() ; booking.admitted = True ; booking.save()

        scanning_schedule.admissions += 1 ; scanning_schedule.save()

        user_name = booking.user.name
        rdv_id = booking.user.rdv_id
        user_category = booking.user.user_category

        u_cat_map = {
            'S': 'IITD Student',
            'F': 'IITD Faculty and Staff',
            'T': 'Team',
            'E': 'External',
            'X': 'Others'
        }

        Log.objects.create(user=request.user, action=f"Admitted user {booking.user.rdv_id} for pronite {booking.slot.pronite}")

        return Response({
            'success': True, 
            'detail': 'Pass Validated Successfully',
            'name': user_name,
            'rdv_id': rdv_id,
            'pass_no': ticket_id,
            'pass_type': u_cat_map[user_category]
        }, status=status.HTTP_200_OK)

class LogView(APIView):

    permission_classes = [IsShashank]

    def get(self, request):
        logs = Log.objects.all().order_by('-time').values()
        users = User.objects.filter(is_staff=True)
        u_list = {
            user.id: user.username
            for user in users
        }
        for log in logs:
            log['user'] = u_list[log['user_id']]
            log['time'] = (log['time']+timedelta(hours=5, minutes=30)).strftime("%d %b %Y %I:%M %p")
        return Response(logs, status=status.HTTP_200_OK)
    
class DownloadPassView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        pronite = request.GET.get('pronite')
        if pronite not in "SKMD": return Response({'detail': 'Invalid pronite.'}, status=status.HTTP_400_BAD_REQUEST)

        profile = get_object_or_404(Profile, rdv_id = request.user.username)

        if not Booking.objects.filter(user=profile, slot__pronite=pronite).exists():
            return Response({'detail': 'No pass found.'}, status=status.HTTP_400_BAD_REQUEST)
        
        booking = Booking.objects.get(user=profile, slot__pronite=pronite)

        enc_data = encrypt(f"ticket_id={booking.ticket_id}", os.environ['ENCRYPTION_KEY'])

        pass_pdf = generate_pronite_pdf(profile.name, profile.rdv_id, pronite, enc_data)

        response = HttpResponse(pass_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Pronite Pass.pdf"'

        return response