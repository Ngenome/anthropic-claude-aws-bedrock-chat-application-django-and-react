import { authenticatedApi } from "@/services/auth";
import {
  DesignProject,
  Group,
  Prototype,
  PrototypeVariant,
  PrototypeVersion,
  GeneratePrototypeRequest,
  EditVersionRequest,
  CreateVariantRequest,
} from "@/types/prototype";
import { BASE_PROTOTYPES_URL } from "@/constants/urls";

const API_BASE_URL = BASE_PROTOTYPES_URL;

// Design Projects
export const fetchDesignProjects = async () => {
  const response = await authenticatedApi.get<DesignProject[]>(
    `${API_BASE_URL}/design-projects/`
  );
  return response.data;
};

export const fetchDesignProject = async (id: string) => {
  const response = await authenticatedApi.get<DesignProject>(
    `${API_BASE_URL}/design-projects/${id}/`
  );
  return response.data;
};

export const createDesignProject = async (data: {
  name: string;
  description: string;
}) => {
  const response = await authenticatedApi.post<DesignProject>(
    `${API_BASE_URL}/design-projects/`,
    {
      title: data.name,
      description: data.description,
    }
  );
  return response.data;
};

export const updateDesignProject = async (
  id: number,
  data: { name?: string; description?: string }
) => {
  const response = await authenticatedApi.patch<DesignProject>(
    `${API_BASE_URL}/design-projects/${id}/`,
    {
      title: data.name,
      description: data.description,
    }
  );
  return response.data;
};

export const deleteDesignProject = async (id: number) => {
  await authenticatedApi.delete(`${API_BASE_URL}/design-projects/${id}/`);
};

export const fetchDesignProjectPrototypes = async (projectId: number) => {
  const response = await authenticatedApi.get<Prototype[]>(
    `${API_BASE_URL}/design-projects/${projectId}/prototypes/`
  );
  return response.data;
};

// Groups
export const fetchGroups = async () => {
  const response = await authenticatedApi.get<Group[]>(
    `${API_BASE_URL}/groups/`
  );
  return response.data;
};

export const fetchGroup = async (id: number) => {
  const response = await authenticatedApi.get<Group>(
    `${API_BASE_URL}/groups/${id}/`
  );
  return response.data;
};

export const createGroup = async (data: {
  name: string;
  description: string;
  design_project: number;
}) => {
  const response = await authenticatedApi.post<Group>(
    `${API_BASE_URL}/groups/`,
    data
  );
  return response.data;
};

export const updateGroup = async (
  id: number,
  data: { name?: string; description?: string }
) => {
  const response = await authenticatedApi.patch<Group>(
    `${API_BASE_URL}/groups/${id}/`,
    data
  );
  return response.data;
};

export const deleteGroup = async (id: number) => {
  await authenticatedApi.delete(`${API_BASE_URL}/groups/${id}/`);
};

export const fetchGroupPrototypes = async (groupId: number) => {
  const response = await authenticatedApi.get<Prototype[]>(
    `${API_BASE_URL}/groups/${groupId}/prototypes/`
  );
  return response.data;
};

// Prototypes
export const fetchPrototypes = async () => {
  const response = await authenticatedApi.get<Prototype[]>(
    `${API_BASE_URL}/prototypes/`
  );
  return response.data;
};

export const fetchPrototype = async (id: string) => {
  const response = await authenticatedApi.get<Prototype>(
    `${API_BASE_URL}/prototypes/${id}/`
  );
  return response.data;
};

export const generatePrototype = async (data: GeneratePrototypeRequest) => {
  const response = await authenticatedApi.post<Prototype>(
    `${API_BASE_URL}/generate-prototype/`,
    data
  );
  return response.data;
};

export const updatePrototype = async (
  id: number,
  data: { name?: string; description?: string; group?: number | null }
) => {
  const response = await authenticatedApi.patch<Prototype>(
    `${API_BASE_URL}/prototypes/${id}/`,
    data
  );
  return response.data;
};

export const deletePrototype = async (id: number) => {
  await authenticatedApi.delete(`${API_BASE_URL}/prototypes/${id}/`);
};

// Variants
export const fetchVariants = async (prototypeId: string) => {
  const response = await authenticatedApi.get<PrototypeVariant[]>(
    `${API_BASE_URL}/variants/?prototype=${prototypeId}`
  );
  return response.data;
};

export const fetchVariant = async (variantId: number) => {
  const response = await authenticatedApi.get<PrototypeVariant>(
    `${API_BASE_URL}/variants/${variantId}/`
  );
  return response.data;
};

export const createVariant = async (data: CreateVariantRequest) => {
  const response = await authenticatedApi.post<PrototypeVariant>(
    `${API_BASE_URL}/variants/`,
    data
  );
  return response.data;
};

// Versions
export const fetchVersions = async (variantId: number) => {
  const response = await authenticatedApi.get<PrototypeVersion[]>(
    `${API_BASE_URL}/versions/?variant=${variantId}`
  );
  return response.data;
};

export const fetchVersion = async (versionId: number) => {
  const response = await authenticatedApi.get<PrototypeVersion>(
    `${API_BASE_URL}/versions/${versionId}/`
  );
  return response.data;
};

export const createVersion = async (data: EditVersionRequest) => {
  const response = await authenticatedApi.post<PrototypeVersion>(
    `${API_BASE_URL}/versions/`,
    data
  );
  return response.data;
};
