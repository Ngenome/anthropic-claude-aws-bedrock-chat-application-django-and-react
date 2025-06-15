// hooks/useMessages.ts
import { useState, useCallback } from "react";
import { toast } from "sonner";
import { Message } from "@/types/chat";
import { chatService } from "@/services/chat";

export const useMessages = (chatId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);

  const fetchMessages = useCallback(async () => {
    if (chatId === "new") return;

    try {
      const chatDetail = await chatService.getChat(chatId);
      // Extract messages from message pairs
      const allMessages: Message[] = [];
      if (chatDetail.message_pairs) {
        chatDetail.message_pairs.forEach((pair: { messages: Message[] }) => {
          allMessages.push(...pair.messages);
        });
      }
      setMessages(allMessages);
    } catch (error) {
      console.error("Error fetching messages:", error);
      toast.error("Failed to fetch messages");
    }
  }, [chatId]);

  const handleEditMessage = useCallback(
    async (messageId: string, newText: string) => {
      try {
        // TODO: Implement message editing API call
        console.log("Edit message:", messageId, newText);

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
      // TODO: Implement message pair deletion API call
      console.log("Delete message pair:", messageId);

      // Remove message from local state for now
      setMessages((prev) => prev.filter((msg) => msg.id !== messageId));
      toast.success("Message deleted successfully");
    } catch (error) {
      console.error("Error deleting message pair:", error);
      toast.error("Failed to delete message pair");
    }
  }, []);

  const handleToggleMessagePair = useCallback(async (messageId: string) => {
    try {
      // TODO: Implement message pair toggle API call
      console.log("Toggle message pair:", messageId);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, hidden: !msg.hidden } : msg
        )
      );
      toast.success("Message visibility toggled");
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
