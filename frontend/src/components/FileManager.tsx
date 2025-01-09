import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Paperclip, X, FileIcon, Loader } from "lucide-react";
import axios from "axios";
import token from "@/constants/token";
import urls from "@/constants/urls";

interface FileManagerProps {
  chatId: string;
  onAttach: (fileIds: string[]) => void;
}

interface Attachment {
  id: string;
  name: string;
  url: string;
}

const FileManager: React.FC<FileManagerProps> = ({ chatId, onAttach }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (isOpen) {
      fetchAttachments();
    }
  }, [isOpen, chatId]);

  const fetchAttachments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get(urls.attachments(chatId), {
        headers: { Authorization: `token ${token}` },
      });
      setAttachments(response.data);
    } catch (error) {
      setError("Error fetching attachments. Please try again.");
      console.error("Error fetching attachments:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setIsLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      await axios.post(urls.upload(chatId), formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `token ${token}`,
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total!
          );
          setUploadProgress(percentCompleted);
        },
      });
      fetchAttachments();
    } catch (error) {
      setError("Error uploading file. Please try again.");
      console.error("Error uploading file:", error);
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  const handleDeleteAttachment = async (attachmentId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await axios.delete(urls.deleteAttachment(attachmentId), {
        headers: { Authorization: `token ${token}` },
      });
      fetchAttachments();
    } catch (error) {
      setError("Error deleting attachment. Please try again.");
      console.error("Error deleting attachment:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAttach = () => {
    onAttach(selectedFiles);
    setIsOpen(false);
    setSelectedFiles([]);
  };

  return (
    <>
      <Button variant="outline" onClick={() => setIsOpen(true)}>
        <Paperclip className="h-4 w-4 mr-2" />
        Manage Files
      </Button>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>File Manager</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <input
              type="file"
              onChange={handleFileUpload}
              accept=".txt,.pdf,.doc,.docx,.zip"
              disabled={isLoading}
            />
            {uploadProgress > 0 && (
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            )}
            {error && <p className="text-red-500">{error}</p>}
            <ScrollArea className="h-[300px]">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader className="h-8 w-8 animate-spin" />
                </div>
              ) : (
                attachments.map((attachment) => (
                  <div
                    key={attachment.id}
                    className="flex items-center space-x-2 py-2"
                  >
                    <Checkbox
                      checked={selectedFiles.includes(attachment.id)}
                      onCheckedChange={(checked) => {
                        setSelectedFiles(
                          checked
                            ? [...selectedFiles, attachment.id]
                            : selectedFiles.filter((id) => id !== attachment.id)
                        );
                      }}
                    />
                    <FileIcon className="h-4 w-4" />
                    <span className="flex-grow truncate">
                      {attachment.name}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteAttachment(attachment.id)}
                      disabled={isLoading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              )}
            </ScrollArea>
            <Button
              onClick={handleAttach}
              disabled={selectedFiles.length === 0 || isLoading}
            >
              Attach Selected Files
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default FileManager;
