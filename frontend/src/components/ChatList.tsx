// src/components/ChatList.tsx
import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import urls from "@/constants/urls";
import token from "@/constants/token";

interface Chat {
  id: number;
  title: string;
}

const ChatList: React.FC = () => {
  const [chats, setChats] = useState<Chat[]>([]);

  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await axios.get<Chat[]>(urls.chatList, {
          headers: {
            Authorization: `token ${token}`,
          },
        });
        setChats(Array.isArray(response.data) ? response.data : []);
      } catch (error) {
        console.error("Error fetching chats:", error);
        setChats([]);
      }
    };

    fetchChats();
  }, []);

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Your Chats</CardTitle>
      </CardHeader>
      <CardContent>
        {chats.length > 0 ? (
          <ul className="space-y-2">
            {chats?.map((chat) => (
              <li key={chat.id}>
                <Link
                  to={`/chat/${chat.id}`}
                  className="text-blue-500 hover:underline"
                >
                  {chat.title}
                </Link>
              </li>
            ))}
          </ul>
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
