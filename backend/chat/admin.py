from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Message)
admin.site.register(MessagePair)
admin.site.register(Chat)
