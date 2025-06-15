Okay, this is a comprehensive Django project focused on providing an AI-powered assistant with chat capabilities, user authentication, and a UI prototyping feature. It leverages Anthropic's Claude models via AWS Bedrock.

Here's a detailed breakdown:

Project Overview:

The project, "myclaude," is a backend system for an AI assistant application. It's built using Django and Django Rest Framework. Key functionalities include:

User Authentication (appauth): Robust user registration, login (email/password and Google OAuth), email verification, password management (reset, change), and profile management. It uses Knox for token-based authentication and includes rate limiting and detailed email notifications.

Chat Functionality (chat): Core AI chat interaction. Users can have multiple conversations (chats), which can be associated with "Projects" (for contextual knowledge). Messages can include text and file uploads (images, documents). The system uses AWS Bedrock to stream responses from Anthropic Claude models. It also features memory extraction (identifying key user info from chats) and management, allowing the AI to maintain context over time. System prompts can be saved and reused. Token usage is tracked.

UI Prototyping (prototypes): Allows users to generate and iterate on UI prototypes (HTML/Tailwind CSS) using AI (Claude). Users can create design projects, group prototypes, generate initial prototypes from prompts, and then create variants or new versions by editing existing ones with further AI prompts.

External Services:

Anthropic Claude (via AWS Bedrock): For chat responses, memory extraction, and UI prototype generation.

AWS S3: For static and media file storage.

Google OAuth: For social login.

Zoho Mail: For sending transactional emails.

Paystack: API key present, but no explicit usage in provided code (possibly for future subscription/payment features).

OpenAI GPT-3.5-turbo: A utility function call_llm.py exists to call this, but it's not integrated into the main chat flow.

Source Directory: /home/kelvin/coding/ai/manticeai/myclaude

File Structure and Details:

myclaude/
└── backend/
├── manage.py
├── get-contents.py
├── claudeapi.py
├── test_memory_integration.py
├── appauth/
│ ├── **init**.py
│ ├── views.py
│ ├── serializers.py
│ ├── tests.py
│ ├── urls.py
│ ├── reset-password.py (Commented out, likely old OTP-based reset)
│ ├── apps.py
│ ├── welcome.py
│ ├── models.py
│ ├── register.py (Potentially old/alternative registration API)
│ ├── otp.py (OTP generation and login/reset views, likely old/alternative)
│ └── services/
│ ├── rate_limit_service.py
│ ├── email_service.py
│ ├── google_auth_service.py
│ └── auth_service.py
├── chat/
│ ├── **init**.py
│ ├── views.py
│ ├── file_handlers.py (Potentially outdated, uses 'Attachment' model not defined)
│ ├── serializers.py
│ ├── tests.py
│ ├── urls.py
│ ├── apps.py
│ ├── models.py
│ ├── prompts/
│ │ ├── coding.py
│ │ └── default.py
│ ├── services/
│ │ ├── chat_service.py
│ │ └── memory_service.py
│ ├── utils/
│ │ ├── file_validators.py
│ │ └── token_counter.py
│ └── management/
│ └── commands/
│ └── import_chat_data.py
├── utils/
│ ├── generate_uid.py (Not explicitly used in provided files)
│ └── call_llm.py (Utility for OpenAI, not main flow)
├── prototypes/
│ ├── **init**.py
│ ├── views.py
│ ├── services.py
│ ├── serializers.py
│ ├── tests.py
│ ├── urls.py
│ ├── apps.py
│ └── models.py
└── aiassistant/ (Django Project Root)
├── **init**.py
├── wsgi.py
├── celery.py
├── urls.py
├── asgi.py
├── settings.py
└── storage_backends.py

Detailed File Descriptions:

1. Root backend/ Files:

manage.py

Purpose: Standard Django command-line utility for administrative tasks.

Key Logic: Sets DJANGO_SETTINGS_MODULE to aiassistant.settings and executes Django management commands.

get-contents.py

Purpose: A utility script to list .svg files in a user-specified directory, remove their extensions, format them as a comma-separated string, and write the result to contents.txt.

Key Logic: Uses os.listdir, os.path.splitext. Not part of the core Django application runtime.

claudeapi.py

Purpose: A standalone script demonstrating interaction with the Anthropic Claude API (specifically claude-3-5-sonnet-20241022).

Key Logic: Initializes the Anthropic client with an API key from environment variables. Sends a hardcoded message to generate 3 ad copies for a "Plushie" product. Prints the API response. Likely for testing or a specific ad-generation task separate from the main chat.

test_memory_integration.py

Purpose: A Django script to test the memory integration features of the chat application.

Key Logic:

Sets up Django environment.

Imports models (Chat, UserMemory, MemoryTag, User) and services (ChatService, MemoryExtractionService) from the chat app.

Creates a test user and chat.

Creates UserMemory instances with associated MemoryTags.

Tests MemoryExtractionService.get_relevant_memories_for_context() and format_memories_for_context().

Tests ChatService.prepare_message_history().

2. appauth/ (Authentication Application)

Purpose: Manages all aspects of user authentication, registration, and profile management.

Models:

AppUser(AbstractUser) (appauth/models.py):

Custom user model using email as USERNAME_FIELD.

id: UUID primary key.

username: Auto-generated, unique.

Email verification fields: email_verified, email_verification_token, email_verification_sent_at.

Password reset fields: password_reset_token, password_reset_sent_at.

Security fields: last_login_ip, login_attempts, locked_until.

Profile field: avatar (ImageField).

Methods: generate_token(), verify_token(), clear_token(), record_login_attempt(), is_locked().

UserManager(BaseUserManager) (appauth/models.py):

Custom manager for AppUser.

Methods: create_user(), create_superuser(), generate_unique_username().

Services:

AuthService (appauth/services/auth_service.py):

Centralizes authentication logic.

Methods: register_user, login_user, logout_user, resend_verification_email, verify_email, initiate_password_reset, reset_password, change_password, authenticate_google.

Integrates EmailService, RateLimitService, and GoogleAuthService.

Includes logic for suspicious login detection (currently placeholder).

EmailService (appauth/services/email_service.py):

Handles sending various emails (verification, password reset, password change notification, suspicious login) using Django templates and SMTP settings (configured for Zoho Mail).

RateLimitService (appauth/services/rate_limit_service.py):

Provides rate limiting functionality for actions like login, registration, password reset.

Uses Django cache or an in-memory store. Configurable limits and block durations.

GoogleAuthService (appauth/services/google_auth_service.py):

Handles the logic for Google OAuth authentication, specifically getting or creating an AppUser based on data from Google.

Views (appauth/views.py):

RegisterView: Handles new user registration. Uses AuthService.

LoginView: Handles user login. Uses AuthService.

EmailVerificationView: Verifies user email using a token. Uses AuthService.

ResendVerificationView: Resends email verification link. Uses AuthService.

PasswordResetRequestView: Initiates password reset. Uses AuthService.

PasswordResetConfirmView: Confirms password reset with token and new password. Uses AuthService.

PasswordChangeView: Allows authenticated users to change their password. Uses AuthService.

LogoutView: Logs out the user, invalidating the Knox token. Uses AuthService.

GoogleAuthView: Handles Google OAuth callback, authenticates/creates user, returns Knox token.

UserProfileView: Retrieves and updates authenticated user's profile.

All views use corresponding serializers and DRF features (generics, permissions).

Serializers (appauth/serializers.py):

UserSerializer: For AppUser model (profile data).

RegisterSerializer: For registration data validation (email, password, names). Includes password strength validation.

LoginSerializer: For login data (email, password, optional device_info).

PasswordResetRequestSerializer, PasswordResetConfirmSerializer, PasswordChangeSerializer: For password management flows.

EmailVerificationSerializer, ResendVerificationSerializer: For email verification flows.

GoogleAuthSerializer: For Google OAuth access token.

URLs (appauth/urls.py):

Defines API endpoints for all authentication views (e.g., /register/, /login/, /login/google/, /password/reset/, etc.).

Other Files:

reset-password.py: Commented out code, likely an older OTP-based password reset mechanism.

welcome.py: A simple function createWelcomeEmail() returning a string.

register.py: Contains RegisterAPI, seemingly an older or alternative registration view.

otp.py: Contains functions and API views for OTP-based login and password reset, using pyotp. This appears to be an alternative or older system not fully integrated with the main AuthService flow.

apps.py: Standard Django app configuration.

tests.py: Empty.

3. chat/ (Chat Application)

Purpose: Manages chat interactions, project-specific knowledge, system prompts, and user memory persistence.

Models (chat/models.py):

MessageContent: Represents a piece of content within a message (text, image, document). Linked to Message. Validates file sizes and types.

Message: A single message from a user or assistant. UUID id. Linked to MessagePair. Fields: role, hidden, token_count. Has get_content() to format for Claude API.

Project: A container for chats and knowledge items. UUID id. Linked to AppUser. Fields: name, description, instructions. Property total_knowledge_tokens.

ProjectKnowledge: A piece of knowledge associated with a Project. Fields: content, title, include_in_chat, token_count.

Chat: A conversation session. UUID id. Linked to AppUser and optionally Project. Fields: title, system_prompt. Property total_tokens.

MessagePair: Groups a user message and its corresponding assistant response. UUID id. Linked to Chat.

SavedSystemPrompt: Allows users to save and reuse system prompts. UUID id. Linked to AppUser.

TokenUsage: Tracks tokens used by a user in a chat (not actively used in views for billing, more for stats).

MemoryTag: Tags for categorizing UserMemory.

UserMemory: Stores information extracted about a user from conversations to provide context. UUID id. Linked to AppUser and Chat. Fields: summary, raw_content, confidence_score, category, tags, is_verified, is_active, source_message_pair.

Services:

ChatService (chat/services/chat_service.py):

Handles core chat logic.

Interacts with AWS Bedrock (Claude 3.5 Sonnet v2, Haiku v1.0, Sonnet v1) with fallback for throttling.

Methods: create_or_get_chat, \_generate_chat_title (uses Haiku), get_project_context, prepare_message_history (includes project context and user memories via MemoryExtractionService), create_chat_request_body, invoke_model, create_new_message (handles MessageContent creation).

MemoryExtractionService (chat/services/memory_service.py):

Extracts user memories from chat conversations using Claude Haiku.

Methods: extract_memories_from_chat, \_get_conversation_text, \_extract_with_claude, \_create_memory, \_add_tags_to_memory, get_relevant_memories, mark_memories_as_referenced, get_relevant_memories_for_context, format_memories_for_context.

Views (chat/views.py):

claude_chat_view: Main streaming chat endpoint. Integrates ChatService and MemoryExtractionService. Handles message creation and file uploads within messages.

ChatMessagesListView, ChatDetailView, ChatListView: For chat and message listing/details.

ChatViewSet: DRF ViewSet for Chat model (list, create, retrieve, update, delete, archive/unarchive, search).

ProjectViewSet: DRF ViewSet for Project model (CRUD, list knowledge/chats).

ProjectKnowledgeViewSet: DRF ViewSet for ProjectKnowledge model (CRUD, toggle inclusion in chat).

SavedSystemPromptListCreateView, SavedSystemPromptRetrieveUpdateDestroyView: For SavedSystemPrompt CRUD.

Various utility views: update_chat_system_prompt, get_chat_token_usage, get_project_token_usage, edit_message, toggle_message_pair, delete_message_pair, validate_file_view.

Memory Management Views: UserMemoryViewSet, MemoryTagViewSet, extract_memories_from_chat (manual trigger), memory_stats, get_user_context.

Serializers (chat/serializers.py):

MessageContentSerializer, MessageSerializer, ChatSerializer, SystemPromptSerializer (for SavedSystemPrompt), MessagePairSerializer, ProjectSerializer, ProjectKnowledgeSerializer (includes token validation logic), MemoryTagSerializer, UserMemorySerializer, UserMemoryListSerializer.

URLs (chat/urls.py):

Uses DRF DefaultRouter for ChatViewSet, ProjectViewSet, ProjectKnowledgeViewSet, UserMemoryViewSet, MemoryTagViewSet.

Defines paths for other views like claude_chat_view, message editing, token usage, memory context, etc.

Prompts (chat/prompts/):

coding.py: Defines CODING_PROMPT (a detailed system prompt for Claude, tailored for coding assistance, referencing project knowledge and file attachments) and get_coding_system_prompt() to inject user-specific prompts. This is used by ChatService.

default.py: Defines DEFAULT_PROMPT (Anthropic's standard system prompt for Claude). Its usage is not clear in the provided ChatService.

Utilities (chat/utils/):

file_validators.py: Functions (validate_image_size, validate_document_size, validate_mime_type using python-magic) for validating uploaded files.

token_counter.py: Functions (count_tokens using "Xenova/claude-tokenizer", validate_token_count, get_token_usage_stats) for counting tokens in text.

Management Commands (chat/management/commands/):

import_chat_data.py: A Django management command to import chat data from a chat_data_export.json file. Useful for seeding or migrating data.

Other Files:

file_handlers.py: Contains functions handle_file_upload, get_file_contents, delete_attachment. It refers to an Attachment model which is not defined in chat/models.py. This file might be outdated as MessageContent model now handles file attachments within messages.

apps.py: Standard Django app configuration.

tests.py: Empty.

4. prototypes/ (UI Prototyping Application)

Purpose: Enables users to generate and iterate on UI prototypes (HTML with Tailwind CSS) using AI.

Models (prototypes/models.py):

DesignProject: Top-level container for UI prototypes, linked to AppUser.

Group: Organizes prototypes within a DesignProject.

Prototype: Represents a specific UI component/screen idea, linked to DesignProject and optionally Group. Stores the initial prompt.

PrototypeVariant: A distinct design/functional variant of a Prototype. Has an is_original flag.

PrototypeVersion: An iteration of a PrototypeVariant. Stores html_content, edit_prompt, and version_number.

Services (prototypes/services.py):

PrototypeService:

Interacts with AWS Bedrock (Claude 3.5 Sonnet v2/v1) to generate, edit, and create variants of UI prototypes.

Defines specific system prompts for prototype generation (get_ui_prototype_system_prompt), editing (get_ui_prototype_edit_system_prompt), and creating variants (get_ui_prototype_variant_system_prompt).

These prompts instruct Claude to output complete HTML with Tailwind CSS, wrapped in <prototype_file name="...">CODE</prototype_file> XML tags, which the service then parses.

Views (prototypes/views.py):

DesignProjectViewSet, GroupViewSet, PrototypeViewSet, PrototypeVariantViewSet, PrototypeVersionViewSet: DRF ViewSets for CRUD operations on their respective models.

PrototypeViewSet has a custom action create_variant which uses PrototypeService to generate a new variant based on an existing one.

PrototypeVariantViewSet has a custom action create_version which uses PrototypeService to edit the latest version of a variant.

generate_prototype: An API view that takes a prompt and design project ID, uses PrototypeService to generate the initial HTML, and creates the Prototype, original PrototypeVariant, and initial PrototypeVersion.

design_project_prototypes, group_prototypes: API views to list prototypes for a given project or group.

Serializers (prototypes/serializers.py):

Serializers for all models: DesignProjectSerializer, GroupSerializer, PrototypeSerializer, PrototypeVariantSerializer, PrototypeVersionSerializer.

Detail serializers (PrototypeDetailSerializer, DesignProjectDetailSerializer, PrototypeVariantDetailSerializer) include nested related objects.

Serializers often include computed fields like variants_count, latest_version.

URLs (prototypes/urls.py):

Uses DRF DefaultRouter for the ViewSets.

Defines paths for custom views like generate_prototype and listing prototypes by project/group.

Other Files:

apps.py: Standard Django app configuration, sets verbose_name = 'UI Prototypes'.

tests.py: Empty.

5. utils/ (General Utilities in backend/utils/)

generate_uid.py:

Purpose: Generates a short, 8-character UID.

Key Logic: Creates a UUID, hashes it with SHA-256, and then base64 encodes the hash, taking the first 8 characters. Its usage within the project is not apparent from the provided files.

call_llm.py:

Purpose: A utility function to make calls to OpenAI's GPT-3.5-turbo model.

Key Logic: Takes a system message and a list of user messages, formats them for the OpenAI API, and returns the model's content response. This is separate from the main Claude-based chat flow.

6. aiassistant/ (Django Project Directory)

settings.py:

Standard Django settings.

Environment variables managed by django-environ.

DEBUG = True.

Installed Apps: appauth, chat, prototypes, rest_framework, knox, corsheaders, social_django, drf_spectacular, storages.

AUTH_USER_MODEL = "appauth.AppUser".

REST_FRAMEWORK configured for Knox token authentication and DRF Spectacular.

REST_KNOX settings for token TTL, etc.

AWS S3 settings for static and media files via django-storages and custom backends.

AWS_BEDROCK_ACCESS_KEY_ID, AWS_BEDROCK_SECRET_ACCESS_KEY.

FRONTEND_URL, SITE_NAME, SUPPORT_EMAIL.

Email configuration for Zoho Mail (SMTP).

CORS and CSRF settings.

PAYSTACK_SECRET_KEY and TOKEN_PRICE are defined but their usage is not shown in these files.

urls.py:

Root URL configuration.

Includes URL patterns from appauth.urls, chat.urls, and prototypes.urls under /api/v1/.

celery.py:

Basic Celery setup for asynchronous tasks. Project name is 'your_project_name' (should likely be 'aiassistant').

No specific Celery tasks are defined in the provided files, but the infrastructure is present.

storage_backends.py:

Defines StaticStorage and MediaStorage classes inheriting from S3Boto3Storage for handling static and media files on AWS S3.

wsgi.py, asgi.py, **init**.py: Standard Django project files.

Key Dependencies Identified:

Django, Django Rest Framework

django-environ (for environment variable management)

djangorestframework-knox (for token authentication)

django-cors-headers (for CORS)

social-auth-app-django (for social authentication, e.g., Google)

drf-spectacular (for API schema generation)

boto3 (for AWS SDK, used for S3 and Bedrock)

django-storages (for S3 file storage)

Pillow (for image processing, dependency of ImageField)

python-magic (for MIME type detection in chat/utils/file_validators.py)

transformers (specifically GPT2TokenizerFast for "Xenova/claude-tokenizer" for token counting)

anthropic (used in the standalone claudeapi.py script, not in the main chat service which uses boto3)

openai (used in utils/call_llm.py)

celery (for asynchronous tasks, setup present)

pyotp (in appauth/otp.py and appauth/reset-password.py, likely older features)

Potential Issues/Observations:

Redundant Auth Code: The appauth app has register.py, otp.py, and the commented-out reset-password.py. These seem to offer alternative/older authentication mechanisms (OTP-based, different registration API) compared to the more comprehensive AuthService and token-based flows in views.py. This could lead to confusion or dead code.

chat/file_handlers.py: This file uses an Attachment model that is not defined in chat/models.py. The MessageContent model seems to be the current way of handling file attachments within messages, making file_handlers.py potentially outdated or unused.

Celery Setup: Celery is configured, but no actual tasks are defined in the provided files. Memory extraction (MemoryExtractionService) is currently synchronous within the chat view's streaming response; it could be a candidate for Celery if it becomes time-consuming.

utils/generate_uid.py and utils/call_llm.py: Their integration or necessity within the main project flow isn't clear from the other files. call_llm.py (OpenAI) is distinct from the primary Claude usage.

chat/prompts/default.py: The DEFAULT_PROMPT (standard Anthropic prompt) doesn't seem to be used by the ChatService, which favors the custom CODING_PROMPT.

Token Price: TOKEN_PRICE is defined in settings but not observably used for any calculations or billing logic in the provided code.

Error Handling in Services: While some error handling is present (e.g., fallback in ChatService.invoke_model), a more systematic approach to custom exceptions and error propagation from services to views could be beneficial.

Test Coverage: Most tests.py files are empty. The test_memory_integration.py script is a good start but doesn't use the Django test runner.

This detailed summary should cover all the information present in the provided code.
