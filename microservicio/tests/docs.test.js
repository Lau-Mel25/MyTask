const fs = require('fs');
const path = require('path');
const request = require('supertest');
const YAML = require('yaml');
const { crearApp } = require('../src/app');

const app = crearApp({ generar: async () => ['a', 'b', 'c'], internalApiKey: 'clave' });
const especificacion = YAML.parse(
  fs.readFileSync(path.join(__dirname, '..', 'openapi.yaml'), 'utf8'),
);

describe('Swagger UI', () => {
  test('GET /api-docs/ responde 200 con HTML y sin clave', async () => {
    const res = await request(app).get('/api-docs/');
    expect(res.status).toBe(200);
    expect(res.headers['content-type']).toMatch(/text\/html/);
  });

  test('GET /openapi.yaml responde 200 con la especificacion', async () => {
    const res = await request(app).get('/openapi.yaml');
    expect(res.status).toBe(200);
    expect(YAML.parse(res.text).openapi).toMatch(/^3\./);
  });
});

describe('openapi.yaml', () => {
  test('declara la version 3.x de OpenAPI', () => {
    expect(especificacion.openapi).toMatch(/^3\./);
  });

  test('documenta /health y POST /api/sugerencias', () => {
    expect(especificacion.paths['/health']).toBeDefined();
    expect(especificacion.paths['/api/sugerencias'].post).toBeDefined();
  });

  test('define el esquema de seguridad ApiKeyAuth en la cabecera X-API-Key', () => {
    const esquema = especificacion.components.securitySchemes.ApiKeyAuth;
    expect(esquema).toMatchObject({ type: 'apiKey', in: 'header', name: 'X-API-Key' });
  });

  test('POST /api/sugerencias documenta 200, 400, 401 y 502 y exige ApiKeyAuth', () => {
    const post = especificacion.paths['/api/sugerencias'].post;
    expect(Object.keys(post.responses)).toEqual(
      expect.arrayContaining(['200', '400', '401', '502']),
    );
    expect(post.security).toEqual([{ ApiKeyAuth: [] }]);
  });
});
