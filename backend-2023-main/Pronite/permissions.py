import os, requests
from rest_framework.permissions import BasePermission

class IsCaptchaVerified(BasePermission):
    def has_permission(self, request, view):
        captcha_response = request.META.get('HTTP_CAPTCHA_RESPONSE')
        captcha_secret = os.environ['CAPTCHA_SECRET_KEY']
        response = requests.get(f"https://www.google.com/recaptcha/api/siteverify?secret={captcha_secret}&response={captcha_response}")
        if response.status_code == 200:
            response = response.json()
            if response['success']:
                return True
        return False
