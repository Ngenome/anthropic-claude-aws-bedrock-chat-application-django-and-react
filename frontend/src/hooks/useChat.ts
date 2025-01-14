import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import token from "@/constants/token";
import urls from "@/constants/urls";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Message, Attachment, SavedSystemPrompt, Chat } from "@/types/chat";

const useChat = (chatId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [savedSystemPrompts, setSavedSystemPrompts] = useState<
    SavedSystemPrompt[]
  >([]);
  const [isLoadingAttachments, setIsLoadingAttachments] = useState(false);
  const [chat, setChat] = useState<Chat | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<Map<string, string>>(
    new Map()
  );
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = useCallback(async (files: File[]) => {
    // Convert FileList to Array if needed
    const fileArray = Array.from(files);
    try {
      setIsUploading(true);
      setSelectedFiles((prev) => [...prev, ...fileArray]);

      // Process previews for images
      fileArray.forEach((file) => {
        if (file.type.startsWith("image/")) {
          const reader = new FileReader();
          reader.onloadend = () => {
            setPreviewUrls((prev) =>
              new Map(prev).set(file.name, reader.result as string)
            );
          };
          reader.readAsDataURL(file);
        }
      });
    } finally {
      setIsUploading(false);
    }
  }, []);

  const handleRemoveFile = useCallback((fileToRemove: File) => {
    setSelectedFiles((prev) => prev.filter((f) => f !== fileToRemove));
    setPreviewUrls((prev) => {
      const newUrls = new Map(prev);
      newUrls.delete(fileToRemove.name);
      return newUrls;
    });
  }, []);

  const clearFiles = useCallback(() => {
    setSelectedFiles([]);
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    setPreviewUrls(new Map());
  }, [previewUrls]);

  const navigate = useNavigate();
  const fetchMessages = useCallback(async () => {
    if (chatId === "new") {
      setMessages([]);
      setSystemPrompt("");
      return;
    }
    try {
      const response = await axios.get(urls.chatMessages(chatId), {
        headers: { Authorization: `Token ${token}` },
      });
      console.log("response.data", response.data);
      setMessages(response.data.messages);
      setSystemPrompt(response.data.system_prompt);
    } catch (error) {
      console.error("Error fetching messages:", error);
      setError("Failed to fetch messages. Please try again.");
      toast.error("Failed to fetch messages");
    }
  }, [chatId]);

  const fetchAttachments = useCallback(async () => {
    setIsLoadingAttachments(true);
    if (chatId === "new") {
      setAttachments([]);
      return;
    }
    try {
      const response = await axios.get(urls.attachments(chatId), {
        headers: { Authorization: `token ${token}` },
      });
      setAttachments(response.data);
    } catch (error) {
      console.error("Error fetching attachments:", error);
      setError("Failed to fetch attachments. Please try again.");
      toast.error("Failed to fetch attachments");
    } finally {
      setIsLoadingAttachments(false);
    }
  }, [chatId]);

  const refreshAttachments = useCallback(() => {
    fetchAttachments();
  }, [fetchAttachments]);

  const fetchSavedSystemPrompts = useCallback(async () => {
    try {
      const response = await axios.get(urls.savedSystemPrompts, {
        headers: { Authorization: `Token ${token}` },
      });
      setSavedSystemPrompts(response.data);
    } catch (error) {
      console.error("Error fetching saved system prompts:", error);
      setError("Failed to fetch saved system prompts. Please try again.");
      toast.error("Failed to fetch saved system prompts");
    }
  }, []);

  const fetchChat = useCallback(async () => {
    if (chatId === "new") {
      setChat(null);
      setSystemPrompt("");
      return;
    }

    try {
      const response = await axios.get(urls.chatDetail(chatId), {
        headers: { Authorization: `Token ${token}` },
      });
      setChat(response.data);
      setSystemPrompt(response.data.system_prompt || "");
    } catch (error) {
      console.error("Error fetching chat:", error);
      setError("Failed to fetch chat details");
      toast.error("Failed to fetch chat details");
    }
  }, [chatId]);

  useEffect(() => {
    fetchChat();
  }, [fetchChat, chatId]);

  useEffect(() => {
    if (chatId !== "new") {
      fetchMessages();
      fetchAttachments();
    } else {
      setMessages([]);
    }
    fetchSavedSystemPrompts();
  }, [chatId, fetchMessages, fetchAttachments, fetchSavedSystemPrompts]);

  const handleSubmit = useCallback(
    async ({
      messageText,
      projectId,
    }: {
      messageText: string;
      projectId?: string;
    }) => {
      if (!messageText.trim() && selectedFiles.length === 0) {
        setError("Please enter a message or attach a file.");
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

      // Add message to UI immediately
      const userMessage: Message = {
        role: "user",
        content: messageText,
        type: "text",
      };

      setMessages((prev) => [...prev, userMessage]);
      setNewMessage("");
      setIsStreaming(true);
      setError(null);

      try {
        const response = await fetch(urls.claude, {
          method: "POST",
          headers: {
            Authorization: `Token ${token}`,
          },
          body: formData,
        });

        if (!response.ok) {
          console.log("response", response);
          // Check if the response is JSON
          const contentType = response.headers.get("content-type");
          if (contentType && contentType.includes("application/json")) {
            const errorData = await response.json();
            throw new Error(errorData.error || "An error occurred");
          } else {
            // Fallback for non-JSON errors
            throw new Error(`HTTP error! status: ${response.status}`);
          }
        }

        let assistantMessage = "";
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("Response body is null");
        }

        let shouldContinue = true;
        while (shouldContinue) {
          const { done, value } = await reader.read();
          if (done) {
            shouldContinue = false;
            break;
          }
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          lines.forEach((line) => {
            if (line.trim() !== "") {
              try {
                const parsed = JSON.parse(line);
                if (parsed.type === "text") {
                  assistantMessage += parsed.content;
                  setMessages((prevMessages) => [
                    ...prevMessages.slice(0, -1),
                    {
                      role: "assistant",
                      content: assistantMessage,
                      type: "text",
                    },
                  ]);
                } else if (parsed.type === "chat_id") {
                  navigate(`/chat/${parsed.content}`);
                }
              } catch (e) {
                console.error("Error parsing stream:", e);
              }
            }
          });
        }
      } catch (error) {
        console.error("Error sending message:", error);
        setError("Failed to send message. Please try again.");
        toast.error("Failed to send message");
      } finally {
        setIsStreaming(false);
        clearFiles(); // Clear files after successful submission
      }
    },
    [chatId, systemPrompt, selectedFiles, clearFiles, navigate]
  );

  const handleAttachment = useCallback(
    async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      try {
        await axios.post(urls.upload(chatId), formData, {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Token ${token}`,
          },
        });
        fetchAttachments();
        toast.success("File uploaded successfully");
      } catch (error) {
        console.error("Error uploading file:", error);
        setError("Failed to upload file. Please try again.");
        toast.error("Failed to upload file");
      }
    },
    [chatId, fetchAttachments]
  );

  const removeAttachment = useCallback(
    async (attachmentId: string) => {
      try {
        await axios.delete(urls.deleteAttachment(attachmentId), {
          headers: { Authorization: `Token ${token}` },
        });
        fetchAttachments();
        toast.success("Attachment removed successfully");
      } catch (error) {
        console.error("Error removing attachment:", error);
        setError("Failed to remove attachment. Please try again.");
        toast.error("Failed to remove attachment");
      }
    },
    [fetchAttachments]
  );

  const handleSystemPromptChange = useCallback((newPrompt: string) => {
    setSystemPrompt(newPrompt);
  }, []);

  const handleSaveSystemPrompt = useCallback(
    async (title: string, prompt: string) => {
      try {
        await axios.post(
          urls.savedSystemPrompts,
          { title, prompt },
          { headers: { Authorization: `Token ${token}` } }
        );
        fetchSavedSystemPrompts();
        toast.success("System prompt saved successfully");
      } catch (error) {
        console.error("Error saving system prompt:", error);
        setError("Failed to save system prompt. Please try again.");
        toast.error("Failed to save system prompt");
      }
    },
    [fetchSavedSystemPrompts]
  );

  const handleUpdateSystemPrompt = useCallback(async () => {
    try {
      await axios.post(
        urls.updateSystemPrompt(chatId),
        { system_prompt: systemPrompt },
        { headers: { Authorization: `Token ${token}` } }
      );
      toast.success("System prompt updated successfully");
    } catch (error) {
      console.error("Error updating system prompt:", error);
      setError("Failed to update system prompt. Please try again.");
      toast.error("Failed to update system prompt");
    }
  }, [chatId, systemPrompt]);

  return {
    messages,
    newMessage,
    fetchMessages,
    setNewMessage,
    isStreaming,
    error,
    attachments,
    systemPrompt,
    savedSystemPrompts,
    isLoadingAttachments,
    handleSubmit,
    handleAttachment,
    removeAttachment,
    handleSystemPromptChange,
    handleSaveSystemPrompt,
    handleUpdateSystemPrompt,
    refreshAttachments,
    chat,
    selectedFiles,
    previewUrls,
    isUploading,
    handleFileSelect,
    handleRemoveFile,
    clearFiles,
  };
};

export default useChat;
