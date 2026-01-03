import logging
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)

CARD_IMAGE_SIZE = (640, 400)


def _resize_image(image_path):
    try:
        with Image.open(image_path) as image:
            original_format = (image.format or "JPEG").upper()
            if image.width <= CARD_IMAGE_SIZE[0] and image.height <= CARD_IMAGE_SIZE[1]:
                return
            image = ImageOps.fit(image, CARD_IMAGE_SIZE, method=Image.LANCZOS)
            image_format = original_format
            save_kwargs = {}
            if image_format in {"JPEG", "JPG"}:
                if image.mode in {"RGBA", "P"}:
                    image = image.convert("RGB")
                save_kwargs.update({"quality": 85, "optimize": True, "progressive": True})
                image.save(image_path, "JPEG", **save_kwargs)
            elif image_format == "PNG":
                image.save(image_path, "PNG", optimize=True)
            else:
                image.save(image_path, image_format)
    except FileNotFoundError:
        return


def _safe_resize(image_path):
    try:
        _resize_image(image_path)
    except Exception:
        logger.exception("Failed to resize product image")


def queue_resize(image_path, async_=True):
    if async_:
        _executor.submit(_safe_resize, image_path)
    else:
        _safe_resize(image_path)
