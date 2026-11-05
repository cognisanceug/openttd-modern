#!/usr/bin/env python3
"""Extract real sprites from a GRF (container v1 or v2) as PNG plus metadata.

Only used as a reference for calibration: we read the OpenGFX base sprites to
learn the exact sprite sizes, offsets and pixel footprints the game expects.

Usage: grf_extract.py <file.grf> <first> <last> <outdir>
Sprite numbers count all sprites in file order (pseudo sprites included),
which is how OpenTTD numbers sprites in base graphics files.
"""

import json
import os
import struct
import sys

from nml.palette import raw_palette_data
from PIL import Image

V2_MAGIC = b"\x00\x00GRF\x82\x0d\x0a\x1a\x0a"


def decompress(data, pos, size):
    """GRF LZ77 variant. Returns (bytes, new_pos)."""
    out = bytearray()
    while len(out) < size:
        code = data[pos]
        pos += 1
        if code & 0x80 == 0:
            n = code if code else 0x80
            out += data[pos:pos + n]
            pos += n
        else:
            scode = code - 0x100
            n = -(scode >> 3)
            offset = ((code & 7) << 8) | data[pos]
            pos += 1
            for _ in range(n):
                out.append(out[-offset])
    return bytes(out[:size]), pos


def decode_tiles(buf, width, height, bpp, long_format):
    """Decode 'tile compression' (chunked) sprite data into a flat pixel buffer."""
    px = bytearray(width * height * bpp)
    mask = bytearray(width * height)
    for y in range(height):
        if long_format:
            off = struct.unpack_from("<I", buf, y * 4)[0]
        else:
            off = struct.unpack_from("<H", buf, y * 2)[0]
        while True:
            if long_format:
                hdr, x = struct.unpack_from("<HH", buf, off)
                off += 4
                last, n = hdr & 0x8000, hdr & 0x7FFF
            else:
                hdr, x = buf[off], buf[off + 1]
                off += 2
                last, n = hdr & 0x80, hdr & 0x7F
            for i in range(n):
                p = (y * width + x + i)
                px[p * bpp:(p + 1) * bpp] = buf[off:off + bpp]
                mask[p] = 1
                off += bpp
            if last:
                break
    return px, mask


def bpp_of(colour):
    return (3 if colour & 1 else 0) + (1 if colour & 2 else 0) + (1 if colour & 4 else 0)


def read_v2(data):
    pos = len(V2_MAGIC)
    gfx_off = struct.unpack_from("<I", data, pos)[0]
    pos += 5  # offset + compression byte
    data_start = pos
    gfx_start = data_start - 1 + gfx_off  # counted from the end of the offset field

    # Graphics section: id -> list of entries.
    gfx = {}
    p = gfx_start
    while True:
        sid = struct.unpack_from("<I", data, p)[0]
        p += 4
        if sid == 0:
            break
        size, typ = struct.unpack_from("<IB", data, p)
        p += 4
        body = data[p + 1:p + size]  # size counts the type byte too
        p += size
        if typ == 0xFF:
            continue
        zoom, h, w, xo, yo = struct.unpack_from("<BHHhh", body, 0)
        gfx.setdefault(sid, []).append(dict(type=typ, zoom=zoom, w=w, h=h, x=xo, y=yo, raw=body[9:]))

    # Data section: sequence of pseudo sprites and references.
    sprites = []
    p = data_start
    while True:
        size = struct.unpack_from("<I", data, p)[0]
        p += 4
        if size == 0:
            break
        info = data[p]
        p += 1
        if info == 0xFD:
            sid = struct.unpack_from("<I", data, p)[0]
            sprites.append(("real", gfx.get(sid, [])))
        else:
            sprites.append(("pseudo", None))
        p += size
    return sprites


def decode_entry(e):
    typ, w, h = e["type"], e["w"], e["h"]
    bpp = bpp_of(typ)
    raw = e["raw"]
    if typ & 0x08:
        dsize = struct.unpack_from("<I", raw, 0)[0]
        buf, _ = decompress(raw, 4, dsize)
        px, mask = decode_tiles(buf, w, h, bpp, dsize > 65535)
    else:
        buf, _ = decompress(raw, 0, w * h * bpp)
        px = bytearray(buf)
        mask = bytearray(1 if any(px[i * bpp:(i + 1) * bpp]) else 0 for i in range(w * h))
    return px, mask, bpp


def main():
    grf, first, last, outdir = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    data = open(grf, "rb").read()
    if not data.startswith(V2_MAGIC):
        sys.exit("only container v2 implemented")
    sprites = read_v2(data)
    os.makedirs(outdir, exist_ok=True)
    meta = {}
    for n in range(first, last + 1):
        kind, entries = sprites[n]
        if kind != "real" or not entries:
            meta[n] = {"kind": kind}
            continue
        e = entries[0]  # base sets: one 8bpp normal-zoom entry
        px, mask, bpp = decode_entry(e)
        img = Image.new("L", (e["w"], e["h"]))
        img.putdata([255 if m else 0 for m in mask])
        img.save(os.path.join(outdir, f"{n}_mask.png"))
        if bpp == 1:
            pal = Image.new("P", (e["w"], e["h"]))
            pal.putpalette(raw_palette_data[0])
            pal.putdata(list(px))
            pal.info["transparency"] = 0
            pal.save(os.path.join(outdir, f"{n}.png"))
        meta[n] = {k: e[k] for k in ("type", "zoom", "w", "h", "x", "y")}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    for n, m in meta.items():
        print(n, m)


if __name__ == "__main__":
    main()
