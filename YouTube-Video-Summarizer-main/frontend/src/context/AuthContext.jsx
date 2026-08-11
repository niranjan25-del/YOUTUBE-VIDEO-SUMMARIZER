import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .me()
      .then((data) => setUser(data.user))
      .finally(() => setLoading(false));
  }, []);

  const login = async (username, password) => {
    const data = await api.login(username, password);
    setUser(data.user);
  };

  const register = async (username, password) => {
    const data = await api.register(username, password);
    setUser(data.user);
  };

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      // Always clear local state, even if the server call fails (e.g. the
      // session already expired) -- the user still expects to be logged out.
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
