import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { useAddKnowledge } from "@/hooks/useProjects";
import { toast } from "sonner";
import { AxiosError } from "axios";

interface AddKnowledgeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: number;
}

export function AddKnowledgeDialog({
  open,
  onOpenChange,
  projectId,
}: AddKnowledgeDialogProps) {
  const [title, setTitle] = React.useState("");
  const [content, setContent] = React.useState("");
  const addKnowledge = useAddKnowledge();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await addKnowledge.mutateAsync({
        project: projectId,
        title,
        content,
      });
      toast.success("Knowledge added successfully");
      onOpenChange(false);
      setTitle("");
      setContent("");
    } catch (error: unknown | AxiosError) {
      console.error(error);
      toast.error(
        error instanceof AxiosError
          ? error.response?.data.non_field_errors[0] || error.message
          : "Failed to add knowledge. Make sure content is within token limits."
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add Knowledge</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="title" className="text-sm font-medium">
              Title
            </label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title for this knowledge"
              required
            />
          </div>
          <div>
            <label htmlFor="content" className="text-sm font-medium">
              Content
            </label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter the knowledge content"
              rows={10}
              required
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={addKnowledge.isPending}>
              Add Knowledge
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
