# from django.contrib import admin
# from django.utils.html import format_html
# from django.db.models import Count, Sum
# from django.urls import reverse
# from django.utils.safestring import mark_safe
# from .models import (
#     Project, ProjectKnowledge, Chat, MessagePair, Message,
#     SavedSystemPrompt, Attachment, TokenUsage
# )

# class ProjectKnowledgeInline(admin.StackedInline):
#     model = ProjectKnowledge
#     extra = 0
#     fields = ('title', 'content', 'include_in_chat', 'token_count')
#     readonly_fields = ('token_count',)
#     show_change_link = True

# @admin.register(Project)
# class ProjectAdmin(admin.ModelAdmin):
#     list_display = ('name', 'user', 'created_at', 'is_archived', 'knowledge_count', 'total_knowledge_tokens')
#     list_filter = ('is_archived', 'created_at', 'user')
#     search_fields = ('name', 'description', 'user__email')
#     readonly_fields = ('created_at', 'updated_at', 'total_knowledge_tokens')
#     inlines = [ProjectKnowledgeInline]
#     actions = ['archive_projects', 'unarchive_projects']

#     def knowledge_count(self, obj):
#         return obj.knowledge_items.count()
#     knowledge_count.short_description = 'Knowledge Items'

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('user')

#     def archive_projects(self, request, queryset):
#         queryset.update(is_archived=True)
#     archive_projects.short_description = "Archive selected projects"

#     def unarchive_projects(self, request, queryset):
#         queryset.update(is_archived=False)
#     unarchive_projects.short_description = "Unarchive selected projects"

# @admin.register(ProjectKnowledge)
# class ProjectKnowledgeAdmin(admin.ModelAdmin):
#     list_display = ('title', 'project', 'include_in_chat', 'token_count', 'updated_at')
#     list_filter = ('include_in_chat', 'created_at', 'project')
#     search_fields = ('title', 'content', 'project__name')
#     readonly_fields = ('token_count', 'created_at', 'updated_at')

# class MessageInline(admin.TabularInline):
#     model = Message
#     extra = 0
#     readonly_fields = ('token_count', 'created_at', 'get_content_preview')
#     fields = ('role', 'type', 'get_content_preview', 'token_count', 'hidden', 'created_at')

#     def get_content_preview(self, obj):
#         if obj.type == 'image':
#             return format_html('<img src="{}" style="max-height: 50px;" />', obj.image.url) if obj.image else ''
#         elif obj.type == 'file':
#             return format_html('<a href="{}">{}</a>', obj.file.url, obj.file.name) if obj.file else ''
#         return obj.text[:100] + '...' if obj.text and len(obj.text) > 100 else obj.text
#     get_content_preview.short_description = 'Content Preview'

# class MessagePairInline(admin.StackedInline):
#     model = MessagePair
#     extra = 0
#     show_change_link = True
#     inlines = [MessageInline]

# @admin.register(Chat)
# class ChatAdmin(admin.ModelAdmin):
#     list_display = ('title', 'user', 'project', 'created_at', 'is_archived', 'total_tokens', 'message_count')
#     list_filter = ('is_archived', 'created_at', 'user', 'project')
#     search_fields = ('title', 'user__email', 'project__name')
#     readonly_fields = ('uuid', 'created_at', 'total_tokens')
#     actions = ['archive_chats', 'unarchive_chats']

#     def message_count(self, obj):
#         return Message.objects.filter(message_pair__chat=obj).count()
#     message_count.short_description = 'Messages'

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('user', 'project')

#     def archive_chats(self, request, queryset):
#         queryset.update(is_archived=True)
#     archive_chats.short_description = "Archive selected chats"

#     def unarchive_chats(self, request, queryset):
#         queryset.update(is_archived=False)
#     unarchive_chats.short_description = "Unarchive selected chats"

# @admin.register(Message)
# class MessageAdmin(admin.ModelAdmin):
#     list_display = ('get_chat_title', 'role', 'type', 'token_count', 'created_at', 'is_archived')
#     list_filter = ('role', 'type', 'is_archived', 'created_at')
#     search_fields = ('text', 'message_pair__chat__title')
#     readonly_fields = ('token_count', 'created_at', 'edited_at', 'get_content_preview')

#     def get_chat_title(self, obj):
#         return obj.message_pair.chat.title
#     get_chat_title.short_description = 'Chat'
#     get_chat_title.admin_order_field = 'message_pair__chat__title'

#     def get_content_preview(self, obj):
#         if obj.type == 'image':
#             return format_html('<img src="{}" style="max-width: 300px;" />', obj.image.url) if obj.image else ''
#         elif obj.type == 'file':
#             return format_html('<a href="{}">{}</a>', obj.file.url, obj.file.name) if obj.file else ''
#         return obj.text
#     get_content_preview.short_description = 'Content Preview'

# @admin.register(SavedSystemPrompt)
# class SavedSystemPromptAdmin(admin.ModelAdmin):
#     list_display = ('title', 'user', 'created_at', 'prompt_preview')
#     list_filter = ('created_at', 'user')
#     search_fields = ('title', 'prompt', 'user__email')
#     readonly_fields = ('created_at',)

#     def prompt_preview(self, obj):
#         return obj.prompt[:100] + '...' if len(obj.prompt) > 100 else obj.prompt
#     prompt_preview.short_description = 'Prompt Preview'

# @admin.register(Attachment)
# class AttachmentAdmin(admin.ModelAdmin):
#     list_display = ('original_name', 'get_chat_title', 'uploaded_at', 'file_preview')
#     list_filter = ('uploaded_at',)
#     search_fields = ('original_name', 'chat__title')
#     readonly_fields = ('uploaded_at',)

#     def get_chat_title(self, obj):
#         return obj.chat.title
#     get_chat_title.short_description = 'Chat'

#     def file_preview(self, obj):
#         return format_html('<a href="{}">{}</a>', obj.file.url, 'View File')
#     file_preview.short_description = 'File'

# @admin.register(TokenUsage)
# class TokenUsageAdmin(admin.ModelAdmin):
#     list_display = ('user', 'chat', 'tokens_used', 'created_at')
#     list_filter = ('created_at', 'user')
#     search_fields = ('user__email', 'chat__title')
#     readonly_fields = ('created_at',)

#     def has_add_permission(self, request):
#         return False  # Prevent manual addition of token usage records

#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related('user', 'chat')

# # Customize admin site header and title
# admin.site.site_header = 'Chat Application Administration'
# admin.site.site_title = 'Chat Admin Portal'
# admin.site.index_title = 'Welcome to Chat Admin Portal'