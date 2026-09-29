"""번호 유지, 입력 검증, 재실행 후 저장 상태, 이미지 오류를 확인하는 회귀 테스트."""

import contextlib
import io
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import main
from image_preview import ImagePreviewError, normalize_image_path, render_ascii
from seed_data import create_initial_prompts

ROOT = Path(__file__).resolve().parents[1]


def call_with_input(function, prompts, answers=(), **kwargs):
    output = io.StringIO()
    with patch("builtins.input", side_effect=answers), contextlib.redirect_stdout(output):
        function(prompts, **kwargs)
    return output.getvalue()


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.prompts = create_initial_prompts()

    def test_initial_data_and_session_reset(self):
        self.assertEqual(len(self.prompts), 3)
        self.assertEqual(self.prompts[0]["content"],
                         "VTuber, full-body pose, girl, Live2D --chaos 40 --ar 2:3 --niji 7")
        self.prompts[0]["favorite"] = True
        self.prompts.append({})
        fresh = create_initial_prompts()
        self.assertEqual(len(fresh), 3)
        self.assertFalse(fresh[0]["favorite"])

    def test_add_rejects_empty_fields_and_supports_multiline_custom_category(self):
        output = call_with_input(main.add_prompt, self.prompts,
            [" ", "테스트", ".", "first line", "second line", ".",
             "bad", "-2", "99", "0", "", "직접 만든 분류", ""])
        added = self.prompts[3]
        self.assertEqual(added["content"], "first line\nsecond line")
        self.assertEqual(added["category"], "직접 만든 분류")
        self.assertFalse(added["favorite"])
        self.assertIsNone(added["image_path"])
        self.assertIn("내용이 비어", output)
        self.assertIn("잘못된 번호", output)
        self.assertIn("직접 만든 분류", main.get_categories(self.prompts))

    def test_search_matches_content_case_insensitively_and_keeps_original_number(self):
        output = call_with_input(main.search_prompts, self.prompts, ["", "ANIME", ""])
        self.assertIn("3. ", output)
        self.assertIn("애니메이션 클로즈업", output)
        self.assertNotIn("Live2D 전신", output)

    def test_search_matches_title_and_handles_no_results(self):
        self.assertIn("2개", call_with_input(main.search_prompts, self.prompts, ["전신", ""]))
        self.assertIn("검색 결과가 없습니다", call_with_input(main.search_prompts, self.prompts, ["없음123"]))

    def test_category_empty_and_original_numbers(self):
        self.assertIn("표시할 프롬프트가 없습니다", call_with_input(main.show_by_category, self.prompts, ["1"]))
        self.assertIn("3. ", call_with_input(main.show_by_category, self.prompts, ["2", ""]))

    def test_favorite_toggle_and_empty_favorites(self):
        call_with_input(main.toggle_favorite, self.prompts, ["x", "99", "2"])
        self.assertTrue(self.prompts[1]["favorite"])
        output = call_with_input(main.show_favorites, self.prompts, [""])
        self.assertIn("2. ⭐", output)
        self.assertNotIn("chaos 40", output)
        call_with_input(main.toggle_favorite, self.prompts, ["2"])
        self.assertFalse(self.prompts[1]["favorite"])
        self.assertIn("즐겨찾기한 프롬프트가 없습니다", call_with_input(main.show_favorites, self.prompts))

    def test_empty_list_and_cancel_selection(self):
        self.assertIn("표시할 프롬프트가 없습니다", call_with_input(main.show_list, []))
        self.assertIn("등록된 프롬프트가 없습니다", call_with_input(main.show_detail, []))
        self.assertNotIn("[상세 보기]", call_with_input(main.show_detail, self.prompts, ["0"]))

    def test_detail_survives_missing_image(self):
        self.prompts[0]["image_path"] = "does-not-exist.png"
        output = call_with_input(main.show_detail, self.prompts, ["1", ""])
        self.assertIn(self.prompts[0]["content"], output)
        self.assertIn("이미지 안내", output)

    def test_attachment_keep_replace_remove_and_invalid_path(self):
        current = self.prompts[0]["image_path"]
        call_with_input(main.attach_image, self.prompts, ["1", ""])
        self.assertEqual(self.prompts[0]["image_path"], current)
        call_with_input(main.attach_image, self.prompts,
                        ["1", "missing.png", '"assets/sample-03.png"'])
        self.assertEqual(self.prompts[0]["image_path"], "assets/sample-03.png")
        call_with_input(main.attach_image, self.prompts, ["1", "-"])
        self.assertIsNone(self.prompts[0]["image_path"])


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.prompts = create_initial_prompts()
        for prompt in self.prompts:
            prompt["image_path"] = None

    def test_list_can_open_multiple_details_without_leaving_results(self):
        output = call_with_input(main.show_list, self.prompts, ["2", "1", ""])
        self.assertEqual(output.count("[상세 보기]"), 2)
        self.assertLess(output.index("[상세 보기] " + self.prompts[1]["title"]),
                        output.index("[상세 보기] " + self.prompts[0]["title"]))
        self.assertEqual(output.count("[현재 목록]"), 2)

    def test_search_rejects_non_result_numbers_and_keeps_original_id(self):
        output = call_with_input(main.search_prompts, self.prompts,
                                 ["ANIME", "abc", "-1", "1", "99", "3", "0"])
        self.assertEqual(output.count("[상세 보기]"), 1)
        self.assertIn("[상세 보기] " + self.prompts[2]["title"], output)
        self.assertNotIn("[상세 보기] " + self.prompts[0]["title"], output)
        self.assertEqual(output.count("현재 목록에 있는"), 3)

    def test_category_details_only_accept_visible_number(self):
        self.prompts[1]["category"] = "텍스트 생성"
        output = call_with_input(main.show_by_category, self.prompts, ["1", "1", "2", ""])
        self.assertIn("현재 목록에 있는", output)
        self.assertIn("[상세 보기] " + self.prompts[1]["title"], output)
        self.assertEqual(output.count("[상세 보기]"), 1)

    def test_favorites_can_open_detail_and_return_with_zero(self):
        self.prompts[1]["favorite"] = True
        output = call_with_input(main.show_favorites, self.prompts, ["1", "2", "0"])
        self.assertIn("현재 목록에 있는", output)
        self.assertIn("즐겨찾기: ⭐ 등록됨", output)
        self.assertEqual(output.count("[상세 보기]"), 1)

    def test_all_detail_routes_preserve_selected_color_mode(self):
        prompts = create_initial_prompts()
        prompts[1]["favorite"] = True
        scenarios = [
            (main.show_list, ["2", ""], 1),
            (main.show_by_category, ["2", "2", ""], 1),
            (main.search_prompts, ["ANIME", "3", ""], 2),
            (main.show_favorites, ["2", ""], 1),
            (main.show_detail, ["1", ""], 0),
        ]
        for function, answers, index in scenarios:
            with self.subTest(route=function.__name__), patch("main.render_ascii", return_value="PREVIEW") as render:
                output = call_with_input(function, prompts, answers, mode="pixel")
                self.assertIn("컬러 픽셀", output)
                self.assertEqual(render.call_count, 1)
                self.assertEqual(render.call_args.args[0], prompts[index]["image_path"])
                self.assertEqual(render.call_args.kwargs["mode"], "pixel")

    def test_empty_results_do_not_wait_for_navigation_input(self):
        for function in (main.show_list, main.show_favorites, main.show_detail):
            with self.subTest(route=function.__name__):
                output = call_with_input(function, [])
                self.assertNotIn("상세 볼 프롬프트 번호", output)


class ImageTests(unittest.TestCase):
    def test_colored_modes_use_valid_rgb_and_reset_each_row(self):
        for mode in ("color", "pixel"):
            with self.subTest(mode=mode):
                result = render_ascii("assets/sample-03.png", width=40, max_height=12, mode=mode)
                self.assertIn("\x1b[38;2;", result)
                self.assertTrue(all(line.endswith("\x1b[0m") for line in result.splitlines()))
                stripped = re.sub(r"\x1b\[[0-9;]*m", "", result)
                self.assertLessEqual(len(stripped.splitlines()), 12)
                self.assertLessEqual(max(map(len, stripped.splitlines())), 40)
                if mode == "pixel":
                    self.assertIn("\x1b[48;2;", result)
                    self.assertEqual(set(stripped.replace("\n", "")), {"▀"})

    def test_half_block_uses_top_foreground_and_bottom_background(self):
        from PIL import Image
        from image_preview import _render_half_blocks
        image = Image.new("RGB", (1, 2))
        image.putpixel((0, 0), (255, 0, 0))
        image.putpixel((0, 1), (0, 0, 255))
        self.assertEqual(_render_half_blocks(image), "\x1b[38;2;255;0;0m\x1b[48;2;0;0;255m▀\x1b[0m")

    def test_half_block_odd_height_and_display_fallback(self):
        from PIL import Image
        from image_preview import _render_half_blocks
        self.assertEqual(len(_render_half_blocks(Image.new("RGB", (2, 3))).splitlines()), 2)
        settings = {"preview_mode": "plain", "color_supported": False}
        output = call_with_input(main.choose_preview_mode, settings, ["3"])
        self.assertEqual(settings["preview_mode"], "plain")
        self.assertIn("흑백 ASCII를 유지", output)
        settings["color_supported"] = True
        call_with_input(main.choose_preview_mode, settings, ["3"])
        self.assertEqual(settings["preview_mode"], "pixel")

    def test_all_samples_render_printable_bounded_ascii(self):
        for prompt in create_initial_prompts():
            with self.subTest(image=prompt["image_path"]):
                result = render_ascii(prompt["image_path"])
                lines = result.splitlines()
                self.assertLessEqual(len(lines), 32)
                self.assertLessEqual(max(map(len, lines)), 72)
                self.assertEqual(len(set(map(len, lines))), 1)
                self.assertTrue(set(result) <= set(" .:-=+*#%@\n"))
                self.assertTrue(result.strip())

    def test_missing_file_directory_and_corrupt_file(self):
        with self.assertRaises(ImagePreviewError):
            render_ascii("not-there.png")
        with self.assertRaises(ImagePreviewError):
            render_ascii(ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            bad = Path(temporary) / "broken.png"
            bad.write_bytes(b"This is not an image.")
            with self.assertRaises(ImagePreviewError):
                render_ascii(bad)

    def test_transparency_composited_as_blank_background(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "transparent.png"
            Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(path)
            self.assertEqual(render_ascii(path).strip(), "")

    def test_pixel_limit(self):
        with patch("image_preview.MAX_IMAGE_PIXELS", 1):
            with self.assertRaisesRegex(ImagePreviewError, "2,000만"):
                render_ascii("assets/sample-01.png")

    def test_project_relative_paths_and_missing_pillow(self):
        self.assertEqual(normalize_image_path('"assets/sample-01.png"'), "assets/sample-01.png")
        with patch.dict(sys.modules, {"PIL": None}):
            with self.assertRaisesRegex(ImagePreviewError, "Pillow"):
                render_ascii("assets/sample-01.png")
            self.assertIn("3개", call_with_input(main.show_list, create_initial_prompts(), [""]))


class ConsoleTests(unittest.TestCase):
    def test_full_console_session_persists_after_relaunch_from_another_directory(self):
        answers = [
            "bad", "2", "", "1", "추가 테스트", "prompt line 1", "prompt line 2", ".", "2", "",
            "4", "prompt line", "4", "", "6", "4", "7", "4", "", "5", "3", "0", "0",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            environment = os.environ.copy()
            environment["NIJI_PROMPT_POCKET_DATA_DIR"] = str(Path(temporary) / "prompt-data")
            run = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "main.py")],
                input="\n".join(answers) + "\n", text=True, encoding="utf-8",
                capture_output=True, cwd=temporary, env=environment, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            for expected in ["잘못된 메뉴 번호", "4번 프롬프트를 추가", "4. ⭐", "[ASCII 미리보기]"]:
                self.assertIn(expected, run.stdout)
            self.assertNotIn("Traceback", run.stdout + run.stderr)
            self.assertNotIn("메뉴로 돌아가려면 Enter를 누르세요", run.stdout)
            self.assertNotIn("입력이 종료되었습니다", run.stdout)
            self.assertEqual(run.stdout.count("잘못된 메뉴 번호"), 1)
            relaunch = subprocess.run([sys.executable, str(ROOT / "main.py")],
                input="2\n\n7\n0\n", text=True, encoding="utf-8", capture_output=True,
                cwd=temporary, env=environment, timeout=20)
            self.assertEqual(relaunch.returncode, 0, relaunch.stderr)
            self.assertIn("전체 프롬프트: 4개", relaunch.stdout)
            self.assertIn("추가 테스트", relaunch.stdout)
            self.assertIn("저장된 프롬프트 4개를 불러왔습니다", relaunch.stdout)
            self.assertNotIn("잘못된 메뉴 번호", relaunch.stdout)

    def test_end_of_input_exits_cleanly(self):
        run = subprocess.run([sys.executable, str(ROOT / "main.py")], input="",
            text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 0)
        self.assertIn("입력이 종료", run.stdout)


if __name__ == "__main__":
    unittest.main()
