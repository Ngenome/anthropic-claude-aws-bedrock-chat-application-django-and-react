import React, { useState, useCallback, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  useInfiniteQuery,
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import {
  Clock,
  Calendar,
  Trash2,
  Pencil,
  Check,
  X,
  Plus,
  FolderIcon,
  Layout,
  ChevronRight,
} from "lucide-react";
import { useDebounce } from "@/hooks/useDebounce";
import { fetchDesignProjects } from "@/services/prototypes";
import { chatService } from "@/services/chat";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Chat {
  id: number;
  title: string;
  created_at: string;
}

export function Sidebar() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editingChatId, setEditingChatId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [chatToDelete, setChatToDelete] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebounce(searchQuery, 300);

  // Replace existing chats query with infinite query
  const {
    data: chatsData,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["chats", debouncedSearch],
    queryFn: async ({ pageParam = 1 }) => {
      const response = await chatService.getChats(
        undefined,
        false,
        20,
        (pageParam - 1) * 20
      );
      // Transform to match expected format
      return {
        results: response || [],
        next: response && response.length === 20 ? pageParam + 1 : null,
      };
    },
    getNextPageParam: (lastPage) => lastPage.next,
    initialPageParam: 1,
  });

  // Flatten chat pages into a single array
  const chats = useMemo(() => {
    return chatsData?.pages.flatMap((page) => page.results) ?? [];
  }, [chatsData]);

  // Handle scroll to load more
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
      if (scrollHeight - scrollTop <= clientHeight * 1.5) {
        if (hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage]
  );

  // Fetch projects query
  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const response = await chatService.getProjects();
      return response || [];
    },
  });

  // Fetch design projects query
  const { data: designProjects } = useQuery({
    queryKey: ["designProjects"],
    queryFn: fetchDesignProjects,
  });

  console.log("design projects from sidebar", designProjects);

  // Delete chat mutation
  const deleteChatMutation = useMutation({
    mutationFn: async (chatId: string) => {
      await chatService.deleteChat(chatId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      navigate("/chat");
      toast({
        title: "Chat deleted",
        description: "The chat has been successfully deleted.",
      });
    },
  });

  // Update chat title mutation
  const updateChatMutation = useMutation({
    mutationFn: async ({
      chatId,
      title,
    }: {
      chatId: string;
      title: string;
    }) => {
      await chatService.updateChat(chatId, { title });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      setEditingChatId(null);
      toast({
        title: "Chat updated",
        description: "The chat title has been successfully updated.",
      });
    },
  });

  const handleEditClick = (chat: Chat) => {
    setEditingChatId(chat.id);
    setEditTitle(chat.title);
  };

  const handleEditSubmit = (chatId: number) => {
    if (editTitle.trim()) {
      updateChatMutation.mutate({
        chatId: chatId.toString(),
        title: editTitle.trim(),
      });
    }
  };

  const handleEditCancel = () => {
    setEditingChatId(null);
    setEditTitle("");
  };

  // Function to categorize chats by date
  const categorizedChats = useMemo(() => {
    if (!chats) return {};

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);

    return chats.reduce((acc: { [key: string]: Chat[] }, chat) => {
      const chatDate = new Date(chat.created_at);
      chatDate.setHours(0, 0, 0, 0);

      if (chatDate.getTime() === today.getTime()) {
        acc.today = [...(acc.today || []), chat];
      } else if (chatDate.getTime() === yesterday.getTime()) {
        acc.yesterday = [...(acc.yesterday || []), chat];
      } else if (chatDate > lastWeek) {
        acc.lastWeek = [...(acc.lastWeek || []), chat];
      } else {
        acc.older = [...(acc.older || []), chat];
      }
      return acc;
    }, {});
  }, [chats]);

  // Chat list section component
  const ChatListSection = ({
    title,
    chats,
  }: {
    title: string;
    chats: Chat[];
  }) => (
    <div className="mb-4">
      <div className="flex items-center gap-2 px-2 mb-2">
        {title === "Today" && (
          <Calendar className="h-4 w-4 text-muted-foreground" />
        )}
        {title === "Yesterday" && (
          <Clock className="h-4 w-4 text-muted-foreground" />
        )}
        <span className="text-sm font-medium text-muted-foreground">
          {title}
        </span>
      </div>
      {chats.map((chat) => (
        <div
          key={chat.id}
          className={`group relative flex items-center px-2 py-1.5 rounded-md transition-colors ${
            chatId === chat.id.toString()
              ? "bg-accent text-accent-foreground"
              : "hover:bg-accent/50 text-foreground"
          }`}
        >
          {editingChatId === chat.id ? (
            <div className="flex w-full items-center gap-1">
              <Input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleEditSubmit(chat.id);
                  } else if (e.key === "Escape") {
                    handleEditCancel();
                  }
                }}
                className="h-7 text-sm"
                autoFocus
              />
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0 hover:bg-accent"
                onClick={() => handleEditSubmit(chat.id)}
              >
                <Check className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0 hover:bg-destructive/90 hover:text-destructive-foreground"
                onClick={handleEditCancel}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <>
              <Link
                to={`/chat/${chat.id}`}
                className="block w-[calc(100%-64px)] truncate"
              >
                {chat.title}
              </Link>
              <div className="absolute right-2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0 hover:bg-accent"
                  onClick={(e) => {
                    e.preventDefault();
                    handleEditClick(chat);
                  }}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0 hover:bg-destructive/90 hover:text-destructive-foreground"
                  onClick={(e) => {
                    e.preventDefault();
                    setChatToDelete(chat.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );

  // extract the chatId from the url (not from the useParams hook)

  // get the current url
  const currentUrl = window.location.href;

  // extract the chatId from the url using regex - memoize this
  const chatId = useMemo(() => {
    const chatId = currentUrl.match(/\/chat\/(\d+)/)?.[1];
    return chatId;
  }, [currentUrl]);

  return (
    <div className="w-72 h-screen border-r bg-background flex flex-col">
      {/* Fixed Header Section */}
      <div className="p-4 space-y-4 border-b">
        <Button className="w-full" onClick={() => navigate("/chat/new")}>
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </Button>

        {/* Add search input */}
        <Input
          placeholder="Search chats..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full"
        />
      </div>

      {/* Scrollable Content */}
      <ScrollArea className="flex-1" onScroll={handleScroll}>
        <div className="p-4 space-y-6">
          {/* Projects Section */}
          <div className="space-y-1">
            <div className="flex items-center px-2 mb-2">
              <FolderIcon className="h-4 w-4 text-muted-foreground mr-2" />
              <span className="text-sm font-medium text-muted-foreground">
                Projects
              </span>
            </div>
            {projects?.slice(0, 3).map((project) => (
              <Button
                key={project.id}
                variant="ghost"
                className="w-full justify-start pl-8 text-sm h-8"
                asChild
              >
                <Link to={`/projects/${project.id}`}>
                  <span className="truncate">
                    {project.name.slice(0, 15) +
                      (project.name.length > 15 ? "..." : "")}
                  </span>
                </Link>
              </Button>
            ))}
            <Button
              variant="ghost"
              className="w-full justify-between text-sm h-8 text-muted-foreground hover:text-foreground"
              asChild
            >
              <Link to="/projects">
                View all projects
                <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>

          {/* Design Projects Section */}
          <div className="space-y-1">
            <div className="flex items-center px-2 mb-2">
              <Layout className="h-4 w-4 text-muted-foreground mr-2" />
              <span className="text-sm font-medium text-muted-foreground">
                Design Projects
              </span>
            </div>
            {designProjects?.slice(0, 3).map((project) => (
              <Button
                key={project.id}
                variant="ghost"
                className="w-full justify-start pl-8 text-sm h-8"
                asChild
              >
                <Link to={`/design-projects/${project.id}`}>
                  <span className="truncate">
                    {project.title.slice(0, 15) +
                      (project.title.length > 15 ? "..." : "")}
                  </span>
                </Link>
              </Button>
            ))}
            <Button
              variant="ghost"
              className="w-full justify-between text-sm h-8 text-muted-foreground hover:text-foreground"
              asChild
            >
              <Link to="/design-projects">
                View all designs
                <ChevronRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>

          {/* Chat List */}
          <ChatListSection title="Today" chats={categorizedChats.today || []} />
          <ChatListSection
            title="Yesterday"
            chats={categorizedChats.yesterday || []}
          />
          <ChatListSection
            title="Last Week"
            chats={categorizedChats.lastWeek || []}
          />
          <ChatListSection title="Older" chats={categorizedChats.older || []} />
        </div>
      </ScrollArea>
    </div>
  );
}
