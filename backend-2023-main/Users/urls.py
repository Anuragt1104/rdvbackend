from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import *

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
	path('login/', LoginView.as_view(), name="login"),
	path('login/admin/', LoginAdminView.as_view(), name="login_admin"),
    path('forgot/send/', ForgotPasswordSendOTPView.as_view(), name="forgot-password-send-otp"),
    path('forgot/verify/', ForgotPasswordVerifyOTPView.as_view(), name="forgot-password-verify-otp"),
    path('reset/', ResetPasswordView.as_view(), name="reset-password"),
    path('profile/', GetProfileView.as_view(), name="get-profile"),
    path('update_pfp/', UpdateProfilePhotoView.as_view(), name="update-pfp"),
    path('fetch_colleges/', FetchCollegesView.as_view(), name='fetch-colleges'),
    path('preregister/', PreRegisterView.as_view(), name='pre-register'),
    path('verify/', VerifyView.as_view(), name='verify'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    path('update_college_name/', UpdateCollegeNameView.as_view(), name='update_college_name'),
]