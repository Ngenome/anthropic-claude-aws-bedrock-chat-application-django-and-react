import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Code,
  Copy,
  FileCode,
  Loader2,
  PenLine,
  Plus,
  Layers,
  Maximize2,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

import {
  fetchPrototype,
  fetchVariants,
  createVariant,
  createVersion,
} from "@/services/prototypes";
import { CreateVariantRequest, EditVersionRequest } from "@/types/prototype";

const PrototypeDetail: React.FC = () => {
  const { prototypeId } = useParams<{ prototypeId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeVariant, setActiveVariant] = useState<string | null>(null);
  const [activeVersion, setActiveVersion] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<"preview" | "code">("preview");
  const [isCreateVariantDialogOpen, setIsCreateVariantDialogOpen] =
    useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [variantForm, setVariantForm] = useState({
    name: "",
    description: "",
    prompt: "",
  });
  const [editForm, setEditForm] = useState({
    edit_prompt: "",
    name: "",
  });

  // Fetch prototype
  const {
    data: prototype,
    isLoading: isPrototypeLoading,
    isError: isPrototypeError,
  } = useQuery({
    queryKey: ["prototype", prototypeId],
    queryFn: () => fetchPrototype(prototypeId ?? ""),
    enabled: !!prototypeId,
  });

  // Fetch variants
  const {
    data: variants,
    isLoading: isVariantsLoading,
    isError: isVariantsError,
  } = useQuery({
    queryKey: ["variants", prototypeId],
    queryFn: () => fetchVariants(prototypeId ?? ""),
    enabled: !!prototypeId,
  });

  console.log("variants on prototype detail", variants);
  console.log("prototype id", prototypeId);
  console.log("active variant", activeVariant);
  console.log("active version", activeVersion);
  console.log("prototype", prototype);

  // Set active variant and version when data is loaded
  useEffect(() => {
    if (variants && variants.length > 0) {
      const originalVariant =
        variants.find((v) => v.is_original) || variants[0];
      setActiveVariant(originalVariant.id);
      if (originalVariant.latest_version) {
        setActiveVersion(originalVariant.latest_version.id);
      }
    }
  }, [variants]);

  // Create variant mutation
  const createVariantMutation = useMutation({
    mutationFn: (data: CreateVariantRequest) => createVariant(data),
    onSuccess: (newVariant) => {
      queryClient.invalidateQueries({ queryKey: ["variants", prototypeId] });
      setIsCreateVariantDialogOpen(false);
      resetVariantForm();
      toast.success("Variant created successfully");
      setActiveVariant(newVariant.id);
      if (newVariant.latest_version) {
        setActiveVersion(newVariant.latest_version.id);
      }
    },
    onError: (error) => {
      toast.error("Failed to create variant");
      console.error("Create variant error:", error);
    },
  });

  // Edit version mutation
  const editVersionMutation = useMutation({
    mutationFn: (data: EditVersionRequest) => createVersion(data),
    onSuccess: (newVersion) => {
      queryClient.invalidateQueries({ queryKey: ["variants", prototypeId] });
      setIsEditDialogOpen(false);
      resetEditForm();
      toast.success("Updated prototype successfully");
      setActiveVersion(newVersion.id);
    },
    onError: (error) => {
      toast.error("Failed to update prototype");
      console.error("Edit version error:", error);
    },
  });

  const resetVariantForm = () => {
    setVariantForm({
      name: "",
      description: "",
      prompt: "",
    });
  };

  const resetEditForm = () => {
    setEditForm({
      edit_prompt: "",
      name: "",
    });
  };

  const handleCreateVariant = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prototypeId) return;

    createVariantMutation.mutate({
      prototype_id: prototypeId,
      name: variantForm.name,
      description: variantForm.description,
      prompt: variantForm.prompt || undefined,
    });
  };

  const handleEditVersion = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeVariant || !activeVersion) return;

    editVersionMutation.mutate({
      variant_id: activeVariant,
      version_id: activeVersion,
      edit_prompt: editForm.edit_prompt,
      name: editForm.name || undefined,
    });
  };

  const copyCode = () => {
    const activeVariantObj = variants?.find((v) => v.id === activeVariant);
    if (!activeVariantObj) return;

    const activeVersionObj = activeVariantObj.versions?.find(
      (v) => v.id === activeVersion
    );
    if (!activeVersionObj) return;

    navigator.clipboard.writeText(activeVersionObj.html_content);
    toast.success("Code copied to clipboard");
  };

  const getVersionContent = () => {
    if (!activeVariant || !activeVersion) return "";

    const activeVariantObj = variants?.find((v) => v.id === activeVariant);
    if (!activeVariantObj) return "";

    const activeVersionObj = activeVariantObj.versions?.find(
      (v) => v.id === activeVersion
    );
    if (!activeVersionObj) return "";

    return activeVersionObj.html_content;
  };

  const openFullscreen = () => {
    const activeVariantObj = variants?.find((v) => v.id === activeVariant);
    if (!activeVariantObj) return;

    const activeVersionObj = activeVariantObj.versions?.find(
      (v) => v.id === activeVersion
    );
    if (!activeVersionObj) return;

    // Create a new window with the HTML content
    const newWindow = window.open("", "_blank");
    if (newWindow) {
      newWindow.document.write(activeVersionObj.html_content);
      newWindow.document.title = `${prototype?.name} - ${activeVariantObj.name} (V${activeVersionObj.version})`;
      newWindow.document.close();
    } else {
      toast.error("Popup blocked. Please allow popups for this site.");
    }
  };

  if (isPrototypeError || isVariantsError) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center text-red-500">
          Error loading prototype. Please try again later.
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center mb-6">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mr-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        {isPrototypeLoading ? (
          <Skeleton className="h-8 w-64" />
        ) : (
          <h1 className="text-2xl font-bold">{prototype?.name}</h1>
        )}
      </div>

      <div className="mb-6">
        {isPrototypeLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : (
          <p className="text-muted-foreground">{prototype?.description}</p>
        )}
      </div>

      {isVariantsLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      ) : variants?.length === 0 ? (
        <div className="text-center py-10">
          <Layers className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg text-muted-foreground mb-4">
            No variants found
          </p>
          <p className="text-muted-foreground mb-6">
            Create your first variant by clicking the "Create Variant" button.
          </p>
          <Button onClick={() => setIsCreateVariantDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Variant
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="space-y-2">
              <div className="flex space-x-2 items-center">
                <h2 className="text-lg font-semibold">Variants</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCreateVariantDialogOpen(true)}
                >
                  <Plus className="h-4 w-4 mr-1" /> New Variant
                </Button>
              </div>
              <Tabs
                value={activeVariant?.toString() || ""}
                onValueChange={(value: string) => {
                  setActiveVariant(value);
                  const variant = variants?.find((v) => v.id === value);
                  if (variant && variant.latest_version) {
                    setActiveVersion(variant.latest_version.id);
                  }
                }}
                className="w-full"
              >
                <TabsList className="w-full">
                  {variants?.map((variant) => (
                    <TabsTrigger key={variant.id} value={variant.id.toString()}>
                      {variant.name} {variant.is_original && "(Original)"}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
            </div>
          </div>

          {activeVariant && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">Versions</h3>
                  <Tabs
                    value={activeVersion?.toString() || ""}
                    onValueChange={(value: string) => setActiveVersion(value)}
                    className="w-full"
                  >
                    <TabsList className="w-full">
                      {(
                        variants?.find((v) => v.id === activeVariant)
                          ?.versions || []
                      ).map((version) => (
                        <TabsTrigger
                          key={version.id}
                          value={version.id.toString()}
                        >
                          V{version.version}{" "}
                          {version.name ? `- ${version.name}` : ""}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                  </Tabs>
                </div>
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsEditDialogOpen(true);
                    const activeVariantObj = variants?.find(
                      (v) => v.id === activeVariant
                    );
                    if (activeVariantObj) {
                      const activeVersionObj = activeVariantObj.versions?.find(
                        (v) => v.id === activeVersion
                      );
                      if (activeVersionObj) {
                        setEditForm({
                          ...editForm,
                          name: activeVersionObj.name,
                        });
                      }
                    }
                  }}
                >
                  <PenLine className="h-4 w-4 mr-2" />
                  Edit Prototype
                </Button>
              </div>

              <Card className="overflow-hidden">
                <Tabs
                  value={selectedTab}
                  onValueChange={(value: string) =>
                    setSelectedTab(value as "preview" | "code")
                  }
                >
                  <CardHeader className="flex flex-row items-center justify-between px-4 py-3">
                    <div className="flex items-center">
                      <TabsList>
                        <TabsTrigger value="preview">
                          <FileCode className="h-4 w-4 mr-2" />
                          Preview
                        </TabsTrigger>
                        <TabsTrigger value="code">
                          <Code className="h-4 w-4 mr-2" />
                          Code
                        </TabsTrigger>
                      </TabsList>
                    </div>
                    <div className="flex gap-2">
                      {selectedTab === "preview" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={openFullscreen}
                        >
                          <Maximize2 className="h-4 w-4 mr-2" />
                          Fullscreen
                        </Button>
                      )}
                      {selectedTab === "code" && (
                        <Button variant="ghost" size="sm" onClick={copyCode}>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy Code
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    <TabsContent value="preview" className="m-0">
                      <div className="bg-background border-t h-[600px] overflow-auto">
                        <iframe
                          srcDoc={getVersionContent()}
                          title="Prototype Preview"
                          className="w-full h-full"
                          sandbox="allow-scripts"
                        />
                      </div>
                    </TabsContent>
                    <TabsContent value="code" className="m-0">
                      <div className="bg-background border-t h-[600px] overflow-auto">
                        <pre className="p-4 text-sm">
                          <code>{getVersionContent()}</code>
                        </pre>
                      </div>
                    </TabsContent>
                  </CardContent>
                </Tabs>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* Create Variant Dialog */}
      <Dialog
        open={isCreateVariantDialogOpen}
        onOpenChange={setIsCreateVariantDialogOpen}
      >
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Create Variant</DialogTitle>
            <DialogDescription>
              Create a new variant of this prototype. You can optionally provide
              a prompt to customize it.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateVariant}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label htmlFor="variant-name" className="text-sm font-medium">
                  Name
                </label>
                <Input
                  id="variant-name"
                  placeholder="Enter variant name"
                  value={variantForm.name}
                  onChange={(e) =>
                    setVariantForm({ ...variantForm, name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="variant-description"
                  className="text-sm font-medium"
                >
                  Description
                </label>
                <Textarea
                  id="variant-description"
                  placeholder="Enter variant description"
                  value={variantForm.description}
                  onChange={(e) =>
                    setVariantForm({
                      ...variantForm,
                      description: e.target.value,
                    })
                  }
                  rows={2}
                  required
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="variant-prompt" className="text-sm font-medium">
                  Prompt (Optional)
                </label>
                <Textarea
                  id="variant-prompt"
                  placeholder="Describe how you want to customize this variant..."
                  value={variantForm.prompt}
                  onChange={(e) =>
                    setVariantForm({ ...variantForm, prompt: e.target.value })
                  }
                  rows={4}
                />
                <p className="text-xs text-muted-foreground">
                  If left empty, we'll create a default variation of the
                  original prototype.
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsCreateVariantDialogOpen(false);
                  resetVariantForm();
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createVariantMutation.isPending}>
                {createVariantMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Version Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Edit Prototype</DialogTitle>
            <DialogDescription>
              Describe the changes you want to make to this prototype.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditVersion}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label htmlFor="version-name" className="text-sm font-medium">
                  Version Name (Optional)
                </label>
                <Input
                  id="version-name"
                  placeholder="Give this version a name"
                  value={editForm.name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="edit-prompt" className="text-sm font-medium">
                  Edit Instructions
                </label>
                <Textarea
                  id="edit-prompt"
                  placeholder="Describe the changes you want to make..."
                  value={editForm.edit_prompt}
                  onChange={(e) =>
                    setEditForm({ ...editForm, edit_prompt: e.target.value })
                  }
                  rows={5}
                  required
                  className="min-h-[150px]"
                />
                <p className="text-xs text-muted-foreground">
                  Example: "Change the button color to red and add a footer with
                  contact information."
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsEditDialogOpen(false);
                  resetEditForm();
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={editVersionMutation.isPending}>
                {editVersionMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Update"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PrototypeDetail;
