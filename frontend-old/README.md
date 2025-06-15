# Chat Application

A React-based chat interface designed to interact with a Claude AI backend, featuring real-time message streaming, file attachments, and customizable system prompts.

## Features

- **Real-time Chat Interface**
  - Message streaming with Claude AI
  - Markdown rendering for assistant responses
  - Message history with user/assistant avatars
  - Typing indicators and loading states

- **File Management**
  - Upload and attach files to conversations
  - Support for multiple file types (.txt, .pdf, .doc, .docx, .zip)
  - File context management within conversations
  - Attachment sidebar for easy file access

- **System Prompt Management**
  - Save and reuse system prompts
  - Update system prompts for existing conversations
  - Configurable prompt templates

- **UI Components**
  - Clean, modern interface using shadcn/ui components
  - Responsive design with mobile support
  - Toast notifications for user feedback
  - Loading states and error handling

## Technical Stack

- React 
- TypeScript
- Vite
- React Router DOM
- Axios
- Tailwind CSS
- shadcn/ui components
- Radix UI primitives

## Project Structure

```
src/
├── components/        # React components
│   ├── ui/           # Reusable UI components
│   └── ...           # Feature-specific components
├── constants/        # Configuration and URLs
├── hooks/           # Custom React hooks
└── lib/            # Utility functions
```

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure API endpoint:
Update `src/constants/urls.ts` with your backend URL.

3. Set authentication:
Update `src/constants/token.ts` with your API token.

4. Start development server:
```bash
npm run dev
```

## API Integration

The application expects a backend API that supports:
- Message streaming
- File uploads and management
- System prompt configuration
- Chat history management

## Development

Built using Vite for fast development and TypeScript for type safety. Uses modern React patterns including hooks and functional components.

The project follows a component-based architecture with shared UI components from shadcn/ui for consistent styling and behavior.

## Security Notes

- API token should be secured and not committed to version control
- File uploads should be validated on both client and server
- System prompts should be reviewed for safety and compliance
