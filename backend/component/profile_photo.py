"""Validate and re-encode avatars; original filenames and EXIF are discarded."""
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 4 * 1024 * 1024

def prepare_photo(data: bytes) -> bytes:
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Choose an image between 1 byte and 4 MB.')
    try:
        with Image.open(BytesIO(data)) as source:
            if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('Choose a JPG, PNG or WebP image.')
            if source.width * source.height > 16_000_000:
                raise ValueError('Choose an image smaller than 16 megapixels.')
            source.load()
            image = ImageOps.exif_transpose(source).convert('RGB')
            image = ImageOps.fit(image, (384, 384), method=Image.Resampling.LANCZOS)
            out = BytesIO()
            image.save(out, format='JPEG', quality=85)
            return out.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('This image could not be read. Choose a JPG, PNG or WebP image.') from exc
