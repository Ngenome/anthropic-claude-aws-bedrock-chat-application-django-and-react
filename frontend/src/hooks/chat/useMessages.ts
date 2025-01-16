// hooks/useMessages.ts
import { useState, useCallback } from "react";
import { toast } from "sonner";
import token from "@/constants/token";
import urls from "@/constants/urls";
import { Message } from "@/types/chat";

export const useMessages = (chatId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);

  const fetchMessages = useCallback(async () => {
    if (chatId === "new") return;

    try {
      const response = await fetch(urls.chatMessages(chatId), {
        headers: { Authorization: `Token ${token}` },
      });
      const data = await response.json();
      setMessages(data.messages);
    } catch (error) {
      console.error("Error fetching messages:", error);
      toast.error("Failed to fetch messages");
    }
  }, [chatId]);

  const handleEditMessage = useCallback(
    async (messageId: string, newText: string) => {
      try {
        const response = await fetch(urls.editMessage(messageId), {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Token ${token}`,
          },
          body: JSON.stringify({ text: newText }),
        });

        if (!response.ok) throw new Error("Failed to edit message");

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId
              ? {
                  ...msg,
                  contents: msg.contents.map((content) =>
                    content.content_type === "text"
                      ? { ...content, text_content: newText }
                      : content
                  ),
                }
              : msg
          )
        );

        toast.success("Message edited successfully");
      } catch (error) {
        console.error("Error editing message:", error);
        toast.error("Failed to edit message");
      }
    },
    []
  );

  const handleDeleteMessagePair = useCallback(async (messageId: string) => {
    try {
      await fetch(urls.deleteMessagePair(messageId), {
        method: "DELETE",
        headers: { Authorization: `Token ${token}` },
      });
    } catch (error) {
      console.error("Error deleting message pair:", error);
      toast.error("Failed to delete message pair");
    }
  }, []);

  const handleToggleMessagePair = useCallback(async (messageId: string) => {
    try {
      await fetch(urls.toggleMessagePair(messageId), {
        method: "PATCH",
        headers: { Authorization: `Token ${token}` },
      });
    } catch (error) {
      console.error("Error toggling message pair:", error);
      toast.error("Failed to toggle message pair");
    }
  }, []);

  return {
    messages,
    setMessages,
    fetchMessages,
    handleEditMessage,
    handleDeleteMessagePair,
    handleToggleMessagePair,
  };
};
