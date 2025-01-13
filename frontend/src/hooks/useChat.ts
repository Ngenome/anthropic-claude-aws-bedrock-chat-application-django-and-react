import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import token from "@/constants/token";
import urls from "@/constants/urls";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

interface Message {
  role: string;
  content: string;
  type?: string;
}

interface Attachment {
  id: string;
  name: string;
  url: string;
}

interface SavedSystemPrompt {
  id: string;
  title: string;
  prompt: string;
}

interface Chat {
  id: number;
  title: string;
  date: string;
  system_prompt: string | null;
  project?: number;
  user: number;
}

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
  const navigate = useNavigate();
  const fetchMessages = useCallback(async () => {
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
      const response = await axios.get(urls.chat(chatId), {
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
    async (
      e: React.FormEvent,
      {
        attachedFileIds,
        projectId,
      }: {
        attachedFileIds: string[];
        projectId: number | undefined;
      }
    ) => {
      e.preventDefault();
      if (!newMessage.trim() && attachedFileIds.length === 0) {
        setError("Please enter a message or attach a file.");
        toast.error(`Please enter a message or attach a file. ${newMessage}`);

        return;
      }

      const userMessage = { role: "user", content: newMessage };
      setMessages((prevMessages) => [...prevMessages, userMessage]);
      setNewMessage("");
      setIsStreaming(true);
      setError(null);

      try {
        const response = await fetch(urls.claude, {
          method: "POST",
          headers: {
            Authorization: `token ${token}`,
            "Content-Type": "application/json",
            Accept: "application/json, text/plain, */*",
          },
          body: JSON.stringify({
            chat_id: chatId,
            message: newMessage,
            attachment_ids: attachedFileIds,
            project_id: projectId,
            system_prompt: systemPrompt,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error(response.statusText);
        }

        let assistantMessage = "";
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
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
                    { role: "assistant", content: assistantMessage },
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
      }
    },
    [chatId, newMessage, navigate, systemPrompt]
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
  };
};

export default useChat;
