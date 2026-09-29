"""번호 유지, 입력 검증, 세션 초기화, 이미지 오류를 확인하는 회귀 테스트."""

import contextlib
import io
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


def call_with_input(function, prompts, answers=()):
    output = io.StringIO()
    with patch("builtins.input", side_effect=answers), contextlib.redirect_stdout(output):
        function(prompts)
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
        output = call_with_input(main.search_prompts, self.prompts, ["", "ANIME"])
        self.assertIn("3. ", output)
        self.assertIn("애니메이션 클로즈업", output)
        self.assertNotIn("Live2D 전신", output)

    def test_search_matches_title_and_handles_no_results(self):
        self.assertIn("2개", call_with_input(main.search_prompts, self.prompts, ["전신"]))
        self.assertIn("검색 결과가 없습니다", call_with_input(main.search_prompts, self.prompts, ["없음123"]))

    def test_category_empty_and_original_numbers(self):
        self.assertIn("표시할 프롬프트가 없습니다", call_with_input(main.show_by_category, self.prompts, ["1"]))
        self.assertIn("3. ", call_with_input(main.show_by_category, self.prompts, ["2"]))

    def test_favorite_toggle_and_empty_favorites(self):
        call_with_input(main.toggle_favorite, self.prompts, ["x", "99", "2"])
        self.assertTrue(self.prompts[1]["favorite"])
        output = call_with_input(main.show_favorites, self.prompts)
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
        output = call_with_input(main.show_detail, self.prompts, ["1"])
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


class ImageTests(unittest.TestCase):
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
            self.assertIn("3개", call_with_input(main.show_list, create_initial_prompts()))


class ConsoleTests(unittest.TestCase):
    def test_full_console_session_and_relaunch_from_another_directory(self):
        answers = [
            "bad", "2", "", "1", "추가 테스트", "prompt line 1", "prompt line 2", ".", "2", "", "",
            "4", "prompt line", "", "6", "4", "", "7", "", "5", "3", "", "0",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            run = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "main.py")],
                input="\n".join(answers) + "\n", text=True, encoding="utf-8",
                capture_output=True, cwd=temporary, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            for expected in ["잘못된 메뉴 번호", "4번 프롬프트를 추가", "4. ⭐", "[ASCII 미리보기]"]:
                self.assertIn(expected, run.stdout)
            self.assertNotIn("Traceback", run.stdout + run.stderr)
            reset = subprocess.run([sys.executable, str(ROOT / "main.py")],
                input="2\n\n7\n\n0\n", text=True, encoding="utf-8", capture_output=True,
                cwd=temporary, timeout=20)
            self.assertEqual(reset.returncode, 0, reset.stderr)
            self.assertIn("전체 프롬프트: 3개", reset.stdout)
            self.assertNotIn("추가 테스트", reset.stdout)
            self.assertIn("즐겨찾기한 프롬프트가 없습니다", reset.stdout)

    def test_end_of_input_exits_cleanly(self):
        run = subprocess.run([sys.executable, str(ROOT / "main.py")], input="",
            text=True, encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 0)
        self.assertIn("입력이 종료", run.stdout)


if __name__ == "__main__":
    unittest.main()
