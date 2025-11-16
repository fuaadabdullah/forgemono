/*
 * Simple image optimizer script that attempts to convert existing public images
 * to webp and avif for improved performance. This script requires `sharp`.
 * If `sharp` is not installed, it will skip conversion and log a notice.
 *
 * Usage: node scripts/optimize-images.js
 * Or add to package.json as: "optimize:images": "node scripts/optimize-images.js"
 */

const fs = require('fs');
const path = require('path');

async function main() {
  const publicImages = path.join(__dirname, '..', 'public', 'images');
  const files = fs.readdirSync(publicImages).filter(f => f.endsWith('.jpg') || f.endsWith('.jpeg') || f.endsWith('.png'));
  if (!files.length) {
    console.warn('No images found in public/images; skipping optimization.');
    return;
  }

  let sharp;
  try {
    sharp = require('sharp');
  } catch (err) {
    console.warn('`sharp` is not installed. To enable image optimization, install it with `npm i -D sharp` and rerun this script.');
    return;
  }

  try {
    for (const f of files) {
      const fullPath = path.join(publicImages, f);
      const baseName = path.basename(f, path.extname(f));
      const webpOut = path.join(publicImages, `${baseName}.webp`);
      const avifOut = path.join(publicImages, `${baseName}.avif`);
      const webpSmallOut = path.join(publicImages, `${baseName}-256.webp`);

      try {
        await sharp(fullPath).resize(512).webp({ quality: 75 }).toFile(webpOut);
        console.log('Created', webpOut);
        await sharp(fullPath).resize(512).avif({ quality: 60 }).toFile(avifOut);
        console.log('Created', avifOut);
        // Create smaller 256px version for smaller devices
        await sharp(fullPath).resize(256).webp({ quality: 70 }).toFile(webpSmallOut);
        console.log('Created', webpSmallOut);
      } catch (err) {
        console.warn(`Failed to optimize ${f}:`, err.message);
      }
    }

    console.log('Optimization complete.');
  } catch (err) {
    console.error('Error optimizing images:', err);
  }
}

main();
