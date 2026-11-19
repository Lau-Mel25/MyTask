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

const sinEspera = async () => {};
const opciones = (fetchImpl, extra = {}) => ({
  apiKey: 'clave-de-prueba',
  model: 'modelo-x',
  fetchImpl,
  esperar: sinEspera,
  ...extra,
});
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

describe('reintentos ante fallos temporales de Gemini', () => {
  let consolaError;
  beforeEach(() => {
    consolaError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => consolaError.mockRestore());

  const error503 = { ok: false, status: 503, text: async () => 'alta demanda' };
  const exito = () => respuestaGemini('{"subtareas":["a","b","c"]}');

  test('reintenta tras un 503 y devuelve las subtareas del segundo intento', async () => {
    const fetchImpl = jest.fn().mockResolvedValueOnce(error503).mockResolvedValueOnce(exito());
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).resolves.toEqual(['a', 'b', 'c']);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });

  test('se rinde con IAError despues de 3 intentos seguidos con 503', async () => {
    const fetchImpl = jest.fn().mockResolvedValue(error503);
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });

  test('espera 1 s y luego 2 s entre intentos', async () => {
    const esperar = jest.fn(async () => {});
    const fetchImpl = jest.fn().mockResolvedValue(error503);
    await expect(
      generarSubtareas(tarea, opciones(fetchImpl, { esperar })),
    ).rejects.toBeInstanceOf(IAError);
    expect(esperar.mock.calls.map(([ms]) => ms)).toEqual([1000, 2000]);
  });

  test('reintenta tras un fallo de red', async () => {
    const fetchImpl = jest
      .fn()
      .mockRejectedValueOnce(new Error('ECONNRESET'))
      .mockResolvedValueOnce(exito());
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).resolves.toEqual(['a', 'b', 'c']);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });

  test.each([400, 401, 403, 404, 429])('no reintenta con el estado %i', async (status) => {
    const fetchImpl = jest.fn().mockResolvedValue({ ok: false, status, text: async () => '' });
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  test('no reintenta si Gemini responde bien pero con formato inutilizable', async () => {
    const fetchImpl = jest.fn().mockResolvedValue(respuestaGemini('esto no es json'));
    await expect(generarSubtareas(tarea, opciones(fetchImpl))).rejects.toBeInstanceOf(IAError);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });
});

describe('tiempo limite por intento', () => {
  let consolaError;
  beforeEach(() => {
    consolaError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => consolaError.mockRestore());

  // fetch que nunca responde: solo termina si se aborta la señal que recibe.
  // Si el código no le pasa ninguna señal, se queda colgado para siempre (la prueba falla).
  const colgarHastaAbortar = (_url, init) =>
    new Promise((_resolver, rechazar) => {
      if (init.signal) {
        init.signal.addEventListener('abort', () => rechazar(new Error('abortado por tiempo')));
      }
    });

  test('si Gemini no responde a tiempo, falla con IAError en vez de quedarse esperando', async () => {
    const fetchImpl = jest.fn(colgarHastaAbortar);
    await expect(
      generarSubtareas(tarea, opciones(fetchImpl, { timeoutMs: 20, intentos: 1 })),
    ).rejects.toBeInstanceOf(IAError);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  test('un intento colgado se reintenta y el siguiente puede tener exito', async () => {
    const exito = respuestaGemini('{"subtareas":["a","b","c"]}');
    const fetchImpl = jest
      .fn()
      .mockImplementationOnce(colgarHastaAbortar)
      .mockResolvedValueOnce(exito);
    await expect(
      generarSubtareas(tarea, opciones(fetchImpl, { timeoutMs: 20 })),
    ).resolves.toEqual(['a', 'b', 'c']);
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });
});
