// hooks/useSystemPrompts.ts
import { useState, useCallback } from "react";
import { toast } from "sonner";
import { SavedSystemPrompt } from "@/types/chat";
import { chatService } from "@/services/chat";

export const useSystemPrompts = (chatId: string) => {
  const [systemPrompt, setSystemPrompt] = useState("");
  const [savedSystemPrompts, setSavedSystemPrompts] = useState<
    SavedSystemPrompt[]
  >([]);

  const fetchSavedSystemPrompts = useCallback(async () => {
    try {
      const response = await chatService.getSavedSystemPrompts();
      setSavedSystemPrompts(response);
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
        await chatService.createSavedSystemPrompt({ title, prompt });
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
      await chatService.updateChat(chatId, { system_prompt: systemPrompt });
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
