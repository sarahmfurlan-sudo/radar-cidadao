/**
 * Serviço de Telemetria e Monitoramento de Sensores IoT — Radar Cidadão
 * Baseado nos limiares operacionais do CGE (Centro de Gerenciamento de Emergências de SP).
 */

export function calculateSensorRisk(chuvaMmHora, nivelAguaCm) {
  if (chuvaMmHora >= 40 || nivelAguaCm >= 50) {
    return {
      nivel: "critical",
      rotulo: "Emergência Hidrológica",
      descricao: "Risco de transbordamento iminente ou em andamento. Pistas intransitáveis."
    };
  }
  if (chuvaMmHora >= 20 || nivelAguaCm >= 25) {
    return {
      nivel: "high",
      rotulo: "Alerta de Alagamento",
      descricao: "Lâmina de água acumulada. Tráfego comprometido."
    };
  }
  if (chuvaMmHora >= 5 || nivelAguaCm >= 10) {
    return {
      nivel: "moderate",
      rotulo: "Estado de Atenção",
      descricao: "Precipitação contínua e sarjetas com escoamento lento."
    };
  }
  return {
    nivel: "low",
    rotulo: "Estado de Observação / Normal",
    descricao: "Níveis normais de drenagem e tempo estável."
  };
}

export function getGeneralTelemetryStats(sensors = []) {
  if (!sensors.length) {
    return {
      mediaChuva: 0,
      maiorNivel: 0,
      sensoresAtivos: 0,
      pontosCriticos: 0
    };
  }

  const somaChuva = sensors.reduce((acc, s) => acc + (s.chuvaMmHora || 0), 0);
  const maiorNivel = Math.max(...sensors.map(s => s.nivelAguaCm || 0));
  const pontosCriticos = sensors.filter(s => s.status === 'critical' || s.status === 'high').length;

  return {
    mediaChuva: (somaChuva / sensors.length).toFixed(1),
    maiorNivel: maiorNivel.toFixed(1),
    sensoresAtivos: sensors.length,
    pontosCriticos: pontosCriticos
  };
}

