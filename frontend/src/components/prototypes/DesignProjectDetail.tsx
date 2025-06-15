import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, FolderPlus, Layout, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

import {
  fetchDesignProject,
  fetchDesignProjectPrototypes,
  createGroup,
  generatePrototype,
} from "@/services/prototypes";
import { GeneratePrototypeRequest } from "@/types/prototype";

const DesignProjectDetail: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false);
  const [isGroupDialogOpen, setIsGroupDialogOpen] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [groupForm, setGroupForm] = useState({
    name: "",
    description: "",
  });
  const [generateForm, setGenerateForm] = useState({
    prompt: "",
    group_id: null as number | null,
  });

  // Fetch design project
  const {
    data: project,
    isLoading: isProjectLoading,
    isError: isProjectError,
  } = useQuery({
    queryKey: ["designProject", projectId],
    queryFn: () => fetchDesignProject(projectId),
    enabled: !!projectId,
  });

  // Fetch project prototypes
  const {
    data: prototypes,
    isLoading: isPrototypesLoading,
    isError: isPrototypesError,
  } = useQuery({
    queryKey: ["designProjectPrototypes", projectId],
    queryFn: () => fetchDesignProjectPrototypes(projectId),
    enabled: !!projectId,
  });

  // Create group mutation
  const createGroupMutation = useMutation({
    mutationFn: (data: {
      name: string;
      description: string;
      design_project: number;
    }) => createGroup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      setIsGroupDialogOpen(false);
      resetGroupForm();
      toast.success("Group created successfully");
    },
    onError: (error) => {
      toast.error("Failed to create group");
      console.error("Create group error:", error);
    },
  });

  // Generate prototype mutation
  const generatePrototypeMutation = useMutation({
    mutationFn: (data: GeneratePrototypeRequest) => generatePrototype(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["designProjectPrototypes", projectId],
      });
      setIsGenerateDialogOpen(false);
      resetGenerateForm();
      toast.success("Prototype generated successfully");
      navigate(`/prototypes/${data.id}`);
    },
    onError: (error) => {
      toast.error("Failed to generate prototype");
      console.error("Generate prototype error:", error);
    },
  });

  const resetGroupForm = () => {
    setGroupForm({
      name: "",
      description: "",
    });
  };

  const resetGenerateForm = () => {
    setGenerateForm({
      prompt: "",
      group_id: null,
    });
  };

  const handleCreateGroup = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId) return;

    createGroupMutation.mutate({
      ...groupForm,
      design_project: projectId,
    });
  };

  const handleGeneratePrototype = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId) return;

    generatePrototypeMutation.mutate({
      design_project_id: projectId,
      prompt: generateForm.prompt,
      group_id: generateForm.group_id,
    });
  };

  const handleSelectGroup = (groupId: number | null) => {
    setSelectedGroupId(groupId);
    setGenerateForm({ ...generateForm, group_id: groupId });
  };

  if (isProjectError || isPrototypesError) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center text-red-500">
          Error loading design project. Please try again later.
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate("/design-projects")}
          className="mr-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        {isProjectLoading ? (
          <Skeleton className="h-8 w-64" />
        ) : (
          <h1 className="text-2xl font-bold">{project?.name}</h1>
        )}
      </div>

      <div className="mb-6">
        {isProjectLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : (
          <p className="text-muted-foreground">{project?.description}</p>
        )}
      </div>

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Prototypes</h2>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => setIsGroupDialogOpen(true)}>
            <FolderPlus className="h-4 w-4 mr-2" />
            New Group
          </Button>
          <Button onClick={() => setIsGenerateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Generate Prototype
          </Button>
        </div>
      </div>

      {isPrototypesLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((n) => (
            <Card key={n} className="overflow-hidden">
              <CardHeader>
                <Skeleton className="h-5 w-1/2 mb-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-40 w-full" />
              </CardContent>
              <CardFooter className="flex justify-end">
                <Skeleton className="h-9 w-24" />
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : prototypes?.length === 0 ? (
        <div className="text-center py-10">
          <Layout className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg text-muted-foreground mb-4">
            No prototypes found
          </p>
          <p className="text-muted-foreground mb-6">
            Generate your first prototype by clicking the "Generate Prototype"
            button.
          </p>
          <Button onClick={() => setIsGenerateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Generate Prototype
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {prototypes?.map((prototype) => (
            <Card key={prototype.id} className="overflow-hidden">
              <CardHeader>
                <CardTitle className="text-lg">{prototype.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="aspect-video bg-muted rounded-md flex items-center justify-center">
                  <Layout className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                  {prototype.description}
                </p>
              </CardContent>
              <CardFooter className="flex justify-end">
                <Button
                  variant="default"
                  onClick={() => navigate(`/prototypes/${prototype.id}`)}
                >
                  View Prototype
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Create Group Dialog */}
      <Dialog open={isGroupDialogOpen} onOpenChange={setIsGroupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Group</DialogTitle>
            <DialogDescription>
              Create a new group to organize related prototypes.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateGroup}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label htmlFor="group-name" className="text-sm font-medium">
                  Name
                </label>
                <Input
                  id="group-name"
                  placeholder="Enter group name"
                  value={groupForm.name}
                  onChange={(e) =>
                    setGroupForm({ ...groupForm, name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="group-description"
                  className="text-sm font-medium"
                >
                  Description
                </label>
                <Textarea
                  id="group-description"
                  placeholder="Enter group description"
                  value={groupForm.description}
                  onChange={(e) =>
                    setGroupForm({ ...groupForm, description: e.target.value })
                  }
                  rows={3}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsGroupDialogOpen(false);
                  resetGroupForm();
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createGroupMutation.isPending}>
                {createGroupMutation.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Generate Prototype Dialog */}
      <Dialog
        open={isGenerateDialogOpen}
        onOpenChange={setIsGenerateDialogOpen}
      >
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Generate Prototype</DialogTitle>
            <DialogDescription>
              Describe the UI you want to generate. Be as specific as possible.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleGeneratePrototype}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label htmlFor="prompt" className="text-sm font-medium">
                  Prompt
                </label>
                <Textarea
                  id="prompt"
                  placeholder="Describe the UI you want to generate in detail..."
                  value={generateForm.prompt}
                  onChange={(e) =>
                    setGenerateForm({ ...generateForm, prompt: e.target.value })
                  }
                  rows={6}
                  required
                  className="min-h-[150px]"
                />
                <p className="text-xs text-muted-foreground">
                  Example: "Create a responsive login page with fields for email
                  and password, a login button, and a link to forgot password.
                  Use a modern design with a blue and white color scheme."
                </p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Group (Optional)</label>
                <Tabs
                  value={selectedGroupId ? String(selectedGroupId) : "none"}
                  onValueChange={(value: string) =>
                    handleSelectGroup(value === "none" ? null : Number(value))
                  }
                  className="w-full"
                >
                  <TabsList className="w-full">
                    <TabsTrigger value="none">No Group</TabsTrigger>
                    {/* Would normally fetch groups here, but keeping it simple */}
                    <TabsTrigger value="1">Authentication</TabsTrigger>
                    <TabsTrigger value="2">Dashboard</TabsTrigger>
                    <TabsTrigger value="3">Settings</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsGenerateDialogOpen(false);
                  resetGenerateForm();
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={generatePrototypeMutation.isPending}
              >
                {generatePrototypeMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  "Generate"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DesignProjectDetail;
