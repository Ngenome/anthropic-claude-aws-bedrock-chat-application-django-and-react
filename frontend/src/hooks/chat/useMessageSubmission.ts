// hooks/useMessageSubmission.ts
import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import token from "@/constants/token";
import urls from "@/constants/urls";
import { Message } from "@/types/chat";
import { toast } from "sonner";

export const useMessageSubmission = ({
  chatId,
  systemPrompt,
  selectedFiles,
  clearFiles,
  setMessages,
  setNewMessage,
  setIsStreaming,
}: {
  chatId: string;
  systemPrompt: string;
  selectedFiles: File[];
  clearFiles: () => void;
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  setNewMessage: React.Dispatch<React.SetStateAction<string>>;
  setIsStreaming: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
  const navigate = useNavigate();

  const handleSubmit = useCallback(
    async ({
      messageText,
      projectId,
    }: {
      messageText: string;
      projectId?: string;
    }) => {
      if (!messageText.trim() && selectedFiles.length === 0) {
        toast.error("Please enter a message or attach a file.");
        return;
      }

      const formData = new FormData();
      formData.append("message", messageText);
      formData.append("chat_id", chatId || "new");
      if (projectId) {
        formData.append("project_id", projectId);
      }
      if (systemPrompt) {
        formData.append("system_prompt", systemPrompt);
      }
      selectedFiles.forEach((file) => {
        formData.append("files", file);
      });

      setNewMessage("");
      setIsStreaming(true);

      try {
        const response = await fetch(urls.chat, {
          method: "POST",
          headers: { Authorization: `Token ${token}` },
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("Response body is null");
        }

        let currentAssistantMessage: Message | null = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (!line.trim()) continue;

            try {
              const parsed = JSON.parse(line);

              switch (parsed.type) {
                case "message":
                  if (parsed.message.role === "assistant") {
                    currentAssistantMessage = parsed.message;
                    setMessages((prev) => [...prev, parsed.message]);
                  } else {
                    setMessages((prev) => [...prev, parsed.message]);
                  }
                  break;

                case "content":
                  if (currentAssistantMessage) {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === parsed.message_id
                          ? {
                              ...msg,
                              contents: msg.contents.map((content) =>
                                content.content_type === "text"
                                  ? {
                                      ...content,
                                      text_content:
                                        content.text_content + parsed.content,
                                    }
                                  : content
                              ),
                            }
                          : msg
                      )
                    );
                  }
                  break;

                case "chat_id":
                  navigate(`/chat/${parsed.content}`);
                  break;
              }
            } catch (e) {
              console.error("Error parsing stream:", e);
            }
          }
        }
      } catch (error) {
        console.error("Error sending message:", error);
        toast.error("Failed to send message");
      } finally {
        setIsStreaming(false);
        clearFiles();
      }
    },
    [
      chatId,
      systemPrompt,
      selectedFiles,
      clearFiles,
      navigate,
      setMessages,
      setNewMessage,
      setIsStreaming,
    ]
  );

  return { handleSubmit };
};
