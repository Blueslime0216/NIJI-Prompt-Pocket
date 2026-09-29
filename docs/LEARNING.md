# 코드와 Git 학습 안내

## Python 코드 읽는 순서

1. `seed_data.py`: `SAMPLE_PROMPTS`는 리스트이고, 각 프롬프트는 딕셔너리입니다. `favorite`에는 `True`/`False` 불리언을 사용합니다.
2. `main.py`의 `main()`: 실행마다 새 데이터를 만들고, `while` 반복문에서 메뉴 번호를 입력받습니다. `if` 조건문으로 종료와 잘못된 번호를 처리합니다.
3. `add_prompt()`: 값을 입력받아 딕셔너리를 만들고 `append()`로 리스트에 추가합니다. `read_required()`는 공백 입력을 거절합니다.
4. `show_list()`와 `print_prompt_rows()`: `enumerate(..., start=1)`로 번호를 붙입니다. 검색·카테고리·즐겨찾기 결과에서도 같은 번호를 유지합니다.
5. `search_prompts()`와 `show_by_category()`: 조건에 맞는 데이터만 모읍니다. 검색에서는 `casefold()`로 대소문자 차이를 없앱니다.
6. `toggle_favorite()`: `not`으로 즐겨찾기 여부를 뒤집습니다.
7. `image_preview.py`: 파일을 읽고 작게 줄인 뒤 밝기 값을 문자에 대응시킵니다. 오류는 `try`/`except`로 처리해 기본 기능을 계속 사용할 수 있게 합니다.

`create_initial_prompts()`가 기본 딕셔너리를 복사하기 때문에 실행마다 초기 상태로 시작합니다. 파일 저장 기능을 넣지 않았으므로 프로그램 종료 후 추가 내용과 즐겨찾기는 초기화됩니다.

## Git을 사용하는 이유

Git은 변경 이력을 기록해서 과거 상태를 비교하고 돌아갈 수 있게 합니다. 브랜치는 기능을 따로 작업할 수 있게 하고, 병합은 그 작업을 기본 브랜치에 합칩니다. GitHub는 원격 저장소를 호스팅해 코드를 공유하고 백업할 수 있게 합니다.

- `git init`: 현재 폴더에 로컬 저장소를 만듭니다.
- `git add 파일`: 다음 커밋에 포함할 변경을 선택합니다.
- `git commit -m "설명"`: 선택한 변경을 하나의 이력으로 기록합니다.
- `git push`: 로컬 커밋을 원격 저장소로 올립니다.
- `git pull`: 원격 변경을 가져와 현재 브랜치에 반영합니다. `--ff-only`는 자동 병합 커밋 없이 앞으로 이동할 수 있을 때만 반영합니다.
- `git checkout -b 브랜치`: 새 브랜치를 만들고 전환합니다.
- `git checkout main`: 기존 `main` 브랜치로 전환합니다.
- `git clone URL`: 원격 저장소와 이력을 새 폴더에 내려받습니다.
- `git merge 브랜치`: 지정한 브랜치의 작업을 현재 브랜치에 합칩니다.

## 이 프로젝트의 실제 목록 기능 흐름

```bash
git checkout -b feature/prompt-list
# 목록 출력 기능을 구현
git add main.py
git commit -m "feat: display prompt list with original numbers and favorite stars"
git checkout main
git merge --no-ff feature/prompt-list
```

`--no-ff`로 병합 커밋을 남겼기 때문에 `git log --oneline --graph --all`에서 브랜치가 나뉘고 합쳐진 기록을 확인할 수 있습니다.

## 본인이 확인할 항목

- 기본 프롬프트를 설명하고, 새 프롬프트 하나를 직접 추가해 보세요.
- 검색 결과의 번호와 전체 목록 번호가 같은지 확인하세요.
- 즐겨찾기를 지정했다가 해제해 보세요.
- 이미지를 연결하고, 종료 후 다시 실행해 상태 초기화를 확인하세요.
- 과제의 ‘이전 미션에서 작성한 프롬프트’ 조건에 제공한 3개가 해당하는지 확인하세요.
- `git log`에서 추가·검색·즐겨찾기·이미지 기능 커밋을 찾아보세요.
