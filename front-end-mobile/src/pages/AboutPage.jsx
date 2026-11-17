import React from 'react';
import {
  Globe,
  Layers,
  ShieldCheck,
  HeartHandshake,
  Cpu,
  Radio,
  Sparkles,
  Bot,
  Code2,
  Info,
  CheckCircle2,
  Users
} from 'lucide-react';

export default function AboutPage() {
  const steps = [
    { num: 1, title: "Relato do Cidadão", disc: "Front End & Mobile", desc: "Registro com foto, categoria e geolocalização em São Paulo." },
    { num: 2, title: "Detecção por Imagem", disc: "Visão Computacional", desc: "Identificação de resíduos e lâmina d'água com taxa de confiança." },
    { num: 3, title: "Confirmação por Sensores", disc: "IoT (ESP32)", desc: "Validação da elevação de água e chuva via telemetria." },
    { num: 4, title: "Memória de Alagamento", disc: "Computação Neuromórfica", desc: "Registro persistente pós-escoamento com circuito memristor." },
    { num: 5, title: "Atualização do Mapa de Risco", disc: "Front End & Mobile", desc: "Camada cartográfica com alertas e visualização georreferenciada." },
    { num: 6, title: "Orientação Inteligente", disc: "IA Generativa", desc: "Diretrizes oficiais de segurança com base no corpus da Defesa Civil." },
    { num: 7, title: "Difusão de Alertas", disc: "IoT / Front End", desc: "Disparo e recebimento de avisos de risco para a população da região." },
    { num: 8, title: "Encaminhamento Automatizado", disc: "RPA + IA", desc: "Consolidação de lote e abertura de chamado ao poder público." }
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">

      {/* Apresentação Principal */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-100 dark:bg-sky-950/60 border border-sky-300 dark:border-sky-800 text-sky-700 dark:text-sky-300 text-xs font-bold uppercase tracking-wider">
          <Info className="w-3.5 h-3.5" />
          <span>Global Solution 2026.2 • CitizenTech</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
          Radar Cidadão: Resiliência e Zeladoria Urbana
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
          Plataforma colaborativa projetada para enfrentar o desafio histórico dos alagamentos em São Paulo. Conecta a ação preventiva do cidadão à confirmação por sensores e à inteligência da Defesa Civil.
        </p>
      </div>

      {/* Alinhamento com os ODS */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-emerald-500" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Objetivos de Desenvolvimento Sustentável (ONU)
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded-md bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 text-xs font-bold">
                ODS 11
              </span>
              <span className="text-xs font-mono text-slate-400">Meta 11.5</span>
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Cidades e Comunidades Sustentáveis
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              <strong>Meta 11.5:</strong> Até 2030, reduzir significativamente o número de mortes e o número de pessoas afetadas por catástrofes e diminuir as perdas econômicas diretas causadas por desastres em relação ao PIB global, com foco na proteção dos vulneráveis e em desastres relacionados com a água.
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
              <strong>Aplicação no Radar Cidadão:</strong> O alerta antecipado e o mapeamento de bueiros entupidos reduzem os danos patrimoniais e riscos de afogamento em vias rebaixadas da capital paulista.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded-md bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 text-xs font-bold">
                ODS 13
              </span>
              <span className="text-xs font-mono text-slate-400">Meta 13.1</span>
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Ação Contra a Mudança Global do Clima
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              <strong>Meta 13.1:</strong> Reforçar a resiliência e a capacidade de adaptação a riscos relacionados ao clima e às catástrofes naturais em todos os países.
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
              <strong>Aplicação no Radar Cidadão:</strong> Fortalece a capacidade adaptativa dos bairros paulistanos através de dados distribuídos em tempo real e orientações oficiais de autoproteção.
            </p>
          </div>
        </div>
      </div>

      {/* Os 8 Passos do Fluxo Integrado */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-sky-600 dark:text-sky-400" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            O Fluxo Integrado do Radar Cidadão (Global Solution)
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((st) => (
            <div
              key={st.num}
              className={`p-4 rounded-xl border flex flex-col justify-between ${st.disc.includes('Front End')
                ? 'bg-sky-50/60 dark:bg-sky-950/20 border-sky-200 dark:border-sky-900'
                : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800'
                }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${st.disc.includes('Front End')
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                    }`}>
                    {st.num}
                  </span>
                  <span className="text-[10px] font-semibold text-sky-600 dark:text-sky-400 uppercase">
                    {st.disc}
                  </span>
                </div>
                <h4 className="font-bold text-xs text-slate-900 dark:text-white mb-1">
                  {st.title}
                </h4>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  {st.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Conformidade Técnica do Front End */}
      <div className="p-6 rounded-2xl bg-slate-900 text-white space-y-4">
        <div className="flex items-center gap-2 text-sky-400">
          <Code2 className="w-5 h-5" />
          <h3 className="text-base font-bold">
            Conformidade com a Rubrica de Front End & Mobile Development
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span><strong>Componentes, props e estado:</strong> Arquitetura modular em React com estados locais e hooks customizados.</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span><strong>Rotas de navegação:</strong> Navegação fluida com React Router DOM (Mapa, Novo Relato, Histórico, Alertas, Login, Sobre).</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span><strong>Login local:</strong> Gestão de perfil e sessão persistida no navegador com aceite LGPD.</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span><strong>Persistência no navegador:</strong> Relatos, alertas e dados de sensores armazenados no `localStorage`.</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span><strong>Processamento inteligente:</strong> Integração com a API NVIDIA NIM e contingência determinística do corpus da Defesa Civil SP.</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <span><strong>Acessibilidade & LGPD:</strong> Contrastes WCAG AA, modo escuro/claro, semântica ARIA e anonimização de relatos.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Seção da Equipe */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
        <div className="flex items-center gap-2 text-slate-800 dark:text-white">
          <Users className="w-5 h-5 text-sky-600" />
          <h3 className="text-sm font-bold uppercase tracking-wider">
            Integrantes do Grupo | GLOBAL SOLUTION 2026.2 (CITIZEN TECH) | FIAP 2TIAPR
          </h3>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Identificação dos autores da solução integrada:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
            <span className="font-bold text-slate-800 dark:text-slate-100 block">Mario Antonio Oliveira</span>
            <span className="text-slate-500 dark:text-slate-400">RM: 567713</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
            <span className="font-bold text-slate-800 dark:text-slate-100 block">Sarah Marangoni Furlan</span>
            <span className="text-slate-500 dark:text-slate-400">RM: 566764</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
            <span className="font-bold text-slate-800 dark:text-slate-100 block">Vinicius Augusto Silva</span>
            <span className="text-slate-500 dark:text-slate-400">RM: 566830</span>
          </div>
        </div>
      </div>

    </div>
  );
}

