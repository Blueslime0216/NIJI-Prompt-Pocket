# 제출 안내

저장소 URL: https://github.com/Blueslime0216/NIJI-Prompt-Pocket

## 제출할 자료

1. 위 GitHub 저장소 URL
2. VSCode, Python 버전, Git 설정이 보이는 개발 환경 화면
3. 메뉴, 프롬프트 추가, 목록, 검색, 즐겨찾기, ASCII 미리보기 실행 결과 화면
4. `git log --oneline --graph` 결과 화면

프로젝트 로컬의 `submission/screenshots/`와 `submission/local-*.txt`는 제출 준비용이며 Git에 포함되지 않습니다. 준비된 실행 결과 스크린샷은 실제 콘솔에서 수집한 출력 로그를 VSCode에서 열어 촬영한 것입니다. 실시간 터미널 화면을 요구하는 제출처라면 아래 절차로 별도 촬영하세요.

## 직접 실행하며 촬영하기

```bash
python --version
git --version
git config --get user.name
git config --get user.email
git config --get init.defaultBranch
python main.py
```

1. 시작 메뉴를 촬영합니다.
2. `1`번에서 제목·내용·카테고리를 입력해 추가한 결과를 촬영합니다. 입력 중 Esc로 취소할 수도 있고, 내용 입력은 `.`만 입력한 줄로 마칩니다.
3. `2`번에서 새 항목이 포함된 목록을 촬영합니다. 목록에서 프롬프트 번호를 입력하면 바로 상세 보기가 열립니다. Enter 또는 `0`으로 메뉴로 돌아갑니다.
4. `4`번에서 `Live2D`를 검색한 결과를 촬영하고 `2`번 프롬프트를 바로 열어 봅니다. Enter로 메뉴로 돌아갑니다.
5. `5`번에서 `3`번 프롬프트의 이미지 미리보기를 확인하고 Enter로 메뉴로 돌아갑니다.
6. `6`번에서 즐겨찾기를 등록하고 `7`번 목록을 촬영합니다. 여기서도 번호로 상세를 열 수 있습니다. Enter로 메뉴로 돌아갑니다.
7. `0`으로 종료 후 `git log --oneline --graph`를 실행해 촬영합니다.

프롬프트 추가·삭제·즐겨찾기·이미지 연결은 `local-data/prompts.json`에 자동 저장되므로 재실행 후에도 유지됩니다. `10`번에서 프롬프트를 선택하고 다시 확인해 삭제할 수 있습니다. 추가 도중 Esc를 누르면 입력을 취소합니다. 프로그램이 메뉴로 돌아오면 화면을 정리해 메뉴를 위쪽에 다시 표시합니다.

스크린샷 제출 전 다른 프로젝트나 개인정보가 보이지 않는지 확인하세요. VSCode의 GitHub 계정 연결은 Accounts 메뉴에서 직접 확인할 수 있습니다.
