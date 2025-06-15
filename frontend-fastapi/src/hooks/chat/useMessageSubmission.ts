// hooks/useMessageSubmission.ts
import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Message } from "@/types/chat";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { chatService } from "@/services/chat";

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
  const queryClient = useQueryClient();
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

      setNewMessage("");
      setIsStreaming(true);

      try {
        let currentChatId = chatId;

        // If chatId is "new", create a new chat first
        if (chatId === "new") {
          try {
            const newChat = await chatService.createChat({
              title:
                messageText.slice(0, 50) +
                (messageText.length > 50 ? "..." : ""),
              project_id: projectId,
              system_prompt: systemPrompt || undefined,
            });
            currentChatId = newChat.id;
            navigate(`/chat/${currentChatId}`);
            queryClient.invalidateQueries({ queryKey: ["chats"] });
          } catch (error) {
            console.error("Error creating chat:", error);
            toast.error("Failed to create new chat");
            setIsStreaming(false);
            return;
          }
        }

        // Prepare message data
        const messageData = {
          message: messageText,
          files: [], // TODO: Handle file uploads
          system_prompt_override: systemPrompt || undefined,
        };

        // Send message and get streaming response
        const stream = await chatService.sendMessage(
          currentChatId,
          messageData
        );

        let currentAssistantMessage: Message | null = null;

        // Process streaming chunks
        for await (const chunk of chatService.parseStreamingResponse(stream)) {
          switch (chunk.type) {
            case "text": {
              if (chunk.content && currentAssistantMessage) {
                // Update the assistant message with new text content
                setMessages((prev) => {
                  const updated = prev.map((msg) => {
                    if (msg.id === currentAssistantMessage?.id) {
                      return {
                        ...msg,
                        contents: msg.contents.map((content) =>
                          content.content_type === "text"
                            ? {
                                ...content,
                                text_content:
                                  (content.text_content || "") + chunk.content,
                              }
                            : content
                        ),
                      };
                    }
                    return msg;
                  });
                  return [...updated]; // Ensure new array reference for React re-render
                });
              }
              break;
            }

            case "start": {
              // Changed from "message_start" to "start"
              // Create user message
              const userMessage: Message = {
                id: `user-${Date.now()}`, // Temporary ID
                role: "user",
                contents: [
                  {
                    id: `content-${Date.now()}`,
                    content_type: "text",
                    text_content: messageText,
                    mime_type: undefined,
                    created_at: new Date().toISOString(),
                    edited_at: null,
                  },
                ],
                message_pair: "",
                hidden: false,
                created_at: new Date().toISOString(),
              };

              // Create assistant message (empty initially)
              currentAssistantMessage = {
                id: `assistant-${Date.now()}`, // Temporary ID
                role: "assistant",
                contents: [
                  {
                    id: `content-${Date.now()}-assistant`,
                    content_type: "text",
                    text_content: "",
                    mime_type: undefined,
                    created_at: new Date().toISOString(),
                    edited_at: null,
                  },
                ],
                message_pair: "",
                hidden: false,
                created_at: new Date().toISOString(),
              };

              if (chunk.message_pair_id) {
                userMessage.message_pair = chunk.message_pair_id;
                currentAssistantMessage.message_pair = chunk.message_pair_id;
              }

              setMessages((prev) => [
                ...prev,
                userMessage,
                currentAssistantMessage!,
              ]);
              break;
            }

            case "error": {
              console.error("Stream error:", chunk.error);
              toast.error(
                chunk.error || "An error occurred while processing your message"
              );
              break;
            }

            case "done": {
              // Refresh messages to get the final state from the server
              queryClient.invalidateQueries({
                queryKey: ["chat", currentChatId, "messages"],
              });
              break;
            }

            default: {
              console.log("Unknown chunk type:", chunk.type, chunk);
              break;
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
      queryClient,
    ]
  );

  return { handleSubmit };
};
