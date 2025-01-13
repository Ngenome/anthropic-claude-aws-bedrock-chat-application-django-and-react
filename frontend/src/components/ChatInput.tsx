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

interface ChatInputProps {
  onSubmit: (e: React.FormEvent) => Promise<void>;
  newMessage: string;
  setNewMessage: (message: string) => void;
  isStreaming: boolean;
}

export const ChatInput = React.memo(
  ({ onSubmit, newMessage, setNewMessage, isStreaming }: ChatInputProps) => {
    const [isFullScreen, setIsFullScreen] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [isRecording, setIsRecording] = useState(false);

    const handleKeyDown = useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
          if (!isFullScreen && !e.shiftKey) {
            e.preventDefault();
            if (newMessage.trim()) {
              onSubmit(e);
            }
          }
        }
      },
      [isFullScreen, newMessage, onSubmit]
    );

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
