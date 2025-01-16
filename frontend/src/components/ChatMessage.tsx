import React, { useState } from "react";
import Markdown from "react-markdown";
import { Message, MessageContent } from "@/types/chat";
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
  ChevronDown,
  ChevronRight,
  FileIcon,
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
import useChat from "@/hooks/useChat";

interface ChatMessageProps {
  message: Message;
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
    <span className="text-xs text-muted-foreground mt-2 block">
      {new Date(timestamp || Date.now()).toLocaleTimeString()}
      {editedAt && " (edited)"}
    </span>
  )
);

MessageTimestamp.displayName = "MessageTimestamp";

const MessageContentComponent = React.memo(
  ({ message }: { message: Message }) => {
    const processContent = (content: MessageContent) => {
      switch (content.content_type) {
        case "image":
          return (
            <div key={content.id} className="mt-2">
              <img
                src={content.file_content}
                alt="Uploaded image"
                className="max-w-full rounded-lg"
                style={{ maxHeight: "400px" }}
              />
            </div>
          );

        case "document":
          return (
            <div
              key={content.id}
              className="mt-2 flex items-center gap-2 p-2 bg-muted rounded-lg"
            >
              <FileIcon className="h-4 w-4" />
              <a
                href={content.file_content}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm hover:underline"
              >
                {content.mime_type}
              </a>
            </div>
          );

        case "text":
          return message.role === "assistant" ? (
            <Markdown
              key={`${content.id}-${message.id}`}
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  const code = String(children).replace(/\n$/, "");

                  // If there's no language specified and no newlines, treat as inline code
                  const isInlineCode = !match && !code.includes("\n");

                  if (isInlineCode) {
                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }

                  return (
                    <CodeBlock
                      key={`${node?.position?.start.offset}-${message.id}`}
                      language={match ? match[1] : ""}
                      showExpand={true}
                      {...props}
                    >
                      {code}
                    </CodeBlock>
                  );
                },
              }}
            >
              {content.text_content || ""}
            </Markdown>
          ) : (
            <div key={content.id} className="whitespace-pre-wrap">
              {content.text_content}
            </div>
          );

        default:
          return null;
      }
    };

    return (
      <div className="space-y-2">
        {message.contents.map((content) => processContent(content))}
      </div>
    );
  }
);

MessageContentComponent.displayName = "MessageContentComponent";
export const UserMessage = React.memo(
  ({ message, isHidden }: ChatMessageProps) => {
    const {
      handleEditMessage,
      handleDeleteMessagePair,
      handleToggleMessagePair,
    } = useChat();
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(
      message.contents.find((c) => c.content_type === "text")?.text_content ||
        ""
    );
    const [copied, setCopied] = useState(false);

    const handleSaveEdit = async () => {
      if (handleEditMessage && message.id) {
        await handleEditMessage(message.id, editedContent);
        setIsEditing(false);
      }
    };

    const handleDelete = () => {
      if (handleDeleteMessagePair && message.message_pair) {
        handleDeleteMessagePair(message.message_pair);
      }
    };

    const handleToggle = () => {
      if (handleToggleMessagePair && message.message_pair) {
        handleToggleMessagePair(message.message_pair, !isHidden);
      }
    };

    const copyToClipboard = async () => {
      try {
        const textContent = message.contents
          .filter((c) => c.content_type === "text")
          .map((c) => c.text_content)
          .join("\n");
        await navigator.clipboard.writeText(textContent);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        toast.success("Message copied to clipboard");
      } catch (err) {
        toast.error("Failed to copy message");
      }
    };

    return (
      <div
        className={`px-4 py-6 relative bg-background ${
          isHidden ? "opacity-50" : ""
        }`}
      >
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
        <div className="max-w-3xl mx-auto flex gap-4">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <UserIcon className="w-5 h-5 text-muted-foreground" />
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
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsEditing(false)}
                    >
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleSaveEdit}
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </div>
                </div>
              ) : (
                <MessageContentComponent message={message} />
              )}
            </div>
            <MessageTimestamp
              timestamp={message.created_at}
              editedAt={
                message.contents.find((c) => c.content_type === "text")
                  ?.edited_at
              }
            />
          </div>
        </div>
      </div>
    );
  }
);

export const AssistantMessage = React.memo(
  ({ message, isHidden }: ChatMessageProps) => {
    const {
      handleEditMessage,
      handleDeleteMessagePair,
      handleToggleMessagePair,
    } = useChat();
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(
      message.contents[0]?.text_content || ""
    );
    const [copied, setCopied] = useState(false);
    const [fullScreenCode, setFullScreenCode] = useState<{
      code: string;
      language?: string;
    } | null>(null);
    const [showThinking, setShowThinking] = useState(false);

    // Function to process content and extract thinking section
    const processContent = (content: string) => {
      const thinkingMatch = content.match(/<Thinking>([\s\S]*?)<\/Thinking>/);
      const thinking = thinkingMatch ? thinkingMatch[1].trim() : null;
      const mainContent = content
        .replace(/<Thinking>[\s\S]*?<\/Thinking>/, "")
        .trim();

      return { thinking, mainContent };
    };

    const textContent = message.contents[0]?.text_content || "";
    const { thinking, mainContent } = processContent(textContent);

    const handleSaveEdit = async () => {
      if (handleEditMessage && message.id) {
        await handleEditMessage(message.id, editedContent);
        setIsEditing(false);
      }
    };

    const handleDelete = () => {
      if (handleDeleteMessagePair && message.message_pair) {
        handleDeleteMessagePair(message.message_pair);
      }
    };

    const handleToggle = () => {
      if (handleToggleMessagePair && message.message_pair) {
        handleToggleMessagePair(message.message_pair, !isHidden);
      }
    };

    const copyToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(textContent);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        toast.success("Message copied to clipboard");
      } catch (err) {
        toast.error("Failed to copy message");
      }
    };

    return (
      <div
        className={` relative px-4 py-6 bg-muted/50 ${
          isHidden ? "opacity-50" : ""
        }`}
      >
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
        <div className="max-w-3xl mx-auto flex gap-4">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
            <BotIcon className="w-5 h-5 text-primary-foreground" />
          </div>
          <div className="flex-1 ">
            <div className="relative group prose dark:prose-invert max-w-none">
              {thinking && (
                <div className="mb-4 ">
                  <button
                    onClick={() => setShowThinking(!showThinking)}
                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
                  >
                    {showThinking ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    Thinking Process
                  </button>
                  {showThinking && (
                    <div className="mt-2 text-sm text-muted-foreground">
                      <Markdown remarkPlugins={[remarkGfm]}>
                        {thinking}
                      </Markdown>
                    </div>
                  )}
                </div>
              )}
              {isEditing ? (
                <div className="flex flex-col gap-2">
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="min-h-[100px]"
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsEditing(false)}
                    >
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleSaveEdit}
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </div>
                </div>
              ) : (
                <Markdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    // the pre tag - return a pre tag with the overflow-x style removed
                    pre(props) {
                      return (
                        <pre
                          {...props}
                          className="!overflow-visible !bg-transparent"
                        />
                      );
                    },

                    //the code tag
                    code({ node, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || "");
                      const code = String(children).replace(/\n$/, "");

                      // If there's no language specified and no newlines, treat as inline code
                      const isInlineCode = !match && !code.includes("\n");

                      if (isInlineCode) {
                        return (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      }

                      return (
                        <CodeBlock
                          key={`${node?.position?.start.offset}-${message.id}`}
                          language={match ? match[1] : ""}
                          showExpand={true}
                          onExpand={() =>
                            setFullScreenCode({
                              code,
                              language: match ? match[1] : undefined,
                            })
                          }
                          {...props}
                        >
                          {code}
                        </CodeBlock>
                      );
                    },
                  }}
                >
                  {mainContent}
                </Markdown>
              )}
            </div>
            <MessageTimestamp
              timestamp={message.created_at}
              editedAt={message.contents[0]?.edited_at}
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
