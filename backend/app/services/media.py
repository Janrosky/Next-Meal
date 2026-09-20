import io
import re
import warnings
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from app.domain import BusinessError

MAX_UPLOAD = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000


def image_path(database, name: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}\.webp", name):
        raise BusinessError("Imagen no encontrada.", 404)
    return database.path.parent / "media" / name


def check_image(database, url: str):
    if url and not image_path(database, url.rsplit("/", 1)[-1]).is_file():
        raise BusinessError("La imagen ya no existe. Volvé a subirla.", 422)


def save_image(database, content: bytes) -> dict:
    if not content or len(content) > MAX_UPLOAD:
        raise BusinessError("La imagen debe pesar entre 1 byte y 5 MB.", 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as source:
                if source.format not in ("JPEG", "PNG", "WEBP"):
                    raise BusinessError("Usá una imagen JPG, PNG o WebP.", 422)
                if source.width * source.height > MAX_PIXELS:
                    raise BusinessError("La imagen supera los 20 megapíxeles.", 422)
                source.load()
                pixels = ImageOps.exif_transpose(source).convert("RGBA")
                pixels.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                # A fresh image strips metadata, including location and camera details.
                clean = Image.new("RGBA", pixels.size)
                clean.paste(pixels)
                output = io.BytesIO()
                clean.save(output, "WEBP", quality=85, method=4)
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise BusinessError("No se pudo leer la imagen. Probá con otro archivo.", 422) from error
    name = uuid4().hex + ".webp"
    target = image_path(database, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_suffix(".tmp")
    try:
        staging.write_bytes(output.getvalue())
        staging.replace(target)
    finally:
        staging.unlink(missing_ok=True)
    return {"url": "/api/media/" + name, "width": clean.width, "height": clean.height}
