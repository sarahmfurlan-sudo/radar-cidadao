import { useEffect, useState } from "react";

const FALLBACK_IOT = {
  NORMAL: { device: "RadarCidadao_Bueiro01", regiao: "Pompéia - Ponto - 01", distancia_cm: 120, nivel_agua_pct: 0, chuva_pct: 0, chuva_ativa: false, nivel_risco: "NORMAL", alerta_ativo: false },
  ATENCAO: { device: "RadarCidadao_Bueiro01", regiao: "Pompéia - Ponto - 01", distancia_cm: 55, nivel_agua_pct: 50, chuva_pct: 60, chuva_ativa: true, nivel_risco: "ATENCAO", alerta_ativo: false },
  ALERTA: { device: "RadarCidadao_Bueiro01", regiao: "Pompéia - Ponto - 01", distancia_cm: 25, nivel_agua_pct: 83.3, chuva_pct: 75, chuva_ativa: true, nivel_risco: "ALERTA", alerta_ativo: true }
};

export function useRadarIoT() {
  const [cenarioFallback, setCenarioFallback] = useState("NORMAL");
  const [modo, setModo] = useState("simulado"); // "ao_vivo" | "simulado"
  const [sensor, setSensor] = useState(FALLBACK_IOT.NORMAL);

  useEffect(() => {
    const consultar = async () => {
      try {
        const res = await fetch("http://localhost:1880/api/radar/status", {
          signal: AbortSignal.timeout(1500)
        });
        if (!res.ok) throw new Error("HTTP " + res.status);
        const json = await res.json();
        if (json?.status) {
          setModo("ao_vivo");
          setSensor({ ...json.status, regiao: "Pompéia - Ponto - 01" });
          return;
        }
      } catch {
        setModo("simulado");
        setSensor(FALLBACK_IOT[cenarioFallback]);
      }
    };

    consultar();
    const id = setInterval(consultar, 2000);
    return () => clearInterval(id);
  }, [cenarioFallback]);

  return { sensor, modo, cenarioFallback, setCenarioFallback };
}