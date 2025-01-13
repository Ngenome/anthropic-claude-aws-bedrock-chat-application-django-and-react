export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: string | number;
  edited_at?: string;
  hidden?: boolean;
  message_pair: string;
}

export interface MessagePair {
  id: number;
  messages: Message[];
  chat: number;
}
