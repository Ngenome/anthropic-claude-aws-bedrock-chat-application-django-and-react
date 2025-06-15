from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Project, ProjectKnowledge, Chat, MessagePair, Message,
    SavedSystemPrompt, TokenUsage, UserMemory, MemoryTag
)


class ProjectKnowledgeInline(admin.StackedInline):
    model = ProjectKnowledge
    extra = 0
    fields = ('title', 'content', 'include_in_chat', 'token_count')
    readonly_fields = ('token_count',)
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'is_archived', 'knowledge_count', 'total_knowledge_tokens')
    list_filter = ('is_archived', 'created_at', 'user')
    search_fields = ('name', 'description', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'total_knowledge_tokens')
    inlines = [ProjectKnowledgeInline]
    actions = ['archive_projects', 'unarchive_projects']

    def knowledge_count(self, obj):
        return obj.knowledge_items.count()
    knowledge_count.short_description = 'Knowledge Items'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def archive_projects(self, request, queryset):
        queryset.update(is_archived=True)
    archive_projects.short_description = "Archive selected projects"

    def unarchive_projects(self, request, queryset):
        queryset.update(is_archived=False)
    unarchive_projects.short_description = "Unarchive selected projects"


@admin.register(ProjectKnowledge)
class ProjectKnowledgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'include_in_chat', 'token_count', 'updated_at')
    list_filter = ('include_in_chat', 'created_at', 'project')
    search_fields = ('title', 'content', 'project__name')
    readonly_fields = ('token_count', 'created_at', 'updated_at')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'project', 'created_at', 'is_archived', 'message_count', 'memory_count')
    list_filter = ('is_archived', 'created_at', 'user', 'project')
    search_fields = ('title', 'user__email', 'project__name')
    readonly_fields = ('id', 'created_at')
    actions = ['archive_chats', 'unarchive_chats']

    def message_count(self, obj):
        return Message.objects.filter(message_pair__chat=obj).count()
    message_count.short_description = 'Messages'
    
    def memory_count(self, obj):
        return obj.extracted_memories.filter(is_active=True).count()
    memory_count.short_description = 'Active Memories'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'project')

    def archive_chats(self, request, queryset):
        queryset.update(is_archived=True)
    archive_chats.short_description = "Archive selected chats"

    def unarchive_chats(self, request, queryset):
        queryset.update(is_archived=False)
    unarchive_chats.short_description = "Unarchive selected chats"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('get_chat_title', 'role', 'token_count', 'created_at', 'is_archived')
    list_filter = ('role', 'is_archived', 'created_at')
    search_fields = ('message_pair__chat__title',)
    readonly_fields = ('token_count', 'created_at')

    def get_chat_title(self, obj):
        return obj.message_pair.chat.title
    get_chat_title.short_description = 'Chat'
    get_chat_title.admin_order_field = 'message_pair__chat__title'


@admin.register(SavedSystemPrompt)
class SavedSystemPromptAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'prompt_preview')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'prompt', 'user__email')
    readonly_fields = ('created_at',)

    def prompt_preview(self, obj):
        return obj.prompt[:100] + '...' if len(obj.prompt) > 100 else obj.prompt
    prompt_preview.short_description = 'Prompt Preview'


@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat', 'tokens_used', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__email', 'chat__title')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request):
        return False  # Prevent manual addition of token usage records

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'chat')


# Memory Models Admin
@admin.register(MemoryTag)
class MemoryTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'memory_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)
    
    def memory_count(self, obj):
        return obj.memories.filter(is_active=True).count()
    memory_count.short_description = 'Active Memories'


class MemoryTagInline(admin.TabularInline):
    model = UserMemory.tags.through
    extra = 0
    verbose_name = "Tag"
    verbose_name_plural = "Tags"


@admin.register(UserMemory)
class UserMemoryAdmin(admin.ModelAdmin):
    list_display = ('summary_preview', 'user', 'category', 'confidence_score', 'is_verified', 'is_active', 'created_at')
    list_filter = ('category', 'is_verified', 'is_active', 'created_at', 'confidence_score')
    search_fields = ('summary', 'raw_content', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_referenced')
    filter_horizontal = ('tags',)
    actions = ['verify_memories', 'activate_memories', 'deactivate_memories']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'chat', 'source_message_pair')
        }),
        ('Memory Content', {
            'fields': ('summary', 'raw_content', 'category', 'confidence_score')
        }),
        ('Classification', {
            'fields': ('tags', 'is_verified', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_referenced'),
            'classes': ('collapse',)
        })
    )
    
    def summary_preview(self, obj):
        return obj.summary[:80] + '...' if len(obj.summary) > 80 else obj.summary
    summary_preview.short_description = 'Summary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'chat').prefetch_related('tags')
    
    def verify_memories(self, request, queryset):
        queryset.update(is_verified=True)
    verify_memories.short_description = "Mark selected memories as verified"
    
    def activate_memories(self, request, queryset):
        queryset.update(is_active=True)
    activate_memories.short_description = "Activate selected memories"
    
    def deactivate_memories(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_memories.short_description = "Deactivate selected memories"


# Customize admin site header and title
admin.site.site_header = 'AI Assistant Administration'
admin.site.site_title = 'AI Admin Portal'
admin.site.index_title = 'Welcome to AI Admin Portal'