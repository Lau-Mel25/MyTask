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
