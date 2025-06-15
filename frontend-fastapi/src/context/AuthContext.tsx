import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import {
  AuthContextType,
  AuthState,
  User,
  RegisterRequest,
  PasswordChange,
  PasswordResetConfirm,
} from "@/types/auth";
import authService from "@/services/auth";
import { toast } from "sonner";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    token: null,
  });

  // Initialize auth state on app start
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const { user, isAuthenticated } = await authService.initializeAuth();
        const token = authService.getCurrentToken();

        setAuthState({
          user,
          isAuthenticated,
          isLoading: false,
          token,
        });
      } catch (error) {
        console.error("Failed to initialize auth:", error);
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          token: null,
        });
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    try {
      setAuthState((prev) => ({ ...prev, isLoading: true }));

      const response = await authService.login({ email, password });

      setAuthState({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
        token: response.access_token,
      });

      toast.success("Login successful!");
    } catch (error: any) {
      setAuthState((prev) => ({ ...prev, isLoading: false }));

      // Handle different error formats from FastAPI
      let message = "Login failed";

      if (error.response?.data) {
        const errorData = error.response.data;

        if (typeof errorData.detail === "string") {
          message = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          // Handle validation errors array
          message = errorData.detail.map((err: any) => err.msg).join(", ");
        } else if (Array.isArray(errorData)) {
          // Handle validation errors directly as array
          message = errorData.map((err: any) => err.msg).join(", ");
        } else if (errorData.message) {
          message = errorData.message;
        }
      }

      toast.error(message);
      throw error;
    }
  };

  const register = async (data: RegisterRequest): Promise<void> => {
    try {
      setAuthState((prev) => ({ ...prev, isLoading: true }));

      await authService.register(data);

      setAuthState((prev) => ({ ...prev, isLoading: false }));
      toast.success(
        "Registration successful! Please check your email to verify your account."
      );
    } catch (error: any) {
      setAuthState((prev) => ({ ...prev, isLoading: false }));

      // Handle different error formats from FastAPI
      let message = "Registration failed";

      if (error.response?.data) {
        const errorData = error.response.data;

        if (typeof errorData.detail === "string") {
          message = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          // Handle validation errors array
          message = errorData.detail.map((err: any) => err.msg).join(", ");
        } else if (Array.isArray(errorData)) {
          // Handle validation errors directly as array
          message = errorData.map((err: any) => err.msg).join(", ");
        } else if (errorData.message) {
          message = errorData.message;
        }
      }

      toast.error(message);
      throw error;
    }
  };

  const logout = (): void => {
    authService.logout();
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      token: null,
    });
    toast.success("Logged out successfully");
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const { user, isAuthenticated } = await authService.initializeAuth();
      const token = authService.getCurrentToken();

      setAuthState({
        user,
        isAuthenticated,
        isLoading: false,
        token,
      });
    } catch (error) {
      logout();
      throw error;
    }
  };

  const updateProfile = async (data: Partial<User>): Promise<void> => {
    try {
      const updatedUser = await authService.updateProfile(data);

      setAuthState((prev) => ({
        ...prev,
        user: updatedUser,
      }));

      toast.success("Profile updated successfully");
    } catch (error: any) {
      const message =
        error.response?.data?.detail || "Failed to update profile";
      toast.error(message);
      throw error;
    }
  };

  const changePassword = async (data: PasswordChange): Promise<void> => {
    try {
      await authService.changePassword(data);
      toast.success("Password changed successfully");
    } catch (error: any) {
      const message =
        error.response?.data?.detail || "Failed to change password";
      toast.error(message);
      throw error;
    }
  };

  const forgotPassword = async (email: string): Promise<void> => {
    try {
      await authService.forgotPassword(email);
      toast.success("Password reset email sent! Please check your inbox.");
    } catch (error: any) {
      const message =
        error.response?.data?.detail || "Failed to send reset email";
      toast.error(message);
      throw error;
    }
  };

  const resetPassword = async (data: PasswordResetConfirm): Promise<void> => {
    try {
      await authService.resetPassword(data);
      toast.success("Password reset successful! You can now log in.");
    } catch (error: any) {
      const message =
        error.response?.data?.detail || "Failed to reset password";
      toast.error(message);
      throw error;
    }
  };

  const verifyEmail = async (token: string): Promise<void> => {
    try {
      await authService.verifyEmail(token);
      toast.success("Email verified successfully!");

      // Refresh user data to update email_verified status
      await refreshToken();
    } catch (error: any) {
      const message = error.response?.data?.detail || "Failed to verify email";
      toast.error(message);
      throw error;
    }
  };

  const resendVerification = async (): Promise<void> => {
    try {
      await authService.resendVerification();
      toast.success("Verification email sent! Please check your inbox.");
    } catch (error: any) {
      const message =
        error.response?.data?.detail || "Failed to send verification email";
      toast.error(message);
      throw error;
    }
  };

  const contextValue: AuthContextType = {
    ...authState,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
    changePassword,
    forgotPassword,
    resetPassword,
    verifyEmail,
    resendVerification,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export default AuthContext;
