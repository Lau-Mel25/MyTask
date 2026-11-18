const MODELO_POR_DEFECTO = 'gemini-3.6-flash';
const MAX_SUBTAREAS = 6;
const MIN_SUBTAREAS = 3;
const MAX_LARGO = 100;

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
  { apiKey, model = MODELO_POR_DEFECTO, fetchImpl = globalThis.fetch } = {},
) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(
    model,
  )}:generateContent`;

  let respuesta;
  try {
    respuesta = await fetchImpl(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': apiKey },
      body: JSON.stringify({ contents: [{ parts: [{ text: construirPrompt(tarea) }] }] }),
    });
  } catch (e) {
    throw new IAError('No se pudo conectar con la IA.');
  }

  if (!respuesta.ok) {
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
