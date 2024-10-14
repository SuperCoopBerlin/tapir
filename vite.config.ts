import {defineConfig} from 'vite';
import {join, resolve} from 'path';
import react from "@vitejs/plugin-react-swc";

export default defineConfig(() => {

  const INPUT_DIR = './src';
  const OUTPUT_DIR = './dist/';

  return {
    plugins: [react()],
    root: resolve(INPUT_DIR),
    base: '/static/',
    build: {
      sourcemap: true,
      manifest: true,
      emptyOutDir: true,
      outDir: resolve(OUTPUT_DIR),
      rollupOptions: {
        input: {
          user_page: join(INPUT_DIR, '/user_page/user_page.tsx'),
          welcome_desk: join(INPUT_DIR, '/welcome_desk/welcome_desk.tsx'),
        },
      },
    },
    server: {
      cors: true,
    }
  };
});