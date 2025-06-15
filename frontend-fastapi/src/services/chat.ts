import axios from "axios";
import { API_URL } from "@/constants/urls";
import { tokenStorage, userStorage } from "./auth";

const BASE_CHAT_URL = `${API_URL}/api/v1/chat`;

// Get token from centralized storage
const getAuthToken = () => {
  return tokenStorage.get();
};

// Create axios instance with auth headers
const createAuthHeaders = () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found. Please log in again.");
  }
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
};

// Create axios instance with interceptors
const createChatAxios = () => {
  const instance = axios.create({
    timeout: 30000,
  });

  // Request interceptor to add token
  instance.interceptors.request.use(
    (config) => {
      const token = getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor to handle token expiration
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        // Token expired or invalid - clear storage and redirect to login
        tokenStorage.remove();
        userStorage.remove();

        // If we're not already on the login page, redirect
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );

  return instance;
};

const chatApi = createChatAxios();

export interface ChatMessage {
  message: string;
  files?: string[];
  system_prompt_override?: string;
}

export interface ChatCreateRequest {
  title: string;
  project_id?: string;
  system_prompt?: string;
}

export interface StreamChunk {
  type: string;
  content?: string;
  message_pair_id?: string;
  error?: string;
}

export const chatService = {
  // Create a new chat
  async createChat(chatData: ChatCreateRequest) {
    const response = await chatApi.post(`${BASE_CHAT_URL}/chats`, chatData, {
      headers: createAuthHeaders(),
    });
    return response.data;
  },

  // Get all chats
  async getChats(
    projectId?: string,
    includeArchived = false,
    limit = 50,
    offset = 0
  ) {
    const params = new URLSearchParams({
      include_archived: includeArchived.toString(),
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (projectId) {
      params.append("project_id", projectId);
    }

    const response = await chatApi.get(`${BASE_CHAT_URL}/chats?${params}`, {
      headers: createAuthHeaders(),
    });
    return response.data;
  },

  // Get a specific chat
  async getChat(chatId: string) {
    const response = await chatApi.get(`${BASE_CHAT_URL}/chats/${chatId}`, {
      headers: createAuthHeaders(),
    });
    return response.data;
  },

  // Update chat
  async updateChat(chatId: string, updateData: Partial<ChatCreateRequest>) {
    const response = await chatApi.put(
      `${BASE_CHAT_URL}/chats/${chatId}`,
      updateData,
      { headers: createAuthHeaders() }
    );
    return response.data;
  },

  // Delete chat
  async deleteChat(chatId: string) {
    const response = await chatApi.delete(`${BASE_CHAT_URL}/chats/${chatId}`, {
      headers: createAuthHeaders(),
    });
    return response.data;
  },

  // Send message with streaming response
  async sendMessage(
    chatId: string,
    messageData: ChatMessage
  ): Promise<ReadableStream> {
    const token = getAuthToken();

    if (!token) {
      throw new Error("No authentication token found. Please log in again.");
    }

    const response = await fetch(`${BASE_CHAT_URL}/chats/${chatId}/messages`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(messageData),
    });

    if (response.status === 401) {
      // Handle 401 specifically for streaming requests
      tokenStorage.remove();
      userStorage.remove();

      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
      throw new Error("Authentication failed. Please log in again.");
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("Response body is null");
    }

    return response.body;
  },

  // Parse streaming response
  async *parseStreamingResponse(
    stream: ReadableStream
  ): AsyncGenerator<StreamChunk> {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            try {
              const jsonStr = trimmed.replace("data: ", "").trim();
              if (jsonStr && jsonStr !== "") {
                const parsedChunk = JSON.parse(jsonStr);
                yield parsedChunk;
              }
            } catch (error) {
              console.error(
                "Error parsing stream chunk:",
                error,
                "Raw line:",
                line
              );
            }
          } else if (trimmed !== "") {
            // Handle lines that might not have "data: " prefix
            try {
              const parsedChunk = JSON.parse(trimmed);
              yield parsedChunk;
            } catch (error) {
              // This is expected for SSE format - ignore
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  // Archive/unarchive chat
  async archiveChat(chatId: string, archived = true) {
    const response = await chatApi.post(
      `${BASE_CHAT_URL}/chats/${chatId}/archive`,
      null,
      {
        headers: createAuthHeaders(),
        params: { archived },
      }
    );
    return response.data;
  },

  // Get projects
  async getProjects(includeArchived = false) {
    const response = await chatApi.get(`${BASE_CHAT_URL}/projects`, {
      headers: createAuthHeaders(),
      params: { include_archived: includeArchived },
    });
    return response.data;
  },

  // Create project
  async createProject(projectData: {
    name: string;
    description?: string;
    instructions?: string;
  }) {
    const response = await chatApi.post(
      `${BASE_CHAT_URL}/projects`,
      projectData,
      { headers: createAuthHeaders() }
    );
    return response.data;
  },

  // Get saved system prompts
  async getSavedSystemPrompts() {
    const response = await chatApi.get(`${BASE_CHAT_URL}/system-prompts`, {
      headers: createAuthHeaders(),
    });
    return response.data;
  },

  // Create saved system prompt
  async createSavedSystemPrompt(promptData: { title: string; prompt: string }) {
    const response = await chatApi.post(
      `${BASE_CHAT_URL}/system-prompts`,
      promptData,
      { headers: createAuthHeaders() }
    );
    return response.data;
  },
};
