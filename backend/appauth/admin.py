from django.contrib import admin

# Register your models here.
from .models import AppUser
admin.site.register(AppUser)