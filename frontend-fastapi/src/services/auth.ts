import axios from "axios";
import { authUrls } from "@/constants/urls";
import {
  User,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  PasswordResetRequest,
  PasswordResetConfirm,
  PasswordChange,
  EmailVerification,
  GoogleAuthRequest,
} from "@/types/auth";

// Token management
const TOKEN_KEY = "auth_token";
const USER_KEY = "auth_user";
const USER_TIMESTAMP_KEY = "auth_user_timestamp";

// Grace period for token verification (5 minutes)
const TOKEN_VERIFICATION_GRACE_PERIOD = 5 * 60 * 1000;

export const tokenStorage = {
  get: (): string | null => {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },

  set: (token: string): void => {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      // Handle storage error silently
    }
  },

  remove: (): void => {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch {
      // Handle storage error silently
    }
  },
};

export const userStorage = {
  get: (): User | null => {
    try {
      const userData = localStorage.getItem(USER_KEY);
      return userData ? JSON.parse(userData) : null;
    } catch {
      return null;
    }
  },

  set: (user: User): void => {
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      localStorage.setItem(USER_TIMESTAMP_KEY, Date.now().toString());
    } catch {
      // Handle storage error silently
    }
  },

  remove: (): void => {
    try {
      localStorage.removeItem(USER_KEY);
      localStorage.removeItem(USER_TIMESTAMP_KEY);
    } catch {
      // Handle storage error silently
    }
  },

  getTimestamp: (): number | null => {
    try {
      const timestamp = localStorage.getItem(USER_TIMESTAMP_KEY);
      return timestamp ? parseInt(timestamp, 10) : null;
    } catch {
      return null;
    }
  },
};

// API client with authentication
const createAuthenticatedAxios = () => {
  const instance = axios.create({
    timeout: 30000,
  });

  // Request interceptor to add token
  instance.interceptors.request.use(
    (config) => {
      const token = tokenStorage.get();
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

const api = createAuthenticatedAxios();

// Authentication API methods
export const authService = {
  // Login
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await axios.post<LoginResponse>(
      authUrls.login,
      credentials
    );
    const { user, access_token } = response.data;

    // Store token and user data
    tokenStorage.set(access_token);
    userStorage.set(user);

    return response.data;
  },

  // Register
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await axios.post<RegisterResponse>(
      authUrls.register,
      userData
    );
    return response.data;
  },

  // Logout
  async logout(): Promise<void> {
    try {
      const token = tokenStorage.get();
      if (token) {
        await api.post(authUrls.logout);
      }
    } catch (error) {
      // Even if logout fails on server, clear local storage
      console.warn("Logout request failed:", error);
    } finally {
      tokenStorage.remove();
      userStorage.remove();
    }
  },

  // Get current user profile
  async getProfile(): Promise<User> {
    const response = await api.get<User>(authUrls.profile);
    const user = response.data;
    userStorage.set(user);
    return user;
  },

  // Update user profile
  async updateProfile(userData: Partial<User>): Promise<User> {
    const response = await api.patch<User>(authUrls.profile, userData);
    const user = response.data;
    userStorage.set(user);
    return user;
  },

  // Change password
  async changePassword(passwordData: PasswordChange): Promise<void> {
    await api.post(authUrls.changePassword, passwordData);
  },

  // Request password reset
  async forgotPassword(email: string): Promise<void> {
    await axios.post(authUrls.forgotPassword, { email });
  },

  // Confirm password reset
  async resetPassword(resetData: PasswordResetConfirm): Promise<void> {
    await axios.post(authUrls.resetPassword, resetData);
  },

  // Verify email
  async verifyEmail(token: string): Promise<void> {
    await axios.post(authUrls.verifyEmail, { token });
  },

  // Resend verification email
  async resendVerification(): Promise<void> {
    await api.post(authUrls.resendVerification);
  },

  // Google OAuth
  async googleAuth(accessToken: string): Promise<LoginResponse> {
    const response = await axios.post<LoginResponse>(authUrls.googleAuth, {
      access_token: accessToken,
    });

    const { user, access_token } = response.data;
    tokenStorage.set(access_token);
    userStorage.set(user);

    return response.data;
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = tokenStorage.get();
    const user = userStorage.get();
    return !!(token && user);
  },

  // Get current user from storage
  getCurrentUser(): User | null {
    return userStorage.get();
  },

  // Get current token
  getCurrentToken(): string | null {
    return tokenStorage.get();
  },

  // Initialize auth state (call on app startup)
  async initializeAuth(): Promise<{
    user: User | null;
    isAuthenticated: boolean;
  }> {
    const token = tokenStorage.get();
    const storedUser = userStorage.get();
    const userTimestamp = userStorage.getTimestamp();

    if (!token || !storedUser) {
      return { user: null, isAuthenticated: false };
    }

    // If user data is recent enough, skip API verification
    if (
      userTimestamp &&
      Date.now() - userTimestamp < TOKEN_VERIFICATION_GRACE_PERIOD
    ) {
      return { user: storedUser, isAuthenticated: true };
    }

    try {
      // Verify token is still valid and get fresh user data
      const user = await this.getProfile();
      return { user, isAuthenticated: true };
    } catch (error: any) {
      // Only clear storage on actual authentication errors (401/403)
      // Keep the stored auth for network errors or server issues
      if (error.response?.status === 401 || error.response?.status === 403) {
        // Token invalid, clear storage
        tokenStorage.remove();
        userStorage.remove();
        return { user: null, isAuthenticated: false };
      }

      // For other errors (network, 500, etc), keep the stored auth
      // but indicate we couldn't verify it
      console.warn("Could not verify token, but keeping stored auth:", error);
      return { user: storedUser, isAuthenticated: true };
    }
  },
};

// Export the authenticated axios instance for other services
export const authenticatedApi = api;

export default authService;
