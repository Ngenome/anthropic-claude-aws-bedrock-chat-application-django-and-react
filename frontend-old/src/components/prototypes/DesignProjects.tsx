import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
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
import { Skeleton } from "@/components/ui/skeleton";

import {
  fetchDesignProjects,
  createDesignProject,
  updateDesignProject,
  deleteDesignProject,
} from "@/services/prototypes";

const DesignProjects: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null
  );
  const [formData, setFormData] = useState({
    title: "",
    description: "",
  });

  // Fetch design projects
  const {
    data: designProjects,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["designProjects"],
    queryFn: fetchDesignProjects,
  });

  console.log("design projects", designProjects);

  // Create design project mutation
  const createMutation = useMutation({
    mutationFn: createDesignProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["designProjects"] });
      setIsCreateDialogOpen(false);
      resetForm();
      toast.success("Design project created successfully");
    },
    onError: (error) => {
      toast.error("Failed to create design project");
      console.error("Create error:", error);
    },
  });

  // Update design project mutation
  const updateMutation = useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: { title: string; description: string };
    }) => updateDesignProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["designProjects"] });
      setIsEditDialogOpen(false);
      resetForm();
      toast.success("Design project updated successfully");
    },
    onError: (error) => {
      toast.error("Failed to update design project");
      console.error("Update error:", error);
    },
  });

  // Delete design project mutation
  const deleteMutation = useMutation({
    mutationFn: deleteDesignProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["designProjects"] });
      setIsDeleteDialogOpen(false);
      setSelectedProjectId(null);
      toast.success("Design project deleted successfully");
    },
    onError: (error) => {
      toast.error("Failed to delete design project");
      console.error("Delete error:", error);
    },
  });

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
    });
    setSelectedProjectId(null);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name: formData.title,
      description: formData.description,
    });
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedProjectId) {
      updateMutation.mutate({
        id: selectedProjectId,
        data: {
          title: formData.title,
          description: formData.description,
        },
      });
    }
  };

  const handleDeleteConfirm = () => {
    if (selectedProjectId) {
      deleteMutation.mutate(selectedProjectId);
    }
  };

  const handleEditClick = (id: number, title: string, description: string) => {
    setSelectedProjectId(id);
    setFormData({ title, description });
    setIsEditDialogOpen(true);
  };

  const handleDeleteClick = (id: number) => {
    setSelectedProjectId(id);
    setIsDeleteDialogOpen(true);
  };

  if (isError) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center text-red-500">
          Error loading design projects. Please try again later.
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Design Projects</h1>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" /> New Design Project
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <Card key={n} className="overflow-hidden">
              <CardHeader className="p-4">
                <Skeleton className="h-5 w-1/2 mb-2" />
                <Skeleton className="h-4 w-5/6" />
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <Skeleton className="h-20 w-full" />
              </CardContent>
              <CardFooter className="flex justify-end p-4 pt-0">
                <Skeleton className="h-9 w-24" />
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {designProjects?.length === 0 ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted-foreground">
                No design projects found. Create your first one!
              </p>
            </div>
          ) : (
            designProjects?.map((project) => (
              <Card key={project.id} className="overflow-hidden">
                <CardHeader className="p-4">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-xl">{project.title}</CardTitle>
                    <div className="flex space-x-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() =>
                          handleEditClick(
                            project.id,
                            project.title,
                            project.description
                          )
                        }
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:text-destructive"
                        onClick={() => handleDeleteClick(project.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <CardDescription className="text-sm text-muted-foreground">
                    Created: {new Date(project.created_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {project.description}
                  </p>
                </CardContent>
                <CardFooter className="flex justify-end p-4 pt-0">
                  <Button
                    variant="default"
                    onClick={() => navigate(`/design-projects/${project.id}`)}
                  >
                    View Prototypes
                  </Button>
                </CardFooter>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Create Design Project Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Design Project</DialogTitle>
            <DialogDescription>
              Create a new design project to organize your UI prototypes.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label htmlFor="title" className="text-sm font-medium">
                  Name
                </label>
                <Input
                  id="title"
                  placeholder="Enter project name"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="description" className="text-sm font-medium">
                  Description
                </label>
                <Textarea
                  id="description"
                  placeholder="Enter project description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows={4}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsCreateDialogOpen(false);
                  resetForm();
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Design Project Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Design Project</DialogTitle>
            <DialogDescription>
              Update your design project details.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label htmlFor="edit-title" className="text-sm font-medium">
                  Name
                </label>
                <Input
                  id="edit-title"
                  placeholder="Enter project name"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="edit-description"
                  className="text-sm font-medium"
                >
                  Description
                </label>
                <Textarea
                  id="edit-description"
                  placeholder="Enter project description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows={4}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsEditDialogOpen(false);
                  resetForm();
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "Updating..." : "Update"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Design Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this design project? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsDeleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DesignProjects;
