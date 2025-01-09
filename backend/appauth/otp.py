
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
import json
import datetime
from .serializers import *
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from knox.models import AuthToken
from rest_framework import status
from rest_framework.response import Response
import pyotp

UserSerializer = AppUserSerializer

from .models import *


def send_sms():
    pass


def sendOtp(user, userData):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret).now()

    try:
        user_otp = UserOTP.objects.create(
            user=user,
            otp=totp
        )
        user_otp.save()
        saved_otp = True

        try:
            resp = send_sms(
                mobile=userData.phone.as_e164,
                message=f"Your Jobzy OTP is {user_otp.otp}. It expires in 5 minutes."
            )
            print(resp)
        except Exception as e:
            print(
                f"Error sending the otp: {e.__str__()}"
            )

    except Exception as e:
        print(
            f"Error saving the user otp: {e.__str__()}"
        )


def verifyOtp(userID, otp):
    try:
        user = User.objects.get(id=userID)
        user_otp = UserOTP.objects.get(user=user)
        if user_otp.otp == otp:
            return True
        else:
            return False
    except Exception as e:
        print(
            f"Error verifying the otp: {e.__str__()}"
        )
        return False


@api_view(['POST'])
def RequestOTPForLoginWithPhoneNumber(request):

    data = request.data
    print(data["phone"])
    try:
        user = AppUser.objects.get(
            phone=data["phone"]
        )

    except:
        return Response({"detail": "Sorry we couldnt find a user with such an phone number"}, status=status.HTTP_404_NOT_FOUND)
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret).now()
    try:
        ds = UserOTP.objects.get(user=user)
        timedelta = datetime.datetime.now()-ds.updated_at.replace(tzinfo=None)
        if timedelta.seconds < 180:
            print(f"seconds {timedelta.seconds}")
            return Response({"detail": "Too many requests: Please wait for 180 seconds  before requesting another otp"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        else:
            ds.otp = totp
            ds.save()
    except Exception as e:
        print(
            f"Error saving the user otp: {e.__str__()}"
        )
        ds = UserOTP.objects.create(user=user, otp=totp)
        ds.save()

    try:
        resp = send_sms(
            mobile=data["phone"],
            message=f"Your Jobzy OTP is {ds.otp}. It expires in 5 minutes."
        )
        resp = json.loads(resp)
        print(resp)
        if resp[0]['status_code'] == '1000':
            return Response({
                "detail": "OTP sent successfully",
            }, status=status.HTTP_202_ACCEPTED)
        else:
            print(resp)
            return Response({"detail": "Trouble sending the sms"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print(
            f"Error sending the otp: {e.__str__()}"
        )
        return Response({"detail": "Trouble sending the sms"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def LoginWithOTP(request):

    data = request.data
    phone = data["phone"]
    otp = data["otp"]

    try:
        user = AppUser.objects.get(
            phone=phone
        )

    except:
        print(
            f"Error finding the user: {e.__str__()}"
        )
        return Response({"detail": "Sorry we couldnt find a user with such an phone number"}, status=status.HTTP_404_NOT_FOUND)

    try:
        saved_otp = UserOTP.objects.get(user=user)

        timedelta = datetime.datetime.now()-saved_otp.updated_at.replace(tzinfo=None)
        if timedelta.seconds > 300:
            print(f"seconds {timedelta.seconds}")
            saved_otp.delete()
            return Response({"detail": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        if saved_otp.otp == otp:
            token = AuthToken.objects.create(user)
            saved_otp.delete()
            return Response({
                "user": UserSerializer(user).data,
                "token": token[1],
            })
        else:
            return Response({"detail": "OTP is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(
            f"Error verifying the otp: {e.__str__()}"
        )
        return Response({"detail": "Trouble authenticating the user"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def CreatePasswordResetOtpEmail():
    pass


def OtpMessage():
    pass


@api_view(['POST'])
def request_reset_password(request):
    """reset_password with email, OTP and new password"""
    data = request.data
    print(data["email"])
    try:
        user = User.objects.get(email=data['email'])
    except:
        return Response({"detail": "Sorry we couldnt find a user with such an email"}, status=status.HTTP_404_NOT_FOUND)
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret).now()
    try:
        ds = UserOTP.objects.get(user=user)
    except Exception as e:
        ds = UserOTP.objects.create(user=user, otp=totp)
    timedelta = datetime.now()-ds.timestamp.replace(tzinfo=None)
    if timedelta.seconds < 120:
        print(timedelta.seconds)
        return Response({"detail": "Please wait for 120 seconds before requesting another otp"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    ds.otp = totp
    ds.save()

    html_email = CreatePasswordResetOtpEmail(totp, user.username)
    # plain_text_email = OtpMessage(user.username, totp, False)
    # email_from = settings.EMAIL_HOST_USER
    # recipient_list = [data['email']]
    try:
        # send_mail("Password reset OTP", plain_text_email,
        #           email_from, recipient_list, html_message=html_email)
        return Response("sent a Password reset Email to the email you entered", status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        return Response({"detail": "Trouble sending the email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def verify_otp(request):
    """reset_password with email, OTP and new password"""
    data = request.data
    if data['email'] != '':
        try:
            user = User.objects.get(email=data['email'])
            saved_otp = UserOTP.objects.get(user=user).otp
            if user.is_active:
                # Check if otp is valid
                if data['otp'] == saved_otp:
                    return Response({"detail": "Otp has been verified"}, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"detail": "Sorry we couldnt find a user with such an email"}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({"detail": "email field is needed"},
                        status=status.HTTP_206_PARTIAL_CONTENT)


@api_view(['POST'])
def reset_password(request):
    """reset_password with email, OTP and new password"""
    data = request.data
    if data['email'] != '':
        try:
            user = User.objects.get(email=data['email'])
        except Exception as e:
            return Response({"detail": "Could not find such an email address", "error": e.__str__()}, status=status.HTTP_400_BAD_REQUEST)
        email_otp = data['otp']
        new_password = data['new_password']
        saved_otp = UserOTP.objects.get(user=user).otp
        saved_otp_object = UserOTP.objects.get(user=user)
        if user.is_active:
            # Check if otp is valid
            if data['otp'] == saved_otp:
                if new_password != '':
                    # Change Password
                    user.set_password(data['new_password'])
                    user.save()
                    saved_otp_object.delete()
                    # Here user otp will also be changed on save automatically
                    # email_from = settings.EMAIL_HOST_USER
                    recipient_list = [user.email]
                    try:
                        # send_mail("Successfully reset your password", f"Hi {user.username}, You Successfully reset your password",
                        #           email_from, recipient_list, html_message=SuccessfulPasswordResetHtmlEmail(user.username))
                        pass
                    except Exception as e:
                        print(e)
                    return Response({"detail": 'Successfully changed your password '}, status=status.HTTP_201_CREATED)
                else:
                    message = {
                        'detail': 'Password cant be empty'}
                    return Response(message, status=status.HTTP_400_BAD_REQUEST)
            else:
                message = {
                    'detail': 'OTP did not match'}
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
        else:
            message = {
                'detail': 'Something went wrong'}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
