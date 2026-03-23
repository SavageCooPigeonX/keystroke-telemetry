import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    // Serve dual_view.json from pigeon_brain/ parent dir
    {
      name: 'serve-dual-view',
      configureServer(server) {
        server.middlewares.use('/dual_view.json', (req, res) => {
          const fs = require('fs');
          const filePath = path.resolve(__dirname, '..', 'dual_view.json');
          if (fs.existsSync(filePath)) {
            res.setHeader('Content-Type', 'application/json');
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.end(fs.readFileSync(filePath, 'utf-8'));
          } else {
            res.statusCode = 404;
            res.end('{}');
          }
        });
      },
    },
  ],
  server: { port: 3333 },
});
