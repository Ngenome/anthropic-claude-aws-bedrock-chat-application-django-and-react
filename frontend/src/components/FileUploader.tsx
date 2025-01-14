import React, { useRef } from "react";
import { Button } from "./ui/button";
import { PaperclipIcon, Loader2 } from "lucide-react";

interface FileUploaderProps {
  onFileSelect: (files: FileList | File[]) => void;
  isLoading?: boolean;
  existingFiles?: File[];
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onFileSelect,
  isLoading = false,
  existingFiles = [],
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      onFileSelect(files);
      // Reset the input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleChange}
        className="hidden"
        multiple
      />
      <Button
        type="button"
        size="icon"
        variant="ghost"
        onClick={handleClick}
        disabled={isLoading}
        className="h-8 w-8 hover:bg-accent hover:text-accent-foreground"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <PaperclipIcon className="h-4 w-4" />
        )}
      </Button>
    </>
  );
};
