# Radar Cidadão — Frontend CitizenTech com IA

> **Global Solution 2026.2 — FIAP**  
> **Disciplina:** Front End & Mobile Development  
> **Tema:** Protótipo Integrado CitizenTech com IA para Apoiar o Cidadão  

---

## 1. Identificação da Equipe
| Nome Completo | RM |
| :--- | :--- |
| Mario Antonio Oliveira | RM 567713 |
| Sarah Marangoni Furlan | RM 566764 |
| Vinicius Augusto Silva | RM 566830 |

---

## 2. Descrição do Projeto
O **Radar Cidadão** é uma plataforma colaborativa de zeladoria e resiliência urbana voltada para a prevenção e resposta a alagamentos na cidade de São Paulo. A solução conecta o registro colaborativo do cidadão (bueiros obstruídos por lixo, acúmulo de lâmina d'água e alagamentos) à confirmação técnica por sensores IoT e à inteligência da Defesa Civil, fornecendo orientações práticas de autoproteção e difusão de alertas em tempo real.

---

## 3. Problema Escolhido e Público Afetado
* **Problema:** Alagamentos recorrentes na Região Metropolitana de São Paulo causam perdas materiais severas, paralisam a mobilidade urbana e colocam vidas humanas em risco. Grande parte desses episódios tem origem na obstrução de bocas de lobo e galerias pluviais por descarte irregular de lixo e entulho em vias públicas, agravados pela demora na transmissão de dados entre cidadãos e poder público.
* **Público Afetado:** Moradores, pedestres e condutores que circulam por áreas historicamente vulneráveis a enchentes e inundações em São Paulo (como baixadas dos rios Tietê e Tamanduateí, Anhangabaú, Bresser, Ipiranga e Aricanduva), além de agentes municipais e da Defesa Civil encarregados das ações de resposta e zeladoria.

---

## 4. Relação com os Objetivos de Desenvolvimento Sustentável (ODS)
* **ODS 11 — Cidades e Comunidades Sustentáveis (Meta 11.5):**
  Reduzir significativamente o número de mortes e perdas econômicas diretas causadas por desastres relacionados com a água, através da prevenção e mitigação de alagamentos urbanos.
* **ODS 13 — Ação Contra a Mudança Global do Clima (Meta 13.1):**
  Reforçar a resiliência e a capacidade de adaptação a riscos climáticos e eventos pluviométricos extremos na capital paulista.

---

## 5. Arquitetura e Tecnologias Utilizadas
A aplicação foi desenvolvida em conformidade estrita com o edital da disciplina:
* **Core:** React 18 + Vite (JavaScript puro).
* **Roteamento:** `react-router-dom` com navegação estruturada entre telas (`/`, `/mapa`, `/relato/novo`, `/relatos`, `/alertas`, `/login`, `/sobre`).
* **Estilização e Acessibilidade:** Tailwind CSS seguindo os padrões WCAG AA (alto contraste, tipografia escalável, suporte a Modo Claro e Modo Escuro, e marcações semânticas para leitores de tela).
* **Cartografia Interativa:** Leaflet + `react-leaflet` com OpenStreetMap, renderizando os pontos de risco em tempo real com raios de dispersão semânticos.
* **Persistência Local (Local-First):** Armazenamento em `localStorage` no navegador para relatos, sensores sintéticos, alertas oficiais e sessão de usuário (cumprindo o Requisito 4 do edital sem dependências externas).
* **Processamento Inteligente com IA:** Serviço desacoplado (`src/services/aiService.js`) conectado ao endpoint NVIDIA NIM (`meta/llama-3.2-90b-vision-instruct`), integrado a um motor determinístico de contingência baseado no corpus oficial da Defesa Civil de São Paulo.
* **Iconografia:** `lucide-react`.

---

## 6. Funcionalidades do Protótipo (Requisitos do Edital)

| Requisito | Implementação no Projeto |
| :--- | :--- |
| **1. Componentes, props e estado** | Estrutura modular (`RiskBadge`, `SensorStatusCard`, `GuidanceModal`, `Navbar`, `Footer`) com gerenciamento de estado via hooks nativos (`useState`, `useEffect`). |
| **2. Rotas de navegação** | Configuração no `App.jsx` com suporte a 6 rotas especializadas, rotas protegidas (`ProtectedRoute`) e redirecionamento de fallback. |
| **3. Login local** | Tela de autenticação e cadastro de usuário (`/login`) persistida no navegador (`localStorage`), com suporte a login/logout e termo explícito de aceite LGPD. |
| **4. Telas de cadastro e consulta** | **Cadastro do Cidadão** (`/login`), **Cadastro do Relato** (`/relato/novo`, com upload de fotos e geolocalização) e **Consulta** no Mapa de Risco (`/mapa`) e no Histórico (`/relatos`). |
| **5. Processamento inteligente** | Análise por visão computacional simulada (Etapa 2) e geração de orientação de autoproteção da Defesa Civil via IA (Etapa 6), com acionamento dos canais 199 e 193 em casos críticos. |

---

## 7. Proteção de Dados Pessoais (LGPD)
O projeto respeita o princípio da minimização da LGPD (Art. 6º, III):
* Não são solicitados documentos fiscais (CPF, RG) ou dados biométricos.
* No Mapa de Risco público e nas listas compartilhadas, os relatos são exibidos com identificação anônima ("Cidadão Colaborador" associado apenas ao bairro), garantindo a proteção da identidade do usuário.
* É exigido o consentimento explícito do usuário no cadastro de perfil e no registro de cada relato.

---

## 8. Como Executar o Projeto Localmente

### Pré-requisitos
* Node.js v18+ (testado na versão v22.14.0)
* npm (v10+ / v11+)

### Passos de Instalação e Execução

1. **Clonar o repositório ou abrir o diretório do projeto:**
   ```bash
   cd FRONT
   ```

2. **Instalar as dependências:**
   ```bash
   npm install
   ```

3. **(Opcional) Configurar a chave da API NVIDIA NIM:**
   * Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:
     ```env
     VITE_NVIDIA_API_KEY=sua_chave_nvidia_nim_aqui
     VITE_NVIDIA_MODEL=meta/llama-3.2-90b-vision-instruct
     ```
   * *Nota:* Caso não seja configurada nenhuma chave, o sistema aciona automaticamente a contingência local baseada no corpus oficial da Defesa Civil SP, sem qualquer bloqueio na interface.

4. **Iniciar o servidor de desenvolvimento:**
   ```bash
   npm run dev
   ```
   Acesse no navegador: `http://localhost:5173`

5. **Gerar a build de produção:**
   ```bash
   npm run build
   ```

---

## 9. Termos e Diretrizes de Comunicação
Em conformidade com as diretrizes do projeto:
* Empregam-se os termos: **Radar Cidadão**, **relato**, **Mapa de Risco**, **alerta**, **encaminhamento**, **Defesa Civil**.
* É expressamente evitado o uso de terminologias proibidas como *denúncia*, *vigilância* ou *monitoramento de pessoas*.

