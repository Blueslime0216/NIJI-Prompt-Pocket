"""기본 데이터. 제출 전 본인의 이전 미션 프롬프트 3개로 교체하세요."""

CATEGORIES = ["텍스트 생성", "이미지 생성", "영상 생성", "페르소나", "자동화", "기타"]

# 특정 NIJI 버전의 옵션에 의존하지 않는 개발용 예시입니다.
SAMPLE_PROMPTS = [
    {
        "title": "달빛 아래 고양이 마법사",
        "content": (
            "A small black cat wizard wearing a pointed hat, sitting on a rooftop "
            "under a crescent moon, warm glowing eyes, whimsical anime illustration, "
            "clean line art, deep blue and soft gold palette, no text"
        ),
        "category": "이미지 생성",
        "favorite": False,
        "image_path": None,
    },
    {
        "title": "비 오는 도시의 서점",
        "content": (
            "A quiet bookshop on a rainy evening in a narrow city street, "
            "warm light spilling from the windows, reflections on wet pavement, "
            "anime background art, detailed environment, peaceful mood, no text"
        ),
        "category": "이미지 생성",
        "favorite": False,
        "image_path": None,
    },
    {
        "title": "봄 정원의 캐릭터 초상",
        "content": (
            "Portrait of an original fantasy traveler in a spring garden, "
            "short silver hair, green eyes, simple navy cloak, gentle smile, "
            "anime character illustration, soft daylight, clear silhouette, no text"
        ),
        "category": "이미지 생성",
        "favorite": False,
        "image_path": None,
    },
]


def create_initial_prompts():
    """매 실행마다 독립적인 리스트와 딕셔너리를 만듭니다."""
    return [prompt.copy() for prompt in SAMPLE_PROMPTS]
