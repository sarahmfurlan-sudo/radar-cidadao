import React from 'react';
import { AlertTriangle, ShieldAlert, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function RiskBadge({ level = 'low', label, showIcon = true, size = 'md' }) {
  const configs = {
    critical: {
      bg: 'bg-red-100 text-red-800 dark:bg-red-950/70 dark:text-red-300 border-red-300 dark:border-red-800',
      icon: ShieldAlert,
      defaultLabel: 'Emergência'
    },
    high: {
      bg: 'bg-orange-100 text-orange-800 dark:bg-orange-950/70 dark:text-orange-300 border-orange-300 dark:border-orange-800',
      icon: AlertTriangle,
      defaultLabel: 'Alerta'
    },
    moderate: {
      bg: 'bg-amber-100 text-amber-800 dark:bg-amber-950/70 dark:text-amber-300 border-amber-300 dark:border-amber-800',
      icon: AlertCircle,
      defaultLabel: 'Atenção'
    },
    low: {
      bg: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
      icon: CheckCircle2,
      defaultLabel: 'Normal'
    }
  };

  const current = configs[level] || configs.low;
  const Icon = current.icon;
  const text = label || current.defaultLabel;

  const sizeClasses = size === 'sm' 
    ? 'text-xs px-2 py-0.5 gap-1' 
    : size === 'lg'
    ? 'text-sm px-3.5 py-1.5 gap-2 font-semibold'
    : 'text-xs px-2.5 py-1 gap-1.5 font-medium';

  return (
    <span 
      className={`inline-flex items-center rounded-full border ${current.bg} ${sizeClasses} shadow-sm transition-colors`}
      role="status"
      aria-label={`Nível de risco: ${text}`}
    >
      {showIcon && <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} aria-hidden="true" />}
      <span>{text}</span>
    </span>
  );
}

