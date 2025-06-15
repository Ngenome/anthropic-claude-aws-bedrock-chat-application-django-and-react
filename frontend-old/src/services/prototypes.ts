import axios from "axios";
import token from "@/constants/token";
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
  const response = await axios.get<DesignProject[]>(
    `${API_BASE_URL}/design-projects/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const fetchDesignProject = async (id: string) => {
  const response = await axios.get<DesignProject>(
    `${API_BASE_URL}/design-projects/${id}/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const createDesignProject = async (data: {
  name: string;
  description: string;
}) => {
  const response = await axios.post<DesignProject>(
    `${API_BASE_URL}/design-projects/`,
    {
      title: data.name,
      description: data.description,
    },
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const updateDesignProject = async (
  id: number,
  data: { name?: string; description?: string }
) => {
  const response = await axios.patch<DesignProject>(
    `${API_BASE_URL}/design-projects/${id}/`,
    {
      title: data.name,
      description: data.description,
    },
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const deleteDesignProject = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/design-projects/${id}/`, {
    headers: { Authorization: `token ${token}` },
  });
};

export const fetchDesignProjectPrototypes = async (projectId: number) => {
  const response = await axios.get<Prototype[]>(
    `${API_BASE_URL}/design-projects/${projectId}/prototypes/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

// Groups
export const fetchGroups = async () => {
  const response = await axios.get<Group[]>(`${API_BASE_URL}/groups/`, {
    headers: { Authorization: `token ${token}` },
  });
  return response.data;
};

export const fetchGroup = async (id: number) => {
  const response = await axios.get<Group>(`${API_BASE_URL}/groups/${id}/`, {
    headers: { Authorization: `token ${token}` },
  });
  return response.data;
};

export const createGroup = async (data: {
  name: string;
  description: string;
  design_project: number;
}) => {
  const response = await axios.post<Group>(`${API_BASE_URL}/groups/`, data, {
    headers: { Authorization: `token ${token}` },
  });
  return response.data;
};

export const updateGroup = async (
  id: number,
  data: { name?: string; description?: string }
) => {
  const response = await axios.patch<Group>(
    `${API_BASE_URL}/groups/${id}/`,
    data,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const deleteGroup = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/groups/${id}/`, {
    headers: { Authorization: `token ${token}` },
  });
};

export const fetchGroupPrototypes = async (groupId: number) => {
  const response = await axios.get<Prototype[]>(
    `${API_BASE_URL}/groups/${groupId}/prototypes/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

// Prototypes
export const fetchPrototypes = async () => {
  const response = await axios.get<Prototype[]>(`${API_BASE_URL}/prototypes/`, {
    headers: { Authorization: `token ${token}` },
  });
  return response.data;
};

export const fetchPrototype = async (id: string) => {
  const response = await axios.get<Prototype>(
    `${API_BASE_URL}/prototypes/${id}/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const generatePrototype = async (data: GeneratePrototypeRequest) => {
  const response = await axios.post<Prototype>(
    `${API_BASE_URL}/generate-prototype/`,
    data,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const updatePrototype = async (
  id: number,
  data: { name?: string; description?: string; group?: number | null }
) => {
  const response = await axios.patch<Prototype>(
    `${API_BASE_URL}/prototypes/${id}/`,
    data,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const deletePrototype = async (id: number) => {
  await axios.delete(`${API_BASE_URL}/prototypes/${id}/`, {
    headers: { Authorization: `token ${token}` },
  });
};

// Variants
export const fetchVariants = async (prototypeId: string) => {
  const response = await axios.get<PrototypeVariant[]>(
    `${API_BASE_URL}/variants/?prototype=${prototypeId}`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const fetchVariant = async (variantId: number) => {
  const response = await axios.get<PrototypeVariant>(
    `${API_BASE_URL}/variants/${variantId}/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const createVariant = async (data: CreateVariantRequest) => {
  const response = await axios.post<PrototypeVariant>(
    `${API_BASE_URL}/prototypes/${data.prototype_id}/create_variant/`,
    data,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

// Versions
export const fetchVersions = async (variantId: number) => {
  const response = await axios.get<PrototypeVersion[]>(
    `${API_BASE_URL}/variants/${variantId}/versions/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const fetchVersion = async (versionId: number) => {
  const response = await axios.get<PrototypeVersion>(
    `${API_BASE_URL}/versions/${versionId}/`,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};

export const createVersion = async (data: EditVersionRequest) => {
  const response = await axios.post<PrototypeVersion>(
    `${API_BASE_URL}/variants/${data.variant_id}/create_version/`,
    data,
    {
      headers: { Authorization: `token ${token}` },
    }
  );
  return response.data;
};
