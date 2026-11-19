const fs = require('fs');
const path = require('path');

// En local se lee .env automáticamente. En Render/Docker las variables ya vienen
// del entorno y no se sobrescriben.
const rutaEnv = path.join(__dirname, '..', '..', '.env');
if (fs.existsSync(rutaEnv)) {
  for (const linea of fs.readFileSync(rutaEnv, 'utf8').split(/\r?\n/)) {
    if (!linea || linea.startsWith('#') || !linea.includes('=')) continue;
    const separador = linea.indexOf('=');
    const clave = linea.slice(0, separador).trim();
    const valor = linea.slice(separador + 1).trim();
    if (clave && process.env[clave] === undefined) process.env[clave] = valor;
  }
}

const { crearApp } = require('./app');

const faltantes = ['GEMINI_API_KEY', 'INTERNAL_API_KEY'].filter((v) => !process.env[v]);
if (faltantes.length > 0) {
  console.error(`Faltan variables de entorno: ${faltantes.join(', ')}`);
  process.exit(1);
}

const app = crearApp({ internalApiKey: process.env.INTERNAL_API_KEY });
const puerto = Number(process.env.PORT) || 3000;

app.listen(puerto, '0.0.0.0', () => {
  console.log(`Microservicio de sugerencias escuchando en el puerto ${puerto}`);
});
