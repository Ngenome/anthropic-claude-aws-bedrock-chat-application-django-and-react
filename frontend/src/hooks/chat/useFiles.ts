// hooks/useFiles.ts
import { useState, useCallback } from "react";

export const useFiles = () => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<Map<string, string>>(
    new Map()
  );
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = useCallback(async (files: FileList) => {
    const fileArray = Array.from(files);
    try {
      setIsUploading(true);
      setSelectedFiles((prev) => [...prev, ...fileArray]);

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
    } finally {
      setIsUploading(false);
    }
  }, []);

  const handleRemoveFile = useCallback((fileToRemove: File) => {
    setSelectedFiles((prev) => prev.filter((f) => f !== fileToRemove));
    setPreviewUrls((prev) => {
      const newUrls = new Map(prev);
      newUrls.delete(fileToRemove.name);
      return newUrls;
    });
  }, []);

  const clearFiles = useCallback(() => {
    setSelectedFiles([]);
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    setPreviewUrls(new Map());
  }, [previewUrls]);

  return {
    selectedFiles,
    previewUrls,
    isUploading,
    handleFileSelect,
    handleRemoveFile,
    clearFiles,
  };
};
