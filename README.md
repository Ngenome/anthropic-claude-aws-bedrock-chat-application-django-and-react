# AI Chat Application with Claude and AWS Bedrock

This project is a full-stack AI chat application that uses Claude AI via AWS Bedrock for the backend, and React for the frontend. It allows users to engage in conversations with an AI assistant, manage projects, and handle knowledge bases.

## Features

- Chat with Claude AI
- Project management
- Knowledge base management
- File attachments
- Token usage tracking
- User authentication

## Tech Stack

### Backend

- Django
- Django Rest Framework
- AWS Bedrock
- Knox for token authentication

### Frontend

- React
- TypeScript
- Tailwind CSS
- Shadcn UI components
- React Query for state management

## Prerequisites

- Python 3.8+
- Node.js 14+
- AWS account with Bedrock access
- Django 5.0+
- React 18+

## Setup

### Backend

1. Navigate to the `backend` directory
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Create a `.env` file in the `backend/aiassistants` directory
   - Add the following variables:
     ```
     SECRET_KEY=your_django_secret_key
     AWS_BEDROCK_ACCESS_KEY_ID=your_aws_access_key
     AWS_BEDROCK_SECRET_ACCESS_KEY=your_aws_secret_key
     ```
5. Run migrations:
   ```
   python manage.py migrate
   ```
6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```
7. Generate an AuthToken for the superuser:
   ```
   python manage.py shell
   ```
   In the shell, run:
   ```python
   from django.contrib.auth import get_user_model
   from knox.models import AuthToken
   from appauth.models import AppUser
   user = AppUser.objects.get(email='your_superuser_email')
   token = AuthToken.objects.create(user=user)
   print(token[1])
   ```
   Copy the printed token.
8. Start the Django server:
   ```
   python manage.py runserver
   ```

### Frontend

1. Navigate to the `frontend` directory
2. Install dependencies:
   ```
   npm install
   ```
3. Set up the token:
   - Open `src/constants/token.ts`
   - Replace the existing token value with your copied AuthToken
4. Start the development server:
   ```
   npm run dev
   ```

## Usage

1. Open your browser and go to `http://localhost:5173`
2. Use the superuser credentials to log in
3. Create a new project or select an existing one
4. Start a new chat or continue an existing conversation
5. Use the file manager to upload and attach files to your chats
6. Manage your knowledge base for each project

## API Endpoints

- `/api/v1/auth/`: Authentication endpoints
- `/api/v1/chat/`: Chat and project management endpoints

For a full list of endpoints, refer to the Django URLs configuration.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Follow Me

You can find me on:

- Twitter: [@ngen0me](https://twitter.com/_ngenome)
- LinkedIn: [kelvin-ngeno](https://linkedin.com/in/kelvin-ngeno)

Feel free to reach out for questions, collaborations, or just to connect!
