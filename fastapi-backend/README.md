# Mantice AI Assistant - FastAPI Backend

A production-grade FastAPI application that replicates the functionality of the Django backend with modern async capabilities.

## Features

- **User Authentication & Authorization**

  - Email-based registration with verification
  - JWT token authentication
  - Google OAuth integration
  - Password reset functionality
  - Rate limiting and account lockout protection

- **AI Chat System**

  - Conversations with Claude via AWS Bedrock
  - Streaming responses
  - File uploads (images, documents)
  - Project-based context injection
  - Message history management
  - Token usage tracking

- **Memory System**

  - Automatic memory extraction from conversations
  - User context building
  - Memory categorization and tagging
  - Confidence scoring

- **Project Management**

  - Project-based knowledge organization
  - Context injection into chats
  - Token limit management

- **UI Prototyping**

  - AI-generated HTML/Tailwind prototypes
  - Version management
  - Variant creation
  - Edit capabilities

- **File Management**
  - AWS S3 integration
  - File validation
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

## Project Structure

```
fastapi/
├── main.py                          # FastAPI app entry point
├── requirements.txt                 # Python dependencies
├── alembic.ini                     # Database migration config
├── env.example                     # Environment variables template
├── README.md                       # This file
│
├── app/
│   ├── core/                       # Core configuration and utilities
│   │   ├── config.py               # Settings and configuration
│   │   ├── security.py             # JWT & password utilities
│   │   └── database.py             # Database connection
│   │
│   ├── models/                     # SQLAlchemy models
│   │   └── user.py                 # User model
│   │
│   ├── schemas/                    # Pydantic schemas
│   │   └── user.py                 # User request/response models
│   │
│   ├── api/                        # API endpoints
│   │   ├── deps.py                 # API dependencies
│   │   └── v1/                     # API version 1
│   │       ├── auth.py             # Authentication endpoints
│   │       ├── users.py            # User management
│   │       ├── chat.py             # Chat endpoints
│   │       ├── projects.py         # Project endpoints
│   │       ├── prototypes.py       # Prototype endpoints
│   │       ├── memory.py           # Memory endpoints
│   │       └── files.py            # File upload endpoints
│   │
│   ├── services/                   # Business logic services
│   │   ├── email_service.py        # Email sending
│   │   └── google_auth_service.py  # Google OAuth
│   │
│   └── utils/                      # Utility functions
│
├── alembic/                        # Database migrations
├── tests/                          # Test files
└── scripts/                        # Utility scripts
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- AWS Account (for S3 and Bedrock)

### 1. Clone and Setup Environment

```bash
cd fastapi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your actual configuration values:

```env
# Required settings
SECRET_KEY=your_super_secret_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/myfastapi
SMTP_USER=your_email@yourdomain.com
SMTP_PASSWORD=your_email_password
AWS_BEDROCK_ACCESS_KEY_ID=your_bedrock_access_key
AWS_BEDROCK_SECRET_ACCESS_KEY=your_bedrock_secret_key
```

### 3. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE myfastapi;
```

Initialize the database:

```bash
alembic upgrade head
```

### 4. Run the Application

Development mode:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/verify-email` - Verify email address
- `POST /api/v1/auth/resend-verification` - Resend verification email
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm` - Confirm password reset
- `POST /api/v1/auth/password-change` - Change password
- `POST /api/v1/auth/google` - Google OAuth login

### Users

- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile

### Chat (Planned)

- `POST /api/v1/chat/` - Create new chat
- `GET /api/v1/chat/` - List user chats
- `GET /api/v1/chat/{chat_id}` - Get chat details
- `POST /api/v1/chat/{chat_id}/messages` - Send message
- `GET /api/v1/chat/{chat_id}/messages` - Get chat messages

### Projects (Planned)

- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/` - List projects
- `GET /api/v1/projects/{project_id}` - Get project details
- `PUT /api/v1/projects/{project_id}` - Update project
- `DELETE /api/v1/projects/{project_id}` - Delete project

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
```

### Linting

```bash
flake8 app/
```

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

## Configuration

### Environment Variables

See `env.example` for all available configuration options.

### Key Settings

- `SECRET_KEY`: Used for JWT token signing (required)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `AWS_BEDROCK_*`: AWS Bedrock credentials for Claude AI (required)
- `SMTP_*`: Email configuration for notifications (required)
- `DEBUG`: Enable debug mode and API documentation

### Security Settings

- `ACCOUNT_LOCKOUT_ATTEMPTS`: Failed login attempts before lockout (default: 5)
- `ACCOUNT_LOCKOUT_DURATION`: Lockout duration in seconds (default: 1800)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration (default: 10080 = 7 days)

## Deployment

### Production Checklist

1. Set `DEBUG=false` in environment
2. Use strong `SECRET_KEY`
3. Configure proper CORS origins
4. Set up SSL/TLS certificates
5. Use production database
6. Configure Redis for caching
7. Set up monitoring and logging
8. Configure backup strategies

### Docker Deployment (Future)

Docker support will be added in future versions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support, email support@yourdomain.com or create an issue in the repository.
