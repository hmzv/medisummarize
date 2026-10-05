import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  ApiError,
  clearToken,
  fetchCurrentUser,
  loginAccount,
  readStoredToken,
  registerAccount,
  storeToken,
  type UserPublic,
} from "../api/client";

type AuthContextValue = {
  user: UserPublic | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = readStoredToken();
    if (!token) {
      setReady(true);
      return;
    }
    void fetchCurrentUser(token)
      .then((current) => {
        setUser(current);
      })
      .catch((error: unknown) => {
        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
          clearToken();
        }
        setUser(null);
      })
      .finally(() => {
        setReady(true);
      });
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await loginAccount(email, password);
    storeToken(result.access_token);
    setUser(result.user);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const result = await registerAccount(email, password);
    storeToken(result.access_token);
    setUser(result.user);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, ready, login, register, logout }),
    [user, ready, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
