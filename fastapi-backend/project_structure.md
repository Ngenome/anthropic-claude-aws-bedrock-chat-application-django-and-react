# Production-Grade FastAPI Project Structure

## Overview

This FastAPI application replicates the functionality of the Django backend with:

- User Authentication & Authorization
- AI Chat with Claude via AWS Bedrock
- UI Prototyping System
- File Upload & Management
- Memory Extraction & Management
- Project-based Knowledge Management

## Directory Structure

```
fastapi/
├── main.py                          # FastAPI app entry point
├── requirements.txt                 # Python dependencies
├── alembic.ini                     # Database migration config
├── .env                            # Environment variables
├── README.md                       # Project documentation
│
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration settings
│   │   ├── security.py             # JWT & password utilities
│   │   ├── database.py             # Database connection
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── middleware.py           # Custom middleware
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User model
│   │   ├── chat.py                 # Chat-related models
│   │   ├── project.py              # Project models
│   │   ├── prototype.py            # Prototype models
│   │   └── memory.py               # Memory models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                 # User Pydantic schemas
│   │   ├── chat.py                 # Chat schemas
│   │   ├── project.py              # Project schemas
│   │   ├── prototype.py            # Prototype schemas
│   │   ├── memory.py               # Memory schemas
│   │   └── common.py               # Common schemas
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                 # API dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py             # Authentication endpoints
│   │       ├── users.py            # User management endpoints
│   │       ├── chat.py             # Chat endpoints
│   │       ├── projects.py         # Project endpoints
│   │       ├── prototypes.py       # Prototype endpoints
│   │       ├── memory.py           # Memory endpoints
│   │       └── files.py            # File upload endpoints
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Authentication logic
│   │   ├── email_service.py        # Email sending
│   │   ├── chat_service.py         # AI chat with Claude
│   │   ├── memory_service.py       # Memory extraction
│   │   ├── prototype_service.py    # UI prototype generation
│   │   ├── file_service.py         # File handling
│   │   ├── rate_limit_service.py   # Rate limiting
│   │   └── google_auth_service.py  # Google OAuth
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_validators.py      # File validation utilities
│   │   ├── token_counter.py        # Token counting for AI
│   │   ├── generators.py           # ID/token generators
│   │   └── aws_client.py           # AWS service clients
│   │
│   └── tasks/
│       ├── __init__.py
│       ├── celery_app.py           # Celery configuration
│       ├── memory_extraction.py    # Background memory tasks
│       └── email_tasks.py          # Background email tasks
│
├── alembic/
│   ├── versions/                   # Database migration files
│   ├── env.py                      # Alembic environment
│   └── script.py.mako              # Migration template
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Test configuration
│   ├── test_auth.py                # Authentication tests
│   ├── test_chat.py                # Chat functionality tests
│   ├── test_projects.py            # Project tests
│   └── test_prototypes.py          # Prototype tests
│
└── scripts/
    ├── init_db.py                  # Database initialization
    ├── create_admin.py             # Create admin user
    └── migrate_from_django.py      # Django migration utility
```

## Key Features Replicated

### 1. Authentication System (`app/api/v1/auth.py`)

- Email-based registration with verification
- JWT token authentication
- Google OAuth integration
- Password reset functionality
- Rate limiting
- Account lockout protection

### 2. Chat System (`app/api/v1/chat.py`)

- AI conversations with Claude via AWS Bedrock
- Streaming responses
- File uploads (images, documents)
- Project-based context
- Message history management
- Token usage tracking

### 3. Memory System (`app/services/memory_service.py`)

- Automatic memory extraction from conversations
- User context building
- Memory categorization and tagging
- Confidence scoring

### 4. Project Management (`app/api/v1/projects.py`)

- Project-based knowledge organization
- Context injection into chats
- Token limit management

### 5. UI Prototyping (`app/api/v1/prototypes.py`)

- AI-generated HTML/Tailwind prototypes
- Version management
- Variant creation
- Edit capabilities

### 6. File Management (`app/api/v1/files.py`)

- AWS S3 integration
- File validation
- Image and document handling
- Secure upload/download

## Technology Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM with async support
- **Alembic**: Database migrations
- **PostgreSQL**: Primary database
- **Redis**: Caching and rate limiting
- **Celery**: Background task processing
- **JWT**: Authentication tokens
- **Pydantic**: Data validation
- **AWS Bedrock**: Claude AI integration
- **AWS S3**: File storage
- **SMTP**: Email delivery (Zoho Mail)

## Configuration Management

Environment-based configuration with:

- Development, staging, production settings
- Secure secret management
- Database connection pooling
- Redis configuration
- AWS service configuration

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- Rate limiting per endpoint
- CORS configuration
- Input validation
- File upload security
- SQL injection protection

## Performance Optimizations

- Async/await throughout
- Database connection pooling
- Redis caching
- Background task processing
- Streaming responses for AI
- Efficient file handling

## Monitoring & Logging

- Structured logging
- Error tracking
- Performance monitoring
- API metrics
- Health checks

This structure provides a solid foundation for a production-grade FastAPI application that matches your Django backend's functionality while leveraging FastAPI's async capabilities and modern Python features.
