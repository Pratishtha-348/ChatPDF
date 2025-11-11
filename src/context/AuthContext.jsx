import React, { createContext, useState, useContext, useEffect } from 'react';
import { login as loginAPI, getMe } from '../services/auth';
import { setAuthToken } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        setAuthToken(token);
        try {
          const userData = await getMe(token);
          setUser(userData);
        } catch (error) {
          console.error('Auth init failed:', error);
          logout();
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email, password) => {
    const data = await loginAPI(email, password);
    const { access_token, role } = data;
    
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setAuthToken(access_token);
    
    const userData = await getMe(access_token);
    setUser(userData);
    
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setAuthToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};