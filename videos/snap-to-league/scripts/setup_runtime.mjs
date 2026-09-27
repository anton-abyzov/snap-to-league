import { copyFile, mkdir } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
await mkdir(new URL('assets/vendor/', root), { recursive: true });
await copyFile(new URL('node_modules/gsap/dist/gsap.min.js', root), new URL('assets/vendor/gsap.min.js', root));
console.log('Pinned local GSAP runtime ready.');
