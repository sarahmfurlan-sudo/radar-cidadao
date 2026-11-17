import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { 
  Filter, 
  MapPin, 
  Radio, 
  Sparkles, 
  Eye, 
  Plus, 
  AlertTriangle, 
  Clock, 
  CloudRain, 
  Waves,
  Navigation
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getReports, getSensors } from '../services/storageService';
import RiskBadge from '../components/RiskBadge';
import GuidanceModal from '../components/GuidanceModal';
import { getGeneralTelemetryStats } from '../services/sensorService';

// Função para criar ícones estilizados do Leaflet via DivIcon
function createCustomPin(colorHex, isSensor = false) {
  const iconHtml = isSensor ? `
    <div style="
      background-color: ${colorHex};
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
    ">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="2"></circle>
        <path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"></path>
      </svg>
    </div>
  ` : `
    <div style="
      background-color: ${colorHex};
      width: 30px;
      height: 30px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      border: 2px solid white;
      box-shadow: 0 4px 8px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        width: 10px;
        height: 10px;
        background: white;
        border-radius: 50%;
        transform: rotate(45deg);
      "></div>
    </div>
  `;

  return L.divIcon({
    html: iconHtml,
    className: 'custom-leaflet-pin',
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30]
  });
}

// Componente para recentralizar o mapa
function ChangeMapView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom || 14, { duration: 1.2 });
    }
  }, [center, zoom, map]);
  return null;
}

const WOKWI_COORDS = [-23.537952, -46.690544]; // radar cidadao

function mapIotRiskLevel(nivelRisco) {
  if (nivelRisco === 'ALERTA') return 'critical';
  if (nivelRisco === 'ATENCAO') return 'moderate';
  return 'low';
}

export default function RiskMapPage({ iotState }) {
  const [reports, setReports] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [filterCategory, setFilterCategory] = useState('todos');
  const [selectedReportForGuidance, setSelectedReportForGuidance] = useState(null);
  const [mapCenter, setMapCenter] = useState([-23.5505, -46.6333]); // Centro de São Paulo
  const [mapZoom, setMapZoom] = useState(12);

  const liveSensor = iotState?.sensor;
  const iotMode = iotState?.modo || 'simulado';
  const cenarioFallback = iotState?.cenarioFallback || 'NORMAL';
  const setCenarioFallback = iotState?.setCenarioFallback;

  useEffect(() => {
    setReports(getReports());
    setSensors(getSensors());
  }, []);

  const stats = getGeneralTelemetryStats(sensors);
  const totalSensors = sensors.length + (liveSensor ? 1 : 0);
  const totalCriticos = stats.pontosCriticos + (liveSensor?.nivel_risco === 'ALERTA' ? 1 : 0);

  // Filtragem dos relatos
  const filteredReports = reports.filter(r => {
    if (filterCategory === 'todos') return true;
    return r.categoria === filterCategory;
  });

  const getPinColor = (nivelRisco) => {
    switch (nivelRisco) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'moderate': return '#f59e0b';
      default: return '#10b981';
    }
  };

  const handleSelectReport = (rep) => {
    setMapCenter([rep.lat, rep.lng]);
    setMapZoom(15);
  };

  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex flex-col lg:flex-row bg-slate-100 dark:bg-slate-950 overflow-hidden">
      
      {/* Painel Lateral de Controle e Relatos Recentes (Split-Screen) */}
      <aside className="w-full lg:w-96 lg:h-[calc(100vh-4rem)] bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col z-20 shadow-md">
        
        {/* Cabeçalho do Painel */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <MapPin className="w-4 h-4 text-sky-600 dark:text-sky-400" />
              <span>Mapa de Risco em SP</span>
            </h1>
            <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded-full font-medium">
              Ao Vivo
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Monitoramento de alagamentos, bueiros obstruídos e telemetria de sensores em tempo real.
          </p>

          {/* Cards Rápidos de Telemetria Geral */}
          <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-center">
            <div className="p-2 bg-slate-50 dark:bg-slate-800/60 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Relatos</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{reports.length}</span>
            </div>
            <div className="p-2 bg-slate-50 dark:bg-slate-800/60 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Sensores</span>
              <span className="text-sm font-bold text-sky-600 dark:text-sky-400">{totalSensors}</span>
            </div>
            <div className="p-2 bg-red-50 dark:bg-red-950/40 rounded-lg">
              <span className="text-[10px] text-red-500 uppercase font-semibold block">Críticos</span>
              <span className="text-sm font-bold text-red-600 dark:text-red-400">{totalCriticos}</span>
            </div>
          </div>
        </div>

        {/* Filtros por Categoria */}
        <div className="px-4 py-2 bg-slate-50 dark:bg-slate-900/40 border-b border-slate-200 dark:border-slate-800 flex items-center gap-1.5 overflow-x-auto text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <button
            onClick={() => setFilterCategory('todos')}
            className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
              filterCategory === 'todos' 
                ? 'bg-sky-600 text-white' 
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800'
            }`}
          >
            Todos ({reports.length})
          </button>
          <button
            onClick={() => setFilterCategory('bueiro_entupido')}
            className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
              filterCategory === 'bueiro_entupido' 
                ? 'bg-sky-600 text-white' 
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800'
            }`}
          >
            Bueiros Obstruídos
          </button>
          <button
            onClick={() => setFilterCategory('alagamento_ativo')}
            className={`px-2.5 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
              filterCategory === 'alagamento_ativo' 
                ? 'bg-sky-600 text-white' 
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800'
            }`}
          >
            Alagamentos
          </button>
        </div>

        {/* Lista de Relatos Recentes com Scroll */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {/* Card do Sensor Wokwi / Node-RED (API em tempo real + fallback) */}
          {liveSensor && (
            <div
              onClick={() => {
                setMapCenter(WOKWI_COORDS);
                setMapZoom(15);
              }}
              className="p-3 rounded-xl border border-sky-200 dark:border-sky-800/80 bg-sky-50/70 dark:bg-sky-950/30 cursor-pointer hover:border-sky-400 transition-all space-y-2"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <Radio className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400 animate-pulse" />
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    {liveSensor.device}
                  </span>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                  iotMode === 'ao_vivo'
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                    : 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                }`}>
                  {iotMode === 'ao_vivo' ? 'Ao Vivo (Node-RED)' : 'Simulado (API)'}
                </span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-300">
                <span>{liveSensor.regiao}</span>
                <RiskBadge
                  level={mapIotRiskLevel(liveSensor.nivel_risco)}
                  label={liveSensor.nivel_risco}
                  size="sm"
                />
              </div>

              <div className="grid grid-cols-3 gap-1.5 text-[10px] text-center">
                <div className="bg-white dark:bg-slate-900/70 p-1.5 rounded-lg border border-slate-200/70 dark:border-slate-800">
                  <span className="text-slate-400 block">Nível Água</span>
                  <strong className="text-slate-800 dark:text-slate-100">{liveSensor.nivel_agua_pct}%</strong>
                </div>
                <div className="bg-white dark:bg-slate-900/70 p-1.5 rounded-lg border border-slate-200/70 dark:border-slate-800">
                  <span className="text-slate-400 block">Chuva</span>
                  <strong className="text-slate-800 dark:text-slate-100">{liveSensor.chuva_pct}%</strong>
                </div>
                <div className="bg-white dark:bg-slate-900/70 p-1.5 rounded-lg border border-slate-200/70 dark:border-slate-800">
                  <span className="text-slate-400 block">Distância</span>
                  <strong className="text-slate-800 dark:text-slate-100">{liveSensor.distancia_cm} cm</strong>
                </div>
              </div>

              {iotMode === 'simulado' && setCenarioFallback && (
                <div
                  onClick={(e) => e.stopPropagation()}
                  className="pt-1.5 border-t border-sky-200/70 dark:border-sky-800/60 flex items-center justify-between gap-1"
                >
                  <span className="text-[10px] text-slate-500 dark:text-slate-400">Cenário:</span>
                  <div className="flex gap-1">
                    {['NORMAL', 'ATENCAO', 'ALERTA'].map((cen) => (
                      <button
                        key={cen}
                        type="button"
                        onClick={() => setCenarioFallback(cen)}
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold transition-colors ${
                          cenarioFallback === cen
                            ? 'bg-sky-600 text-white'
                            : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700'
                        }`}
                      >
                        {cen}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
            Pontos de Risco Cadastrados:
          </h2>

          {filteredReports.map((r) => (
            <div 
              key={r.id}
              onClick={() => handleSelectReport(r)}
              className="p-3 bg-white dark:bg-slate-800/80 rounded-xl border border-slate-200 dark:border-slate-700/80 hover:border-sky-400 dark:hover:border-sky-500 cursor-pointer transition-all hover:shadow-sm"
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-100 line-clamp-1">
                  {r.titulo}
                </span>
                <RiskBadge level={r.nivelRisco} size="sm" />
              </div>

              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-2">
                {r.descricao}
              </p>

              <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 pt-1.5 border-t border-slate-100 dark:border-slate-700/50">
                <span className="flex items-center gap-1 line-clamp-1 max-w-[170px]">
                  <MapPin className="w-3 h-3 text-sky-500 flex-shrink-0" />
                  {r.endereco.split('-')[0]}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedReportForGuidance({
                      titulo: r.titulo,
                      nivelRisco: r.nivelRisco,
                      nivelRiscoLabel: r.nivelRiscoLabel,
                      confianca: r.confiancaVisaoComputacional,
                      orientacao: r.resumoOrientacaoIA,
                      recomendacoesImediatas: [
                        "Consulte as atualizações de tráfego antes de se deslocar.",
                        "Não entre em contato com a água de alagamento.",
                        "Em caso de urgência, ligue 199 (Defesa Civil)."
                      ],
                      fonteOficial: "Defesa Civil SP / Corpus Oficial",
                      origemProcessamento: "Síntese Baseada no Corpus da Defesa Civil"
                    });
                  }}
                  className="inline-flex items-center gap-1 text-sky-600 dark:text-sky-400 hover:underline font-semibold"
                >
                  <Sparkles className="w-3 h-3" />
                  IA Orientação
                </button>
              </div>
            </div>
          ))}

          {filteredReports.length === 0 && (
            <div className="text-center py-8 text-xs text-slate-400">
              Nenhum relato encontrado nesta categoria.
            </div>
          )}
        </div>

        {/* CTA para Registrar Novo Relato */}
        <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
          <Link
            to="/relato/novo"
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs shadow-md shadow-sky-600/30 transition-all hover:scale-[1.01]"
          >
            <Plus className="w-4 h-4" />
            <span>Registrar Novo Relato na Cidade</span>
          </Link>
        </div>

      </aside>

      {/* Área Central: Mapa Interativo com Leaflet */}
      <main className="flex-1 h-[50vh] lg:h-[calc(100vh-4rem)] relative">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          <ChangeMapView center={mapCenter} zoom={mapZoom} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Marcadores dos Relatos de Cidadãos */}
          {filteredReports.map((rep) => {
            const pinColor = getPinColor(rep.nivelRisco);
            return (
              <React.Fragment key={rep.id}>
                {/* Raio visual de impacto para riscos altos */}
                {(rep.nivelRisco === 'critical' || rep.nivelRisco === 'high') && (
                  <Circle
                    center={[rep.lat, rep.lng]}
                    radius={rep.nivelRisco === 'critical' ? 450 : 250}
                    pathOptions={{
                      color: pinColor,
                      fillColor: pinColor,
                      fillOpacity: 0.15,
                      weight: 1.5,
                      dashArray: '4, 4'
                    }}
                  />
                )}

                <Marker
                  position={[rep.lat, rep.lng]}
                  icon={createCustomPin(pinColor, false)}
                >
                  <Popup>
                    <div className="p-1 max-w-[240px]">
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <RiskBadge level={rep.nivelRisco} size="sm" />
                        <span className="text-[10px] text-slate-400 font-mono">
                          {rep.protocolo || 'RC-SP'}
                        </span>
                      </div>
                      <h4 className="font-bold text-xs text-slate-900 mb-1">
                        {rep.titulo}
                      </h4>
                      <p className="text-[11px] text-slate-600 mb-2 leading-relaxed">
                        {rep.descricao}
                      </p>
                      
                      <div className="bg-slate-50 p-2 rounded text-[10px] text-slate-500 mb-2 border border-slate-100">
                        <strong className="block text-slate-700">Visão Computacional:</strong>
                        {rep.tipoDetecao} ({rep.confiancaVisaoComputacional}% confiança)
                      </div>

                      <div className="flex items-center justify-between pt-1 border-t border-slate-200">
                        <button
                          onClick={() => setSelectedReportForGuidance({
                            titulo: rep.titulo,
                            nivelRisco: rep.nivelRisco,
                            nivelRiscoLabel: rep.nivelRiscoLabel,
                            confianca: rep.confiancaVisaoComputacional,
                            orientacao: rep.resumoOrientacaoIA,
                            recomendacoesImediatas: [
                              "Evite transitar no local até a água escoar.",
                              "Não entre em contato com a água de alagamento.",
                              "Emergência ligue 199 (Defesa Civil)."
                            ],
                            fonteOficial: "Corpus Defesa Civil SP",
                            origemProcessamento: "Processamento Inteligente"
                          })}
                          className="text-[11px] font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1"
                        >
                          <Sparkles className="w-3 h-3" /> Ver Orientação IA
                        </button>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              </React.Fragment>
            );
          })}

          {/* Marcador do Sensor Wokwi / Node-RED em Tempo Real */}
          {liveSensor && (() => {
            const liveLevel = mapIotRiskLevel(liveSensor.nivel_risco);
            const liveColor = getPinColor(liveLevel);
            return (
              <React.Fragment>
                {liveSensor.nivel_risco !== 'NORMAL' && (
                  <Circle
                    center={WOKWI_COORDS}
                    radius={liveSensor.nivel_risco === 'ALERTA' ? 400 : 220}
                    pathOptions={{
                      color: liveColor,
                      fillColor: liveColor,
                      fillOpacity: 0.18,
                      weight: 2,
                      dashArray: '4, 4'
                    }}
                  />
                )}
                <Marker
                  position={WOKWI_COORDS}
                  icon={createCustomPin(liveColor, true)}
                >
                  <Popup>
                    <div className="p-1 max-w-[230px]">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-sky-600 font-bold text-xs">
                          <Radio className="w-3.5 h-3.5 animate-pulse" />
                          <span>{liveSensor.device}</span>
                        </div>
                      </div>
                      <p className="text-[11px] text-slate-500 mb-2">{liveSensor.regiao}</p>

                      <div className="grid grid-cols-3 gap-1.5 text-[10px] bg-slate-50 p-2 rounded mb-2 border border-slate-200 text-center">
                        <div>
                          <span className="text-slate-400 block font-semibold">Água</span>
                          <strong className="text-slate-800">{liveSensor.nivel_agua_pct}%</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 block font-semibold">Chuva</span>
                          <strong className="text-slate-800">{liveSensor.chuva_pct}%</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 block font-semibold">Dist.</span>
                          <strong className="text-slate-800">{liveSensor.distancia_cm}cm</strong>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span>{iotMode === 'ao_vivo' ? 'Node-RED Ao Vivo' : 'Fallback Simulado'}</span>
                        <RiskBadge level={liveLevel} label={liveSensor.nivel_risco} size="sm" />
                      </div>
                    </div>
                  </Popup>
                </Marker>
              </React.Fragment>
            );
          })()}

          {/* Marcadores dos Sensores IoT (ESP32) */}
          {sensors.map((sensor) => (
            <Marker
              key={sensor.id}
              position={[sensor.lat, sensor.lng]}
              icon={createCustomPin('#0284c7', true)}
            >
              <Popup>
                <div className="p-1 max-w-[220px]">
                  <div className="flex items-center gap-1.5 text-sky-600 font-bold text-xs mb-1">
                    <Radio className="w-3.5 h-3.5 animate-pulse" />
                    <span>{sensor.nome}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mb-2">{sensor.localizacao}</p>

                  <div className="grid grid-cols-2 gap-2 text-[10px] bg-slate-50 p-2 rounded mb-2 border border-slate-200">
                    <div>
                      <span className="text-slate-400 block font-semibold">Chuva:</span>
                      <strong className="text-slate-800">{sensor.chuvaMmHora} mm/h</strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-semibold">Nível d'água:</span>
                      <strong className="text-slate-800">{sensor.nivelAguaCm} cm</strong>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span>ESP32 (Simulado)</span>
                    <RiskBadge level={sensor.status} label={sensor.statusLabel} size="sm" />
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Legenda Flutuante sobre o Mapa */}
        <div className="absolute bottom-4 right-4 z-[500] bg-white/95 dark:bg-slate-900/95 backdrop-blur-md p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-lg text-[11px] max-w-xs space-y-1.5 hidden sm:block">
          <span className="font-bold text-slate-700 dark:text-slate-200 block uppercase tracking-wider text-[10px]">
            Legenda do Mapa de Risco
          </span>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-600 dark:text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> Emergência
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span> Alerta
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Atenção
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-600"></span> Sensor IoT
            </span>
          </div>
        </div>

      </main>

      {/* Modal de Orientação da Defesa Civil (Etapa 6) */}
      <GuidanceModal
        isOpen={!!selectedReportForGuidance}
        onClose={() => setSelectedReportForGuidance(null)}
        guidanceData={selectedReportForGuidance}
        reportTitle={selectedReportForGuidance?.titulo}
      />

    </div>
  );
}

