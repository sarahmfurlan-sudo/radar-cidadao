import { INITIAL_REPORTS, INITIAL_SENSORS, INITIAL_ALERTS } from '../data/initialData';

const KEYS = {
  REPORTS: 'radar_cidadao_reports',
  SENSORS: 'radar_cidadao_sensors',
  ALERTS: 'radar_cidadao_alerts',
  USERS_LIST: 'radar_cidadao_users_list',
  CURRENT_USER: 'radar_cidadao_current_user',
  THEME: 'radar_cidadao_theme'
};

export const DEFAULT_USERS = [
  {
    id: "usr-01",
    nome: "Mario Antonio Oliveira",
    email: "mario.oliveira@cidadao.sp.gov.br",
    senha: "123456",
    bairro: "Vila Anglo Brasileira",
    cidade: "São Paulo",
    termoLgpdAceito: true,
    dataCadastro: "2026-11-12T10:00:00Z"
  },
  {
    id: "usr-02",
    nome: "Sarah Marangoni Furlan",
    email: "sarah.furlan@cidadao.sp.gov.br",
    senha: "123456",
    bairro: "Mooca",
    cidade: "São Paulo",
    termoLgpdAceito: true,
    dataCadastro: "2026-11-12T11:00:00Z"
  },
  {
    id: "usr-03",
    nome: "Vinicius Augusto Silva",
    email: "vinicius.silva@cidadao.sp.gov.br",
    senha: "123456",
    bairro: "Aclimação",
    cidade: "São Paulo",
    termoLgpdAceito: true,
    dataCadastro: "2026-11-12T12:00:00Z"
  }
];

/**
 * Inicializa e sincroniza a persistência no navegador
 */
export function initStorage() {
  if (!localStorage.getItem(KEYS.REPORTS)) {
    localStorage.setItem(KEYS.REPORTS, JSON.stringify(INITIAL_REPORTS));
  }
  if (!localStorage.getItem(KEYS.SENSORS)) {
    localStorage.setItem(KEYS.SENSORS, JSON.stringify(INITIAL_SENSORS));
  }
  if (!localStorage.getItem(KEYS.ALERTS)) {
    localStorage.setItem(KEYS.ALERTS, JSON.stringify(INITIAL_ALERTS));
  }

  // Sincroniza a lista de usuários no localStorage:
  // Garante que DEFAULT_USERS atualizados no código sejam mesclados imediatamente,
  // preservando quaisquer novos cadastros que o usuário tenha feito no formulário.
  const storedUsersRaw = localStorage.getItem(KEYS.USERS_LIST);
  if (!storedUsersRaw) {
    localStorage.setItem(KEYS.USERS_LIST, JSON.stringify(DEFAULT_USERS));
  } else {
    try {
      const storedUsers = JSON.parse(storedUsersRaw);
      const userMap = new Map();
      
      // Insere os usuários padrão do código
      DEFAULT_USERS.forEach(u => userMap.set(u.email.toLowerCase(), u));
      
      // Preserva outros usuários cadastrados manualmente
      storedUsers.forEach(u => {
        if (!userMap.has(u.email.toLowerCase())) {
          userMap.set(u.email.toLowerCase(), u);
        }
      });

      localStorage.setItem(KEYS.USERS_LIST, JSON.stringify(Array.from(userMap.values())));
    } catch (e) {
      localStorage.setItem(KEYS.USERS_LIST, JSON.stringify(DEFAULT_USERS));
    }
  }
}

/**
 * Retorna todos os usuários cadastrados localmente
 */
export function getUsersList() {
  try {
    const raw = localStorage.getItem(KEYS.USERS_LIST);
    return raw ? JSON.parse(raw) : DEFAULT_USERS;
  } catch (e) {
    return DEFAULT_USERS;
  }
}

/**
 * Cadastra um novo cidadão localmente no navegador
 */
export function registerUser({ nome, email, senha, bairro }) {
  const users = getUsersList();
  
  // Verifica duplicidade de e-mail
  const exists = users.find(u => u.email.toLowerCase() === email.toLowerCase());
  if (exists) {
    throw new Error("Este e-mail já está cadastrado localmente no navegador.");
  }

  const newUser = {
    id: `usr-${Date.now().toString().slice(-4)}`,
    nome,
    email,
    senha,
    bairro: bairro || "Cambuci",
    cidade: "São Paulo",
    termoLgpdAceito: true,
    dataCadastro: new Date().toISOString()
  };

  const updated = [...users, newUser];
  localStorage.setItem(KEYS.USERS_LIST, JSON.stringify(updated));
  setCurrentUser(newUser);
  return newUser;
}

/**
 * Autentica o cidadão com e-mail e senha salvos no localStorage
 */
export function authenticateUser(email, senha) {
  const users = getUsersList();
  const user = users.find(u => 
    u.email.toLowerCase() === email.toLowerCase().trim() && 
    u.senha === senha.trim()
  );

  if (!user) {
    throw new Error("E-mail ou senha incorretos.");
  }

  setCurrentUser(user);
  return user;
}

/**
 * Retorna o usuário logado no momento (ou null se deslogado)
 */
export function getCurrentUser() {
  try {
    const raw = localStorage.getItem(KEYS.CURRENT_USER);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

export function setCurrentUser(user) {
  if (user) {
    localStorage.setItem(KEYS.CURRENT_USER, JSON.stringify(user));
  } else {
    localStorage.removeItem(KEYS.CURRENT_USER);
  }
}

export function logoutUser() {
  localStorage.removeItem(KEYS.CURRENT_USER);
}

/**
 * Login com conta de demonstração (permite escolher pelo índice, padrão 0 = Mario Antonio)
 */
export function loginDemoUser(index = 0) {
  const users = getUsersList();
  const demo = users[index] || DEFAULT_USERS[0];
  setCurrentUser(demo);
  return demo;
}

/**
 * Gerenciamento de relatos
 */
export function getReports() {
  try {
    const raw = localStorage.getItem(KEYS.REPORTS);
    return raw ? JSON.parse(raw) : INITIAL_REPORTS;
  } catch (e) {
    return INITIAL_REPORTS;
  }
}

export function saveReport(report) {
  const reports = getReports();
  const updated = [report, ...reports];
  localStorage.setItem(KEYS.REPORTS, JSON.stringify(updated));
  return report;
}

export function getSensors() {
  try {
    const raw = localStorage.getItem(KEYS.SENSORS);
    return raw ? JSON.parse(raw) : INITIAL_SENSORS;
  } catch (e) {
    return INITIAL_SENSORS;
  }
}

export function getAlerts() {
  try {
    const raw = localStorage.getItem(KEYS.ALERTS);
    return raw ? JSON.parse(raw) : INITIAL_ALERTS;
  } catch (e) {
    return INITIAL_ALERTS;
  }
}

export function getStoredTheme() {
  return localStorage.getItem(KEYS.THEME) || 'light';
}

export function setStoredTheme(theme) {
  localStorage.setItem(KEYS.THEME, theme);
}

export function resetStorageToDefaults() {
  localStorage.setItem(KEYS.REPORTS, JSON.stringify(INITIAL_REPORTS));
  localStorage.setItem(KEYS.SENSORS, JSON.stringify(INITIAL_SENSORS));
  localStorage.setItem(KEYS.ALERTS, JSON.stringify(INITIAL_ALERTS));
  localStorage.setItem(KEYS.USERS_LIST, JSON.stringify(DEFAULT_USERS));
  localStorage.removeItem(KEYS.CURRENT_USER);
}
