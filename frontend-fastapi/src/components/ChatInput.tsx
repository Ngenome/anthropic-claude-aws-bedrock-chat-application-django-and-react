import React, { useState, useRef, useCallback, useEffect } from "react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import {
  Loader2,
  Maximize2,
  Minimize2,
  SendIcon,
  Mic,
  SmileIcon,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { FileUploader } from "@/components/FileUploader";
import { FilePreview } from "@/components/FilePreview";
import useChat from "@/hooks/useChat";
import { debounce } from "@/utils/debounce";
import { useFiles } from "@/hooks/chat/useFiles";
import { useMessageSubmission } from "@/hooks/chat/useMessageSubmission";
import { useParams } from "react-router-dom";

export const ChatInput = React.memo(({ projectId }: { projectId?: string }) => {
  const { chatId } = useParams<{
    chatId: string;
  }>();
  const { systemPrompt, isStreaming, setIsStreaming, setMessages } = useChat();
  const [newMessage, setNewMessage] = useState("");
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const {
    selectedFiles,
    previewUrls,
    isUploading,
    handleFileSelect,
    handleRemoveFile,
    clearFiles,
  } = useFiles();

  const { handleSubmit: submitMessage } = useMessageSubmission({
    chatId: chatId || "new",
    systemPrompt,
    selectedFiles,
    clearFiles,
    setMessages,
    setNewMessage,
    setIsStreaming,
  });

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustTextareaHeight = useCallback(
    debounce((textarea: HTMLTextAreaElement) => {
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
    }, 10),
    [isFullScreen]
  );

  const handleMessageChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value;
      setNewMessage(value);
      adjustTextareaHeight(e.target);
    },
    [setNewMessage, adjustTextareaHeight]
  );

  useEffect(() => {
    if (textareaRef.current) {
      adjustTextareaHeight(textareaRef.current);
    }
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

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      await submitMessage({
        messageText: newMessage,
        projectId: projectId,
      });
    },
    [newMessage, submitMessage, projectId]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        if (!isFullScreen && !e.shiftKey) {
          e.preventDefault();
          if (newMessage.trim()) {
            submitMessage({
              messageText: newMessage,
              projectId: projectId,
            });
          }
        }
      }
    },
    [isFullScreen, newMessage, submitMessage, projectId]
  );

  const renderFilePreviews = () => (
    <div className="flex gap-2 flex-wrap mt-2">
      {selectedFiles.map((file, index) => (
        <FilePreview
          key={`${file.name}-${index}`}
          file={file}
          previewUrl={previewUrls.get(file.name)}
          onRemove={() => handleRemoveFile(file)}
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
          onSubmit={onSubmit}
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
                      <FileUploader
                        onFileSelect={handleFileSelect}
                        isLoading={isUploading}
                        existingFiles={selectedFiles}
                      />
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
});

ChatInput.displayName = "ChatInput";
