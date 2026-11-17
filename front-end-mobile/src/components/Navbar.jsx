import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Radio, 
  MapPin, 
  PlusCircle, 
  ListFilter, 
  Bell, 
  Info, 
  User, 
  Sun, 
  Moon, 
  Menu, 
  X, 
  PhoneCall, 
  Activity, 
  LogIn
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ darkMode, setDarkMode, activeSensorCount = 4 }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user: currentUser } = useAuth();

  const navLinks = [
    { to: '/', label: 'Mapa de Risco', icon: MapPin },
    { to: '/relato/novo', label: 'Registrar Relato', icon: PlusCircle, highlight: true },
    { to: '/relatos', label: 'Histórico', icon: ListFilter },
    { to: '/alertas', label: 'Alertas', icon: Bell },
    { to: '/sobre', label: 'Sobre & ODS', icon: Info },
  ];

  const isActive = (path) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo e Nome */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-blue-700 text-white shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
                <Radio className="w-5 h-5 animate-pulse" />
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
              </div>
              <div>
                <span className="font-extrabold text-base sm:text-lg tracking-tight text-slate-900 dark:text-white">
                  Radar <span className="text-sky-600 dark:text-sky-400">Cidadão</span>
                </span>
                <span className="hidden sm:block text-[10px] text-slate-400 dark:text-slate-500 uppercase font-semibold tracking-wider">
                  São Paulo • Prevenção & Alagamento
                </span>
              </div>
            </Link>

            {/* Badge de Telemetria Ativa */}
            <div className="hidden lg:flex items-center gap-2 ml-4 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-700 dark:text-emerald-300">
              <Activity className="w-3.5 h-3.5 animate-pulse" />
              <span>{activeSensorCount} Sensores IoT Ativos</span>
            </div>
          </div>

          {/* Navegação Desktop */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                    link.highlight
                      ? 'bg-sky-600 hover:bg-sky-700 text-white shadow-sm shadow-sky-600/30'
                      : active
                      ? 'bg-slate-100 dark:bg-slate-800 text-sky-600 dark:text-sky-400'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Ações: Tema, Telefone de Emergência e Usuário */}
          <div className="flex items-center gap-2">
            {/* Atalho 199 Emergência */}
            <a
              href="tel:199"
              title="Ligar para Defesa Civil (199)"
              className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs font-bold hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              <span>199</span>
            </a>

            {/* Alternador de Tema */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label={darkMode ? "Ativar Modo Claro" : "Ativar Modo Escuro"}
            >
              {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
            </button>

            {/* Perfil do Cidadão / Login */}
            <Link
              to="/login"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
                currentUser 
                  ? 'border-emerald-300 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300'
                  : 'border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200'
              }`}
              title={currentUser ? `Logado como ${currentUser.nome}` : "Entrar ou Criar Cadastro Local"}
            >
              <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                currentUser ? 'bg-emerald-600 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
              }`}>
                {currentUser ? currentUser.nome.charAt(0) : <LogIn className="w-3 h-3" />}
              </div>
              <span className="hidden sm:inline max-w-[110px] truncate">
                {currentUser ? currentUser.nome.split(' ')[0] : 'Entrar'}
              </span>
            </Link>

            {/* Botão Mobile Hamburger */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Abrir menu de navegação"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

        </div>
      </div>

      {/* Menu Dropdown Mobile */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3 space-y-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.to);
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-semibold ${
                  link.highlight
                    ? 'bg-sky-600 text-white'
                    : active
                    ? 'bg-slate-100 dark:bg-slate-800 text-sky-600 dark:text-sky-400'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </Link>
            );
          })}
          
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-400">Emergência Defesa Civil</span>
            <a
              href="tel:199"
              className="flex items-center gap-1 text-xs font-bold text-red-600 dark:text-red-400"
            >
              <PhoneCall className="w-3.5 h-3.5" />
              Ligar 199
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
