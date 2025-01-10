import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import token from "@/constants/token";
import urls from "@/constants/urls";
import { Plus, FolderOpen, Loader2 } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

interface Chat {
  id: number;
  title: string;
}

export function Sidebar() {
  const navigate = useNavigate();

  const { data: chats, isLoading } = useQuery({
    queryKey: ["chats"],
    queryFn: async () => {
      const response = await axios.get<Chat[]>(urls.chatList, {
        headers: { Authorization: `token ${token}` },
      });
      return response.data;
    },
  });

  return (
    <div className="w-64 h-screen bg-gray-800 text-white p-4 flex flex-col">
      {/* New Chat Button */}
      <Button className="w-full mb-4" onClick={() => navigate("/chat/new")}>
        <Plus className="h-4 w-4 mr-2" />
        New Chat
      </Button>

      {/* Projects Link */}
      <Button
        variant="ghost"
        className="w-full mb-4 text-white hover:text-white hover:bg-gray-700"
        asChild
      >
        <Link to="/projects">
          <FolderOpen className="h-4 w-4 mr-2" />
          Projects
        </Link>
      </Button>

      {/* Chat List */}
      <div className="text-sm font-semibold mb-2 text-gray-400">Chats</div>
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex justify-center items-center py-4">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : (
          <div className="space-y-1">
            {chats?.map((chat) => (
              <Link
                key={chat.id}
                to={`/chat/${chat.id}`}
                className="block px-2 py-1.5 rounded hover:bg-gray-700 transition-colors"
              >
                {chat.title}
              </Link>
            ))}
          </div>
        )}
      </ScrollArea>

      <div className="p-4 mt-auto border-t">
        <ThemeToggle />
      </div>
    </div>
  );
}
