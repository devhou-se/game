const zlib = require('zlib');

const SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

function decode(buf) {
    let width, height, type, pos = 8;
    const idat = [];
    while (pos < buf.length) {
        const len = buf.readUInt32BE(pos), name = buf.toString('latin1', pos + 4, pos + 8);
        const data = buf.subarray(pos + 8, pos + 8 + len);
        if (name === 'IHDR') {
            width = data.readUInt32BE(0); height = data.readUInt32BE(4); type = data[9];
            if (data[8] !== 8 || (type !== 6 && type !== 2) || data[12]) throw new Error('png: only 8-bit RGB/RGBA, non-interlaced');
        } else if (name === 'IDAT') idat.push(data);
        pos += 12 + len;
    }
    const bpp = type === 6 ? 4 : 3, stride = width * bpp;
    const raw = zlib.inflateSync(Buffer.concat(idat));
    const out = Buffer.alloc(width * height * 4);
    let prev = Buffer.alloc(stride);
    for (let y = 0; y < height; y++) {
        const filter = raw[y * (stride + 1)];
        const line = Buffer.from(raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)));
        for (let i = 0; i < stride; i++) {
            const a = i >= bpp ? line[i - bpp] : 0, b = prev[i], c = i >= bpp ? prev[i - bpp] : 0;
            let add = 0;
            if (filter === 1) add = a;
            else if (filter === 2) add = b;
            else if (filter === 3) add = (a + b) >> 1;
            else if (filter === 4) {
                const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
                add = pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
            }
            line[i] = (line[i] + add) & 255;
        }
        for (let x = 0; x < width; x++) {
            const o = (y * width + x) * 4;
            out[o] = line[x * bpp]; out[o + 1] = line[x * bpp + 1]; out[o + 2] = line[x * bpp + 2];
            out[o + 3] = bpp === 4 ? line[x * bpp + 3] : 255;
        }
        prev = line;
    }
    return { width, height, data: out };
}

function encode(img) {
    const stride = img.width * 4;
    const raw = Buffer.alloc((stride + 1) * img.height);
    for (let y = 0; y < img.height; y++) img.data.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
    const chunk = (name, data) => {
        const head = Buffer.alloc(8);
        head.writeUInt32BE(data.length, 0);
        head.write(name, 4, 'latin1');
        const crc = Buffer.alloc(4);
        crc.writeUInt32BE(zlib.crc32(Buffer.concat([head.subarray(4), data])) >>> 0, 0);
        return Buffer.concat([head, data, crc]);
    };
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(img.width, 0); ihdr.writeUInt32BE(img.height, 4);
    ihdr[8] = 8; ihdr[9] = 6;
    return Buffer.concat([SIGNATURE, chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

function blank(width, height) {
    const data = Buffer.alloc(width * height * 4);
    for (let i = 3; i < data.length; i += 4) data[i] = 255;
    return { width, height, data };
}

function blend(img, o, r, g, b, a) {
    if (a === 0) return;
    const d = img.data, k = a / 255;
    d[o] = Math.round(r * k + d[o] * (1 - k));
    d[o + 1] = Math.round(g * k + d[o + 1] * (1 - k));
    d[o + 2] = Math.round(b * k + d[o + 2] * (1 - k));
}

function paste(img, src, px, py) {
    for (let y = Math.max(0, -py); y < src.height && py + y < img.height; y++) {
        for (let x = Math.max(0, -px); x < src.width && px + x < img.width; x++) {
            const s = (y * src.width + x) * 4;
            blend(img, ((py + y) * img.width + px + x) * 4, src.data[s], src.data[s + 1], src.data[s + 2], src.data[s + 3]);
        }
    }
}

function wash(img, px, py, w, h, [r, g, b, a]) {
    for (let y = Math.max(0, py); y < py + h && y < img.height; y++) {
        for (let x = Math.max(0, px); x < px + w && x < img.width; x++) blend(img, (y * img.width + x) * 4, r, g, b, a);
    }
}

function scale(img, factor) {
    const width = Math.max(1, Math.round(img.width * factor)), height = Math.max(1, Math.round(img.height * factor));
    const out = blank(width, height);
    for (let y = 0; y < height; y++) {
        const y0 = Math.floor(y / factor), y1 = Math.max(y0 + 1, Math.min(img.height, Math.floor((y + 1) / factor)));
        for (let x = 0; x < width; x++) {
            const x0 = Math.floor(x / factor), x1 = Math.max(x0 + 1, Math.min(img.width, Math.floor((x + 1) / factor)));
            let r = 0, g = 0, b = 0, n = 0;
            for (let sy = y0; sy < y1; sy++) for (let sx = x0; sx < x1; sx++) {
                const s = (sy * img.width + sx) * 4;
                r += img.data[s]; g += img.data[s + 1]; b += img.data[s + 2]; n++;
            }
            const o = (y * width + x) * 4;
            out.data[o] = r / n; out.data[o + 1] = g / n; out.data[o + 2] = b / n;
        }
    }
    return out;
}

module.exports = { decode, encode, blank, paste, wash, scale };
