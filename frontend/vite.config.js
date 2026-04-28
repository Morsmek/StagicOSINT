import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: [
      'react-force-graph-3d',
      'three-forcegraph',
      'three-spritetext',
    ],
    esbuildOptions: {
      plugins: [
        {
          name: 'stub-three-webgpu',
          setup(build) {
            build.onResolve({ filter: /^three\/webgpu$/ }, () => ({
              path: 'three-webgpu-stub',
              namespace: 'stub',
            }))
            build.onLoad({ filter: /.*/, namespace: 'stub' }, () => ({
              contents: `
                export default {};
                export const WebGPURenderer = class {};
                export const StorageBufferAttribute = class {};
                export const StorageTexture = class {};
                export const NodeMaterial = class {};
              `,
            }))
          },
        },
      ],
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
