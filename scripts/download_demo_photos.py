"""Maintainer-only asset refresh. Installation and runtime never download photos.

Attribution and licenses: frontend/public/demo-photo-credits.html.
"""

import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

SOURCES = {
    "casado": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Casado_Tico.jpg",
    "hamburguesa": "https://upload.wikimedia.org/wikipedia/commons/4/47/Hamburger_%28black_bg%29.jpg",
    "papas": "https://upload.wikimedia.org/wikipedia/commons/8/83/French_Fries.JPG",
    "pinto": "https://upload.wikimedia.org/wikipedia/commons/4/4d/CRI_07_2018_0119.jpg",
    "tortilla": "https://upload.wikimedia.org/wikipedia/commons/7/75/Quesadilla_2.jpg",
    "cas": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Psidium_friedrichsthalianum%2C_the_Wild_Guava_%2810841338553%29.jpg",
    "cafe": "https://pd.w.org/2026/04/69369d47c385ab453.65578776.jpg",
    "queque": "https://pd.w.org/2026/04/74669d77e90a86de5.76641907-1536x1152.jpg",
}


def download(item):
    slug, url = item
    request = Request(url, headers={"User-Agent": "SodaLocalDemoAssets/1.0"})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    with Image.open(io.BytesIO(content)) as source:
        pixels = ImageOps.exif_transpose(source).convert("RGB")
        pixels.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        clean = Image.new("RGB", pixels.size)
        clean.paste(pixels)
        target = Path(__file__).resolve().parents[1] / "backend/app/assets/demo" / f"{slug}.webp"
        target.parent.mkdir(parents=True, exist_ok=True)
        clean.save(target, "WEBP", quality=85, method=6)
        print(f"{slug}: {target.stat().st_size} bytes", flush=True)


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(download, SOURCES.items()))
