// src/constants/urls.ts

const BASE_CHATS_URL = "http://localhost:8001/api/v1/chat/";
export const BASE_PROTOTYPES_URL = "http://localhost:8001/api/v1/prototypes";

export const API_URL = "http://0.0.0.0:8001";
const urls = {
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
  chats: `${BASE_CHATS_URL}chats/`,
  chatMessages: (chatId: string) =>
    `${BASE_CHATS_URL}chats/${chatId}/messages/`,
  chatDetail: (chatId: string) => `${BASE_CHATS_URL}chats/${chatId}/`,
  chatTokens: (chatId: string) => `${BASE_CHATS_URL}chats/${chatId}/tokens/`,
  chat: `${BASE_CHATS_URL}chat/`,
  savedSystemPrompts: `${BASE_CHATS_URL}saved-system-prompts/`,
  updateSystemPrompt: (chatId: string) =>
    `${BASE_CHATS_URL}chats/${chatId}/system-prompt/`,
  updateSavedSystemPrompt: (promptId: number) =>
    `${BASE_CHATS_URL}saved-system-prompts/${promptId}/`,
  upload: (chatId: string) => `${BASE_CHATS_URL}chats/${chatId}/upload/`,
  attachments: (chatId: string) =>
    `${BASE_CHATS_URL}chats/${chatId}/attachments/`,
  deleteAttachment: (attachmentId: string) =>
    `${BASE_CHATS_URL}attachments/${attachmentId}/`,
  fileContent: (attachmentId: string) =>
    `${BASE_CHATS_URL}attachments/${attachmentId}/content/`,
  projects: `${BASE_CHATS_URL}projects/`,
  project: (projectId: string) => `${BASE_CHATS_URL}projects/${projectId}/`,
  projectKnowledge: (projectId: string) =>
    `${BASE_CHATS_URL}projects/${projectId}/knowledge/`,
  projectChats: (projectId: string) =>
    `${BASE_CHATS_URL}projects/${projectId}/chats/`,
  knowledge: `${BASE_CHATS_URL}knowledge/`,
  toggleKnowledge: (knowledgeId: number) =>
    `${BASE_CHATS_URL}knowledge/${knowledgeId}/toggle/`,
  deleteKnowledge: (knowledgeId: number) =>
    `${BASE_CHATS_URL}knowledge/${knowledgeId}/`,
  editMessage: (messageId: string) =>
    `${BASE_CHATS_URL}messages/${messageId}/edit/`,
  deleteMessagePair: (pairId: string) =>
    `${BASE_CHATS_URL}message-pairs/${pairId}/delete/`,
  toggleMessagePair: (pairId: string) =>
    `${BASE_CHATS_URL}message-pairs/${pairId}/toggle/`,
};

export default urls;
