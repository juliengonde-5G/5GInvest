"""Génère des icônes PNG pour la PWA (utilise Pillow si dispo, sinon placeholder)."""
import os

SIZES = [192, 512]
DIR = os.path.dirname(__file__)

try:
    from PIL import Image, ImageDraw, ImageFont

    for size in SIZES:
        img = Image.new("RGB", (size, size), "#3b82f6")
        draw = ImageDraw.Draw(img)
        # Cercle de fond
        margin = size // 10
        draw.ellipse([margin, margin, size - margin, size - margin], fill="#1e293b")
        # Texte "5G"
        font_size = size // 3
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "5G", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) / 2, (size - th) / 2 - size // 20), "5G", fill="white", font=font)
        # Sous-texte
        small_size = size // 10
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small_size)
        except OSError:
            small_font = ImageFont.load_default()
        draw.text((size // 2 - size // 5, size // 2 + size // 8), "INVEST", fill="#94a3b8", font=small_font)
        path = os.path.join(DIR, f"icon-{size}.png")
        img.save(path)
        print(f"  Icône {size}x{size} générée: {path}")

except ImportError:
    # Fallback: 1x1 transparent PNG (minimum viable)
    import struct, zlib
    def make_minimal_png(size):
        # Create a minimal solid-color PNG
        width = height = size
        raw = b''
        for y in range(height):
            raw += b'\x00'  # filter byte
            for x in range(width):
                raw += b'\x3b\x82\xf6\xff'  # RGBA blue
        def chunk(ctype, data):
            c = ctype + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
        return (b'\x89PNG\r\n\x1a\n' +
                chunk(b'IHDR', ihdr) +
                chunk(b'IDAT', zlib.compress(raw)) +
                chunk(b'IEND', b''))
    for size in SIZES:
        path = os.path.join(DIR, f"icon-{size}.png")
        with open(path, 'wb') as f:
            f.write(make_minimal_png(size))
        print(f"  Icône basique {size}x{size}: {path}")

print("  Icônes générées.")
