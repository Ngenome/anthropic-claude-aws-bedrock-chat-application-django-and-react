// hooks/useSystemPrompts.ts
import { useState, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import token from "@/constants/token";
import urls from "@/constants/urls";
import { SavedSystemPrompt } from "@/types/chat";

export const useSystemPrompts = (chatId: string) => {
  const [systemPrompt, setSystemPrompt] = useState("");
  const [savedSystemPrompts, setSavedSystemPrompts] = useState<
    SavedSystemPrompt[]
  >([]);

  const fetchSavedSystemPrompts = useCallback(async () => {
    try {
      const response = await axios.get(urls.savedSystemPrompts, {
        headers: { Authorization: `Token ${token}` },
      });
      setSavedSystemPrompts(response.data);
    } catch (error) {
      console.error("Error fetching saved system prompts:", error);
      toast.error("Failed to fetch saved system prompts");
    }
  }, []);

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
      toast.error("Failed to update system prompt");
    }
  }, [chatId, systemPrompt]);

  return {
    systemPrompt,
    savedSystemPrompts,
    setSystemPrompt,
    handleSystemPromptChange,
    handleSaveSystemPrompt,
    handleUpdateSystemPrompt,
    fetchSavedSystemPrompts,
  };
};
