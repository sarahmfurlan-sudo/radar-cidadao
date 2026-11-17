import React from 'react';
import { CloudRain, Waves, BatteryCharging, Radio } from 'lucide-react';
import RiskBadge from './RiskBadge';

export default function SensorStatusCard({ sensor }) {
  if (!sensor) return null;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              sensor.status === 'critical' ? 'bg-red-400' : sensor.status === 'high' ? 'bg-orange-400' : 'bg-emerald-400'
            }`}></span>
            <span className={`relative inline-flex rounded-full h-3 w-3 ${
              sensor.status === 'critical' ? 'bg-red-500' : sensor.status === 'high' ? 'bg-orange-500' : 'bg-emerald-500'
            }`}></span>
          </span>
          <div>
            <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-100">{sensor.nome}</h4>
            <p className="text-xs text-slate-500 dark:text-slate-400">{sensor.localizacao}</p>
          </div>
        </div>
        <RiskBadge level={sensor.status} label={sensor.statusLabel} size="sm" />
      </div>

      <div className="grid grid-cols-2 gap-3 my-3 pt-2 border-t border-slate-100 dark:border-slate-700/60 text-xs">
        <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900/60 p-2 rounded-lg">
          <CloudRain className="w-4 h-4 text-sky-500 flex-shrink-0" />
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Precipitação</span>
            <span className="font-bold text-slate-700 dark:text-slate-200">{sensor.chuvaMmHora} mm/h</span>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900/60 p-2 rounded-lg">
          <Waves className="w-4 h-4 text-blue-500 flex-shrink-0" />
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Lâmina d'água</span>
            <span className="font-bold text-slate-700 dark:text-slate-200">{sensor.nivelAguaCm} cm</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 mt-2">
        <span className="inline-flex items-center gap-1">
          <Radio className="w-3 h-3 text-emerald-500" />
          ESP32 IoT ({sensor.ultimaAtualizacao})
        </span>
        <span className="inline-flex items-center gap-1">
          <BatteryCharging className="w-3 h-3" />
          {sensor.bateriaPercent}%
        </span>
      </div>
    </div>
  );
}

