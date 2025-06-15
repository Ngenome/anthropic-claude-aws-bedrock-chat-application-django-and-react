// hooks/chat/useFetchChat.ts
import { useState, useCallback } from "react";
import { toast } from "sonner";
import { Chat } from "@/types/chat";
import { chatService } from "@/services/chat";

export const useFetchChat = (chatId: string) => {
  const [chat, setChat] = useState<Chat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchChat = useCallback(async () => {
    if (chatId === "new") {
      setChat(null);
      return;
    }

    try {
      const response = await chatService.getChat(chatId);
      setChat(response);
    } catch (error) {
      console.error("Error fetching chat:", error);
      setError("Failed to fetch chat details");
      toast.error("Failed to fetch chat details");
    }
  }, [chatId]);

  return { chat, error, fetchChat };
};
