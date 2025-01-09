import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import token from "@/constants/token";
import urls from "@/constants/urls";

interface Project {
  id: number;
  name: string;
  description: string;
  instructions: string;
  created_at: string;
  updated_at: string;
  total_knowledge_tokens: number;
}

interface KnowledgeItem {
  id: number;
  title: string;
  content: string;
  include_in_chat: boolean;
  token_count: number;
  created_at: string;
  updated_at: string;
}

interface CreateProjectData {
  name: string;
  description?: string;
}

interface AddKnowledgeData {
  project: number;
  title: string;
  content: string;
}

export function useProjects() {
  const { data, isLoading, isError, error } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: async () => {
      const response = await axios.get(urls.projects, {
        headers: { Authorization: `token ${token}` },
      });
      return response.data;
    },
  });
  // if error, log it
  if (isError) {
    console.error(error);
  }

  return { projects: data, isLoading, isError, error };
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: async () => {
      const response = await axios.get(urls.project(projectId), {
        headers: { Authorization: `token ${token}` },
      });
      return response.data as Project;
    },
  });
}

export function useProjectKnowledge(projectId: string) {
  return useQuery({
    queryKey: ["project-knowledge", projectId],
    queryFn: async () => {
      const response = await axios.get(urls.projectKnowledge(projectId), {
        headers: { Authorization: `token ${token}` },
      });
      return response.data as KnowledgeItem[];
    },
  });
}

export function useProjectChats(projectId: string) {
  return useQuery({
    queryKey: ["project-chats", projectId],
    queryFn: async () => {
      const response = await axios.get(urls.projectChats(projectId), {
        headers: { Authorization: `token ${token}` },
      });
      return response.data;
    },
  });
}

export function useToggleKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id }: { id: number }) => {
      const response = await axios.patch(
        urls.toggleKnowledge(id),
        {},
        { headers: { Authorization: `token ${token}` } }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-knowledge"] });
    },
  });
}

export function useDeleteKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await axios.delete(urls.deleteKnowledge(id), {
        headers: { Authorization: `token ${token}` },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-knowledge"] });
    },
  });
}

export function useUpdateProjectInstructions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectId,
      instructions,
    }: {
      projectId: number;
      instructions: string;
    }) => {
      const response = await axios.patch(
        urls.project(projectId.toString()),
        { instructions },
        { headers: { Authorization: `token ${token}` } }
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["project", variables.projectId],
      });
    },
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreateProjectData) => {
      const response = await axios.post(urls.projects, data, {
        headers: { Authorization: `token ${token}` },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useAddKnowledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AddKnowledgeData) => {
      const response = await axios.post(urls.knowledge, data, {
        headers: { Authorization: `token ${token}` },
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["project-knowledge", variables.project.toString()],
      });
      queryClient.invalidateQueries({
        queryKey: ["project", variables.project.toString()],
      });
    },
  });
}
