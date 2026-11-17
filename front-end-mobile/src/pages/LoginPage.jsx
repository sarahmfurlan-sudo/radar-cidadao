import React, { useState } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { 
  UserCheck, 
  Lock, 
  ShieldCheck, 
  CheckCircle2, 
  LogOut, 
  User, 
  MapPin, 
  Mail, 
  KeyRound, 
  AlertCircle, 
  Sparkles, 
  PlusCircle, 
  Search, 
  Eye, 
  EyeOff, 
  Check, 
  X 
} from 'lucide-react';
import { 
  authenticateUser, 
  registerUser, 
  loginDemoUser,
  DEFAULT_USERS
} from '../services/storageService';
import { fetchAddressByCep, formatCep } from '../services/cepService';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const { user: currentUser, login, logout } = useAuth();

  const redirectUrl = searchParams.get('redirect') || '/';
  const incomingMessage = location.state?.message;

  const [activeTab, setActiveTab] = useState('login'); // 'login' | 'register'

  // Estados do login
  const [loginEmail, setLoginEmail] = useState('');
  const [loginSenha, setLoginSenha] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Estados do cadastro
  const [registerNome, setRegisterNome] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerCep, setRegisterCep] = useState('');
  const [registerBairro, setRegisterBairro] = useState('');
  const [registerCidade, setRegisterCidade] = useState('São Paulo');
  const [loadingCep, setLoadingCep] = useState(false);
  const [cepSuccessMsg, setCepSuccessMsg] = useState('');

  // Senhas e validação
  const [registerSenha, setRegisterSenha] = useState('');
  const [registerConfirmarSenha, setRegisterConfirmarSenha] = useState('');
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);

  // Consentimento LGPD: inicia desmarcado para consentimento afirmativo
  const [registerLgpd, setRegisterLgpd] = useState(false);

  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Cálculo de força da senha
  const getPasswordStrength = (pass) => {
    if (!pass) return { score: 0, label: '', color: '' };
    let score = 0;
    if (pass.length >= 6) score++;
    if (/[A-Z]/.test(pass)) score++;
    if (/[0-9]/.test(pass)) score++;
    if (/[^A-Za-z0-9]/.test(pass)) score++;

    if (score <= 1) return { score: 1, label: 'Fraca (mín. 6 caracteres)', color: 'bg-red-500 text-red-600' };
    if (score === 2) return { score: 2, label: 'Média (adicione números/letras maiúsculas)', color: 'bg-amber-500 text-amber-600' };
    return { score: 3, label: 'Forte', color: 'bg-emerald-500 text-emerald-600' };
  };

  const passwordStrength = getPasswordStrength(registerSenha);
  const passwordsMatch = registerSenha && registerConfirmarSenha && registerSenha === registerConfirmarSenha;

  // Busca do CEP via API do ViaCEP
  const handleCepChange = async (e) => {
    const formatted = formatCep(e.target.value);
    setRegisterCep(formatted);
    setCepSuccessMsg('');

    const clean = formatted.replace(/\D/g, '');
    if (clean.length === 8) {
      setLoadingCep(true);
      setErrorMsg('');
      try {
        const address = await fetchAddressByCep(clean);
        setRegisterBairro(address.bairro || '');
        setRegisterCidade(`${address.cidade} - ${address.uf}`);
        setCepSuccessMsg(`Localizado: ${address.bairro ? address.bairro + ', ' : ''}${address.cidade}/${address.uf}`);
      } catch (err) {
        setErrorMsg(err.message || 'Não foi possível localizar o CEP.');
      } finally {
        setLoadingCep(false);
      }
    }
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const user = authenticateUser(loginEmail, loginSenha);
      login(user);
      setSuccessMsg(`Bem-vindo(a) de volta, ${user.nome.split(' ')[0]}!`);
      setTimeout(() => {
        navigate(redirectUrl);
      }, 700);
    } catch (err) {
      setErrorMsg(err.message || 'Falha ao autenticar.');
    }
  };

  const handleRegisterSubmit = (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (registerSenha.length < 6) {
      setErrorMsg('A senha deve possuir no mínimo 6 caracteres.');
      return;
    }

    if (registerSenha !== registerConfirmarSenha) {
      setErrorMsg('As senhas digitadas não coincidem. Por favor, confirme a mesma senha nos dois campos.');
      return;
    }

    if (!registerBairro.trim()) {
      setErrorMsg('Por favor, informe o seu bairro de residência.');
      return;
    }

    if (!registerLgpd) {
      setErrorMsg('É obrigatório concordar com os termos de privacidade cívica e proteção de dados (LGPD) para criar a sua conta.');
      return;
    }

    try {
      const user = registerUser({
        nome: registerNome,
        email: registerEmail,
        senha: registerSenha,
        bairro: registerBairro.trim()
      });
      login(user);
      setSuccessMsg(`Cadastro realizado com sucesso! Bem-vindo(a), ${user.nome.split(' ')[0]}.`);
      setTimeout(() => {
        navigate(redirectUrl);
      }, 900);
    } catch (err) {
      setErrorMsg(err.message || 'Falha ao cadastrar cidadão.');
    }
  };

  const handleDemoLogin = (demo) => {
    setErrorMsg('');
    const userToLogin = demo || DEFAULT_USERS[0];
    login(userToLogin);
    setSuccessMsg(`Logado com sucesso como ${userToLogin.nome.split(' ')[0]}!`);
    setTimeout(() => {
      navigate(redirectUrl);
    }, 600);
  };

  const handleLogout = () => {
    logout();
    setSuccessMsg('Sessão encerrada com sucesso.');
    setTimeout(() => setSuccessMsg(''), 2500);
  };

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 py-10">
      
      {/* Mensagem de Redirecionamento da Rota Protegida */}
      {incomingMessage && !currentUser && (
        <div className="mb-6 p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 flex items-start gap-3 text-amber-800 dark:text-amber-300 text-xs animate-in fade-in">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
          <div>
            <strong className="block font-bold">Identificação Necessária</strong>
            <span>{incomingMessage}</span>
          </div>
        </div>
      )}

      {/* Alertas de Sucesso e Erro */}
      {errorMsg && (
        <div className="mb-4 p-3.5 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 flex items-center gap-2.5 text-red-700 dark:text-red-300 text-xs font-semibold">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="mb-4 p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex items-center gap-2.5 text-emerald-700 dark:text-emerald-300 text-xs font-semibold">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* CASO JÁ ESTEJA LOGADO: Painel de Perfil */}
      {currentUser ? (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-sky-100 dark:bg-sky-950 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold text-xl">
              {currentUser.nome.charAt(0)}
            </div>
            <div>
              <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider block">
                ● Cidadão Conectado
              </span>
              <h2 className="text-lg font-extrabold text-slate-900 dark:text-white">
                {currentUser.nome}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {currentUser.email} • {currentUser.bairro}, São Paulo
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-2">
            <div className="flex justify-between text-slate-600 dark:text-slate-300">
              <span className="font-semibold">Bairro monitorado:</span>
              <span>{currentUser.bairro} (SP)</span>
            </div>
            <div className="flex justify-between text-slate-600 dark:text-slate-300">
              <span className="font-semibold">Consentimento LGPD:</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Ativo e Anonimizado
              </span>
            </div>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center gap-3">
            <button
              onClick={() => navigate('/relato/novo')}
              className="w-full sm:flex-1 py-2.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs shadow-md shadow-sky-600/30 transition-all flex items-center justify-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Registrar Novo Relato</span>
            </button>

            <button
              onClick={handleLogout}
              className="w-full sm:w-auto py-2.5 px-4 rounded-xl border border-red-300 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 text-xs font-bold transition-colors flex items-center justify-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sair da Conta</span>
            </button>
          </div>
        </div>
      ) : (

        /* CASO DESLOGADO: Abas de Login ou Cadastro */
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 sm:p-8 space-y-6">
          
          {/* Header */}
          <div className="text-center space-y-1.5">
            <div className="w-12 h-12 rounded-2xl bg-sky-100 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 flex items-center justify-center mx-auto shadow-inner">
              <UserCheck className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-extrabold text-slate-900 dark:text-white">
              Identificação do Cidadão
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Requisitos 3 e 4 do Edital • Login e Cadastro persistidos no navegador.
            </p>
          </div>

          {/* Seletor de Abas: Login vs Cadastro */}
          <div className="grid grid-cols-2 gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs font-bold">
            <button
              type="button"
              onClick={() => { setActiveTab('login'); setErrorMsg(''); }}
              className={`py-2 rounded-lg transition-all ${
                activeTab === 'login'
                  ? 'bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Já tenho conta (Entrar)
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('register'); setErrorMsg(''); }}
              className={`py-2 rounded-lg transition-all ${
                activeTab === 'register'
                  ? 'bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Novo Cadastro
            </button>
          </div>

          {/* ABA 1: ENTRAR (LOGIN LOCAL) */}
          {activeTab === 'login' && (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
                  E-mail do Cidadão *
                </label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    placeholder="mario.oliveira@cidadao.sp.gov.br"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                  />
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
                  Senha Local *
                </label>
                <div className="relative">
                  <input
                    type={showLoginPassword ? "text" : "password"}
                    required
                    placeholder="Sua senha local (ex: 123)"
                    value={loginSenha}
                    onChange={(e) => setLoginSenha(e.target.value)}
                    className="w-full pl-9 pr-10 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                  />
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    aria-label="Alternar visualização da senha"
                  >
                    {showLoginPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs shadow-md shadow-sky-600/30 transition-all hover:scale-[1.01]"
              >
                Entrar no Radar Cidadão
              </button>

              {/* Botões de Acesso Rápido para a Banca e Integrantes */}
              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 text-center space-y-2">
                <span className="text-[11px] text-slate-400 block font-medium">Acesso rápido para avaliação da banca:</span>
                <div className="grid grid-cols-1 gap-2">
                  {DEFAULT_USERS.map((usr) => (
                    <button
                      key={usr.id}
                      type="button"
                      onClick={() => handleDemoLogin(usr)}
                      className="w-full py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 transition-colors flex items-center justify-between"
                    >
                      <span className="flex items-center gap-1.5 truncate">
                        <Sparkles className="w-3.5 h-3.5 text-sky-500 flex-shrink-0" />
                        <span className="truncate">{usr.nome}</span>
                      </span>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 font-normal ml-2 flex-shrink-0">
                        {usr.bairro}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </form>
          )}

          {/* ABA 2: CRIAR NOVO CADASTRO */}
          {activeTab === 'register' && (
            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              
              {/* Nome */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
                  Nome Completo *
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    placeholder="Ex.: João da Silva"
                    value={registerNome}
                    onChange={(e) => setRegisterNome(e.target.value)}
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                  />
                  <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                </div>
              </div>

              {/* E-mail */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
                  E-mail de Acesso *
                </label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    placeholder="joao.silva@exemplo.com.br"
                    value={registerEmail}
                    onChange={(e) => setRegisterEmail(e.target.value)}
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                  />
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                </div>
              </div>

              {/* Localização: CEP (ViaCEP) + Bairro */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      CEP (ViaCEP)
                    </label>
                    {loadingCep && (
                      <span className="text-[10px] text-sky-600 dark:text-sky-400 flex items-center gap-1">
                        <div className="w-2.5 h-2.5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                        Buscando...
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type="text"
                      maxLength={9}
                      placeholder="01001-000"
                      value={registerCep}
                      onChange={handleCepChange}
                      className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                    />
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
                    Bairro de Residência *
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      placeholder="Ex.: Sé, Mooca, Butantã..."
                      value={registerBairro}
                      onChange={(e) => setRegisterBairro(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                    />
                    <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  </div>
                </div>
              </div>

              {cepSuccessMsg && (
                <div className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{cepSuccessMsg}</span>
                </div>
              )}

              {/* Senha e Confirmação de Senha com Validador */}
              <div className="space-y-3 pt-1">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Criar Senha *
                    </label>
                    {registerSenha && (
                      <span className={`text-[10px] font-semibold ${passwordStrength.color}`}>
                        {passwordStrength.label}
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type={showRegisterPassword ? "text" : "password"}
                      required
                      placeholder="Mínimo de 6 caracteres"
                      value={registerSenha}
                      onChange={(e) => setRegisterSenha(e.target.value)}
                      className="w-full pl-9 pr-10 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs focus:ring-2 focus:ring-sky-500 outline-none"
                    />
                    <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <button
                      type="button"
                      onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                      className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      aria-label="Alternar visualização da senha"
                    >
                      {showRegisterPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Barra visual de força da senha */}
                  {registerSenha && (
                    <div className="grid grid-cols-3 gap-1 mt-1.5 h-1">
                      <div className={`rounded-full ${passwordStrength.score >= 1 ? 'bg-red-500' : 'bg-slate-200 dark:bg-slate-700'}`} />
                      <div className={`rounded-full ${passwordStrength.score >= 2 ? 'bg-amber-500' : 'bg-slate-200 dark:bg-slate-700'}`} />
                      <div className={`rounded-full ${passwordStrength.score >= 3 ? 'bg-emerald-500' : 'bg-slate-200 dark:bg-slate-700'}`} />
                    </div>
                  )}
                </div>

                {/* Campo de Confirmação de Senha */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Confirmar Senha *
                    </label>
                    {registerConfirmarSenha && (
                      <span className={`text-[10px] font-semibold flex items-center gap-1 ${
                        passwordsMatch ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500'
                      }`}>
                        {passwordsMatch ? (
                          <>
                            <Check className="w-3 h-3" /> Senhas coincidem
                          </>
                        ) : (
                          <>
                            <X className="w-3 h-3" /> Não coincidem
                          </>
                        )}
                      </span>
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type={showRegisterPassword ? "text" : "password"}
                      required
                      placeholder="Digite a mesma senha novamente"
                      value={registerConfirmarSenha}
                      onChange={(e) => setRegisterConfirmarSenha(e.target.value)}
                      className={`w-full pl-9 pr-10 py-2.5 rounded-xl border bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-xs outline-none transition-all ${
                        registerConfirmarSenha
                          ? passwordsMatch
                            ? 'border-emerald-500 focus:ring-2 focus:ring-emerald-500'
                            : 'border-red-400 focus:ring-2 focus:ring-red-500'
                          : 'border-slate-300 dark:border-slate-700 focus:ring-2 focus:ring-sky-500'
                      }`}
                    />
                    <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  </div>
                </div>
              </div>

              {/* Termo de Consentimento LGPD - Inicia desmarcado para consentimento afirmativo */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Privacidade e Proteção de Dados (LGPD)</span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  Seus dados são armazenados localmente no navegador e utilizados exclusivamente para identificar o bairro de origem dos relatos, preservando o anonimato perante a comunidade.
                </p>
                <label className="flex items-start gap-2.5 pt-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={registerLgpd}
                    onChange={(e) => setRegisterLgpd(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500 cursor-pointer"
                  />
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300 leading-tight">
                    Concordo com os termos de uso e privacidade cívica. <span className="text-red-500 font-bold">*</span>
                  </span>
                </label>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-600/30 transition-all hover:scale-[1.01]"
              >
                Concluir Cadastro e Acessar
              </button>
            </form>
          )}

        </div>
      )}

    </div>
  );
}
