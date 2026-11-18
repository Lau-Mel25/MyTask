const request = require('supertest');
const { crearApp } = require('../src/app');
const { IAError } = require('../src/gemini');

const CLAVE = 'clave-interna-de-prueba';

function appCon(generar) {
  return crearApp({ generar, internalApiKey: CLAVE });
}

const generarOk = () => jest.fn(async () => ['paso 1', 'paso 2', 'paso 3']);

const post = (app, cuerpo, clave = CLAVE) => {
  const req = request(app).post('/api/sugerencias');
  if (clave !== null) req.set('X-API-Key', clave);
  return req.send(cuerpo);
};

describe('GET /health', () => {
  test('responde 200 con estado ok y sin clave', async () => {
    const res = await request(appCon(generarOk())).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ estado: 'ok' });
  });
});

describe('POST /api/sugerencias: autenticacion', () => {
  test('sin X-API-Key responde 401 y no llama a la IA', async () => {
    const generar = generarOk();
    const res = await post(appCon(generar), { titulo: 'Estudiar' }, null);
    expect(res.status).toBe(401);
    expect(res.body.error).toEqual(expect.any(String));
    expect(generar).not.toHaveBeenCalled();
  });

  test('con clave incorrecta responde 401 y no llama a la IA', async () => {
    const generar = generarOk();
    const res = await post(appCon(generar), { titulo: 'Estudiar' }, 'otra-clave');
    expect(res.status).toBe(401);
    expect(generar).not.toHaveBeenCalled();
  });
});

describe('POST /api/sugerencias: exito', () => {
  test('devuelve tarea y subtareas', async () => {
    const generar = generarOk();
    const res = await post(appCon(generar), { titulo: 'Estudiar', descripcion: 'Parcial' });
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ tarea: 'Estudiar', subtareas: ['paso 1', 'paso 2', 'paso 3'] });
    expect(generar).toHaveBeenCalledWith({ titulo: 'Estudiar', descripcion: 'Parcial' });
  });

  test('un titulo con emojis y acentos llega intacto a la IA', async () => {
    const generar = generarOk();
    const titulo = 'Organizar fiesta 🎉 de cumpleaños';
    const res = await post(appCon(generar), { titulo });
    expect(res.status).toBe(200);
    expect(generar).toHaveBeenCalledWith({ titulo, descripcion: '' });
  });
});

describe('POST /api/sugerencias: validacion', () => {
  test.each([
    ['titulo ausente', {}],
    ['titulo vacio', { titulo: '' }],
    ['titulo solo con espacios', { titulo: '    ' }],
    ['titulo que no es texto', { titulo: 123 }],
    ['titulo de 101 caracteres', { titulo: 'x'.repeat(101) }],
    ['descripcion de 1001 caracteres', { titulo: 'ok', descripcion: 'x'.repeat(1001) }],
    ['descripcion que no es texto', { titulo: 'ok', descripcion: 5 }],
  ])('%s responde 400', async (_nombre, cuerpo) => {
    const generar = generarOk();
    const res = await post(appCon(generar), cuerpo);
    expect(res.status).toBe(400);
    expect(res.body.error).toEqual(expect.any(String));
    expect(generar).not.toHaveBeenCalled();
  });

  test('un cuerpo que no es JSON responde 400', async () => {
    const res = await request(appCon(generarOk()))
      .post('/api/sugerencias')
      .set('X-API-Key', CLAVE)
      .set('Content-Type', 'application/json')
      .send('{esto no es json');
    expect(res.status).toBe(400);
    expect(res.body.error).toEqual(expect.any(String));
  });
});

describe('POST /api/sugerencias: fallos de la IA', () => {
  test('IAError responde 502 con el mensaje en espanol', async () => {
    const generar = jest.fn(async () => {
      throw new IAError('La IA no está disponible en este momento.');
    });
    const res = await post(appCon(generar), { titulo: 'Estudiar' });
    expect(res.status).toBe(502);
    expect(res.body).toEqual({ error: 'La IA no está disponible en este momento.' });
  });

  test('cualquier otro error tambien responde 502, nunca 500', async () => {
    const generar = jest.fn(async () => {
      throw new TypeError('algo inesperado');
    });
    const res = await post(appCon(generar), { titulo: 'Estudiar' });
    expect(res.status).toBe(502);
    expect(res.body.error).toEqual(expect.any(String));
  });
});

describe('crearApp', () => {
  test('sin clave interna configurada lanza error', () => {
    expect(() => crearApp({ generar: generarOk(), internalApiKey: '' })).toThrow();
  });
});
