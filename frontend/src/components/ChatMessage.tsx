import React from "react";
import MarkdownPreview from "@uiw/react-markdown-preview";
import { Message } from "@/types/chat";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import { Copy, CheckCheck } from "lucide-react";
import { toast } from "sonner";

interface ChatMessageProps {
  message: Message;
}

export function UserMessage({ message }: ChatMessageProps) {
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
    <div className="flex gap-2 mb-4 items-start">
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
        U
      </div>
      <div className="flex-1">
        <div className="relative group">
          <div className="p-4 rounded-lg bg-blue-100 dark:bg-blue-900/50">
            <p className="whitespace-pre-wrap text-gray-800 dark:text-gray-200">
              {message.content}
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={copyToClipboard}
          >
            {copied ? (
              <CheckCheck className="h-4 w-4" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        </div>
        <span className="text-xs text-gray-500 ml-2">
          {new Date(message.timestamp || Date.now()).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}

export function AssistantMessage({ message }: ChatMessageProps) {
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
    <div className="flex gap-2 mb-4 items-start">
      <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white font-semibold">
        A
      </div>
      <div className="flex-1">
        <div className="relative group">
          <div className="p-4 rounded-lg bg-gray-100 dark:bg-gray-800">
            <MarkdownPreview source={message.content} />
            <div className="flex justify-end mt-2">
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={copyToClipboard}
              >
                {copied ? (
                  <CheckCheck className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200" />
                )}
              </Button>
            </div>
          </div>
        </div>
        <span className="text-xs text-gray-500 ml-2">
          {new Date(message.timestamp || Date.now()).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
