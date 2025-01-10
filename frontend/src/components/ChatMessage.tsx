import React from "react";
import Markdown from "react-markdown";
import { Message } from "@/types/chat";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import { Copy, CheckCheck } from "lucide-react";
import { toast } from "sonner";
import { UserIcon, BotIcon } from "lucide-react";
import remarkGfm from "remark-gfm";

interface ChatMessageProps {
  message: Message;
}

export const UserMessage = ({ message }: ChatMessageProps) => {
  const [copied, setCopied] = React.useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Message copied to clipboard");
    } catch (err) {
      toast.error("Failed to copy message");
    }
  };

  return (
    <div className="px-4 py-6 bg-white dark:bg-gray-800">
      <div className="max-w-3xl mx-auto flex gap-4">
        <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
          <UserIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </div>
        <div className="flex-1">
          <div className="relative group prose dark:prose-invert max-w-none">
            {message.content}
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={copyToClipboard}
            >
              {copied ? (
                <CheckCheck className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
          <span className="text-xs text-gray-500 mt-2 block">
            {new Date(message.timestamp || Date.now()).toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export const AssistantMessage = ({ message }: ChatMessageProps) => {
  const [copied, setCopied] = React.useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Message copied to clipboard");
    } catch (err) {
      toast.error("Failed to copy message");
    }
  };

  return (
    <div className="px-4 py-6 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-3xl mx-auto flex gap-4">
        <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
          <BotIcon className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <div className="relative group prose dark:prose-invert max-w-none">
            <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={copyToClipboard}
            >
              {copied ? (
                <CheckCheck className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
          <span className="text-xs text-gray-500 mt-2 block">
            {new Date(message.timestamp || Date.now()).toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
};
