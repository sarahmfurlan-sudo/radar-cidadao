import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { initStorage, getStoredTheme, setStoredTheme } from './services/storageService';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import RiskMapPage from './pages/RiskMapPage';
import NewReportPage from './pages/NewReportPage';
import ReportsHistoryPage from './pages/ReportsHistoryPage';
import AlertsPage from './pages/AlertsPage';
import LoginPage from './pages/LoginPage';
import AboutPage from './pages/AboutPage';

import { useRadarIoT } from "./hooks/useRadarIoT";

export default function App() {
  const { sensor, modo, cenarioFallback, setCenarioFallback } = useRadarIoT();
  const iotState = { sensor, modo, cenarioFallback, setCenarioFallback };
  const [darkMode, setDarkMode] = useState(() => {
    return getStoredTheme() === 'dark';
  });

  useEffect(() => {
    initStorage();
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      setStoredTheme('dark');
    } else {
      document.documentElement.classList.remove('dark');
      setStoredTheme('light');
    }
  }, [darkMode]);

  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
          <Navbar darkMode={darkMode} setDarkMode={setDarkMode} activeSensorCount={sensor ? 5 : 4} />
          
          <div className="flex-1">
            <Routes>
              <Route path="/" element={<RiskMapPage iotState={iotState} />} />
              <Route path="/mapa" element={<RiskMapPage iotState={iotState} />} />
              
              {/* Rota Protegida: Apenas cidadãos autenticados localmente podem registrar novos relatos */}
              <Route 
                path="/relato/novo" 
                element={
                  <ProtectedRoute>
                    <NewReportPage />
                  </ProtectedRoute>
                } 
              />
              
              <Route path="/relatos" element={<ReportsHistoryPage />} />
              <Route path="/alertas" element={<AlertsPage iotState={iotState} />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/sobre" element={<AboutPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>

          <Footer />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
