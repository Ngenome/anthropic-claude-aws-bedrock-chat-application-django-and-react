import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import urls from "@/constants/urls";
import token from "@/constants/token";

interface TokenStats {
  message_tokens: number;
  project_tokens: number;
  total_tokens: number;
  max_tokens: number;
  usage_percentage: number;
}

export function useChatTokens(chatId?: string) {
  return useQuery({
    queryKey: ["chats", chatId, "tokens"],
    queryFn: async () => {
      if (!chatId) return null;
      const { data } = await axios.get<TokenStats>(urls.chatTokens(chatId), {
        headers: {
          Authorization: `Token ${token}`,
        },
      });
      return data;
    },
    enabled: !!chatId && chatId !== "new",
  });
}
