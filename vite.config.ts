import {defineConfig} from 'vite';
import {join, resolve} from 'path';
import react from "@vitejs/plugin-react-swc";

export default defineConfig(() => {

  const INPUT_DIR = './src';
  const OUTPUT_DIR = './static/';

  return {
    plugins: [react()],
    root: resolve(INPUT_DIR),
    base: '/static/',
    build: {
      manifest: true,
      emptyOutDir: true,
      outDir: resolve(OUTPUT_DIR),
      rollupOptions: {
        input: {
          home: join(INPUT_DIR, '/main.tsx'),
          css: join(INPUT_DIR, '/index.css'),
          user_page: join(INPUT_DIR, '/user_page/user_page.tsx'),
        },
      },
    },
  };
});