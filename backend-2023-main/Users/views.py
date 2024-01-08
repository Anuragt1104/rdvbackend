from django.shortcuts import get_object_or_404
import random
import requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import 	IsAuthenticated

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth.models import User
from .models import Profile
from .serializers import *
from .tasks import *

from Pronite.permissions import IsCaptchaVerified

from django.contrib.auth.tokens import PasswordResetTokenGenerator

def generate_rdv_id(name="X"):
    latest_profile = Profile.objects.all().order_by('id').last()
    if not latest_profile:
        return 'A00001'
    id_ = latest_profile.id
    convert_to_hex = (id_ + 1) % 65536
    rand_ = random.randint(0, 15)
    rdv_id = name[0].upper() + hex(rand_)[2:].upper() + hex(convert_to_hex)[2:].upper().zfill(4)
    return rdv_id

class ForgotPasswordSendOTPView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        email = serializer.data["email"]

        user = get_object_or_404(User, email=email)

        token = PasswordResetTokenGenerator().make_token(user)

        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        profile = get_object_or_404(Profile, rdv_id=user.username)
        profile.otp = otp
        profile.save()

        send_otp.delay(email, otp)

        return Response({'token': token})

class ForgotPasswordVerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPSerializer(data={'otp': request.data.get('otp')}, context={'token': request.data.get('token')})

        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)

class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        new_password = request.data.get('new_password')

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully'})

class GetProfileView(APIView):
    def get(self, request):
        user = get_object_or_404(Profile, rdv_id = request.user.username)
        serializer = ProfileSerializer(user)
        return Response(serializer.data)
    
class UpdateProfilePhotoView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        user = get_object_or_404(Profile, rdv_id = request.user.username)
        
        serializer = ProfilePhotoSerializer(data=request.data)
        
        if serializer.is_valid():
            profile_photo = serializer.validated_data['profile_photo']
            user.profile_photo = profile_photo
            user.save()
            
            return Response({'message': 'Profile photo updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class LoginView(APIView):

    permission_classes = [IsCaptchaVerified]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)
        
class LoginAdminView(APIView):

    def post(self, request):
        serializer = LoginAdminSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)

class FetchCollegesView(APIView):
    def get(self, request):
        college_state = request.GET.get('state')
        college_city = request.GET.get('city')

        if college_city:
            colleges = College.objects.filter(college_state=college_state, college_city=college_city)

            serializer = CollegeSerializer(colleges, many=True)
            return Response(serializer.data)
        else:
            colleges = College.objects.filter(college_state=college_state).values('college_city').distinct()

            college_list = [college['college_city'] for college in colleges]
            return Response(college_list)
        
class PreRegisterView(APIView):

    permission_classes = [IsCaptchaVerified]

    def post(self, request):
        password = request.data.get('password')

        rdv_id = generate_rdv_id(request.data.get('name'))
        serializer = ProfileRegisterSerializer(data={'rdv_id': rdv_id, 'name': request.data.get('name'), 'email': request.data.get('email'), 'mobile_number': request.data.get('mobile_number'), 'college_id': request.data.get('college_id')})
        
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user = User.objects.create_user(username=rdv_id, email=serializer.data['email'], password=password)

        token = PasswordResetTokenGenerator().make_token(user)

        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        profile = get_object_or_404(Profile, rdv_id=user.username)
        profile.otp = otp
        profile.save()

        send_otp.delay(serializer.data['email'], otp)

        return Response({"rdv_id": rdv_id, "token": token})
    
class VerifyView(APIView):
    def post(self, request):
        serializer = OTPSerializer(data={'otp': request.data.get('otp')}, context={'token': request.data.get('token')})

        serializer.is_valid(raise_exception=True)

        profile = get_object_or_404(Profile, rdv_id=serializer.validated_data['rdv_id'])
        profile.isVerified = True
        profile.save()

        send_welcome_email.delay(profile.email)

        return Response({"rdv_id": profile.rdv_id, "message": "Account verified successfully"})

class GoogleAuthView(APIView):

    def post(self, request):
        access_token = request.data.get('access_token')
        google_api_url = f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}'
        response = requests.get(google_api_url)

        if response.status_code == 200:
            google_user_data = response.json()
            email = google_user_data.get('email')
            name = google_user_data.get('name')

            try:
                profile = Profile.objects.get(email=email)
                profile.isVerified = True
                profile.name = name
                profile.save()

                user, created = User.objects.get_or_create(username=profile.rdv_id, email=email)
                if created:
                    user.set_unusable_password()
                    user.save()

                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'is_staff': user.is_staff,
                }, status=status.HTTP_200_OK)

            except Profile.DoesNotExist:
                profile = Profile.objects.create(
                    rdv_id=generate_rdv_id(name),
                    email=email,
                    name=name,
                    isVerified=True,
                    mobile_number=None,
                    college_id='34350'
                )

                user = User.objects.create(username=profile.rdv_id, email=email)
                user.set_unusable_password()
                user.save()

                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'is_staff': user.is_staff,
                }, status=status.HTTP_200_OK)

        else:
            return Response({'error': 'Failed to fetch user data from Google API'}, status=status.HTTP_400_BAD_REQUEST)

class UpdateCollegeNameView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = get_object_or_404(Profile, rdv_id = request.user.username)
        if user.user_category in "SFT":
            return Response({'message': 'You are not allowed to change your college name'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('manual_set'):
            user.college_name = request.data.get('college_name')
        if not request.data.get('college_id').isdigit():
            return Response({'message': 'College ID must be a number'}, status=status.HTTP_400_BAD_REQUEST)
        if not College.objects.filter(college_id=request.data.get('college_id')).exists():
            return Response({'message': 'College ID does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        user.college_id = request.data.get('college_id')
        user.save()
        return Response({'message': 'College name updated successfully'})