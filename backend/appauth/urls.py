from django.urls import path,include
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

app_name = 'appauth'

urlpatterns = [
    # Registration and authentication
    path('register/', 
         views.RegisterView.as_view(), 
         name='register'),
    
    path('login/',
         views.LoginView.as_view(),
         name='login'),
    
       path('login/google/', views.GoogleAuthView.as_view(), name='google-auth'),

    
    path('logout/',
         views.LogoutView.as_view(),
         name='logout'),
    
    # Email verification
    path('verify-email/',
         views.EmailVerificationView.as_view(),
         name='verify-email'),
    
    path('verify-email/resend/',
         views.ResendVerificationView.as_view(),
         name='resend-verification'),
    
    # Password management
    path('password/reset/',
         views.PasswordResetRequestView.as_view(),
         name='password-reset-request'),
    
    path('password/reset/confirm/',
         views.PasswordResetConfirmView.as_view(),
         name='password-reset-confirm'),
    
    path('password/change/',
         views.PasswordChangeView.as_view(),
         name='password-change'),
    
    # User profile
    path('profile/',
         views.UserProfileView.as_view(),
         name='profile'),
]

# Add support for format suffixes (e.g., .json)
# urlpatterns = format_suffix_patterns(urlpatterns)