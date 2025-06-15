from django.contrib import admin
from .models import DesignProject, Group, Prototype, PrototypeVariant, PrototypeVersion

@admin.register(DesignProject)
class DesignProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('created_at',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'design_project', 'created_at')
    search_fields = ('name', 'design_project__title')
    list_filter = ('created_at',)

@admin.register(Prototype)
class PrototypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'design_project', 'group', 'created_at')
    search_fields = ('title', 'design_project__title', 'group__name')
    list_filter = ('created_at',)

@admin.register(PrototypeVariant)
class PrototypeVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'prototype', 'is_original', 'created_at')
    search_fields = ('name', 'prototype__title')
    list_filter = ('is_original', 'created_at')

@admin.register(PrototypeVersion)
class PrototypeVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'variant', 'version_number', 'created_at')
    search_fields = ('name', 'variant__name', 'variant__prototype__title')
    list_filter = ('version_number', 'created_at')
    readonly_fields = ('html_content',)
