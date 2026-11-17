/**
 * Dados sintéticos iniciais para o Radar Cidadão (São Paulo)
 * Alinhados com as Etapas 1, 3, 5 e 7 do fluxo e diretrizes do CGE / Defesa Civil de SP.
 */

export const INITIAL_REPORTS = [
  {
    id: "rel-001",
    titulo: "Bueiro completamente obstruído com sacos plásticos",
    categoria: "bueiro_entupido",
    categoriaLabel: "Bueiro Obstruído",
    descricao: "Boca de lobo entupida com garrafas PET e sacolas plásticas. Água começa a empossar na sarjeta.",
    endereco: "Av. do Estado, 4500 - Cambuci, São Paulo - SP",
    lat: -23.5631,
    lng: -46.6212,
    dataHora: "2026-11-12T14:30:00Z",
    status: "confirmado_sensor",
    statusLabel: "Confirmado por Sensores",
    nivelRisco: "moderate",
    nivelRiscoLabel: "Atenção",
    autorAnonimo: "Cidadão Colaborador #1204",
    confiancaVisaoComputacional: 92.4, // Detecção de lixo em via pública
    tipoDetecao: "Lixo e resíduos sólidos em boca de lobo",
    resumoOrientacaoIA: "Evite contato com a água de escoamento superficial. Mantenha distância do meio-fio para evitar bueiros destampados ou bueiros com refluxo.",
    encaminhamentoStatus: "Protocolado Subprefeitura Mooca",
    protocolo: "RC-2026-08912"
  },
  {
    id: "rel-002",
    titulo: "Lâmina d'água cobrindo calçada na Praça da Bandeira",
    categoria: "alagamento_ativo",
    categoriaLabel: "Ponto de Alagamento",
    descricao: "Água acumulada atinge cerca de 25 cm. Veículos baixos estão com dificuldade de transitar.",
    endereco: "Praça da Bandeira, Centro Histórico de São Paulo - SP",
    lat: -23.5489,
    lng: -46.6401,
    dataHora: "2026-11-12T15:10:00Z",
    status: "confirmado_sensor",
    statusLabel: "Confirmado por Sensores",
    nivelRisco: "high",
    nivelRiscoLabel: "Alerta",
    autorAnonimo: "Cidadão Colaborador #0942",
    confiancaVisaoComputacional: 95.8,
    tipoDetecao: "Lâmina de alagamento em pista de rolamento",
    resumoOrientacaoIA: "Não tente atravessar a via a pé ou com veículo de passeio. Uma lâmina de 15 cm pode arrastar pedestres e 30 cm arrasta automóveis.",
    encaminhamentoStatus: "Encaminhado Defesa Civil / CET",
    protocolo: "RC-2026-08915"
  },
  {
    id: "rel-003",
    titulo: "Descarte irregular de entulho em via pública próximo a córrego",
    categoria: "lixo_via",
    categoriaLabel: "Lixo / Entulho em Via",
    descricao: "Restos de construção civil e madeiras depositados na sarjeta, risco de bloquear o escoamento no início da chuva.",
    endereco: "Av. Aricanduva, 2800 - Vila Matilde, São Paulo - SP",
    lat: -23.5512,
    lng: -46.5218,
    dataHora: "2026-11-12T11:45:00Z",
    status: "encaminhado",
    statusLabel: "Encaminhado ao Poder Público",
    nivelRisco: "low",
    nivelRiscoLabel: "Preventivo",
    autorAnonimo: "Cidadão Colaborador #3310",
    confiancaVisaoComputacional: 88.2,
    tipoDetecao: "Entulho de alvenaria e galhos",
    resumoOrientacaoIA: "Ação preventiva registrada. Os dados foram consolidados no lote de limpeza programada da subprefeitura.",
    encaminhamentoStatus: "Em fila de zeladoria urbana",
    protocolo: "RC-2026-08890"
  },
  {
    id: "rel-004",
    titulo: "Alagamento intransitável na baixada da Marginal Tietê",
    categoria: "alagamento_ativo",
    categoriaLabel: "Alagamento Intransitável",
    descricao: "Nível da água acima do eixo dos ônibus. Pista local totalmente bloqueada.",
    endereco: "Marginal Tietê, próximo à Ponte das Bandeiras - Bom Retiro, São Paulo - SP",
    lat: -23.5186,
    lng: -46.6264,
    dataHora: "2026-11-12T16:05:00Z",
    status: "confirmado_sensor",
    statusLabel: "Confirmado por Sensores",
    nivelRisco: "critical",
    nivelRiscoLabel: "Emergência",
    autorAnonimo: "Cidadão Colaborador #7741",
    confiancaVisaoComputacional: 98.1,
    tipoDetecao: "Alagamento severo com via bloqueada",
    resumoOrientacaoIA: "Área de risco crítico. Permaneça em local elevado e seguro. Não tente manobrar contra a correnteza. Ligue 199 (Defesa Civil) ou 193 (Bombeiros) se houver pessoas ilhadas.",
    encaminhamentoStatus: "Encaminhamento prioritário emitido",
    protocolo: "RC-2026-08920"
  }
];

export const INITIAL_SENSORS = [
  {
    id: "esp32-sp-01",
    nome: "Sensor Anhangabaú / Centro",
    localizacao: "Vale do Anhangabaú, SP",
    lat: -23.5468,
    lng: -46.6385,
    chuvaMmHora: 28.5,
    nivelAguaCm: 32.0,
    status: "high",
    statusLabel: "Alerta de Alagamento",
    ultimaAtualizacao: "há 2 minutos",
    bateriaPercent: 94
  },
  {
    id: "esp32-sp-02",
    nome: "Sensor Cambuci / Av. do Estado",
    localizacao: "Av. do Estado x Rua da Mooca",
    lat: -23.5590,
    lng: -46.6230,
    chuvaMmHora: 14.0,
    nivelAguaCm: 18.5,
    status: "moderate",
    statusLabel: "Atenção (Lâmina em elevação)",
    ultimaAtualizacao: "há 4 minutos",
    bateriaPercent: 88
  },
  {
    id: "esp32-sp-03",
    nome: "Sensor Marginal Tietê / Pte. Bandeiras",
    localizacao: "Marginal Tietê, km 14",
    lat: -23.5186,
    lng: -46.6264,
    chuvaMmHora: 42.0,
    nivelAguaCm: 55.0,
    status: "critical",
    statusLabel: "Emergência (Transbordamento)",
    ultimaAtualizacao: "há 1 minuto",
    bateriaPercent: 82
  },
  {
    id: "esp32-sp-04",
    nome: "Sensor Aricanduva / Córrego",
    localizacao: "Av. Aricanduva x Radial Leste",
    lat: -23.5480,
    lng: -46.5190,
    chuvaMmHora: 6.0,
    nivelAguaCm: 8.0,
    status: "low",
    statusLabel: "Normal / Estável",
    ultimaAtualizacao: "há 8 minutos",
    bateriaPercent: 99
  }
];

export const INITIAL_ALERTS = [
  {
    id: "alt-01",
    titulo: "Estado de Alerta para Alagamentos na Bacia do Rio Tietê",
    regiao: "Zona Norte e Centro",
    severidade: "critical",
    severidadeLabel: "Emergência Hidrológica",
    mensagem: "Chuva torrencial contínua atinge a bacia do Tietê. Risco crítico de transbordamento de córregos afluentes na região da Ponte das Bandeiras e Anhembi. Evite deslocamentos pela pista local.",
    dataHora: "2026-11-12T16:00:00Z",
    orgaoEmissor: "Defesa Civil do Município de São Paulo",
    recomendacoes: [
      "Não enfrente correnteza com automóveis ou a pé.",
      "Desconecte aparelhos elétricos caso a água ameace invadir a residência.",
      "Em caso de perigo imediato, ligue 199 (Defesa Civil) ou 193 (Corpo de Bombeiros)."
    ]
  },
  {
    id: "alt-02",
    titulo: "Estado de Atenção na Subprefeitura Mooca e Cambuci",
    regiao: "Zona Sudeste e Ipiranga",
    severidade: "moderate",
    severidadeLabel: "Atenção",
    mensagem: "Acúmulo de água registrado na Av. do Estado próximo aos viadutos. Trânsito lento e lâminas d'água na faixa da direita.",
    dataHora: "2026-11-12T15:20:00Z",
    orgaoEmissor: "Centro de Gerenciamento de Emergências (CGE-SP)",
    recomendacoes: [
      "Reduza a velocidade do veículo e aumente a distância do carro à frente.",
      "Não estacione próximo a árvores ou postes sujeitos a encharcamento de solo."
    ]
  }
];

