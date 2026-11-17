import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Camera, 
  MapPin, 
  Sparkles, 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  Upload, 
  Navigation,
  FileCheck2,
  Lock,
  Search
} from 'lucide-react';
import { saveReport } from '../services/storageService';
import { processReportWithAI, simulateVisionAnalysis } from '../services/aiService';
import { fetchAddressByCep, formatCep, geocodeAddress } from '../services/cepService';
import { useAuth } from '../context/AuthContext';
import GuidanceModal from '../components/GuidanceModal';

const SAMPLE_IMAGES = [
  {
    label: "Bueiro com garrafas e lixo",
    url: "https://images.unsplash.com/photo-1618477461853-cf6ed80faba5?auto=format&fit=crop&w=600&q=80",
    categoria: "bueiro_entupido"
  },
  {
    label: "Pista alagada sob chuva",
    url: "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&w=600&q=80",
    categoria: "alagamento_ativo"
  },
  {
    label: "Entulho descartado na sarjeta",
    url: "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?auto=format&fit=crop&w=600&q=80",
    categoria: "lixo_via"
  }
];

export default function NewReportPage() {
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();

  const [formData, setFormData] = useState({
    titulo: '',
    categoria: 'bueiro_entupido',
    categoriaLabel: 'Bueiro Obstruído',
    descricao: '',
    endereco: 'Rua da Consolação, 1300 - Consolação, São Paulo - SP',
    lat: -23.5532,
    lng: -46.6541,
    imageUrl: '',
    termoLgpd: false // Inicia desmarcado para consentimento afirmativo
  });

  const [cepInput, setCepInput] = useState('');
  const [loadingCep, setLoadingCep] = useState(false);
  const [cepNotice, setCepNotice] = useState('');

  const [loading, setLoading] = useState(false);
  const [visionResult, setVisionResult] = useState(null);
  const [aiGuidance, setAiGuidance] = useState(null);
  const [createdReport, setCreatedReport] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleCategoryChange = (e) => {
    const val = e.target.value;
    const labels = {
      bueiro_entupido: 'Bueiro Obstruído',
      alagamento_ativo: 'Ponto de Alagamento',
      lixo_via: 'Lixo / Entulho em Via',
      acumulo_agua: 'Lâmina de Água em Pista'
    };
    setFormData(prev => ({
      ...prev,
      categoria: val,
      categoriaLabel: labels[val] || val
    }));
  };

  const handleUseCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setFormData(prev => ({
            ...prev,
            lat: Number(pos.coords.latitude.toFixed(4)),
            lng: Number(pos.coords.longitude.toFixed(4)),
            endereco: `Localização GPS detectada (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}) - São Paulo - SP`
          }));
        },
        () => {
          // Fallback para ponto de SP se permissão for negada
          setFormData(prev => ({
            ...prev,
            lat: -23.5505,
            lng: -46.6333,
            endereco: "Praça da Sé, Centro Histórico de São Paulo - SP"
          }));
        }
      );
    }
  };

  const handleCepSearch = async (e) => {
    const formatted = formatCep(e.target.value);
    setCepInput(formatted);
    setCepNotice('');

    const clean = formatted.replace(/\D/g, '');
    if (clean.length === 8) {
      setLoadingCep(true);
      setErrorMsg('');
      try {
        const addr = await fetchAddressByCep(clean);
        const fullAddr = `${addr.logradouro ? addr.logradouro + ' - ' : ''}${addr.bairro}, ${addr.cidade} - ${addr.uf}`;
        const coords = await geocodeAddress(addr);
        setFormData(prev => ({
          ...prev,
          endereco: fullAddr,
          ...(coords ? { lat: coords.lat, lng: coords.lng } : {})
        }));
        setCepNotice(
          coords
            ? `Endereço e coordenadas do mapa localizados via CEP: ${addr.bairro}, ${addr.cidade}`
            : `Endereço localizado via CEP: ${addr.bairro}, ${addr.cidade}`
        );
      } catch (err) {
        setErrorMsg(err.message || 'Falha ao buscar CEP.');
      } finally {
        setLoadingCep(false);
      }
    }
  };

  const handleImageFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData(prev => ({ ...prev, imageUrl: reader.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!formData.titulo.trim() || !formData.descricao.trim()) {
      setErrorMsg('Por favor, preencha o título e a descrição do relato.');
      return;
    }

    if (!formData.termoLgpd) {
      setErrorMsg('É obrigatório concordar com o termo de proteção de dados (LGPD) para enviar o relato.');
      return;
    }

    setLoading(true);

    try {
      // 1. Simulação da Etapa 2: Detector de Visão Computacional na imagem
      const vision = simulateVisionAnalysis(formData.categoria);
      setVisionResult(vision);

      // 2. Etapa 6: Processamento Inteligente via IA (NVIDIA NIM / Fallback Defesa Civil)
      const guidance = await processReportWithAI({
        titulo: formData.titulo,
        categoria: formData.categoria,
        categoriaLabel: formData.categoriaLabel,
        descricao: formData.descricao,
        endereco: formData.endereco
      });

      // 3. Estruturação do novo Relato para persistência
      const reportId = `rel-${Date.now().toString().slice(-5)}`;
      const protocol = `RC-2026-${Math.floor(10000 + Math.random() * 90000)}`;

      const newReport = {
        id: reportId,
        titulo: formData.titulo,
        categoria: formData.categoria,
        categoriaLabel: formData.categoriaLabel,
        descricao: formData.descricao,
        endereco: formData.endereco,
        lat: formData.lat,
        lng: formData.lng,
        imageUrl: formData.imageUrl || SAMPLE_IMAGES[0].url,
        dataHora: new Date().toISOString(),
        status: "confirmado_sensor",
        statusLabel: "Confirmado por Sensores",
        nivelRisco: guidance.nivelRisco,
        nivelRiscoLabel: guidance.nivelRiscoLabel,
        autorAnonimo: currentUser ? `Cidadão Colaborador (${currentUser.bairro})` : "Cidadão Anônimo",
        confiancaVisaoComputacional: vision.taxaConfianca,
        tipoDetecao: vision.tipoObjeto,
        resumoOrientacaoIA: guidance.orientacao,
        encaminhamentoStatus: "Encaminhado para a Subprefeitura e Defesa Civil",
        protocolo: protocol
      };

      // 4. Persistência no navegador (localStorage)
      saveReport(newReport);
      setCreatedReport(newReport);
      setAiGuidance(guidance);

    } catch (err) {
      console.error(err);
      setErrorMsg('Ocorreu uma falha no processamento do relato.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Título e Contextualização */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sky-600 dark:text-sky-400 text-xs font-bold uppercase tracking-wider mb-1">
          <ShieldCheck className="w-4 h-4" />
          <span>Etapa 1 do Fluxo • Zeladoria Colaborativa</span>
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
          Registrar Novo Relato na Cidade
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Informe bueiros obstruídos, acúmulo de lixo ou pontos de alagamento. Os dados passam por detecção visual e geram orientações imediatas de segurança da Defesa Civil.
        </p>

        {currentUser && (
          <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs text-slate-600 dark:text-slate-300">
            <span>Relatando como: <strong>{currentUser.nome}</strong> (Bairro: {currentUser.bairro})</span>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 flex items-center gap-3 text-red-700 dark:text-red-300 text-xs font-semibold">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Formulário Principal */}
      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 sm:p-8 space-y-6">
        
        {/* Título do Relato */}
        <div>
          <label htmlFor="titulo" className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
            Título do Relato *
          </label>
          <input
            id="titulo"
            type="text"
            required
            placeholder="Ex.: Bueiro obstruído com garrafas e terra na sarjeta"
            value={formData.titulo}
            onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-sky-500 outline-none transition-all"
          />
        </div>

        {/* Categoria */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="categoria" className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
              Categoria do Problema *
            </label>
            <select
              id="categoria"
              value={formData.categoria}
              onChange={handleCategoryChange}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-sky-500 outline-none transition-all"
            >
              <option value="bueiro_entupido">Bueiro Obstruído por Lixo ou Resíduos</option>
              <option value="alagamento_ativo">Ponto de Alagamento Transitável / Intransitável</option>
              <option value="lixo_via">Acúmulo de Lixo / Entulho em Via Pública</option>
              <option value="acumulo_agua">Lâmina de Água em Pista de Rolamento</option>
            </select>
          </div>

          {/* Busca por CEP (ViaCEP) */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Preencher por CEP (ViaCEP)
              </label>
              {loadingCep && (
                <span className="text-[10px] text-sky-600 dark:text-sky-400 flex items-center gap-1">
                  <div className="w-2.5 h-2.5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                  Consultando...
                </span>
              )}
            </div>
            <div className="relative">
              <input
                type="text"
                maxLength={9}
                placeholder="Ex.: 01001-000 (Opcional)"
                value={cepInput}
                onChange={handleCepSearch}
                className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-sky-500 outline-none transition-all"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
            </div>
          </div>
        </div>

        {/* Endereço / Localização */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label htmlFor="endereco" className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Endereço Completo do Relato *
            </label>
            <button
              type="button"
              onClick={handleUseCurrentLocation}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-sky-600 dark:text-sky-400 hover:underline"
            >
              <Navigation className="w-3 h-3" /> Usar GPS
            </button>
          </div>
          <div className="relative">
            <input
              id="endereco"
              type="text"
              required
              value={formData.endereco}
              onChange={(e) => setFormData({ ...formData, endereco: e.target.value })}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-sky-500 outline-none transition-all"
            />
            <MapPin className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
          </div>
          {cepNotice && (
            <p className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> {cepNotice}
            </p>
          )}
        </div>

        {/* Upload de Imagem e Amostras Rápidas */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
            Foto do Local (Detecção de Imagem - Etapa 2)
          </label>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
            {/* Input de arquivo */}
            <label className="md:col-span-1 border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-sky-500 dark:hover:border-sky-400 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer bg-slate-50 dark:bg-slate-800/40 hover:bg-sky-50/50 transition-colors text-center">
              <Upload className="w-6 h-6 text-slate-400 mb-1" />
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Carregar Foto</span>
              <span className="text-[10px] text-slate-400">PNG, JPG até 5MB</span>
              <input type="file" accept="image/*" onChange={handleImageFileChange} className="hidden" />
            </label>

            {/* Amostras Rápidas da Demonstração */}
            <div className="md:col-span-2 flex flex-col justify-center bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Ou selecione uma foto de teste da demonstração:
              </span>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_IMAGES.map((img, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setFormData(prev => ({
                        ...prev,
                        imageUrl: img.url,
                        categoria: img.categoria
                      }));
                    }}
                    className={`text-xs px-2.5 py-1.5 rounded-lg border text-left transition-all flex items-center gap-1.5 ${
                      formData.imageUrl === img.url
                        ? 'border-sky-600 bg-sky-50 dark:bg-sky-950 text-sky-700 dark:text-sky-300 font-bold'
                        : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100'
                    }`}
                  >
                    <Camera className="w-3.5 h-3.5 text-slate-400" />
                    <span>{img.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Pré-visualização da imagem selecionada */}
          {formData.imageUrl && (
            <div className="relative mt-2 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 max-h-48 bg-slate-100">
              <img src={formData.imageUrl} alt="Foto do relato" className="w-full h-48 object-cover" />
              <span className="absolute bottom-2 left-2 bg-slate-900/80 text-white text-[10px] px-2 py-0.5 rounded backdrop-blur-sm">
                Foto vinculada ao relato
              </span>
            </div>
          )}
        </div>

        {/* Descrição Detalhada */}
        <div>
          <label htmlFor="descricao" className="block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
            Descrição da Situação *
          </label>
          <textarea
            id="descricao"
            required
            rows={3}
            placeholder="Descreva o que está ocorrendo (ex: água cobrindo sarjeta, refluxo de esgoto, lixo acumulado impedindo escoamento)..."
            value={formData.descricao}
            onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-sky-500 outline-none transition-all"
          />
        </div>

        {/* Termo de Consentimento LGPD - Inicia desmarcado para consentimento ativo */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.termoLgpd}
              onChange={(e) => setFormData({ ...formData, termoLgpd: e.target.checked })}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500 cursor-pointer"
            />
            <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              <span className="font-bold text-slate-800 dark:text-white flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-sky-600" /> Consentimento e Proteção de Dados (LGPD) <span className="text-red-500 font-bold">*</span>
              </span>
              Concordo em compartilhar as informações deste relato para monitoramento de risco e zeladoria urbana. Compreendo que meu nome não será exposto publicamente no mapa e os dados não serão utilizados para vigilância ou monitoramento pessoal.
            </div>
          </label>
        </div>

        {/* Botão de Envio */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-xs text-slate-400">
            * Processamento inteligente em conformidade com as diretrizes da Defesa Civil SP.
          </span>

          <button
            type="submit"
            disabled={loading}
            className={`w-full sm:w-auto px-6 py-3 rounded-xl font-bold text-xs text-white shadow-lg transition-all flex items-center justify-center gap-2 ${
              loading 
                ? 'bg-slate-400 cursor-not-allowed' 
                : 'bg-sky-600 hover:bg-sky-700 shadow-sky-600/30 hover:scale-[1.02]'
            }`}
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Processando com Visão Computacional e IA...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Processar e Enviar Relato</span>
              </>
            )}
          </button>
        </div>

      </form>

      {/* Modal de Orientação da Defesa Civil pós-envio */}
      <GuidanceModal
        isOpen={!!aiGuidance}
        onClose={() => {
          setAiGuidance(null);
          navigate('/mapa');
        }}
        guidanceData={aiGuidance}
        reportTitle={createdReport?.titulo}
      />

    </div>
  );
}
