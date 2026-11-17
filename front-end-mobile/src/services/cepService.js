/**
 * Serviço de Integração com o ViaCEP
 * API pública gratuita brasileira para geolocalização e preenchimento de endereços.
 */

export async function fetchAddressByCep(cep) {
  const clean = cep.replace(/\D/g, '');
  
  if (clean.length !== 8) {
    throw new Error('O CEP deve conter exatamente 8 dígitos.');
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

    const response = await fetch(`https://viacep.com.br/ws/${clean}/json/`, {
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error('Serviço de CEP temporariamente indisponível.');
    }

    const data = await response.json();

    if (data.erro) {
      throw new Error('CEP não encontrado na base dos Correios.');
    }

    return {
      logradouro: data.logradouro || '',
      bairro: data.bairro || '',
      cidade: data.localidade || 'São Paulo',
      uf: data.uf || 'SP',
      cep: data.cep
    };
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Tempo limite excedido ao consultar o CEP.');
    }
    throw error;
  }
}

/**
 * Geocodifica um endereço para latitude e longitude via Nominatim (OpenStreetMap)
 */
export async function geocodeAddress({ logradouro, bairro, cidade, uf, cep }) {
  const queries = [
    [logradouro, bairro, cidade, uf, 'Brasil'].filter(Boolean).join(', '),
    [bairro, cidade, uf, 'Brasil'].filter(Boolean).join(', '),
    cep ? `${cep}, Brasil` : null
  ].filter(Boolean);

  for (const q of queries) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(q)}`;
      const response = await fetch(url, {
        signal: controller.signal,
        headers: { 'Accept-Language': 'pt-BR' }
      });

      clearTimeout(timeoutId);

      if (!response.ok) continue;
      const results = await response.json();
      if (results && results.length > 0) {
        return {
          lat: Number(parseFloat(results[0].lat).toFixed(6)),
          lng: Number(parseFloat(results[0].lon).toFixed(6))
        };
      }
    } catch {
      // Tenta próxima query ou segue sem travar o formulário
    }
  }

  return null;
}

/**
 * Aplica máscara de CEP (00000-000)
 */
export function formatCep(value) {
  return value
    .replace(/\D/g, '')
    .slice(0, 8)
    .replace(/^(\d{5})(\d)/, '$1-$2');
}

