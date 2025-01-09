import React from "react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { X, ChevronRight, ExternalLink } from "lucide-react";
import { KnowledgeItem } from "./KnowledgeItem";
import { useProjectKnowledge } from "@/hooks/useProjects";
import { Link } from "react-router-dom";

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
  const { data: knowledge } = useProjectKnowledge(projectId);

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-white shadow-lg p-4 z-50">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Project Context</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <Link
        to={`/projects/${projectId}`}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <span>Open project details</span>
        <ExternalLink className="h-4 w-4" />
      </Link>

      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-medium mb-2">Recent Chats</h3>
          <ScrollArea className="h-40">
            {recentChats.map((chat) => (
              <Link
                key={chat.id}
                to={`/chat/${chat.id}`}
                className="flex items-center justify-between p-2 hover:bg-gray-100 rounded"
              >
                <span className="truncate">{chat.title}</span>
                <ChevronRight className="h-4 w-4" />
              </Link>
            ))}
          </ScrollArea>
        </div>

        <div>
          <h3 className="text-sm font-medium mb-2">Knowledge Base</h3>
          <ScrollArea className="h-[calc(100vh-280px)]">
            <div className="space-y-2">
              {knowledge?.map((item) => (
                <KnowledgeItem key={item.id} item={item} preview />
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
