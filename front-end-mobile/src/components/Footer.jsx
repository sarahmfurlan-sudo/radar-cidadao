import React from 'react';
import { ShieldAlert, Globe, RotateCcw, HeartHandshake } from 'lucide-react';
import { resetStorageToDefaults } from '../services/storageService';

export default function Footer({ onResetData }) {
  const handleReset = () => {
    if (window.confirm("Deseja restaurar os dados de demonstração iniciais de São Paulo?")) {
      resetStorageToDefaults();
      if (onResetData) onResetData();
      window.location.reload();
    }
  };

  return (
    <footer className="bg-slate-900 text-slate-300 border-t border-slate-800 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Coluna 1: Sobre */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-white text-base tracking-tight">
                Radar <span className="text-sky-400">Cidadão</span>
              </span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Plataforma colaborativa de zeladoria e resiliência urbana. Cidadãos registram problemas, sensores confirmam os riscos e a população recebe alertas preventivos contra alagamentos em São Paulo.
            </p>
            <div className="pt-2">
              <button
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] border border-slate-700 transition-colors"
                title="Restaura os relatos e sensores para a configuração padrão da demonstração"
              >
                <RotateCcw className="w-3 h-3 text-sky-400" />
                <span>Restaurar Dados da Demo</span>
              </button>
            </div>
          </div>

          {/* Coluna 2: ODS Vinculados */}
          <div className="space-y-3">
            <h4 className="font-bold text-white text-xs uppercase tracking-wider flex items-center gap-1.5">
              <Globe className="w-4 h-4 text-emerald-400" /> Objetivos de Desenvolvimento Sustentável
            </h4>
            <div className="space-y-2">
              <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="block font-semibold text-white text-xs">ODS 11 • Meta 11.5</span>
                <span className="text-[11px] text-slate-400">
                  Reduzir mortes e perdas econômicas causadas por desastres relacionados à água.
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="block font-semibold text-white text-xs">ODS 13 • Meta 13.1</span>
                <span className="text-[11px] text-slate-400">
                  Reforçar a resiliência e a adaptação a riscos climáticos e desastres naturais.
                </span>
              </div>
            </div>
          </div>

          {/* Coluna 3: Telefones de Emergência */}
          <div className="space-y-3">
            <h4 className="font-bold text-white text-xs uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-red-400" /> Emergência Oficial
            </h4>
            <p className="text-slate-400 text-[11px]">
              O Radar Cidadão não substitui canais oficiais. Em perigo imediato, ligue:
            </p>
            <ul className="space-y-1.5 text-xs">
              <li className="flex justify-between items-center py-1 border-b border-slate-800">
                <span className="text-slate-300">Defesa Civil</span>
                <a href="tel:199" className="font-bold text-red-400 hover:underline">199</a>
              </li>
              <li className="flex justify-between items-center py-1 border-b border-slate-800">
                <span className="text-slate-300">Corpo de Bombeiros</span>
                <a href="tel:193" className="font-bold text-red-400 hover:underline">193</a>
              </li>
              <li className="flex justify-between items-center py-1 border-b border-slate-800">
                <span className="text-slate-300">SAMU</span>
                <a href="tel:192" className="font-bold text-red-400 hover:underline">192</a>
              </li>
              <li className="flex justify-between items-center py-1">
                <span className="text-slate-300">CGE São Paulo</span>
                <span className="text-slate-400 text-[11px]">cgesp.org</span>
              </li>
            </ul>
          </div>

          {/* Coluna 4: Conformidade Acadêmica e LGPD */}
          <div className="space-y-3">
            <h4 className="font-bold text-white text-xs uppercase tracking-wider flex items-center gap-1.5">
              <HeartHandshake className="w-4 h-4 text-sky-400" /> Governança & LGPD
            </h4>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Global Solution 2026.2 • Disciplina de Front End & Mobile Development (FIAP).
            </p>
            <div className="text-[11px] text-slate-400 bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/80">
              <strong className="text-slate-300 block mb-0.5">Privacidade Garantida:</strong>
              Relatos são armazenados localmente no navegador (`localStorage`) com dados mínimos anonimizados, sem monitoramento individual de cidadãos.
            </div>
          </div>

        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-slate-500 text-[11px] gap-2">
          <p>© 2026 Radar Cidadão • Protótipo CitizenTech Integrado com IA</p>
          <p>Front End em React + Vite • Persistência Local-First</p>
        </div>
      </div>
    </footer>
  );
}

