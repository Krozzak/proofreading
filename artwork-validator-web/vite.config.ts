import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { viteSingleFile } from 'vite-plugin-singlefile'

// Single-file build: everything (JS, CSS, pdf.js worker) is inlined into
// dist/index.html so the app can be opened via file:// and shared as one file.
export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile()],
  build: {
    // Transpile syntax down for older corporate browsers (APIs are handled by
    // the small polyfill block in index.html).
    target: 'es2019',
    assetsInlineLimit: 100_000_000,
    cssCodeSplit: false,
    chunkSizeWarningLimit: 10_000,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
})
