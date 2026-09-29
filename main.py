"""NIJI Prompt Pocket: 번호 메뉴로 사용하는 프롬프트 관리 프로그램."""

import sys
import shutil

from seed_data import CATEGORIES, create_initial_prompts
from image_preview import ImagePreviewError, normalize_image_path, render_ascii
from terminal_support import clear_screen, enable_color

PREVIEW_LABELS = {"plain": "흑백 ASCII", "color": "컬러 ASCII", "pixel": "컬러 픽셀"}


def read_required(message):
    """공백만 입력하면 다시 입력받습니다."""
    while True:
        value = input(message).strip()
        if value:
            return value
        print("빈 값은 입력할 수 없습니다. 다시 입력해 주세요.")


def read_content():
    print("프롬프트 내용을 입력하세요. 여러 줄 입력 가능 / 마지막에 . 만 입력하면 완료")
    while True:
        lines = []
        while True:
            line = input("> ")
            if line.strip() == ".":
                break
            lines.append(line)
        content = "\n".join(lines).strip()
        if content:
            return content
        print("내용이 비어 있습니다. 내용을 입력하고 . 으로 마쳐 주세요.")


def get_categories(prompts):
    categories = CATEGORIES.copy()
    for prompt in prompts:
        if prompt["category"] not in categories:
            categories.append(prompt["category"])
    return categories


def read_number(message, maximum):
    """0은 취소 또는 직접 입력을 뜻하며, 범위 밖의 값은 다시 받습니다."""
    while True:
        try:
            number = int(input(message).strip())
            if 0 <= number <= maximum:
                return number
        except ValueError:
            pass
        print(f"잘못된 번호입니다. 0부터 {maximum}까지 입력해 주세요.")


def choose_category(prompts):
    categories = get_categories(prompts)
    for number, category in enumerate(categories, start=1):
        print(f"{number}. {category}")
    print("0. 카테고리 직접 입력")
    number = read_number("카테고리 번호: ", len(categories))
    if number == 0:
        return read_required("새 카테고리 이름: ")
    return categories[number - 1]


def add_prompt(prompts):
    print("\n[프롬프트 추가]")
    title = read_required("제목: ")
    content = read_content()
    category = choose_category(prompts)
    image_path = read_image_path()
    prompts.append({
        "title": title,
        "content": content,
        "category": category,
        "favorite": False,
        "image_path": image_path,
    })
    print(f"{len(prompts)}번 프롬프트를 추가했습니다: {title}")


def print_prompt_rows(rows):
    """필터링해도 원본 번호를 유지하도록 (번호, 프롬프트) 쌍을 출력합니다."""
    if not rows:
        print("표시할 프롬프트가 없습니다.")
        return
    for number, prompt in rows:
        star = "⭐" if prompt["favorite"] else "  "
        print(f"{number:>3}. {star} {prompt['title']} | {prompt['category']}")


def browse_prompt_rows(rows, mode="plain"):
    """현재 결과 목록 안에서 번호로 상세 보기를 반복해서 엽니다."""
    print_prompt_rows(rows)
    if not rows:
        return
    available = dict(rows)
    while True:
        value = input("\n상세 볼 프롬프트 번호 (Enter 또는 0: 메뉴): ").strip()
        if not value:
            return
        try:
            number = int(value)
        except ValueError:
            print("프롬프트 번호를 입력하거나 Enter로 메뉴로 돌아가세요.")
            continue
        if number == 0:
            return
        if number not in available:
            print("현재 목록에 있는 프롬프트 번호를 입력해 주세요.")
            continue
        clear_screen()
        print_prompt_detail(available[number], mode)
        print("\n[현재 목록]")
        print_prompt_rows(rows)


def show_list(prompts, mode="plain"):
    print(f"\n[전체 프롬프트: {len(prompts)}개]")
    browse_prompt_rows(list(enumerate(prompts, start=1)), mode)


def show_by_category(prompts, mode="plain"):
    print("\n[카테고리별 조회]")
    categories = get_categories(prompts)
    for number, category in enumerate(categories, start=1):
        print(f"{number}. {category}")
    number = read_number("카테고리 번호 (0: 취소): ", len(categories))
    if number == 0:
        return
    category = categories[number - 1]
    print(f"\n[{category}]")
    rows = [(i, p) for i, p in enumerate(prompts, 1) if p["category"] == category]
    browse_prompt_rows(rows, mode)


def search_prompts(prompts, mode="plain"):
    print("\n[프롬프트 검색]")
    keyword = read_required("검색어 (제목 또는 내용): ").casefold()
    rows = [
        (i, p) for i, p in enumerate(prompts, 1)
        if keyword in p["title"].casefold() or keyword in p["content"].casefold()
    ]
    if not rows:
        print("검색 결과가 없습니다.")
        return
    print(f"\n[검색 결과: {len(rows)}개]")
    browse_prompt_rows(rows, mode)


def select_prompt(prompts):
    if not prompts:
        print("등록된 프롬프트가 없습니다.")
        return None
    print(f"\n[전체 프롬프트: {len(prompts)}개]")
    print_prompt_rows(list(enumerate(prompts, start=1)))
    number = read_number("프롬프트 번호 (0: 취소): ", len(prompts))
    return prompts[number - 1] if number else None


def show_detail(prompts, mode="plain"):
    if not prompts:
        print("등록된 프롬프트가 없습니다.")
        return
    show_list(prompts, mode)


def print_prompt_detail(prompt, mode="plain"):
    """프롬프트 하나의 내용과 이미지를 출력합니다. 선택 입력은 받지 않습니다."""
    print(f"\n[상세 보기] {prompt['title']}")
    print(f"카테고리: {prompt['category']}")
    print(f"즐겨찾기: {'⭐ 등록됨' if prompt['favorite'] else '미등록'}")
    print("내용:")
    print(prompt["content"])
    image_path = prompt.get("image_path")
    if not image_path:
        print("참고 이미지: 없음 (8번 메뉴에서 연결할 수 있습니다.)")
        return
    print(f"\n참고 이미지: {image_path}")
    try:
        width = min(72, max(8, shutil.get_terminal_size((80, 24)).columns - 4))
        print(f"[ASCII 미리보기] {PREVIEW_LABELS[mode]}")
        print(render_ascii(image_path, width=width, mode=mode))
    except ImagePreviewError as error:
        print(f"이미지 안내: {error}")


def toggle_favorite(prompts):
    prompt = select_prompt(prompts)
    if prompt is None:
        return
    prompt["favorite"] = not prompt["favorite"]
    state = "등록" if prompt["favorite"] else "해제"
    print(f"'{prompt['title']}' 즐겨찾기를 {state}했습니다.")


def show_favorites(prompts, mode="plain"):
    print("\n[즐겨찾기 목록]")
    rows = [(i, p) for i, p in enumerate(prompts, 1) if p["favorite"]]
    if not rows:
        print("즐겨찾기한 프롬프트가 없습니다.")
        return
    browse_prompt_rows(rows, mode)


def read_image_path(current=None):
    print("참고 이미지 한 장을 연결할 수 있습니다. 상대 경로는 프로젝트 폴더 기준입니다.")
    print("파일 경로 입력 / Enter: 현재 연결 유지 또는 건너뛰기 / -: 연결 해제")
    while True:
        value = input("이미지 경로: ").strip()
        if not value:
            return current
        if value == "-":
            return None
        try:
            return normalize_image_path(value)
        except ImagePreviewError as error:
            print(f"이미지 안내: {error}")


def attach_image(prompts):
    prompt = select_prompt(prompts)
    if prompt is None:
        return
    print(f"현재 이미지: {prompt.get('image_path') or '없음'}")
    prompt["image_path"] = read_image_path(prompt.get("image_path"))
    print(f"참고 이미지: {prompt['image_path'] or '없음'}")


def choose_preview_mode(settings):
    print(f"\n현재 표시 방식: {PREVIEW_LABELS[settings['preview_mode']]}")
    print("1. 흑백 ASCII\n2. 컬러 ASCII\n3. 컬러 픽셀 (한 문자에 위/아래 두 픽셀)")
    number = read_number("표시 방식 번호 (0: 취소): ", 3)
    if number == 0:
        return
    mode = {1: "plain", 2: "color", 3: "pixel"}[number]
    if mode != "plain" and not settings["color_supported"]:
        print("현재 출력 환경에서 컬러를 사용할 수 없어 흑백 ASCII를 유지합니다.")
        print("VSCode 터미널이나 Windows Terminal에서 직접 실행해 주세요.")
        settings["preview_mode"] = "plain"
        return
    settings["preview_mode"] = mode
    print(f"이미지 표시 방식을 {PREVIEW_LABELS[mode]}로 바꿨습니다.")


def show_menu(actions):
    print("\n" + "=" * 46)
    print("NIJI Prompt Pocket | 프롬프트 관리")
    print("=" * 46)
    for number, (label, _) in actions.items():
        print(f"{number}. {label}")
    print("0. 종료")


def main():
    # Windows 터미널에서도 한글과 즐겨찾기 별을 출력합니다.
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    prompts = create_initial_prompts()
    color_supported = enable_color()
    settings = {
        "color_supported": color_supported,
        "preview_mode": "pixel" if color_supported else "plain",
    }
    actions = {
        "1": ("프롬프트 추가", add_prompt),
        "2": ("전체 목록", lambda data: show_list(data, settings["preview_mode"])),
        "3": ("카테고리별 조회", lambda data: show_by_category(data, settings["preview_mode"])),
        "4": ("키워드 검색", lambda data: search_prompts(data, settings["preview_mode"])),
        "5": ("상세 보기 / 이미지 미리보기", lambda data: show_detail(data, settings["preview_mode"])),
        "6": ("즐겨찾기 추가 / 해제", toggle_favorite),
        "7": ("즐겨찾기 목록", lambda data: show_favorites(data, settings["preview_mode"])),
        "8": ("참고 이미지 연결 / 교체 / 해제", attach_image),
        "9": ("이미지 표시 방식 변경", lambda _: choose_preview_mode(settings)),
    }
    clear_screen()
    print("NIJI용 기본 프롬프트 3개가 준비되어 있습니다.")
    print("추가한 데이터와 즐겨찾기는 종료하면 초기화됩니다.")
    print(f"이미지 표시: {PREVIEW_LABELS[settings['preview_mode']]} (9번 메뉴에서 변경)")
    try:
        while True:
            show_menu(actions)
            choice = input("메뉴 번호: ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                print("잘못된 메뉴 번호입니다. 메뉴에서 다시 선택해 주세요.")
                continue
            clear_screen()
            action[1](prompts)
    except (EOFError, KeyboardInterrupt):
        print("\n입력이 종료되었습니다.")
    print("프로그램을 종료합니다. 이번 실행의 변경사항은 초기화됩니다.")


if __name__ == "__main__":
    main()
