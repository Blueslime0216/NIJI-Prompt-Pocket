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
    actions = {}
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
    except (EOFError, KeyboardInterrupt):
        print("\n입력이 종료되었습니다.")
    print("프로그램을 종료합니다. 이번 실행의 변경사항은 초기화됩니다.")


if __name__ == "__main__":
    main()
