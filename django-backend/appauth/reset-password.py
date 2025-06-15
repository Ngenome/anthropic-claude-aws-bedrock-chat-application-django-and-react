# # from stream_chat import StreamChat
# from datetime import datetime
# # from api.emails.PasswordResetEmail import CreatePasswordResetOtpEmail

# # from api.emails.SuccessfulPasswordReset import SuccessfulPasswordResetHtmlEmail
# # from ..serializers import *
# from rest_framework.response import Response
# from rest_framework import status
# from ..models import *

# from django.contrib.auth.models import User
# from django.conf import settings
# from django.core.mail import send_mail
# from rest_framework.decorators import api_view
# import pyotp
# from api.emails.elements import logo, styles
# from api.emails.elements import OtpMessage, SuccessfulPasswordResetEmail, logo, styles


# @api_view(['POST'])
# def request_reset_password(request):
#     """reset_password with email, OTP and new password"""
#     data = request.data
#     print(data["email"])
#     try:
#         user = User.objects.get(email=data['email'])
#     except:
#         return Response({"detail": "Sorry we couldnt find a user with such an email"}, status=status.HTTP_404_NOT_FOUND)
#     secret = pyotp.random_base32()
#     totp = pyotp.TOTP(secret).now()
#     try:
#         ds = UserOTP.objects.get(user=user)
#     except Exception as e:
#         ds = UserOTP.objects.create(user=user, otp=totp)
#     timedelta = datetime.now()-ds.timestamp.replace(tzinfo=None)
#     if timedelta.seconds < 120:
#         print(timedelta.seconds)
#         return Response({"detail": "Please wait for 120 seconds before requesting another otp"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
#     ds.otp = totp
#     ds.save()

#     html_email = CreatePasswordResetOtpEmail(totp, user.username)
#     plain_text_email = OtpMessage(user.username, totp, False)
#     email_from = settings.EMAIL_HOST_USER
#     recipient_list = [data['email']]
#     try:
#         send_mail("Password reset OTP", plain_text_email,
#                   email_from, recipient_list, html_message=html_email)
#         return Response("sent a Password reset Email to the email you entered", status=status.HTTP_202_ACCEPTED)
#     except Exception as e:
#         return Response({"detail": "Trouble sending the email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['POST'])
# def verify_otp(request):
#     """reset_password with email, OTP and new password"""
#     data = request.data
#     if data['email'] != '':
#         try:
#             user = User.objects.get(email=data['email'])
#             saved_otp = UserOTP.objects.get(user=user).otp
#             if user.is_active:
#                 # Check if otp is valid
#                 if data['otp'] == saved_otp:
#                     return Response({"detail": "Otp has been verified"}, status=status.HTTP_202_ACCEPTED)
#         except Exception as e:
#             return Response({"detail": "Sorry we couldnt find a user with such an email"}, status=status.HTTP_404_NOT_FOUND)
#     else:
#        return Response({"detail": "email field is needed"},
#                        status=status.HTTP_206_PARTIAL_CONTENT)


# @api_view(['POST'])
# def reset_password(request):
#     """reset_password with email, OTP and new password"""
#     data = request.data
#     if data['email'] != '':
#         try:
#             user = User.objects.get(email=data['email'])
#         except Exception as e:
#             return Response({"detail": "Could not find such an email address", "error": e.__str__()}, status=status.HTTP_400_BAD_REQUEST)
#         email_otp = data['otp']
#         new_password = data['new_password']
#         saved_otp = UserOTP.objects.get(user=user).otp
#         saved_otp_object = UserOTP.objects.get(user=user)
#         if user.is_active:
#             # Check if otp is valid
#             if data['otp'] == saved_otp:
#                 if new_password != '':
#                     # Change Password
#                     user.set_password(data['new_password'])
#                     user.save()
#                     saved_otp_object.delete()
#                     # Here user otp will also be changed on save automatically
#                     email_from = settings.EMAIL_HOST_USER
#                     recipient_list = [user.email]
#                     try:
#                         send_mail("Successfully reset your password", f"Hi {user.username}, You Successfully reset your password",
#                                   email_from, recipient_list, html_message=SuccessfulPasswordResetHtmlEmail(user.username))
#                     except Exception as e:
#                         print(e)
#                     return Response({"detail": 'Successfully changed your password '}, status=status.HTTP_201_CREATED)
#                 else:
#                     message = {
#                         'detail': 'Password cant be empty'}
#                     return Response(message, status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 message = {
#                     'detail': 'OTP did not match'}
#                 return Response(message, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             message = {
#                 'detail': 'Something went wrong'}
#             return Response(message, status=status.HTTP_400_BAD_REQUEST)
