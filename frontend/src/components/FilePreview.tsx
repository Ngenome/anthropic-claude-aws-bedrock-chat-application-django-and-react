import React from "react";
import { X, FileIcon, ImageIcon } from "lucide-react";
import { Button } from "./ui/button";

interface FilePreviewProps {
  file: File;
  previewUrl?: string;
  onRemove: () => void;
}

const truncateFilename = (filename: string, maxLength: number = 10): string => {
  const extension = filename.split(".").pop() || "";
  const name = filename.substring(0, filename.lastIndexOf("."));

  if (name.length <= maxLength) {
    return filename;
  }

  return `${name.substring(0, maxLength)}...${
    extension ? `.${extension}` : ""
  }`;
};

export const FilePreview: React.FC<FilePreviewProps> = ({
  file,
  previewUrl,
  onRemove,
}) => {
  const isImage = file.type.startsWith("image/");
  const truncatedName = truncateFilename(file.name);

  return (
    <div className="relative flex-shrink-0 w-[200px] bg-muted rounded-lg p-2">
      <div className="flex items-center gap-2">
        {isImage && previewUrl ? (
          <img
            src={previewUrl}
            alt="Preview"
            className="w-10 h-10 object-cover rounded"
          />
        ) : (
          <FileIcon className="w-10 h-10 p-2" />
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate" title={file.name}>
            {truncatedName}
          </p>
          <p className="text-xs text-muted-foreground">
            {(file.size / 1024).toFixed(1)} KB
          </p>
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-8 w-8 hover:bg-background/80 absolute top-1 right-1"
          onClick={onRemove}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};
