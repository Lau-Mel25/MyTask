const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const express = require('express');
const swaggerUi = require('swagger-ui-express');
const YAML = require('yaml');
const { generarSubtareas, IAError } = require('./gemini');

const MAX_TITULO = 100;
const MAX_DESCRIPCION = 1000;

function clavesIguales(recibida, esperada) {
  const a = crypto.createHash('sha256').update(String(recibida || '')).digest();
  const b = crypto.createHash('sha256').update(String(esperada)).digest();
  return crypto.timingSafeEqual(a, b);
}

function validar(cuerpo) {
  const { titulo, descripcion } = cuerpo || {};
  if (typeof titulo !== 'string' || titulo.trim() === '') {
    return { error: 'El título es obligatorio.' };
  }
  if (titulo.trim().length > MAX_TITULO) {
    return { error: `El título no puede superar ${MAX_TITULO} caracteres.` };
  }
  if (descripcion !== undefined && typeof descripcion !== 'string') {
    return { error: 'La descripción debe ser texto.' };
  }
  const desc = (descripcion || '').trim();
  if (desc.length > MAX_DESCRIPCION) {
    return { error: `La descripción no puede superar ${MAX_DESCRIPCION} caracteres.` };
  }
  return { valor: { titulo: titulo.trim(), descripcion: desc } };
}

function crearApp({ generar, internalApiKey } = {}) {
  if (!internalApiKey) {
    throw new Error('Falta INTERNAL_API_KEY: el servicio no puede arrancar sin clave interna.');
  }
  const generarTarea =
    generar ||
    ((tarea) =>
      generarSubtareas(tarea, {
        apiKey: process.env.GEMINI_API_KEY,
        model: process.env.GEMINI_MODEL || undefined,
      }));

  const app = express();
  app.use(express.json({ limit: '10kb' }));

  app.get('/health', (req, res) => res.json({ estado: 'ok' }));

  // Documentación pública (Swagger UI) y la especificación en bruto.
  const rutaEspecificacion = path.join(__dirname, '..', 'openapi.yaml');
  const especificacion = YAML.parse(fs.readFileSync(rutaEspecificacion, 'utf8'));
  app.get('/openapi.yaml', (req, res) => res.type('text/yaml').sendFile(rutaEspecificacion));
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(especificacion));

  app.post('/api/sugerencias', async (req, res) => {
    if (!clavesIguales(req.get('X-API-Key'), internalApiKey)) {
      return res.status(401).json({ error: 'Clave de API ausente o incorrecta.' });
    }
    const { error, valor } = validar(req.body);
    if (error) {
      return res.status(400).json({ error });
    }
    try {
      const subtareas = await generarTarea(valor);
      return res.json({ tarea: valor.titulo, subtareas });
    } catch (e) {
      const mensaje =
        e instanceof IAError ? e.message : 'No se pudieron generar las sugerencias.';
      return res.status(502).json({ error: mensaje });
    }
  });

  // Errores de Express (por ejemplo, JSON mal formado): siempre JSON en español.
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    if (err.type === 'entity.parse.failed' || err.status === 400) {
      return res.status(400).json({ error: 'El cuerpo de la petición no es un JSON válido.' });
    }
    if (err.type === 'entity.too.large') {
      return res.status(400).json({ error: 'El cuerpo de la petición es demasiado grande.' });
    }
    return res.status(500).json({ error: 'Error interno del servicio.' });
  });

  return app;
}

module.exports = { crearApp };
