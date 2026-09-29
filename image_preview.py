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
    except ImagePreviewError:
        raise
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


def render_ascii(value, width=72, max_height=32, mode="plain"):
    """plain / color / pixel 모드로 터미널 문자열을 만듭니다.

    pixel은 ▀의 글자색과 배경색에 위/아래 픽셀을 각각 넣습니다.
    색상 지원 여부 판단은 호출하는 콘솔 코드가 담당합니다.
    """
    from math import floor

    if mode not in {"plain", "color", "pixel"}:
        raise ValueError("지원하지 않는 이미지 표시 방식입니다.")
    width = max(8, min(160, int(width)))
    max_height = max(4, min(80, int(max_height)))
    with _load_image(value) as source:
        from PIL import Image

        ratio = source.height / source.width * (1.0 if mode == "pixel" else 0.5)
        height = max(1, round(width * ratio))
        limit = max_height * 2 if mode == "pixel" else max_height
        if height > limit:
            height = limit
            width = max(1, floor(height / ratio))
        resized = source.resize((width, height), Image.Resampling.LANCZOS)
        if mode == "pixel":
            return _render_half_blocks(resized)
        pixels = resized.convert("L").tobytes()
        rgb = resized.tobytes()

    # 흰 배경과 검은 배경 모두에서 빈 배경이 공백에 가깝게 보이도록 선택합니다.
    border = list(pixels[:width]) + list(pixels[-width:])
    border += [pixels[row * width] for row in range(height)]
    border += [pixels[(row + 1) * width - 1] for row in range(height)]
    shades = " .:-=+*#%@" if sum(border) / len(border) < 128 else "@%#*+=-:. "
    if mode == "color":
        shades = " .:-=+*#%@"
    lines = []
    for row in range(height):
        line = []
        for column in range(width):
            position = row * width + column
            character = shades[pixels[position] * (len(shades) - 1) // 255]
            if mode == "color":
                red, green, blue = rgb[position * 3:position * 3 + 3]
                line.append(f"\x1b[38;2;{red};{green};{blue}m{character}")
            else:
                line.append(character)
        if mode == "color":
            line.append("\x1b[0m")
        lines.append("".join(line))
    return "\n".join(lines)


def _render_half_blocks(image):
    """한 문자에 세로 두 픽셀을 출력하고 줄마다 색상을 초기화합니다."""
    width, height = image.size
    pixels = image.tobytes()
    lines = []
    for row in range(0, height, 2):
        line = []
        for column in range(width):
            upper = (row * width + column) * 3
            lower = (min(row + 1, height - 1) * width + column) * 3
            red1, green1, blue1 = pixels[upper:upper + 3]
            red2, green2, blue2 = pixels[lower:lower + 3]
            line.append(
                f"\x1b[38;2;{red1};{green1};{blue1}m"
                f"\x1b[48;2;{red2};{green2};{blue2}m▀"
            )
        lines.append("".join(line) + "\x1b[0m")
    return "\n".join(lines)
