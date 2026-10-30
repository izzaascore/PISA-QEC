import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Home from './pages/Home';
import Database from './pages/Database';
import Groups from './pages/Groups';
import Results from './pages/Results';
import Settings from './pages/Settings';
import Login from './pages/Login';
import BlockDetails from './pages/BlockDetails';
import { ThemeProvider } from './context/ThemeContext';

const ProtectedRoute = ({ children, user, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 text-gray-600 dark:bg-gray-900 dark:text-gray-300">
        Yuklanmoqda...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  const [user, setUser] = useState(null);
  const [isUserLoading, setIsUserLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('teacher_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Saqlangan foydalanuvchi ma’lumotlarini o‘qib bo‘lmadi:', error);
        localStorage.removeItem('teacher_user');
      }
    }
    setIsUserLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('teacher_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('teacher_user');
  };

  return (
    <Routes>
      <Route path="/login" element={<Login onLogin={handleLogin} />} />
      
      <Route path="/" element={<ProtectedRoute user={user} isLoading={isUserLoading}><MainLayout onLogout={handleLogout} /></ProtectedRoute>}>
        <Route index element={<Home />} />
        <Route path="database" element={<Database />} />
        <Route path="database/blocks/:id" element={<BlockDetails />} />
        <Route path="groups" element={<Groups />} />
        <Route path="results" element={<Results />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;
