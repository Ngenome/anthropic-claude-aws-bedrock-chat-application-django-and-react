import { ChatContextType } from "@/types/chat-context";
import { useContext } from "react";
import ChatContext from "@/context/ChatContext";

const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

export default useChat;
