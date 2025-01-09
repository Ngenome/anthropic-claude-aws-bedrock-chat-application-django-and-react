import React from "react";
import { Card, CardHeader, CardContent } from "./ui/card";
import { Switch } from "./ui/switch";
import { Button } from "./ui/button";
import { Trash2 } from "lucide-react";
import { useToggleKnowledge, useDeleteKnowledge } from "@/hooks/useProjects";
import { Dialog, DialogContent } from "./ui/dialog";
import { toast } from "sonner";

interface KnowledgeItemProps {
  item: {
    id: number;
    title: string;
    content: string;
    include_in_chat: boolean;
    token_count: number;
  };
  preview?: boolean;
}

export function KnowledgeItem({ item, preview = false }: KnowledgeItemProps) {
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const toggleKnowledge = useToggleKnowledge();
  const deleteKnowledge = useDeleteKnowledge();

  const handleToggle = async () => {
    try {
      await toggleKnowledge.mutateAsync({ id: item.id });
    } catch (error) {
      toast.error("Failed to toggle knowledge item");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteKnowledge.mutateAsync(item.id);
      toast.success("Knowledge item deleted");
    } catch (error) {
      toast.error("Failed to delete knowledge item");
    }
  };

  const previewContent =
    item.content.slice(0, 50) + (item.content.length > 50 ? "..." : "");

  return (
    <>
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="font-semibold">{item.title}</div>
          <div className="flex items-center space-x-2">
            <Switch
              checked={item.include_in_chat}
              onCheckedChange={handleToggle}
              aria-label="Toggle knowledge inclusion"
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              className="text-red-500 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div
            className="text-sm text-gray-600 cursor-pointer"
            onClick={() => preview && setDialogOpen(true)}
          >
            {preview ? previewContent : item.content}
          </div>
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <h2 className="text-xl font-semibold mb-4">{item.title}</h2>
          <p className="whitespace-pre-wrap">{item.content}</p>
        </DialogContent>
      </Dialog>
    </>
  );
}
