"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { UserProfile, loginUser, fetchCurrentUser } from "@/lib/api";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Hydrate session from localStorage
    const storedToken = localStorage.getItem("gaa_token");
    if (storedToken) {
      setToken(storedToken);
      fetchCurrentUser(storedToken)
        .then((userData) => setUser(userData))
        .catch(() => {
          localStorage.removeItem("gaa_token");
          setToken(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, pass: string) => {
    const data = await loginUser(email, pass);
    if (data.access_token) {
      localStorage.setItem("gaa_token", data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    }
  };

  const logout = () => {
    localStorage.removeItem("gaa_token");
    setToken(null);
    setUser(null);
    window.location.href = "/login";
  };

  const refreshUser = async () => {
    if (token) {
      const userData = await fetchCurrentUser(token);
      setUser(userData);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, loading: isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
