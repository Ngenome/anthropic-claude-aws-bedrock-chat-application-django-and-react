// ChatContext.tsx
import React, { createContext, useEffect, useState } from "react";
import { ChatContextType } from "@/types/chat-context";
import { useSystemPrompts } from "@/hooks/chat/useSystemPrompts";
import { useFetchChat } from "@/hooks/chat/useFetchChat";
import { useMessages } from "@/hooks/chat/useMessages";

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{
  children: React.ReactNode;
  chatId: string;
  projectId?: string;
}> = ({ children, chatId }) => {
  const [isStreaming, setIsStreaming] = useState(false);

  const {
    systemPrompt,
    savedSystemPrompts,
    setSystemPrompt,
    handleSystemPromptChange,
    handleSaveSystemPrompt,
    handleUpdateSystemPrompt,
    fetchSavedSystemPrompts,
  } = useSystemPrompts(chatId);

  const { chat, error, fetchChat } = useFetchChat(chatId);

  const {
    messages,
    setMessages,
    fetchMessages,
    handleEditMessage,
    handleDeleteMessagePair,
    handleToggleMessagePair,
  } = useMessages(chatId);

  useEffect(() => {
    fetchChat();
  }, [fetchChat]);

  useEffect(() => {
    if (chatId !== "new") {
      fetchMessages();
    } else {
      setMessages([]);
    }
    fetchSavedSystemPrompts();
  }, [chatId, fetchMessages, fetchSavedSystemPrompts, setMessages]);

  const value = {
    messages,
    setMessages,
    error,
    isStreaming,
    systemPrompt,
    setSystemPrompt,
    savedSystemPrompts,
    chat,
    fetchMessages,
    handleSystemPromptChange,
    handleSaveSystemPrompt,
    handleUpdateSystemPrompt,
    handleEditMessage,
    handleDeleteMessagePair,
    handleToggleMessagePair,
    setIsStreaming,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

export default ChatContext;
