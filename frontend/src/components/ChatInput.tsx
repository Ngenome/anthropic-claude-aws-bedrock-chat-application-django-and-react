import React, { useState, useRef, useCallback, useEffect } from "react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import {
  Loader2,
  Maximize2,
  Minimize2,
  PaperclipIcon,
  SendIcon,
  Mic,
  SmileIcon,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { FileUploader } from "./FileUploader";
import { FilePreview } from "./FilePreview";
import { toast } from "sonner";

interface ChatInputProps {
  onSubmit: ({
    messageText,
    projectId,
  }: {
    messageText: string;
    projectId?: string;
  }) => Promise<void>;
  newMessage: string;
  setNewMessage: (message: string) => void;
  isStreaming: boolean;
  selectedFiles?: File[];
  setSelectedFiles?: React.Dispatch<React.SetStateAction<File[]>>;
  projectId?: string;
}

export const ChatInput = React.memo(
  ({
    onSubmit,
    newMessage,
    setNewMessage,
    isStreaming,
    selectedFiles: selectedFilesProp = [],
    setSelectedFiles: setSelectedFilesProp,
    projectId,
  }: ChatInputProps) => {
    const [isFullScreen, setIsFullScreen] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [previewUrls, setPreviewUrls] = useState<Map<string, string>>(
      new Map()
    );
    const [isUploading, setIsUploading] = useState(false);

    const adjustTextareaHeight = useCallback(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = "inherit";
        const computed = window.getComputedStyle(textarea);
        const height =
          textarea.scrollHeight +
          parseInt(computed.borderTopWidth) +
          parseInt(computed.borderBottomWidth);

        const maxHeight = isFullScreen ? window.innerHeight * 0.5 : 200;
        textarea.style.height = `${Math.min(height, maxHeight)}px`;
      }
    }, [isFullScreen]);

    const handleMessageChange = useCallback(
      (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setNewMessage(e.target.value);
        adjustTextareaHeight();
      },
      [setNewMessage, adjustTextareaHeight]
    );

    useEffect(() => {
      adjustTextareaHeight();
      if (isFullScreen && textareaRef.current) {
        textareaRef.current.focus();
      }
    }, [isFullScreen, adjustTextareaHeight]);

    const toggleFullScreen = () => {
      setIsFullScreen(!isFullScreen);
    };

    const toggleRecording = () => {
      setIsRecording(!isRecording);
      // Implement voice recording logic here
    };

    const handleFileSelect = useCallback(
      async (files: FileList | File[]) => {
        try {
          setIsUploading(true);

          if (setSelectedFilesProp) {
            // Convert FileList to Array if needed
            const fileArray = Array.from(files);
            setSelectedFilesProp((prev) => [...prev, ...fileArray]);

            // Process previews for images
            fileArray.forEach((file) => {
              if (file.type.startsWith("image/")) {
                const reader = new FileReader();
                reader.onloadend = () => {
                  setPreviewUrls((prev) =>
                    new Map(prev).set(file.name, reader.result as string)
                  );
                };
                reader.readAsDataURL(file);
              }
            });
          }
        } finally {
          setIsUploading(false);
        }
      },
      [setSelectedFilesProp]
    );

    const handleRemoveFile = useCallback(
      (fileToRemove: File) => {
        if (setSelectedFilesProp) {
          setSelectedFilesProp(
            selectedFilesProp.filter((f) => f !== fileToRemove)
          );
          setPreviewUrls((prev) => {
            const newUrls = new Map(prev);
            newUrls.delete(fileToRemove.name);
            return newUrls;
          });
        }
      },
      [selectedFilesProp, setSelectedFilesProp]
    );

    const handleSubmit = useCallback(
      async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim() && selectedFilesProp.length === 0) return;

        try {
          await onSubmit({
            messageText: newMessage,
            projectId: projectId,
          });
        } catch (error) {
          console.error("Error sending message:", error);
          toast.error("Failed to send message");
        }
      },
      [newMessage, onSubmit, selectedFilesProp, projectId]
    );

    const clearPreviewUrls = () => {
      previewUrls.forEach((url) => URL.revokeObjectURL(url));
      setPreviewUrls(new Map());
    };

    const handleKeyDown = useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
          if (!isFullScreen && !e.shiftKey) {
            e.preventDefault();
            if (newMessage.trim()) {
              handleSubmit(e);
            }
          }
        }
      },
      [isFullScreen, newMessage, handleSubmit]
    );

    const renderFilePreviews = () => (
      <div className="flex gap-2 flex-wrap mt-2">
        {selectedFilesProp.map((file, index) => (
          <FilePreview
            key={`${file.name}-${index}`}
            file={file}
            previewUrl={previewUrls.get(file.name)}
            onRemove={() => {
              if (setSelectedFilesProp) {
                setSelectedFilesProp(
                  selectedFilesProp.filter((_, i) => i !== index)
                );
                if (previewUrls.has(file.name)) {
                  URL.revokeObjectURL(previewUrls.get(file.name)!);
                  setPreviewUrls((prev) => {
                    const newMap = new Map(prev);
                    newMap.delete(file.name);
                    return newMap;
                  });
                }
              }
            }}
          />
        ))}
      </div>
    );

    return (
      <div
        className={`relative transition-all duration-300 ease-in-out ${
          isFullScreen
            ? "fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
            : ""
        }`}
      >
        <div
          className={`transition-all duration-300 ${
            isFullScreen
              ? "fixed bottom-0 left-0 right-0 bg-background border-t p-6 rounded-t-xl shadow-lg max-h-[80vh] overflow-hidden"
              : ""
          }`}
        >
          <form
            onSubmit={handleSubmit}
            className={`relative max-w-3xl mx-auto ${
              isFullScreen ? "flex flex-col space-y-4" : ""
            }`}
          >
            <div className="relative">
              {isFullScreen && (
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Compose Message</h3>
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    onClick={toggleFullScreen}
                    className="h-8 w-8"
                  >
                    <Minimize2 className="h-4 w-4" />
                  </Button>
                </div>
              )}
              {renderFilePreviews()}
              <Textarea
                ref={textareaRef}
                value={newMessage}
                onChange={handleMessageChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  isFullScreen
                    ? "Compose your message... (Enter for new line, Ctrl+Enter to send)"
                    : "Type your message here... (Enter to send, Shift+Enter for new line)"
                }
                className={`w-full resize-none bg-background 
                border-input focus-visible:ring-ring
                ${isFullScreen ? "min-h-[200px] pr-4" : "pr-32"}
                transition-all duration-200`}
                disabled={isStreaming}
              />

              <div
                className={`flex items-center space-x-2 ${
                  isFullScreen
                    ? "mt-4 justify-between"
                    : "absolute right-2 bottom-2"
                }`}
              >
                <div className="flex items-center space-x-2">
                  <FileUploader
                    onFileSelect={handleFileSelect}
                    isLoading={isUploading}
                    existingFiles={selectedFilesProp}
                  />
                  <TooltipProvider delayDuration={300}>
                    {!isFullScreen && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            onClick={toggleFullScreen}
                            className="h-8 w-8 hover:bg-accent hover:text-accent-foreground"
                          >
                            <Maximize2 className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Full screen</TooltipContent>
                      </Tooltip>
                    )}

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 hover:bg-accent hover:text-accent-foreground"
                        >
                          <PaperclipIcon className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Attach files</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 hover:bg-accent hover:text-accent-foreground"
                        >
                          <SmileIcon className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Insert emoji</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          onClick={toggleRecording}
                          className={`h-8 w-8 hover:bg-accent hover:text-accent-foreground
                            ${isRecording ? "text-destructive" : ""}`}
                        >
                          <Mic className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        {isRecording ? "Stop recording" : "Start recording"}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>

                <Button
                  type="submit"
                  disabled={isStreaming || !newMessage.trim()}
                  className={`h-8 ${isFullScreen ? "px-8" : ""}`}
                  size="sm"
                >
                  {isStreaming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <span className="mr-2">Send</span>
                      <SendIcon className="h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  }
);

ChatInput.displayName = "ChatInput";
