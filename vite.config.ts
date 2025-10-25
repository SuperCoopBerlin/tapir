import { defineConfig } from "vite";
import { join, resolve } from "path";
import react from "@vitejs/plugin-react-swc";

export default defineConfig(() => {
  const INPUT_DIR = "./src";
  const OUTPUT_DIR = "./dist/";

  return {
    plugins: [react()],
    root: resolve(INPUT_DIR),
    base: "/static/",
    build: {
      target: "es6",
      sourcemap: true,
      manifest: "manifest.json",
      emptyOutDir: true,
      outDir: resolve(OUTPUT_DIR),
      rollupOptions: {
        input: {
          welcome_desk: join(INPUT_DIR, "/welcome_desk/welcome_desk_entry.tsx"),
          member_registration: join(
            INPUT_DIR,
            "/member_registration/member_registration_entry.tsx",
          ),
          fancy_graph: join(INPUT_DIR, "/statistics/fancy_graph_entry.tsx"),
          fancy_export: join(INPUT_DIR, "/statistics/fancy_export_entry.tsx"),
        },
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      cors: true,
    },
  };
});
