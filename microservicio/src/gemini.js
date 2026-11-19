const MODELO_POR_DEFECTO = 'gemini-3.8-flash';
const MAX_SUBTAREAS = 6;
const MIN_SUBTAREAS = 3;
const MAX_LARGO = 100;
const MAX_INTENTOS = 3;
const ESPERA_BASE_MS = 1000;
// Cada intento espera a Gemini como máximo 8 s: 3 intentos + esperas (1 s y 2 s) ≈ 27 s.
// Así la respuesta llega antes de que parezca colgada y sigue por debajo del
// tiempo límite de Django (SUGERENCIAS_TIMEOUT = 60 s).
const TIMEOUT_INTENTO_MS = 8000;
const ESTADOS_REINTENTABLES = new Set([500, 502, 503, 504]);

class IAError extends Error {
  constructor(mensaje) {
    super(mensaje);
    this.name = 'IAError';
  }
}

function construirPrompt({ titulo, descripcion }) {
  const detalle = descripcion ? `\nDescripción: ${descripcion}` : '';
  return (
    'Eres un asistente que ayuda a empezar tareas dividiéndolas en pasos concretos.\n' +
    `Tarea: ${titulo}${detalle}\n\n` +
    `Propón entre ${MIN_SUBTAREAS} y ${MAX_SUBTAREAS} subtareas en español, cortas ` +
    `(máximo ${MAX_LARGO} caracteres cada una), accionables y en orden.\n` +
    'Responde SOLO con un JSON con esta forma exacta, sin texto adicional: ' +
    '{"subtareas": ["paso 1", "paso 2", "paso 3"]}'
  );
}

function extraerJson(texto) {
  const inicio = texto.indexOf('{');
  const fin = texto.lastIndexOf('}');
  if (inicio === -1 || fin <= inicio) {
    throw new IAError('La IA no devolvió un formato válido.');
  }
  try {
    return JSON.parse(texto.slice(inicio, fin + 1));
  } catch (e) {
    throw new IAError('La IA no devolvió un formato válido.');
  }
}

function limpiar(subtareas) {
  if (!Array.isArray(subtareas)) {
    throw new IAError('La IA no devolvió subtareas.');
  }
  const limpias = subtareas
    .filter((s) => typeof s === 'string')
    .map((s) => s.trim().slice(0, MAX_LARGO))
    .filter((s) => s.length > 0)
    .slice(0, MAX_SUBTAREAS);
  if (limpias.length < MIN_SUBTAREAS) {
    throw new IAError('La IA no devolvió suficientes subtareas.');
  }
  return limpias;
}

async function generarSubtareas(
  tarea,
  {
    apiKey,
    model = MODELO_POR_DEFECTO,
    fetchImpl = globalThis.fetch,
    esperar = (ms) => new Promise((resolver) => setTimeout(resolver, ms)),
    intentos = MAX_INTENTOS,
    timeoutMs = TIMEOUT_INTENTO_MS,
  } = {},
) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(
    model,
  )}:generateContent`;

  const peticion = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-goog-api-key': apiKey },
    body: JSON.stringify({ contents: [{ parts: [{ text: construirPrompt(tarea) }] }] }),
  };

  // Gemini a veces responde 503 por exceso de demanda: se reintenta con espera creciente
  // (1 s, 2 s). Los errores permanentes (clave, modelo, límite) no se reintentan.
  let respuesta;
  for (let intento = 1; ; intento += 1) {
    const hayMasIntentos = intento < intentos;
    try {
      respuesta = await fetchImpl(url, { ...peticion, signal: AbortSignal.timeout(timeoutMs) });
    } catch (e) {
      console.error(`No se pudo conectar con Gemini (intento ${intento}):`, e.message);
      if (hayMasIntentos) {
        await esperar(ESPERA_BASE_MS * 2 ** (intento - 1));
        continue;
      }
      throw new IAError('No se pudo conectar con la IA.');
    }
    if (respuesta.ok) break;

    const detalle =
      typeof respuesta.text === 'function' ? await respuesta.text().catch(() => '') : '';
    console.error(
      `Gemini respondió HTTP ${respuesta.status} (intento ${intento}):`,
      detalle.slice(0, 500),
    );
    if (ESTADOS_REINTENTABLES.has(respuesta.status) && hayMasIntentos) {
      await esperar(ESPERA_BASE_MS * 2 ** (intento - 1));
      continue;
    }
    throw new IAError(
      respuesta.status === 429
        ? 'La IA alcanzó su límite de uso. Intenta de nuevo en un momento.'
        : 'La IA no está disponible en este momento.',
    );
  }

  let cuerpo;
  try {
    cuerpo = await respuesta.json();
  } catch (e) {
    throw new IAError('La IA devolvió una respuesta ilegible.');
  }
  const texto = cuerpo?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (typeof texto !== 'string') {
    throw new IAError('La IA devolvió una respuesta vacía.');
  }
  return limpiar(extraerJson(texto).subtareas);
}

module.exports = { generarSubtareas, IAError, MODELO_POR_DEFECTO };
