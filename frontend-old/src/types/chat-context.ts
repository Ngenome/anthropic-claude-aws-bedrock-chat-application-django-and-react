import { Message, SavedSystemPrompt, Chat } from "@/types/chat";

export interface ChatContextType {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  error: string | null;
  isStreaming: boolean;
  systemPrompt: string;
  savedSystemPrompts: SavedSystemPrompt[];
  chat: Chat | null;
  fetchMessages: () => Promise<void>;
  handleSystemPromptChange: (prompt: string) => void;
  handleSaveSystemPrompt: (title: string, prompt: string) => Promise<void>;
  handleUpdateSystemPrompt: () => Promise<void>;
  handleEditMessage: (messageId: string, newText: string) => Promise<void>;
  handleDeleteMessagePair: (pairId: string) => Promise<void>;
  handleToggleMessagePair: (pairId: string, hidden: boolean) => Promise<void>;
  setSystemPrompt: React.Dispatch<React.SetStateAction<string>>;
  setIsStreaming: React.Dispatch<React.SetStateAction<boolean>>;
}
