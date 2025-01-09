import React, { useRef, useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import useChat from "@/hooks/useChat";
import { TokenUsageBar } from "./TokenUsageBar";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { useChatTokens } from "@/hooks/useChatTokens";
import { ProjectDrawer } from "./ProjectDrawer";
import { useProject, useProjectChats } from "@/hooks/useProjects";

import { Loader2, Sidebar } from "lucide-react";
import { toast } from "sonner";
import { UserMessage, AssistantMessage } from "./ChatMessage";

export default function Chat() {
  const { chatId } = useParams<{
    chatId: string;
  }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get("projectId");

  const [drawerOpen, setDrawerOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const {
    messages,
    handleSubmit,
    isStreaming,
    error,
    newMessage,
    setNewMessage,
    chat,
  } = useChat(chatId || "new");
  const { data: tokenStats } = useChatTokens(chatId);
  const { data: project } = useProject(chat?.project?.toString() || "");
  const { data: projectChats } = useProjectChats(
    chat?.project?.toString() || ""
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isStreaming) return;

    try {
      await handleSubmit(e, {
        attachedFileIds: [],
        projectId: projectId ? parseInt(projectId) : undefined,
      });
      setNewMessage("");
    } catch (error) {
      console.error("Failed to send message:", error);
      toast.error("Failed to send message. Please try again.");
    }
  };

  return (
    <div className="flex flex-col h-full max-h-screen relative">
      {tokenStats && (
        <div className="flex-none px-4 py-2 border-b bg-gray-50 dark:bg-gray-900 w-[30%]">
          <TokenUsageBar
            current={tokenStats.total_tokens}
            max={200000}
            label="Chat Token Usage"
          />
        </div>
      )}

      {project && (
        <div className="absolute top-4 right-4 z-10">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDrawerOpen(true)}
          >
            <Sidebar className="h-4 w-4 mr-2" />
            {project.name}
          </Button>
        </div>
      )}

      <ScrollArea className="flex-1 p-4">
        {messages?.map((message, i) =>
          message.role === "user" ? (
            <UserMessage key={i} message={message} />
          ) : (
            <AssistantMessage key={i} message={message} />
          )
        )}
        {isStreaming && (
          <div className="flex items-center justify-center p-4">
            <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </ScrollArea>

      <form onSubmit={onSubmit} className="flex-none p-4 border-t">
        <div className="flex gap-2">
          <Textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1"
            rows={3}
            disabled={isStreaming}
          />
          <Button
            type="submit"
            disabled={isStreaming || !newMessage.trim()}
            className="min-w-[80px]"
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Send"
            )}
          </Button>
        </div>
      </form>

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
