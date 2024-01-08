from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import Profile, College, TeamData, FacultyData
from CAP.models import PointsLedger
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Min
from datetime import datetime
from django.db.models.functions import Coalesce
from django.utils import timezone
from Pronite.models import Booking

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ['otp']
                
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['college_name'] = College.objects.get(college_id=data['college_id']).college_name
        data['college_city'] = College.objects.get(college_id=data['college_id']).college_city

        if(data['is_ca']):
            data['rank'] = (
                list(
                    PointsLedger.objects.annotate(last_submission_time=Coalesce(Min('user__submission__datetime_of_submission'), datetime.now()))
                    .order_by('-points', 'last_submission_time')
                    .values_list('user', flat=True)
                ).index(data['id']) + 1
            )
            data['points'] = PointsLedger.objects.get(user=data['id']).points
        
        data['pronites'] = {
            "spectrum": Booking.objects.filter(user__id=data['id'], slot__pronite="S").exists(),
            "kaleidoscope": Booking.objects.filter(user__id=data['id'], slot__pronite="K").exists(),
            "melange": Booking.objects.filter(user__id=data['id'], slot__pronite="M").exists(),
            "dhoom": Booking.objects.filter(user__id=data['id'], slot__pronite="D").exists(),
        }
        
        return data
                
class ProfilePhotoSerializer(serializers.Serializer):
    profile_photo = serializers.ImageField()

    class Meta:
        fields = ("profile_photo")

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ("email")

class OTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, write_only=True)

    class Meta:
        field = ("otp")

    def validate(self, data):
        otp = data.get("otp")
        token = self.context.get("token")

        if token is None:
            print(token)
            raise serializers.ValidationError("Missing data.")

        profile = get_object_or_404(Profile, otp=otp)
        user = User.objects.get(username=profile.rdv_id)

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError("The reset token is invalid")
        
        profile.isVerified = True
        profile.otp = None
        profile.save()

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'rdv_id': user.username,
        }

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        fields = ("email", "password")

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email is None:
            raise serializers.ValidationError("An email address is required to log in.")

        if password is None:
            raise serializers.ValidationError("A password is required to log in.")
        
        if email.endswith('.iitd.ac.in'):
            email = email.split('@')[0].lower() + '@iitd.ac.in'

        user = get_object_or_404(User, email=email)

        if user is None:
            raise serializers.ValidationError("A user with this email and password is not found.")

        if not user.check_password(password):
            raise serializers.ValidationError("A user with this email and password is not found.")
        
        is_ca = False

        if not user.is_staff:
            profile = Profile.objects.get(rdv_id=user.username)
            is_ca = profile.is_ca

            if not profile.isVerified:
                raise serializers.ValidationError("A user with this email and password is not found.")

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'is_staff': user.is_staff,
            'is_ca': is_ca,
        }

class LoginAdminSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        fields = ("email", "password")

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if email is None:
            raise serializers.ValidationError("An email address is required to log in.")

        if password is None:
            raise serializers.ValidationError("A password is required to log in.")

        user = get_object_or_404(User, email=email)

        if user is None:
            raise serializers.ValidationError("A user with this email and password is not found.")

        if not user.check_password(password):
            raise serializers.ValidationError("A user with this email and password is not found.")
        
        is_ca = False

        if not user.is_staff:
            raise serializers.ValidationError("Unauthorized.")

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'is_staff': user.is_staff,
            'is_ca': is_ca,
        }
    
class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = '__all__'

class ProfileRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['rdv_id', 'name', 'email', 'mobile_number', 'college_id']

    def validate(self, data):
        email = data.get('email')
        mobile_number = data.get('mobile_number')

        if email.endswith('@iitd.ac.in'):
            data['college_id'] = 4570
            username = email.split('@')[0].lower()
            if len(username) == 9 and username[:2].isalpha() and username[3:].isdigit():
                data['user_category'] = 'S'
        
        if email.endswith('.iitd.ac.in'):
            data['college_id'] = 4570
            username = email.split('@')[0].lower()
            if len(username) == 9 and username[:2].isalpha() and username[3:].isdigit() and username[3:5] in [str(i) for i in range(10, 24)]:
                data['user_category'] = 'S'
            data['email'] = username + '@iitd.ac.in'
            email = data['email']

        existing_profile = Profile.objects.filter(email=email).first()

        if existing_profile:
            if existing_profile.isVerified:
                raise serializers.ValidationError("A user with that Email already exists.")
            else:
                user = User.objects.get(username=existing_profile.rdv_id)
                if (timezone.now() - user.date_joined).total_seconds() < 600:
                    raise serializers.ValidationError("Please wait for 10 minutes before trying again.")
                user.delete()
                existing_profile.delete()

        if email.endswith("@iitd.ac.in"):
            isTeamMember = TeamData.objects.filter(email=email).exists()
            if isTeamMember:
                memberDet = TeamData.objects.get(email=email)
                data['user_category'] = 'T'
                data['name'] = memberDet.name
            isFacultyMember = FacultyData.objects.filter(email=email).exists()
            if isFacultyMember:
                memberDet = FacultyData.objects.get(email=email)
                data['user_category'] = 'F'
                data['name'] = memberDet.name

        return data
    