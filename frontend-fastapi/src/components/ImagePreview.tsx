import React from "react";
import { X } from "lucide-react";
import { Button } from "./ui/button";

interface ImagePreviewProps {
  url: string;
  onRemove: () => void;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  url,
  onRemove,
}) => {
  return (
    <div className="relative inline-block">
      <img
        src={url}
        alt="Preview"
        className="max-w-[100px] max-h-[100px] rounded-md"
      />
      <Button
        size="icon"
        variant="destructive"
        className="absolute -top-2 -right-2 h-5 w-5 rounded-full"
        onClick={onRemove}
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
};
