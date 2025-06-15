// hooks/chat/useFetchChat.ts
import { useState, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import token from "@/constants/token";
import urls from "@/constants/urls";
import { Chat } from "@/types/chat";

export const useFetchChat = (chatId: string) => {
  const [chat, setChat] = useState<Chat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchChat = useCallback(async () => {
    if (chatId === "new") {
      setChat(null);
      return;
    }

    try {
      const response = await axios.get(urls.chatDetail(chatId), {
        headers: { Authorization: `Token ${token}` },
      });
      setChat(response.data);
    } catch (error) {
      console.error("Error fetching chat:", error);
      setError("Failed to fetch chat details");
      toast.error("Failed to fetch chat details");
    }
  }, [chatId]);

  return { chat, error, fetchChat };
};
