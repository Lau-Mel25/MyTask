const { generarSubtareas, IAError } = require('../src/gemini');

function respuestaGemini(texto, { ok = true, status = 200 } = {}) {
  return {
    ok,
    status,
    json: async () => ({ candidates: [{ content: { parts: [{ text: texto }] } }] }),
  };
}

function fetchQueDevuelve(respuesta) {
  const fn = jest.fn(async () => respuesta);
  return fn;
}

const opciones = (fetchImpl) => ({ apiKey: 'clave-de-prueba', model: 'modelo-x', fetchImpl });
const tarea = { titulo: 'Preparar el informe', descripcion: 'Entrega del viernes' };

describe('generarSubtareas', () => {
  test('devuelve la lista de subtareas cuando Gemini responde JSON valido', async () => {
    const fetchImpl = fetchQueDevuelve(respuestaGemini('{"subtareas":["a","b","c"]}'));
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).resolves.toEqual(['a', 'b', 'c']);
  });

  test('recorta a 6 elementos, a 100 caracteres y descarta vacios', async () => {
    const largo = 'x'.repeat(150);
    const items = ['uno', '', '   ', largo, 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete'];
    const fetchImpl = fetchQueDevuelve(respuestaGemini(JSON.stringify({ subtareas: items })));
    const resultado = await generarSubtareas(tarea, opciones(fetchImpl));
    expect(resultado).toHaveLength(6);
    expect(resultado).not.toContain('');
    expect(resultado[1]).toHaveLength(100);
    expect(resultado.every((s) => s.length <= 100)).toBe(true);
  });

  test('acepta el JSON aunque venga dentro de un bloque de codigo markdown', async () => {
    const texto = 'Aqui tienes:\n```json\n{"subtareas":["a","b","c"]}\n```';
    const fetchImpl = fetchQueDevuelve(respuestaGemini(texto));
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).resolves.toEqual(['a', 'b', 'c']);
  });

  test('lanza IAError si Gemini responde 429', async () => {
    const fetchImpl = fetchQueDevuelve({ ok: false, status: 429, json: async () => ({}) });
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
  });

  test('lanza IAError si Gemini responde 500', async () => {
    const fetchImpl = fetchQueDevuelve({ ok: false, status: 500, json: async () => ({}) });
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
  });

  test('lanza IAError si falla la red', async () => {
    const fetchImpl = jest.fn(async () => {
      throw new Error('ECONNRESET');
    });
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
  });

  test('lanza IAError si el texto no es JSON', async () => {
    const fetchImpl = fetchQueDevuelve(respuestaGemini('esto no es json'));
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
  });

  test('lanza IAError si el JSON no trae subtareas', async () => {
    const fetchImpl = fetchQueDevuelve(respuestaGemini('{"otra":"cosa"}'));
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
  });

  test('lanza IAError si quedan menos de 3 subtareas utiles', async () => {
    const fetchImpl = fetchQueDevuelve(respuestaGemini('{"subtareas":["a","","  "]}'));
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
  });

  test('envia la clave en la cabecera x-goog-api-key y no en la URL', async () => {
    const fetchImpl = fetchQueDevuelve(respuestaGemini('{"subtareas":["a","b","c"]}'));
    await generarSubtareas(tarea, opciones(fetchImpl));
    const [url, init] = fetchImpl.mock.calls[0];
    expect(init.headers['x-goog-api-key']).toBe('clave-de-prueba');
    expect(url).not.toContain('clave-de-prueba');
    expect(url).toContain('modelo-x');
  });
});

describe('registro de fallos en consola', () => {
  let consolaError;
  beforeEach(() => {
    consolaError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => consolaError.mockRestore());

  test('registra el estado y el cuerpo cuando Gemini responde con error', async () => {
    const fetchImpl = fetchQueDevuelve({
      ok: false,
      status: 404,
      text: async () => '{"error":{"message":"modelo no encontrado"}}',
    });
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
    const salida = consolaError.mock.calls.flat().join(' ');
    expect(salida).toContain('404');
    expect(salida).toContain('modelo no encontrado');
  });

  test('registra el motivo cuando falla la red', async () => {
    const fetchImpl = jest.fn(async () => {
      throw new Error('ECONNRESET');
    });
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
    expect(consolaError.mock.calls.flat().join(' ')).toContain('ECONNRESET');
  });
});
