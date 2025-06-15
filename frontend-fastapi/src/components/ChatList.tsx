// src/components/ChatList.tsx
import React, { useState, useEffect, useRef, useMemo } from "react";
import { Link } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { chatService } from "@/services/chat";

interface Chat {
  id: string;
  title: string;
  created_at: string;
}

const ChatList: React.FC = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Use a ref to prevent unnecessary re-fetches
  const fetchController = useRef<AbortController>();

  useEffect(() => {
    const fetchChats = async () => {
      try {
        // Cancel previous fetch if exists
        if (fetchController.current) {
          fetchController.current.abort();
        }

        fetchController.current = new AbortController();

        const response = await chatService.getChats();
        setChats(Array.isArray(response) ? response : []);
      } catch (error) {
        console.error("Error fetching chats:", error);
        setChats([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchChats();

    return () => {
      fetchController.current?.abort();
    };
  }, []);

  // Memoize the chat list rendering
  const renderChatList = useMemo(
    () => (
      <ul className="space-y-2">
        {chats?.map((chat) => (
          <li key={chat.id}>
            <Link
              to={`/chat/${chat.id}`}
              className="text-blue-500 hover:underline block p-2 rounded-md hover:bg-muted/50 transition-colors"
            >
              {chat.title}
            </Link>
          </li>
        ))}
      </ul>
    ),
    [chats]
  );

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Your Chats</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center p-4">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : chats.length > 0 ? (
          renderChatList
        ) : (
          <p>No chats available.</p>
        )}
        <Button className="mt-4" asChild>
          <Link to="/chat/new">Start New Chat</Link>
        </Button>
      </CardContent>
    </Card>
  );
};

export default ChatList;
