"""로컬 참고 이미지를 터미널용 ASCII 문자열로 변환합니다."""

from pathlib import Path
import warnings

PROJECT_DIR = Path(__file__).resolve().parent
MAX_IMAGE_PIXELS = 20_000_000


class ImagePreviewError(ValueError):
    """사용자에게 바로 표시할 수 있는 이미지 오류입니다."""


def resolve_image_path(value):
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    try:
        path = Path(text).expanduser()
        if not path.is_absolute():
            path = PROJECT_DIR / path
        path = path.resolve(strict=True)
        if not path.is_file():
            raise ImagePreviewError("이미지 파일 경로를 입력해 주세요. 폴더는 연결할 수 없습니다.")
        return path
    except (OSError, RuntimeError, ValueError) as error:
        raise ImagePreviewError("이미지 파일을 찾을 수 없습니다. 경로를 확인해 주세요.") from error


def _load_image(value):
    try:
        from PIL import Image, ImageOps
    except ImportError as error:
        raise ImagePreviewError(
            "이미지 미리보기에는 Pillow가 필요합니다. "
            "python -m pip install -r requirements.txt 를 실행해 주세요."
        ) from error

    path = resolve_image_path(value)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as source:
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise ImagePreviewError("이미지는 2,000만 픽셀 이하로 준비해 주세요.")
                # EXIF 회전을 반영하고, 투명 영역은 흰 배경에 합성합니다.
                rgba = ImageOps.exif_transpose(source).convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                rgba.close()
                return background
    except (OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as error:
        if isinstance(error, ImagePreviewError):
            raise
        raise ImagePreviewError(
            "이미지를 읽을 수 없습니다. 정상적인 PNG, JPG, WebP 등의 파일인지 확인해 주세요."
        ) from error


def normalize_image_path(value):
    """이미지를 확인한 뒤 프로젝트 안의 파일은 상대 경로로 보관합니다."""
    path = resolve_image_path(value)
    with _load_image(path):
        pass
    if path.is_relative_to(PROJECT_DIR):
        return path.relative_to(PROJECT_DIR).as_posix()
    return str(path)


def render_ascii(value, width=72, max_height=32):
    """문자 셀의 가로:세로 비율(약 1:2)을 보정한 흑백 미리보기입니다."""
    from math import floor

    width = max(8, min(160, int(width)))
    max_height = max(4, min(80, int(max_height)))
    with _load_image(value) as source:
        from PIL import Image

        ratio = source.height / source.width * 0.5
        height = max(1, round(width * ratio))
        if height > max_height:
            height = max_height
            width = max(1, floor(height / ratio))
        gray = source.convert("L").resize((width, height), Image.Resampling.LANCZOS)
        pixels = gray.tobytes()

    # 흰 배경과 검은 배경 모두에서 빈 배경이 공백에 가깝게 보이도록 선택합니다.
    border = list(pixels[:width]) + list(pixels[-width:])
    border += [pixels[row * width] for row in range(height)]
    border += [pixels[(row + 1) * width - 1] for row in range(height)]
    shades = " .:-=+*#%@" if sum(border) / len(border) < 128 else "@%#*+=-:. "
    lines = []
    for row in range(height):
        line = pixels[row * width:(row + 1) * width]
        lines.append("".join(shades[pixel * (len(shades) - 1) // 255] for pixel in line))
    return "\n".join(lines)
