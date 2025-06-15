import React, { useRef, useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import useChat from "@/hooks/useChat";
import { TokenUsageBar } from "./TokenUsageBar";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { useChatTokens } from "@/hooks/useChatTokens";
import { ProjectDrawer } from "./ProjectDrawer";
import { useProject, useProjectChats } from "@/hooks/useProjects";

import { Loader2, Sidebar } from "lucide-react";
import { toast } from "sonner";
import { UserMessage, AssistantMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ChatProvider } from "@/context/ChatContext";

const MessageList = React.memo(() => {
  const { messages, isStreaming } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const prevMessagesLength = useRef(messages.length);

  useEffect(() => {
    if (isStreaming || messages.length > prevMessagesLength.current) {
      const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      };
      requestAnimationFrame(scrollToBottom);
    }
    prevMessagesLength.current = messages.length;
  }, [messages.length, isStreaming]);

  const renderMessage = useCallback((message: Message) => {
    return message.role === "user" ? (
      <UserMessage key={message.id} message={message} />
    ) : (
      <AssistantMessage key={message.id} message={message} />
    );
  }, []);

  return (
    <ScrollArea className="overflow-y-auto relative">
      <div className="max-w-3xl mx-auto" ref={listRef}>
        {messages?.length === 0 ? (
          <div className="flex items-center justify-center h-full min-h-[400px]">
            <h1 className="text-2xl font-semibold text-muted-foreground">
              What can I help with?
            </h1>
          </div>
        ) : (
          messages.map(renderMessage)
        )}
        {isStreaming && (
          <div className="flex items-center justify-center p-4">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </ScrollArea>
  );
});

MessageList.displayName = "MessageList";
export default function ChatContainer() {
  const { chatId } = useParams<{
    chatId: string;
  }>();

  return (
    <ChatProvider chatId={chatId || "new"}>
      <Chat />
    </ChatProvider>
  );
}
function Chat() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get("projectId");
  const { chatId } = useParams<{
    chatId: string;
  }>();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { error, chat } = useChat();
  const { data: tokenStats } = useChatTokens(chatId);
  const { data: project } = useProject(chat?.project?.toString() || "");
  const { data: projectChats } = useProjectChats(
    chat?.project?.toString() || ""
  );

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  return (
    <div
      className={`flex flex-col h-full max-h-screen relative bg-background transition-[margin] duration-200 ease-in-out ${
        drawerOpen ? "mr-80" : ""
      }`}
    >
      <div className="flex-none px-4 w-full mx-auto py-2 border-b border-border">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          {tokenStats && (
            <TokenUsageBar
              current={tokenStats.total_tokens}
              max={200000}
              label="Chat Token Usage:"
            />
          )}

          {project && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDrawerOpen(true)}
              className="bg-background ml-4 whitespace-nowrap"
            >
              <Sidebar className="h-4 w-4 mr-2" />
              <span className="truncate max-w-[150px]">{project.name}</span>
            </Button>
          )}
        </div>
      </div>

      <MessageList />

      <div className="flex-none bg-background ">
        <div className="max-w-3xl mx-auto">
          <ChatInput projectId={projectId || undefined} />
          <div className="mt-2 text-xs text-center text-muted-foreground">
            This chatbot can make mistakes. Consider checking important
            information.
          </div>
        </div>
      </div>

      {project && (
        <ProjectDrawer
          isOpen={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          projectId={project.id}
          recentChats={projectChats?.slice(0, 5) || []}
        />
      )}
    </div>
  );
}
