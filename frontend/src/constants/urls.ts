// src/constants/urls.ts
const BASE_URL = "http://localhost:8001/api/v1/chat/";
export const API_URL = "http://0.0.0.0:8001";
const urls = {
  chatList: `${BASE_URL}chat-list/`,
  chatMessages: (chatId: string) => `${BASE_URL}chats/${chatId}/messages/`,
  chat: (chatId: string) => `${BASE_URL}chats/${chatId}/`,
  chatTokens: (chatId: string) => `${BASE_URL}chats/${chatId}/tokens/`,
  claude: `${BASE_URL}claude/`,
  savedSystemPrompts: `${BASE_URL}saved-system-prompts/`,
  updateSystemPrompt: (chatId: string) =>
    `${BASE_URL}chats/${chatId}/system-prompt/`,
  updateSavedSystemPrompt: (promptId: number) =>
    `${BASE_URL}saved-system-prompts/${promptId}/`,
  upload: (chatId: string) => `${BASE_URL}chats/${chatId}/upload/`,
  attachments: (chatId: string) => `${BASE_URL}chats/${chatId}/attachments/`,
  deleteAttachment: (attachmentId: string) =>
    `${BASE_URL}attachments/${attachmentId}/`,
  fileContent: (attachmentId: string) =>
    `${BASE_URL}attachments/${attachmentId}/content/`,
  projects: `${BASE_URL}projects/`,
  project: (projectId: string) => `${BASE_URL}projects/${projectId}/`,
  projectKnowledge: (projectId: string) =>
    `${BASE_URL}projects/${projectId}/knowledge/`,
  projectChats: (projectId: string) =>
    `${BASE_URL}projects/${projectId}/chats/`,
  knowledge: `${BASE_URL}knowledge/`,
  toggleKnowledge: (knowledgeId: number) =>
    `${BASE_URL}knowledge/${knowledgeId}/toggle/`,
  deleteKnowledge: (knowledgeId: number) =>
    `${BASE_URL}knowledge/${knowledgeId}/`,
  editMessage: (messageId: string) => `${BASE_URL}messages/${messageId}/edit/`,
  deleteMessagePair: (pairId: string) => `${BASE_URL}message-pairs/${pairId}/`,
  toggleMessagePair: (pairId: string) =>
    `${BASE_URL}message-pairs/${pairId}/toggle/`,
};

export default urls;
