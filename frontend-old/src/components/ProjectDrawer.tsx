import React from "react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { X, Plus } from "lucide-react";
import { KnowledgeItem } from "./KnowledgeItem";
import { useProjectKnowledge, useProject } from "@/hooks/useProjects";
import { Link, useNavigate } from "react-router-dom";

interface ProjectDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: number;
  recentChats: Array<{
    id: number;
    title: string;
    date: string;
  }>;
}

export function ProjectDrawer({
  isOpen,
  onClose,
  projectId,
  recentChats,
}: ProjectDrawerProps) {
  const { data: knowledge } = useProjectKnowledge(projectId.toString());
  const { data: project } = useProject(projectId.toString());
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleNewChat = () => {
    navigate(`/chat/new?projectId=${projectId}`);
    onClose();
  };

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-background border-l shadow-lg z-50">
      <div className="flex justify-between items-center p-3 bg-muted/50 border-b">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleNewChat}
          className="flex items-center gap-1 bg-background"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {project && (
        <div className="px-3 py-2 border-b bg-background">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-foreground">{project.name}</h2>
            <Link
              to={`/projects/${projectId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Details →
            </Link>
          </div>
        </div>
      )}

      <div className="flex flex-col h-[calc(100vh-120px)]">
        <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b">
          <h3 className="text-sm font-medium text-foreground">
            Knowledge Base
          </h3>
          <span className="text-xs text-muted-foreground">
            {knowledge?.length || 0} items
          </span>
        </div>
        <ScrollArea className="flex-1">
          <div className="space-y-2 p-3 pr-4">
            {knowledge?.map((item) => (
              <KnowledgeItem key={item.id} item={item} preview />
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
