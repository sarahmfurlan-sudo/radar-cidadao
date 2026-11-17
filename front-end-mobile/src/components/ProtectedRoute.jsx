import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    // Redireciona para o login guardando a rota original de destino
    return (
      <Navigate 
        to={`/login?redirect=${encodeURIComponent(location.pathname)}`} 
        state={{ message: "Identifique-se ou crie seu cadastro local para registrar um relato na sua comunidade." }}
        replace 
      />
    );
  }

  return children;
}
