import { Message, Attachment, SavedSystemPrompt, Chat } from "@/types/chat";

export interface ChatContextType {
  messages: Message[];
  newMessage: string;
  isStreaming: boolean;
  error: string | null;
  attachments: Attachment[];
  systemPrompt: string;
  savedSystemPrompts: SavedSystemPrompt[];
  isLoadingAttachments: boolean;
  chat: Chat | null;
  selectedFiles: File[];
  previewUrls: Map<string, string>;
  isUploading: boolean;

  // Methods
  fetchMessages: () => Promise<void>;
  setNewMessage: (message: string) => void;
  handleSubmit: (params: {
    messageText: string;
    projectId?: string;
  }) => Promise<void>;
  handleAttachment: (file: File) => Promise<void>;
  removeAttachment: (attachmentId: string) => Promise<void>;
  handleSystemPromptChange: (newPrompt: string) => void;
  handleSaveSystemPrompt: (title: string, prompt: string) => Promise<void>;
  handleUpdateSystemPrompt: () => Promise<void>;
  refreshAttachments: () => void;
  handleFileSelect: (files: File[]) => Promise<void>;
  handleRemoveFile: (fileToRemove: File) => void;
  clearFiles: () => void;
}
