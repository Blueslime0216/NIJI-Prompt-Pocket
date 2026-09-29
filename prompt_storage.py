"""프롬프트 상태를 Git에서 제외된 로컬 JSON 파일에 보관합니다."""

import json
import os
from pathlib import Path

from seed_data import create_initial_prompts

_APP_DIRECTORY = Path(__file__).resolve().parent
_DEFAULT_DATA_DIRECTORY = _APP_DIRECTORY / "local-data"
_CUSTOM_DATA_DIRECTORY = os.environ.get("NIJI_PROMPT_POCKET_DATA_DIR", "").strip()
if _CUSTOM_DATA_DIRECTORY:
    _CUSTOM_DATA_DIRECTORY = Path(_CUSTOM_DATA_DIRECTORY).expanduser()
    if not _CUSTOM_DATA_DIRECTORY.is_absolute():
        _CUSTOM_DATA_DIRECTORY = _APP_DIRECTORY / _CUSTOM_DATA_DIRECTORY
else:
    _CUSTOM_DATA_DIRECTORY = _DEFAULT_DATA_DIRECTORY
STORAGE_PATH = _CUSTOM_DATA_DIRECTORY / "prompts.json"
STORAGE_VERSION = 1


class PromptStorageError(Exception):
    """저장 파일을 안전하게 읽거나 기록하지 못했습니다."""


def _validated_prompts(document):
    if not isinstance(document, dict) or document.get("version") != STORAGE_VERSION:
        raise PromptStorageError("저장 파일 형식 또는 버전이 올바르지 않습니다.")
    prompts = document.get("prompts")
    if not isinstance(prompts, list):
        raise PromptStorageError("저장 파일의 프롬프트 목록을 읽을 수 없습니다.")

    validated = []
    for prompt in prompts:
        if not isinstance(prompt, dict):
            raise PromptStorageError("저장 파일의 프롬프트 항목이 올바르지 않습니다.")
        title = prompt.get("title")
        content = prompt.get("content")
        category = prompt.get("category")
        favorite = prompt.get("favorite")
        image_path = prompt.get("image_path")
        if not all(isinstance(value, str) and value.strip()
                   for value in (title, content, category)):
            raise PromptStorageError("저장 파일에 비어 있는 필수 항목이 있습니다.")
        if not isinstance(favorite, bool):
            raise PromptStorageError("저장 파일의 즐겨찾기 값이 올바르지 않습니다.")
        if image_path is not None and not isinstance(image_path, str):
            raise PromptStorageError("저장 파일의 이미지 경로가 올바르지 않습니다.")
        validated.append({
            "title": title,
            "content": content,
            "category": category,
            "favorite": favorite,
            "image_path": image_path,
        })
    return validated


def load_prompts(path=STORAGE_PATH):
    """저장 파일이 없으면 기본 데이터를, 있으면 검증한 상태를 반환합니다."""
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as source:
            document = json.load(source)
    except FileNotFoundError:
        return create_initial_prompts()
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PromptStorageError("로컬 저장 파일을 읽을 수 없습니다.") from error
    return _validated_prompts(document)


def save_prompts(prompts, path=STORAGE_PATH):
    """임시 파일을 완성한 뒤 교체해 중간 종료에도 기존 데이터를 보존합니다."""
    path = Path(path)
    temporary_path = path.with_name(path.name + ".tmp")
    document = {"version": STORAGE_VERSION, "prompts": prompts}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with temporary_path.open("w", encoding="utf-8", newline="\n") as destination:
            json.dump(document, destination, ensure_ascii=False, indent=2)
            destination.write("\n")
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary_path, path)
    except (OSError, TypeError, ValueError) as error:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise PromptStorageError("로컬 저장 파일을 기록하지 못했습니다.") from error
