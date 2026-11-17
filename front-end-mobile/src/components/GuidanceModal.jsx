import React, { useEffect } from 'react';
import { X, ShieldAlert, PhoneCall, FileText, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';
import RiskBadge from './RiskBadge';

export default function GuidanceModal({ isOpen, onClose, guidanceData, reportTitle }) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !guidanceData) return null;

  const isEmergency = guidanceData.nivelRisco === 'critical';

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div 
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden transform transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header com tom de emergência se crítico */}
        <div className={`p-5 flex items-center justify-between border-b ${
          isEmergency 
            ? 'bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900' 
            : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-800'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl ${
              isEmergency 
                ? 'bg-red-600 text-white' 
                : 'bg-blue-600 text-white'
            }`}>
              {isEmergency ? <ShieldAlert className="w-6 h-6" /> : <Sparkles className="w-6 h-6" />}
            </div>
            <div>
              <h3 id="modal-title" className="text-lg font-bold text-slate-900 dark:text-white">
                Orientação Oficial da Defesa Civil
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Processamento Inteligente do Relato • Radar Cidadão
              </p>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Fechar janela de orientação"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Corpo com a resposta da IA */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {reportTitle && (
            <div className="text-xs bg-slate-100 dark:bg-slate-800 p-2.5 rounded-lg text-slate-600 dark:text-slate-300">
              <span className="font-semibold text-slate-700 dark:text-slate-200">Relato analisado:</span> {reportTitle}
            </div>
          )}

          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Classificação de Risco:</span>
              <RiskBadge level={guidanceData.nivelRisco} label={guidanceData.nivelRiscoLabel} size="md" />
            </div>
            {guidanceData.confianca && (
              <span className="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md">
                Confiança do modelo: <strong>{guidanceData.confianca}%</strong>
              </span>
            )}
          </div>

          <div className="bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200/80 dark:border-blue-900/60 p-4 rounded-xl">
            <h4 className="text-xs font-bold uppercase tracking-wider text-blue-700 dark:text-blue-300 mb-2 flex items-center gap-1.5">
              <FileText className="w-4 h-4" /> Diretriz de Segurança
            </h4>
            <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-line">
              {guidanceData.orientacao}
            </p>
          </div>

          {guidanceData.recomendacoesImediatas && guidanceData.recomendacoesImediatas.length > 0 && (
            <div>
              <h5 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2.5">
                Recomendações Práticas Imediatas:
              </h5>
              <ul className="space-y-2">
                {guidanceData.recomendacoesImediatas.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Seção de Telefones de Emergência */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800">
            <h5 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider">
              Canais Oficiais de Atendimento Emergencial:
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <a
                href="tel:199"
                className="flex items-center justify-between p-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 transition-colors group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 rounded-lg group-hover:scale-105 transition-transform">
                    <PhoneCall className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-slate-800 dark:text-slate-100">199 — Defesa Civil</span>
                    <span className="block text-[11px] text-slate-500 dark:text-slate-400">Alagamentos e riscos</span>
                  </div>
                </div>
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400">Ligar</span>
              </a>

              <a
                href="tel:193"
                className="flex items-center justify-between p-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 transition-colors group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-red-100 dark:bg-red-900/60 text-red-700 dark:text-red-300 rounded-lg group-hover:scale-105 transition-transform">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-slate-800 dark:text-slate-100">193 — Bombeiros</span>
                    <span className="block text-[11px] text-slate-500 dark:text-slate-400">Resgate e salvamento</span>
                  </div>
                </div>
                <span className="text-xs font-bold text-red-600 dark:text-red-400">Ligar</span>
              </a>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 dark:text-slate-500 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
            <span>Fonte: {guidanceData.fonteOficial}</span>
            <span>{guidanceData.origemProcessamento}</span>
          </div>
        </div>

        {/* Footer do Modal */}
        <div className="p-4 bg-slate-50 dark:bg-slate-800/80 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-white transition-colors"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}

