import React from "react";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import Chat from "@/components/Chat";
import { Sidebar } from "@/components/Sidebar";
import Projects from "@/components/Projects";
import ProjectDetail from "@/components/ProjectDetail";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/ThemeProvider";
import DesignProjects from "@/components/prototypes/DesignProjects";
import DesignProjectDetail from "@/components/prototypes/DesignProjectDetail";
import PrototypeDetail from "@/components/prototypes/PrototypeDetail";
import PrototypesByGroup from "@/components/prototypes/PrototypesByGroup";

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected routes */}
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <div className="flex h-screen bg-background">
                      <Sidebar />
                      <div className="flex-1 overflow-auto">
                        <Routes>
                          <Route
                            path="/"
                            element={<Navigate to="/projects" replace />}
                          />
                          <Route path="/projects" element={<Projects />} />
                          <Route
                            path="/projects/:projectId"
                            element={<ProjectDetail />}
                          />
                          <Route
                            path="/projects/:projectId/chat/:chatId"
                            element={<Chat />}
                          />
                          <Route path="/chat/:chatId" element={<Chat />} />
                          {/* Prototypes Routes */}
                          <Route
                            path="/design-projects"
                            element={<DesignProjects />}
                          />
                          <Route
                            path="/design-projects/:projectId"
                            element={<DesignProjectDetail />}
                          />
                          <Route
                            path="/prototypes/:prototypeId"
                            element={<PrototypeDetail />}
                          />
                          <Route
                            path="/groups/:groupId/prototypes"
                            element={<PrototypesByGroup />}
                          />
                        </Routes>
                      </div>
                    </div>
                  </ProtectedRoute>
                }
              />
            </Routes>
            <Toaster />
            <SonnerToaster />
          </Router>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default App;
