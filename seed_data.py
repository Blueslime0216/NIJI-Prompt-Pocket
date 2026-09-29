"""사용자가 제공한 NIJI 프롬프트와 참고 이미지. 실행마다 새 복사본을 사용합니다."""

CATEGORIES = ["텍스트 생성", "이미지 생성", "영상 생성", "페르소나", "자동화", "기타"]

SAMPLE_PROMPTS = [
    {
        "title": "Live2D 전신 캐릭터 (chaos 40)",
        "content": "VTuber, full-body pose, girl, Live2D --chaos 40 --ar 2:3 --niji 7",
        "category": "이미지 생성",
        "favorite": False,
        "image_path": "assets/sample-01.png",
    },
    {
        "title": "Live2D 전신 캐릭터 (기본)",
        "content": "VTuber, full-body pose, girl, Live2D --ar 2:3 --niji 7",
        "category": "이미지 생성",
        "favorite": False,
        "image_path": "assets/sample-02.png",
    },
    {
        "title": "애니메이션 클로즈업 장면",
        "content": (
            "anime screencap, anime episode still, girl, close-up, cinematic lighting, "
            "8k, high resolution --ar 16:9 --niji 7 --raw --stylize 200 --profile 7ztapke"
        ),
        "category": "이미지 생성",
        "favorite": False,
        "image_path": "assets/sample-03.png",
    },
]


def create_initial_prompts():
    """매 실행마다 독립적인 리스트와 딕셔너리를 만듭니다."""
    return [prompt.copy() for prompt in SAMPLE_PROMPTS]
