import React from "react";
import { X, Copy, CheckCheck } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { CodeBlock } from "./CodeBlock";

interface FullScreenCodeProps {
  code: string;
  language?: string;
  onClose: () => void;
}

export const FullScreenCode: React.FC<FullScreenCodeProps> = ({
  code,
  language,
  onClose,
}) => {
  const [copied, setCopied] = React.useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Code copied to clipboard");
    } catch (err) {
      toast.error("Failed to copy code");
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-900/80 z-50 flex flex-col">
      <div className="flex justify-between items-center p-4 bg-gray-800">
        <h2 className="text-white text-lg">Code View</h2>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={copyToClipboard}
            className="text-white hover:text-white"
          >
            {copied ? (
              <CheckCheck className="h-4 w-4" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-white hover:text-white"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4">
        <CodeBlock className={language}>{code}</CodeBlock>
      </div>
    </div>
  );
};
