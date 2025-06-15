// src/constants/urls.ts

// FastAPI backend URL (port 8000)
export const API_URL = "http://localhost:8000";
const BASE_AUTH_URL = `${API_URL}/api/v1/auth`;
const BASE_CHAT_URL = `${API_URL}/api/v1/chat`;
export const BASE_PROTOTYPES_URL = `${API_URL}/api/v1/prototypes`;

// Authentication endpoints
export const authUrls = {
  register: `${BASE_AUTH_URL}/register`,
  login: `${BASE_AUTH_URL}/login`,
  logout: `${BASE_AUTH_URL}/logout`,
  profile: `${BASE_AUTH_URL}/profile`,
  verifyEmail: `${BASE_AUTH_URL}/verify-email`,
  resendVerification: `${BASE_AUTH_URL}/resend-verification`,
  forgotPassword: `${BASE_AUTH_URL}/forgot-password`,
  resetPassword: `${BASE_AUTH_URL}/reset-password`,
  changePassword: `${BASE_AUTH_URL}/change-password`,
  googleAuth: `${BASE_AUTH_URL}/google`,
};

// Main application URLs
const urls = {
  // Prototype URLs (updated for FastAPI structure)
  designProjects: `${BASE_PROTOTYPES_URL}/design-projects/`,
  designProject: (designProjectId: string) =>
    `${BASE_PROTOTYPES_URL}/design-projects/${designProjectId}/`,
  groups: `${BASE_PROTOTYPES_URL}/groups/`,
  group: (groupId: string) => `${BASE_PROTOTYPES_URL}/groups/${groupId}/`,
  prototypes: `${BASE_PROTOTYPES_URL}/prototypes/`,
  prototype: (prototypeId: string) =>
    `${BASE_PROTOTYPES_URL}/prototypes/${prototypeId}/`,
  variants: (prototypeId: string) =>
    `${BASE_PROTOTYPES_URL}/prototypes/${prototypeId}/variants/`,
  variant: (variantId: string) =>
    `${BASE_PROTOTYPES_URL}/variants/${variantId}/`,
  versions: (variantId: string) =>
    `${BASE_PROTOTYPES_URL}/variants/${variantId}/versions/`,
  version: (versionId: string) =>
    `${BASE_PROTOTYPES_URL}/versions/${versionId}/`,

  // Chat URLs (updated for FastAPI structure)
  chats: `${BASE_CHAT_URL}/chats`,
  chatMessages: (chatId: string) => `${BASE_CHAT_URL}/chats/${chatId}/messages`,
  chatDetail: (chatId: string) => `${BASE_CHAT_URL}/chats/${chatId}`,
  chatTokens: (chatId: string) => `${BASE_CHAT_URL}/chats/${chatId}/tokens`,
  chat: `${BASE_CHAT_URL}/chat/`, // Legacy endpoint if needed

  // Project URLs
  projects: `${BASE_CHAT_URL}/projects`,
  project: (projectId: string) => `${BASE_CHAT_URL}/projects/${projectId}`,
  projectKnowledge: (projectId: string) =>
    `${BASE_CHAT_URL}/projects/${projectId}/knowledge`,
  projectChats: (projectId: string) =>
    `${BASE_CHAT_URL}/projects/${projectId}/chats`,

  // Knowledge URLs
  knowledge: `${BASE_CHAT_URL}/knowledge/`,
  toggleKnowledge: (knowledgeId: number) =>
    `${BASE_CHAT_URL}/knowledge/${knowledgeId}/toggle/`,
  deleteKnowledge: (knowledgeId: number) =>
    `${BASE_CHAT_URL}/knowledge/${knowledgeId}/`,

  // Message URLs
  editMessage: (messageId: string) =>
    `${BASE_CHAT_URL}/messages/${messageId}/edit/`,
  deleteMessagePair: (pairId: string) =>
    `${BASE_CHAT_URL}/message-pairs/${pairId}/delete/`,
  toggleMessagePair: (pairId: string) =>
    `${BASE_CHAT_URL}/message-pairs/${pairId}/toggle/`,

  // System prompts
  savedSystemPrompts: `${BASE_CHAT_URL}/saved-system-prompts/`,
  updateSystemPrompt: (chatId: string) =>
    `${BASE_CHAT_URL}/chats/${chatId}/system-prompt/`,
  updateSavedSystemPrompt: (promptId: number) =>
    `${BASE_CHAT_URL}/saved-system-prompts/${promptId}/`,

  // File uploads
  upload: (chatId: string) => `${BASE_CHAT_URL}/chats/${chatId}/upload/`,
  attachments: (chatId: string) =>
    `${BASE_CHAT_URL}/chats/${chatId}/attachments/`,
  deleteAttachment: (attachmentId: string) =>
    `${BASE_CHAT_URL}/attachments/${attachmentId}/`,
  fileContent: (attachmentId: string) =>
    `${BASE_CHAT_URL}/attachments/${attachmentId}/content/`,
};

export default urls;
