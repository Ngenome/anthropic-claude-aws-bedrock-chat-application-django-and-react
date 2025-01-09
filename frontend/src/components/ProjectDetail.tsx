import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  useProject,
  useProjectKnowledge,
  useProjectChats,
  useUpdateProjectInstructions,
} from "@/hooks/useProjects";
import { TokenUsageBar } from "./TokenUsageBar";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Plus, ArrowLeft } from "lucide-react";
import { AddKnowledgeDialog } from "./AddKnowledgeDialog";
import { KnowledgeItem } from "./KnowledgeItem";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { toast } from "sonner";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [addOpen, setAddOpen] = React.useState(false);
  const [instructions, setInstructions] = React.useState("");
  const { data: project, isLoading: projectLoading } = useProject(projectId!);
  const { data: knowledge, isLoading: knowledgeLoading } = useProjectKnowledge(
    projectId!
  );
  const { data: chats } = useProjectChats(projectId!);
  const updateInstructions = useUpdateProjectInstructions();

  React.useEffect(() => {
    if (project) {
      setInstructions(project.instructions || "");
    }
  }, [project]);

  const handleUpdateInstructions = async () => {
    try {
      await updateInstructions.mutateAsync({
        projectId: parseInt(projectId!),
        instructions,
      });
      toast.success("Project instructions updated");
    } catch (error) {
      toast.error("Failed to update instructions");
    }
  };

  if (projectLoading || knowledgeLoading) {
    return <div>Loading...</div>;
  }

  if (!project) {
    return <div>Project not found</div>;
  }

  return (
    <div className="container mx-auto py-6">
      <Button
        variant="ghost"
        className="mb-4"
        onClick={() => navigate("/projects")}
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Projects
      </Button>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <div>
            <h1 className="text-3xl font-bold">{project.name}</h1>
            <p className="text-gray-500 mt-1">{project.description}</p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Project Instructions</h2>
            <Textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Enter project instructions..."
              rows={5}
            />
            <Button
              onClick={handleUpdateInstructions}
              disabled={updateInstructions.isPending}
            >
              Save Instructions
            </Button>
          </div>

          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Knowledge Base</h2>
              <Button onClick={() => setAddOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Knowledge
              </Button>
            </div>
            <TokenUsageBar
              current={project.total_knowledge_tokens}
              max={160000}
              label="Knowledge Base Token Usage"
              className="mb-4"
            />
            <div className="space-y-4">
              {knowledge?.map((item) => (
                <KnowledgeItem key={item.id} item={item} />
              ))}
            </div>
          </div>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Project Chats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button
                  className="w-full"
                  onClick={() => navigate(`/chat/new?projectId=${projectId}`)}
                >
                  New Chat
                </Button>
                {chats?.map((chat) => (
                  <div
                    key={chat.id}
                    className="p-2 hover:bg-gray-100 rounded cursor-pointer"
                    onClick={() => navigate(`/chat/${chat.id}`)}
                  >
                    <h3 className="font-medium">{chat.title}</h3>
                    <p className="text-sm text-gray-500">
                      {new Date(chat.date).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <AddKnowledgeDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        projectId={parseInt(projectId!)}
      />
    </div>
  );
}
