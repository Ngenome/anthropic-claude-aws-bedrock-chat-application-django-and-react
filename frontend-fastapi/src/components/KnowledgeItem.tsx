import React from "react";
import { Card, CardHeader, CardContent } from "./ui/card";
import { Switch } from "./ui/switch";
import { Button } from "./ui/button";
import { Trash2, ExternalLink } from "lucide-react";
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

  return (
    <>
      <Card
        onClick={() => preview && setDialogOpen(true)}
        className="group hover:bg-accent transition-colors border shadow-sm w-full cursor-pointer"
      >
        <CardHeader className="p-3">
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between w-full">
              <div className="font-medium text-sm text-foreground flex-1">
                {item.title}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-muted-foreground">Include</span>
                  <Switch
                    checked={item.include_in_chat}
                    onCheckedChange={handleToggle}
                    className="scale-75"
                    aria-label="Toggle knowledge inclusion"
                  />
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-destructive"
                  onClick={handleDelete}
                  aria-label="Delete knowledge item"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="text-xs text-muted-foreground/75">
              {item.token_count.toLocaleString()} tokens
            </div>
          </div>
        </CardHeader>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <h2 className="text-xl font-semibold mb-4">{item.title}</h2>
          <p className="whitespace-pre-wrap">{item.content}</p>
          <div className="mt-4 text-sm text-muted-foreground">
            {item.token_count.toLocaleString()} tokens
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
