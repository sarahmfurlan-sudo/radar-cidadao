import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  ShieldAlert, 
  AlertTriangle, 
  Radio, 
  PhoneCall, 
  CheckCircle2, 
  Calendar,
  Building2,
  Sparkles,
  Zap
} from 'lucide-react';
import { getAlerts, getSensors, initStorage } from '../services/storageService';
import RiskBadge from '../components/RiskBadge';
import SensorStatusCard from '../components/SensorStatusCard';

export default function AlertsPage({ iotState }) {
  const [alerts, setAlerts] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [dispatchedNotice, setDispatchedNotice] = useState(false);

  const liveSensor = iotState?.sensor;
  const iotMode = iotState?.modo || 'simulado';
  const cenarioFallback = iotState?.cenarioFallback || 'NORMAL';
  const setCenarioFallback = iotState?.setCenarioFallback;

  useEffect(() => {
    initStorage();
    setAlerts(getAlerts());
    setSensors(getSensors());
  }, []);

  const handleSimulateNewAlert = () => {
    const newAlert = {
      id: `alt-${Date.now().toString().slice(-4)}`,
      titulo: "Novo Alerta de Alagamento Iminente — Bacia do Aricanduva",
      regiao: "Zona Leste",
      severidade: "high",
      severidadeLabel: "Alerta Imediato",
      mensagem: "Sensores IoT detectaram elevação de 35 cm na lâmina d'água com chuva torrencial de 38 mm/h nos últimos 20 minutos. Risco iminente de extravasamento no viaduto Aricanduva. Busque rotas alternativas.",
      dataHora: new Date().toISOString(),
      orgaoEmissor: "Defesa Civil do Município de São Paulo",
      recomendacoes: [
        "Desvie de trechos baixos da Av. Aricanduva.",
        "Não tente transpor enxurradas.",
        "Comunique emergências pelo 199."
      ]
    };

    const updated = [newAlert, ...alerts];
    localStorage.setItem('radar_cidadao_alerts', JSON.stringify(updated));
    setAlerts(updated);
    setDispatchedNotice(true);
    setTimeout(() => setDispatchedNotice(false), 5000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header com Notificação de Disparo */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-xs font-bold uppercase tracking-wider mb-1">
            <Bell className="w-4 h-4 animate-bounce" />
            <span>Etapa 7 do Fluxo • Difusão de Alertas</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Central de Alertas da Defesa Civil
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Avisos oficiais emitidos com base na confirmação de relatos de cidadãos e dados dos sensores de chuva e nível d'água em São Paulo.
          </p>
        </div>

        {/* Botão para Simular Disparo de Alerta */}
        <button
          onClick={handleSimulateNewAlert}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-md shadow-red-600/30 transition-all hover:scale-105"
        >
          <Zap className="w-4 h-4" />
          <span>Simular Disparo de Alerta IoT</span>
        </button>
      </div>

      {dispatchedNotice && (
        <div className="p-4 rounded-xl bg-red-500 text-white shadow-lg flex items-center justify-between animate-in fade-in slide-in-from-top-3">
          <div className="flex items-center gap-3 text-xs font-bold">
            <Bell className="w-5 h-5 animate-pulse" />
            <span>Novo Alerta Hidrológico transmitido para a população da Zona Leste!</span>
          </div>
          <span className="text-[11px] bg-red-700/60 px-2 py-0.5 rounded">Agora</span>
        </div>
      )}

      {/* Grid de Alertas Oficiais */}
      <div className="space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-red-500" /> Alertas Vigentes Emitidos:
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {alerts.map((alt) => (
            <div
              key={alt.id}
              className={`rounded-2xl border p-6 shadow-sm transition-all flex flex-col justify-between ${
                alt.severidade === 'critical'
                  ? 'bg-red-50/50 dark:bg-red-950/20 border-red-200 dark:border-red-900/60'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                      Região: {alt.regiao}
                    </span>
                    <h3 className="text-base font-extrabold text-slate-900 dark:text-white mt-0.5">
                      {alt.titulo}
                    </h3>
                  </div>
                  <RiskBadge level={alt.severidade} label={alt.severidadeLabel} size="md" />
                </div>

                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed mb-4">
                  {alt.mensagem}
                </p>

                {alt.recomendacoes && (
                  <div className="space-y-1.5 pt-3 border-t border-slate-200/60 dark:border-slate-800 mb-4">
                    <span className="text-[11px] font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider block">
                      Recomendações da Defesa Civil:
                    </span>
                    <ul className="space-y-1">
                      {alt.recomendacoes.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-400">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  {alt.orgaoEmissor}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  {new Date(alt.dataHora).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Seção de Sensores IoT em Operação */}
      <div className="pt-6 border-t border-slate-200 dark:border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-sky-600 dark:text-sky-400" />
            <h2 className="text-base font-extrabold text-slate-900 dark:text-white">
              Telemetria de Sensores IoT (ESP32)
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            Etapa 3 • Sensores de Nível e Chuva
          </span>
        </div>

        {liveSensor && (
          <div className="p-4 rounded-2xl border border-sky-200 dark:border-sky-800 bg-sky-50/70 dark:bg-sky-950/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-extrabold text-slate-900 dark:text-white">
                  {liveSensor.device}
                </span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                  iotMode === 'ao_vivo'
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                }`}>
                  {iotMode === 'ao_vivo' ? 'Ao Vivo (Node-RED)' : 'Simulado (Fallback)'}
                </span>
                <RiskBadge
                  level={liveSensor.nivel_risco === 'ALERTA' ? 'critical' : liveSensor.nivel_risco === 'ATENCAO' ? 'moderate' : 'low'}
                  label={liveSensor.nivel_risco}
                  size="sm"
                />
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {liveSensor.regiao} • Água: <strong>{liveSensor.nivel_agua_pct}%</strong> • Chuva: <strong>{liveSensor.chuva_pct}%</strong> • Distância: <strong>{liveSensor.distancia_cm} cm</strong>
              </p>
            </div>

            {iotMode === 'simulado' && setCenarioFallback && (
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] text-slate-500 dark:text-slate-400">Cenário:</span>
                {['NORMAL', 'ATENCAO', 'ALERTA'].map((cen) => (
                  <button
                    key={cen}
                    type="button"
                    onClick={() => setCenarioFallback(cen)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-colors ${
                      cenarioFallback === cen
                        ? 'bg-sky-600 text-white'
                        : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
                    }`}
                  >
                    {cen}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sensors.map((sensor) => (
            <SensorStatusCard key={sensor.id} sensor={sensor} />
          ))}
        </div>
      </div>

    </div>
  );
}

