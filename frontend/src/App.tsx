import React from "react";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Chat from "@/components/Chat";
import { Sidebar } from "@/components/Sidebar";
import Projects from "@/components/Projects";
import ProjectDetail from "@/components/ProjectDetail";
import { Toaster } from "@/components/ui/sonner";

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
          <Sidebar />
          <div className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/projects" replace />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/projects/:projectId" element={<ProjectDetail />} />
              <Route
                path="/projects/:projectId/chat/:chatId"
                element={<Chat />}
              />
              <Route path="/chat/:chatId" element={<Chat />} />
            </Routes>
          </div>
        </div>
        <Toaster />
      </Router>
    </QueryClientProvider>
  );
};

export default App;
