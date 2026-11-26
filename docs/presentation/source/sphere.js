// Rasterise the halftone ball from OVI's logo SVG (same dots, any size) into a transparent PNG.
const fs = require('fs'), zlib = require('zlib')
const svg = fs.readFileSync(process.argv[2], 'utf8')
const SIZE = 2400, COLOR = [0x1c, 0x1a, 0x17]
// Dots sit inside <g transform="translate(10,10)">; the clip circle is (110,110) r96 in outer units.
const dots = [...svg.matchAll(/<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"\/>/g)].map(m => [+m[1] + 10, +m[2] + 10, +m[3]]).filter(([, , r]) => r < 20) // drop the clip-path circle itself
const CX = 110, CY = 110, R = 96, scale = SIZE / (2 * R), ox = CX - R, oy = CY - R
const alpha = new Float32Array(SIZE * SIZE)
const clipA = (px, py) => Math.min(1, Math.max(0, R * scale - Math.hypot(px - SIZE / 2, py - SIZE / 2) + 0.5))
for (const [cx, cy, r] of dots) {
  const x = (cx - ox) * scale, y = (cy - oy) * scale, rr = r * scale
  for (let py = Math.max(0, Math.floor(y - rr - 1)); py <= Math.min(SIZE - 1, Math.ceil(y + rr + 1)); py++)
    for (let px = Math.max(0, Math.floor(x - rr - 1)); px <= Math.min(SIZE - 1, Math.ceil(x + rr + 1)); px++) {
      const a = Math.min(1, Math.max(0, rr - Math.hypot(px + 0.5 - x, py + 0.5 - y) + 0.5)) * clipA(px + 0.5, py + 0.5)
      if (a > alpha[py * SIZE + px]) alpha[py * SIZE + px] = a
    }
}
const raw = Buffer.alloc((SIZE * 4 + 1) * SIZE)
for (let y = 0; y < SIZE; y++) {
  raw[y * (SIZE * 4 + 1)] = 0
  for (let x = 0; x < SIZE; x++) {
    const o = y * (SIZE * 4 + 1) + 1 + x * 4
    raw[o] = COLOR[0]; raw[o + 1] = COLOR[1]; raw[o + 2] = COLOR[2]; raw[o + 3] = Math.round(alpha[y * SIZE + x] * 255)
  }
}
const crc = (b) => { let c, t = []; for (let n = 0; n < 256; n++) { c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0 } let v = 0xffffffff; for (const x of b) v = t[(v ^ x) & 0xff] ^ (v >>> 8); return (v ^ 0xffffffff) >>> 0 }
const chunk = (type, data) => { const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]) }
const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(SIZE, 0); ihdr.writeUInt32BE(SIZE, 4); ihdr[8] = 8; ihdr[9] = 6
fs.writeFileSync(process.argv[3], Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]))
console.log(`${dots.length} dots -> ${process.argv[3]}`)
