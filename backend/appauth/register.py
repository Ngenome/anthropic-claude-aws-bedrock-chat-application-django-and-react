from .models import *
from rest_framework import generics
from rest_framework import status
from .welcome import createWelcomeEmail
from .serializers import *
from rest_framework import generics
from knox.models import AuthToken
from rest_framework.response import Response
from rest_framework import generics, status
from django.conf import settings
from django.core.mail import send_mail
User = AppUser

# from api.getEnv import api_key, api_secret


class RegisterAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.create_user(
                username=serializer.validated_data.get('username'),
                password=serializer.validated_data.get('password'),
                email=serializer.validated_data.get('email'),
                first_name=serializer.validated_data.get('first_name'),
                last_name=serializer.validated_data.get('last_name'),
                phone=serializer.validated_data.get('phone'),
                avatar=serializer.validated_data.get('avatar'))
            user.save()
        except Exception as e:
            raise e

        token = AuthToken.objects.create(user)
        body = createWelcomeEmail(user.username)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email]
        try:
            send_mail("Welcome to DissolveAI", f'''Welcome {user.username} to DissolveAI''',
                      email_from, recipient_list, html_message=body)
        except Exception as e:
            print("Error sending the email")

        return Response({
            "user": AppUserSerializer(user, context=self.get_serializer_context()).data,
            "token": token[1],
            "message": "User created successfully",
        }, status=status.HTTP_201_CREATED
        )
