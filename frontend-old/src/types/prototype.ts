export interface DesignProject {
  id: number;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Group {
  id: number;
  name: string;
  description: string;
  design_project: number;
  created_at: string;
  updated_at: string;
}

export interface Prototype {
  id: number;
  name: string;
  description: string;
  design_project: number;
  group: number | null;
  created_at: string;
  updated_at: string;
}

export interface PrototypeVariant {
  id: string;
  name: string;
  description: string;
  prototype: string;
  is_original: boolean;
  created_at: string;
  updated_at: string;
  versions: PrototypeVersion[];
  version_count: number;
  latest_version: PrototypeVersion;
}

export interface PrototypeVersion {
  id: string;
  name: string;
  version: number;
  variant: string;
  html_content: string;
  created_at: string;
  updated_at: string;
}

export interface GeneratePrototypeRequest {
  design_project_id: number;
  prompt: string;
  group_id?: number | null;
}

export interface EditVersionRequest {
  variant_id: string;
  version_id: string;
  edit_prompt: string;
  name?: string;
}

export interface CreateVariantRequest {
  prototype_id: string;
  name: string;
  description: string;
  prompt?: string;
}
