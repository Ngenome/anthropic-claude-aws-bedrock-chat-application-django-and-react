import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

interface SavedSystemPrompt {
  id: number;
  title: string;
  prompt: string;
}

interface ConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  systemPrompt: string;
  onSystemPromptChange: (prompt: string) => void;
  savedSystemPrompts: SavedSystemPrompt[];
  onSaveSystemPrompt: (title: string, prompt: string) => void;
  onUpdateSystemPrompt: (id: number, title: string, prompt: string) => void;
  onSelectSystemPrompt: (prompt: string) => void;
}

const ConfigDialog: React.FC<ConfigDialogProps> = ({
  isOpen,
  onClose,
  systemPrompt,
  onSystemPromptChange,
  savedSystemPrompts,
  onSaveSystemPrompt,
  onUpdateSystemPrompt,
  onSelectSystemPrompt,
}) => {
  const [promptTitle, setPromptTitle] = useState("");
  const [selectedPromptId, setSelectedPromptId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveSystemPrompt(promptTitle, systemPrompt);
      setPromptTitle("");
      toast.success("System prompt saved successfully.");
    } catch (error) {
      console.error("Error saving system prompt:", error);
      toast.error("Failed to save system prompt. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdate = async () => {
    if (selectedPromptId === null) return;
    setIsUpdating(true);
    try {
      await onUpdateSystemPrompt(selectedPromptId, promptTitle, systemPrompt);
      toast.success("System prompt updated successfully.");
    } catch (error) {
      console.error("Error updating system prompt:", error);
      toast.error("Failed to update system prompt. Please try again.");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleSelect = (promptId: string) => {
    const selected = savedSystemPrompts.find(
      (p) => p.id === parseInt(promptId)
    );
    if (selected) {
      setSelectedPromptId(selected.id);
      setPromptTitle(selected.title);
      onSystemPromptChange(selected.prompt);
      onSelectSystemPrompt(selected.prompt);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>System Prompt Configuration</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Input
              id="prompt-title"
              value={promptTitle}
              onChange={(e) => setPromptTitle(e.target.value)}
              placeholder="Enter prompt title..."
              className="col-span-4"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Textarea
              id="system-prompt"
              value={systemPrompt}
              onChange={(e) => onSystemPromptChange(e.target.value)}
              placeholder="Enter system prompt..."
              rows={5}
              className="col-span-4"
            />
          </div>
          <div className="flex justify-between items-center">
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save Prompt"}
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={isUpdating || selectedPromptId === null}
            >
              {isUpdating ? "Updating..." : "Update Prompt"}
            </Button>
          </div>
          <Select onValueChange={handleSelect}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a saved prompt" />
            </SelectTrigger>
            <SelectContent>
              {savedSystemPrompts.map((prompt) => (
                <SelectItem key={prompt.id} value={prompt.id.toString()}>
                  {prompt.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ConfigDialog;
