"""NIJI Prompt Pocket: 번호 메뉴로 사용하는 프롬프트 관리 프로그램."""

import sys

from seed_data import CATEGORIES, create_initial_prompts


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
    prompts.append({
        "title": title,
        "content": content,
        "category": category,
        "favorite": False,
        "image_path": None,
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


def show_list(prompts):
    print(f"\n[전체 프롬프트: {len(prompts)}개]")
    print_prompt_rows(list(enumerate(prompts, start=1)))


def show_by_category(prompts):
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
    print_prompt_rows(rows)


def search_prompts(prompts):
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
    print_prompt_rows(rows)


def select_prompt(prompts):
    if not prompts:
        print("등록된 프롬프트가 없습니다.")
        return None
    show_list(prompts)
    number = read_number("프롬프트 번호 (0: 취소): ", len(prompts))
    return prompts[number - 1] if number else None


def show_detail(prompts):
    prompt = select_prompt(prompts)
    if prompt is None:
        return
    print(f"\n[상세 보기] {prompt['title']}")
    print(f"카테고리: {prompt['category']}")
    print(f"즐겨찾기: {'⭐ 등록됨' if prompt['favorite'] else '미등록'}")
    print("내용:")
    print(prompt["content"])


def toggle_favorite(prompts):
    prompt = select_prompt(prompts)
    if prompt is None:
        return
    prompt["favorite"] = not prompt["favorite"]
    state = "등록" if prompt["favorite"] else "해제"
    print(f"'{prompt['title']}' 즐겨찾기를 {state}했습니다.")


def show_favorites(prompts):
    print("\n[즐겨찾기 목록]")
    rows = [(i, p) for i, p in enumerate(prompts, 1) if p["favorite"]]
    if not rows:
        print("즐겨찾기한 프롬프트가 없습니다.")
        return
    print_prompt_rows(rows)


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
    actions = {
        "1": ("프롬프트 추가", add_prompt),
        "2": ("전체 목록", show_list),
        "3": ("카테고리별 조회", show_by_category),
        "4": ("키워드 검색", search_prompts),
        "5": ("상세 보기 / 이미지 미리보기", show_detail),
        "6": ("즐겨찾기 추가 / 해제", toggle_favorite),
        "7": ("즐겨찾기 목록", show_favorites),
    }
    print("NIJI용 예시 프롬프트 3개가 준비되어 있습니다.")
    print("추가한 데이터와 즐겨찾기는 종료하면 초기화됩니다.")
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
            action[1](prompts)
            input("\n메뉴로 돌아가려면 Enter를 누르세요: ")
    except (EOFError, KeyboardInterrupt):
        print("\n입력이 종료되었습니다.")
    print("프로그램을 종료합니다. 이번 실행의 변경사항은 초기화됩니다.")


if __name__ == "__main__":
    main()
