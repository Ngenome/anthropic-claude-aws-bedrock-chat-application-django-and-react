import React, { useState } from "react";
import Markdown from "react-markdown";
import { Message } from "@/types/chat";
import { Button } from "./ui/button";
import {
  Copy,
  CheckCheck,
  Pencil,
  X,
  Check,
  MoreVertical,
  Trash,
  Eye,
  Maximize2,
} from "lucide-react";
import { toast } from "sonner";
import { UserIcon, BotIcon } from "lucide-react";
import remarkGfm from "remark-gfm";
import { CodeBlock } from "./CodeBlock";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Textarea } from "./ui/textarea";
import { FullScreenCode } from "./FullScreenCode";

interface ChatMessageProps {
  message: Message;
  onEdit?: (messageId: string, newText: string) => Promise<void>;
  onDelete?: (pairId: string) => Promise<void>;
  onToggle?: (pairId: string, hidden: boolean) => Promise<void>;
  isHidden?: boolean;
}

const MessageControls = ({
  isEditing,
  setIsEditing,
  onDelete,
  onToggle,
  isHidden,
  message,
  copied,
  onCopy,
}: {
  isEditing: boolean;
  setIsEditing: (editing: boolean) => void;
  onDelete?: () => void;
  onToggle?: () => void;
  isHidden?: boolean;
  message: Message;
  copied: boolean;
  onCopy: () => void;
}) => (
  <div className="absolute top-0 right-0 flex gap-2">
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm">
          <MoreVertical className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => setIsEditing(true)}>
          <Pencil className="h-4 w-4 mr-2" />
          Edit
        </DropdownMenuItem>
        {onToggle && (
          <DropdownMenuItem onClick={onToggle}>
            <Eye className="h-4 w-4 mr-2" />
            {isHidden ? "Show" : "Hide"}
          </DropdownMenuItem>
        )}
        {onDelete && (
          <DropdownMenuItem onClick={onDelete} className="text-red-600">
            <Trash className="h-4 w-4 mr-2" />
            Delete
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
    <Button variant="ghost" size="sm" onClick={onCopy}>
      {copied ? (
        <CheckCheck className="h-4 w-4" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </Button>
  </div>
);

// Extract timestamp into a separate memoized component
const MessageTimestamp = React.memo(
  ({
    timestamp,
    editedAt,
  }: {
    timestamp: string | number;
    editedAt?: string | null;
  }) => (
    <span className="text-xs text-gray-500 mt-2 block">
      {new Date(timestamp || Date.now()).toLocaleTimeString()}
      {editedAt && " (edited)"}
    </span>
  )
);

MessageTimestamp.displayName = "MessageTimestamp";

export const UserMessage = React.memo(
  ({ message, onEdit, onDelete, onToggle, isHidden }: ChatMessageProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(message.content);
    const [copied, setCopied] = useState(false);

    const handleSaveEdit = async () => {
      if (onEdit) {
        await onEdit(message.id, editedContent);
        setIsEditing(false);
      }
    };

    const handleDelete = () => {
      if (onDelete && message.message_pair) {
        onDelete(message.message_pair);
      }
    };

    const handleToggle = () => {
      if (onToggle && message.message_pair) {
        onToggle(message.message_pair, !isHidden);
      }
    };

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
      <div
        className={`px-4 py-6 bg-white dark:bg-gray-800 ${
          isHidden ? "opacity-50" : ""
        }`}
      >
        <div className="max-w-3xl mx-auto flex gap-4">
          <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
            <UserIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </div>
          <div className="flex-1">
            <div className="relative group prose dark:prose-invert max-w-none">
              {isEditing ? (
                <div className="flex flex-col gap-2">
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="min-h-[100px]"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSaveEdit}>
                      <Check className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setIsEditing(false)}
                    >
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  {message.content}
                  <MessageControls
                    isEditing={isEditing}
                    setIsEditing={setIsEditing}
                    onDelete={handleDelete}
                    onToggle={handleToggle}
                    isHidden={isHidden}
                    message={message}
                    copied={copied}
                    onCopy={copyToClipboard}
                  />
                </>
              )}
            </div>
            <MessageTimestamp
              timestamp={message.timestamp}
              editedAt={message.edited_at}
            />
          </div>
        </div>
      </div>
    );
  }
);

export const AssistantMessage = React.memo(
  ({ message, onEdit, onDelete, onToggle, isHidden }: ChatMessageProps) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(message.content);
    const [copied, setCopied] = useState(false);
    const [fullScreenCode, setFullScreenCode] = useState<{
      code: string;
      language?: string;
    } | null>(null);

    const handleSaveEdit = async () => {
      if (onEdit) {
        await onEdit(message.id, editedContent);
        setIsEditing(false);
      }
    };

    const handleDelete = () => {
      if (onDelete && message.message_pair) {
        onDelete(message.message_pair);
      }
    };

    const handleToggle = () => {
      if (onToggle && message.message_pair) {
        onToggle(message.message_pair, !isHidden);
      }
    };

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
      <div
        className={`px-4 py-6 bg-gray-50 dark:bg-gray-900 ${
          isHidden ? "opacity-50" : ""
        }`}
      >
        <div className="max-w-3xl mx-auto flex gap-4">
          <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
            <BotIcon className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <div className="relative group prose dark:prose-invert max-w-none">
              {isEditing ? (
                <div className="flex flex-col gap-2">
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="min-h-[100px]"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSaveEdit}>
                      <Check className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setIsEditing(false)}
                    >
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <Markdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ className, children }) {
                        const code = String(children).replace(/\n$/, "");
                        const language = className?.replace("language-", "");

                        return (
                          <div className="relative group">
                            <CodeBlock className={className}>{code}</CodeBlock>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="absolute top-2 right-12 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={() =>
                                setFullScreenCode({ code, language })
                              }
                            >
                              <Maximize2 className="h-4 w-4" />
                            </Button>
                          </div>
                        );
                      },
                    }}
                  >
                    {message.content}
                  </Markdown>
                  <MessageControls
                    isEditing={isEditing}
                    setIsEditing={setIsEditing}
                    onDelete={handleDelete}
                    onToggle={handleToggle}
                    isHidden={isHidden}
                    message={message}
                    copied={copied}
                    onCopy={copyToClipboard}
                  />
                </>
              )}
            </div>
            <MessageTimestamp
              timestamp={message.timestamp}
              editedAt={message.edited_at}
            />
          </div>
        </div>
        {fullScreenCode && (
          <FullScreenCode
            code={fullScreenCode.code}
            language={fullScreenCode.language}
            onClose={() => setFullScreenCode(null)}
          />
        )}
      </div>
    );
  }
);

UserMessage.displayName = "UserMessage";
AssistantMessage.displayName = "AssistantMessage";
