// Base interfaces for common fields
interface BaseModel {
  id: number;
  created_at: string;
  updated_at?: string;
}

// User related types
export interface User {
  id: number;
  username: string;
  email: string;
}

// Message related types
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type?: "text" | "image";
  image?: string;
  text?: string;
  token_count: number;
  hidden?: boolean;
  edited_at?: string;
  original_text?: string;
  created_at: string;
  is_archived?: boolean;
  message_pair: string;
}

export interface MessagePair extends BaseModel {
  id: number;
  messages: Message[];
  chat: number;
}

// Chat related types
export interface Chat extends BaseModel {
  id: number;
  uuid: string;
  title: string;
  user: number;
  project?: number;
  system_prompt?: string;
  is_archived?: boolean;
  total_tokens?: number;
}

// Project related types
export interface Project extends BaseModel {
  id: number;
  name: string;
  description?: string;
  instructions?: string;
  user: number;
  is_archived?: boolean;
  total_knowledge_tokens: number;
}

export interface ProjectKnowledge extends BaseModel {
  id: number;
  project: number;
  content: string;
  title: string;
  include_in_chat: boolean;
  token_count: number;
}

// System prompt related types
export interface SavedSystemPrompt extends BaseModel {
  id: number;
  user: number;
  title: string;
  prompt: string;
}

// File attachment related types
export interface Attachment extends BaseModel {
  id: number;
  chat: number;
  file: string;
  original_name: string;
}

// Token usage related types
export interface TokenUsage extends BaseModel {
  id: number;
  user: number;
  chat: number;
  tokens_used: number;
}

// API Response types
export interface TokenStats {
  message_tokens: number;
  project_tokens: number;
  total_tokens: number;
  max_tokens: number;
  usage_percentage: number;
}

export interface ChatResponse {
  messages: Message[];
  system_prompt: string;
}

export interface StreamResponse {
  type: "text" | "chat_id";
  content: string;
}

// Request types
export interface SendMessageRequest {
  chat_id: string;
  message: string;
  attachment_ids: string[];
  project_id?: number;
  system_prompt?: string;
}

export interface UpdateSystemPromptRequest {
  system_prompt: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  instructions?: string;
}

export interface CreateKnowledgeRequest {
  project: number;
  content: string;
  title: string;
  include_in_chat?: boolean;
}

export interface EditMessageRequest {
  text: string;
}

// Enum types
export enum MessageRole {
  User = "user",
  Assistant = "assistant",
}

export enum MessageType {
  Text = "text",
  Image = "image",
}
