import React, { useRef, useEffect, useState } from "react";
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
import axios from "axios";
import urls from "@/constants/urls";
import { Message } from "@/types/chat";
import token from "@/constants/token";

const MessageList = React.memo(
  ({
    messages,
    isStreaming,
    onEditMessage,
    onDeleteMessagePair,
    onToggleMessagePair,
  }: {
    messages: Message[];
    isStreaming: boolean;
    onEditMessage: (messageId: string, newText: string) => Promise<void>;
    onDeleteMessagePair: (pairId: string) => Promise<void>;
    onToggleMessagePair: (pairId: string, hidden: boolean) => Promise<void>;
  }) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // useEffect(() => {
    //   requestAnimationFrame(() => {
    //     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    //   });
    // }, [messages]);

    return (
      <div className="max-w-3xl mx-auto">
        {messages?.length === 0 && (
          <div className="flex items-center justify-center h-full min-h-[400px]">
            <h1 className="text-2xl font-semibold text-gray-500 dark:text-gray-400">
              What can I help with?
            </h1>
          </div>
        )}

        {messages?.map((message, i) =>
          message.role === "user" ? (
            <UserMessage
              key={i}
              message={message}
              onEdit={onEditMessage}
              onDelete={onDeleteMessagePair}
              onToggle={onToggleMessagePair}
            />
          ) : (
            <AssistantMessage
              key={i}
              message={message}
              onEdit={onEditMessage}
              onDelete={onDeleteMessagePair}
              onToggle={onToggleMessagePair}
            />
          )
        )}
        {isStreaming && (
          <div className="flex items-center justify-center p-4">
            <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    );
  },
  (prevProps, nextProps) => {
    return (
      prevProps.isStreaming === nextProps.isStreaming &&
      prevProps.messages.length === nextProps.messages.length &&
      prevProps.messages.every(
        (msg, i) =>
          msg.id === nextProps.messages[i].id &&
          msg.content === nextProps.messages[i].content
      )
    );
  }
);

MessageList.displayName = "MessageList";

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
    fetchMessages,
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

  const handleEditMessage = async (messageId: string, newText: string) => {
    // if message ID is undefined, show a toast
    if (!messageId) {
      toast.error("Message ID is undefined");
      return;
    }
    try {
      await axios.patch(
        `${urls.editMessage(messageId)}`,
        { text: newText },
        { headers: { Authorization: `Token ${token}` } }
      );

      // If this was a user message, we need to get a new response
      const message = messages.find((m) => m.id === messageId);
      if (message?.role === "user") {
        await handleSubmit(new Event("submit") as any, {
          editedMessageId: messageId,
          attachedFileIds: [],
        });
      }

      // Refresh messages
      await fetchMessages();
    } catch (error) {
      toast.error("Failed to edit message");
    }
  };

  const handleDeleteMessagePair = async (pairId: string) => {
    try {
      await axios.delete(`${urls.deleteMessagePair(pairId)}`, {
        headers: { Authorization: `Token ${token}` },
      });
      await fetchMessages();
      toast.success("Message pair deleted");
    } catch (error) {
      toast.error("Failed to delete message pair");
    }
  };

  const handleToggleMessagePair = async (pairId: string, hidden: boolean) => {
    try {
      await axios.patch(
        `${urls.toggleMessagePair(pairId)}`,
        { hidden },
        { headers: { Authorization: `Token ${token}` } }
      );
      await fetchMessages();
      toast.success(hidden ? "Message pair hidden" : "Message pair shown");
    } catch (error) {
      toast.error("Failed to toggle message pair");
    }
  };

  return (
    <div className="flex flex-col h-full max-h-screen relative bg-gray-50 dark:bg-gray-900">
      {tokenStats && (
        <div className="flex-none px-4 max-w-3xl mx-auto py-2 border-b dark:border-gray-800">
          <TokenUsageBar
            current={tokenStats.total_tokens}
            max={200000}
            label="Chat Token Usage:"
          />
        </div>
      )}

      {project && (
        <div className="absolute top-4 right-4 z-10">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDrawerOpen(true)}
            className="bg-white dark:bg-gray-800"
          >
            <Sidebar className="h-4 w-4 mr-2" />
            {project.name}
          </Button>
        </div>
      )}

      <ScrollArea className="flex-1 overflow-y-auto">
        <MessageList
          messages={messages}
          isStreaming={isStreaming}
          onEditMessage={handleEditMessage}
          onDeleteMessagePair={handleDeleteMessagePair}
          onToggleMessagePair={handleToggleMessagePair}
        />
      </ScrollArea>

      <div className="flex-none p-4 bg-white dark:bg-gray-900 border-t dark:border-gray-800">
        <ChatInput
          onSubmit={onSubmit}
          newMessage={newMessage}
          setNewMessage={setNewMessage}
          isStreaming={isStreaming}
        />
        <div className="mt-2 text-xs text-center text-gray-400">
          This chatbot can make mistakes. Consider checking important
          information.
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
