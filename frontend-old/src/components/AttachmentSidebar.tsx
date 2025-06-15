import React from "react";
import { X, Trash2, MinusCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Attachment {
  id: string;
  name: string;
  url: string;
}

interface AttachmentSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  attachments: Attachment[];
  attachedFiles: string[];
  onRemoveFromContext: (fileId: string) => void;
  onDelete: (fileId: string) => void;
}

const AttachmentSidebar: React.FC<AttachmentSidebarProps> = ({
  isOpen,
  onClose,
  attachments,
  attachedFiles,
  onRemoveFromContext,
  onDelete,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-64 bg-white shadow-lg p-4 z-50">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Attachments</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <ScrollArea className="h-[calc(100vh-6rem)]">
        {attachments.map((attachment) => (
          <div
            key={attachment.id}
            className="flex items-center justify-between py-2 border-b"
          >
            <span className="truncate flex-grow">{attachment.name}</span>
            <div className="flex space-x-1">
              {attachedFiles.includes(attachment.id) && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onRemoveFromContext(attachment.id)}
                  title="Remove from context"
                >
                  <MinusCircle className="h-4 w-4" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onDelete(attachment.id)}
                title="Delete attachment"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </ScrollArea>
    </div>
  );
};

export default AttachmentSidebar;
