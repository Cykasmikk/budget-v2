import { defineConfig } from 'vitest/config';

export default defineConfig({
    server: {
        host: true, // Listen on all addresses
        port: 8080, // Match Kubernetes Service port
        watch: {
            usePolling: true, // Required for Docker/WSL hot reload
        },
        proxy: {
            '/api': {
                target: process.env.VITE_API_TARGET || 'http://localhost:8000',
                changeOrigin: true,
                configure: (proxy, _options) => {
                    proxy.on('error', (err, _req, _res) => {
                        console.log('proxy error', err);
                    });
                    proxy.on('proxyReq', (proxyReq, req, _res) => {
                        console.log('Sending Request to the Target:', req.method, req.url);
                    });
                    proxy.on('proxyRes', (proxyRes, req, _res) => {
                        console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
                    });
                },
            },
        },
    },
    build: {
        outDir: 'dist',
        target: 'esnext',
    },
    test: {
        environment: 'jsdom',
        setupFiles: ['./vitest.setup.ts'],
    },
});
