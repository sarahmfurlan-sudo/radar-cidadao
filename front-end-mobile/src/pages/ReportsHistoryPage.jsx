import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  MapPin, 
  Calendar, 
  Sparkles, 
  FileText, 
  CheckCircle, 
  Clock, 
  ExternalLink,
  Plus
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getReports } from '../services/storageService';
import RiskBadge from '../components/RiskBadge';
import GuidanceModal from '../components/GuidanceModal';

export default function ReportsHistoryPage() {
  const [reports, setReports] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [selectedGuidance, setSelectedGuidance] = useState(null);

  useEffect(() => {
    setReports(getReports());
  }, []);

  const filtered = reports.filter(r => {
    const matchesSearch = 
      r.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.endereco.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.categoriaLabel.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.protocolo && r.protocolo.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesRisk = riskFilter === 'all' || r.nivelRisco === riskFilter;

    return matchesSearch && matchesRisk;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Histórico e Consulta de Relatos
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Acompanhe o status dos relatos registrados pela comunidade, validações de sensores e encaminhamentos ao poder público.
          </p>
        </div>

        <Link
          to="/relato/novo"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs shadow-md shadow-sky-600/30 transition-all hover:scale-105"
        >
          <Plus className="w-4 h-4" />
          <span>Novo Relato</span>
        </Link>
      </div>

      {/* Barra de Busca e Filtros */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm mb-6 flex flex-col md:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <input
            type="text"
            placeholder="Buscar por rua, bairro, categoria ou protocolo..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 outline-none"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto text-xs">
          <span className="text-slate-400 flex items-center gap-1 text-[11px] font-semibold uppercase">
            <Filter className="w-3 h-3" /> Risco:
          </span>
          <button
            onClick={() => setRiskFilter('all')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              riskFilter === 'all' 
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900' 
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => setRiskFilter('critical')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              riskFilter === 'critical' ? 'bg-red-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
            }`}
          >
            Emergência
          </button>
          <button
            onClick={() => setRiskFilter('high')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              riskFilter === 'high' ? 'bg-orange-500 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
            }`}
          >
            Alerta
          </button>
          <button
            onClick={() => setRiskFilter('moderate')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              riskFilter === 'moderate' ? 'bg-amber-500 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
            }`}
          >
            Atenção
          </button>
        </div>
      </div>

      {/* Grid de Cards de Relato */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((rep) => (
          <div
            key={rep.id}
            className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all flex flex-col justify-between overflow-hidden"
          >
            {/* Foto opcional */}
            {rep.imageUrl && (
              <div className="relative h-40 w-full bg-slate-100 dark:bg-slate-800">
                <img src={rep.imageUrl} alt={rep.titulo} className="w-full h-full object-cover" />
                <div className="absolute top-3 left-3">
                  <RiskBadge level={rep.nivelRisco} label={rep.nivelRiscoLabel} size="sm" />
                </div>
                <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-slate-900/80 text-white text-[10px] font-mono">
                  {rep.protocolo || 'RC-SP'}
                </span>
              </div>
            )}

            <div className="p-5 flex-1 flex flex-col justify-between">
              <div>
                {!rep.imageUrl && (
                  <div className="flex items-center justify-between mb-2">
                    <RiskBadge level={rep.nivelRisco} label={rep.nivelRiscoLabel} size="sm" />
                    <span className="text-[10px] text-slate-400 font-mono">{rep.protocolo}</span>
                  </div>
                )}

                <h3 className="font-bold text-sm text-slate-900 dark:text-white line-clamp-2 mb-1.5">
                  {rep.titulo}
                </h3>

                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-3 mb-3">
                  {rep.descricao}
                </p>

                <div className="space-y-1.5 text-[11px] text-slate-500 dark:text-slate-400 mb-4">
                  <div className="flex items-center gap-1.5 line-clamp-1">
                    <MapPin className="w-3.5 h-3.5 text-sky-500 flex-shrink-0" />
                    <span>{rep.endereco}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                    <span>{new Date(rep.dataHora).toLocaleString('pt-BR')}</span>
                  </div>
                </div>

                {/* Bloco de Visão Computacional e Encaminhamento */}
                <div className="bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-xl border border-slate-100 dark:border-slate-800 text-[11px] space-y-1 mb-4">
                  <div className="flex justify-between text-slate-600 dark:text-slate-300">
                    <span className="font-semibold">Detecção por Imagem:</span>
                    <span className="text-sky-600 dark:text-sky-400 font-bold">{rep.confiancaVisaoComputacional}%</span>
                  </div>
                  <p className="text-slate-500 dark:text-slate-400 text-[10px] line-clamp-1">
                    {rep.tipoDetecao}
                  </p>
                  <div className="pt-1 border-t border-slate-200 dark:border-slate-700/60 flex items-center justify-between text-[10px] text-slate-500">
                    <span>{rep.statusLabel}</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{rep.encaminhamentoStatus}</span>
                  </div>
                </div>
              </div>

              {/* Ações do Card */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <Link
                  to="/"
                  className="text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-sky-600 flex items-center gap-1"
                >
                  <MapPin className="w-3.5 h-3.5" /> Ver no Mapa
                </Link>

                <button
                  onClick={() => setSelectedGuidance({
                    titulo: rep.titulo,
                    nivelRisco: rep.nivelRisco,
                    nivelRiscoLabel: rep.nivelRiscoLabel,
                    confianca: rep.confiancaVisaoComputacional,
                    orientacao: rep.resumoOrientacaoIA,
                    recomendacoesImediatas: [
                      "Acompanhe os alertas do Radar Cidadão antes de trafegar pela via.",
                      "Não toque na água de alagamento.",
                      "Emergência ligue 199 (Defesa Civil)."
                    ],
                    fonteOficial: "Defesa Civil SP / Processamento Inteligente",
                    origemProcessamento: "Síntese Oficial"
                  })}
                  className="inline-flex items-center gap-1 text-xs font-bold text-sky-600 dark:text-sky-400 hover:underline"
                >
                  <Sparkles className="w-3.5 h-3.5" /> Orientação IA
                </button>
              </div>

            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="col-span-full py-16 text-center text-slate-400 text-xs">
            Nenhum relato encontrado com os critérios de busca.
          </div>
        )}
      </div>

      {/* Modal de Orientação */}
      <GuidanceModal
        isOpen={!!selectedGuidance}
        onClose={() => setSelectedGuidance(null)}
        guidanceData={selectedGuidance}
        reportTitle={selectedGuidance?.titulo}
      />

    </div>
  );
}

