import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  getCurrentUser, 
  setCurrentUser as setStorageUser, 
  logoutUser as logoutStorageUser 
} from '../services/storageService';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getCurrentUser());

  const login = (userData) => {
    setStorageUser(userData);
    setUser(userData);
  };

  const logout = () => {
    logoutStorageUser();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser utilizado dentro de um AuthProvider');
  }
  return context;
}

