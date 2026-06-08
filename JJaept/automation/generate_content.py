from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "automation" / "state.json"
INDEX_PATH = ROOT / "content-index.json"
KST = ZoneInfo("Asia/Seoul")

LIFESTYLE_TOPICS = {
    "lifestyle_am": [
        "7평 원룸 제습기 10L면 충분할까?",
        "변기 핑크색 물때, 곰팡이일까?",
        "원룸 화장실 냄새가 계속 날 때 확인할 5가지",
        "자취방 습도 몇 %가 적당할까?",
        "장마철 원룸 빨래 냄새 안 나게 말리는 법",
    ],
    "lifestyle_pm": [
        "원룸 곰팡이가 계속 생기는 진짜 이유",
        "처음 자취할 때 꼭 필요한 물건과 안 사도 되는 물건",
        "원룸 전기세 많이 나오는 이유",
        "원룸 계약 전 꼭 봐야 할 체크리스트",
        "작은 원룸 수납, 먼저 버려야 할 것부터 정리하기",
    ],
}


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default.copy()
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write("\n")
    temporary.replace(path)


def extract_title(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def lifestyle_prompt(topic: str, today: str) -> str:
    return f"""
오늘 날짜는 {today}, 대한민국 기준이다.

다음 주제로 한국의 자취·원룸 생활 블로그에 바로 게시할 완성형 글을 작성하라.
주제: {topic}

목표:
- 실제 생활 문제를 해결하는 검색형 콘텐츠
- 월 10만 방문자를 목표로 하는 고품질 생활지식 블로그
- 독자는 한국에서 원룸 또는 소형 주거공간에 혼자 사는 사람

작성 규칙:
- 결과는 설명 없이 블로그 콘텐츠 자체만 출력한다.
- 첫 줄은 반드시 '# 제목' 형식으로 쓴다.
- 결론을 초반에 제시하고 H2/H3 제목으로 읽기 쉽게 구성한다.
- 실제 자취 상황, 원인, 해결 순서, 체크리스트, 흔한 실수, 비교표를 필요한 만큼 포함한다.
- 최신 가격·제품 사양·법률·공공정책·건강·안전 관련 주장은 웹 검색으로 검증한다.
- 중요한 사실은 출처 링크와 자료 게시일 또는 업데이트일을 본문 또는 출처 영역에 적는다.
- 국내 공식기관 자료를 우선하고, 건강·과학 주장은 공공기관 또는 신뢰할 수 있는 의료기관 자료와 교차 검증한다.
- 근거가 없는 숫자나 개인 경험을 만들지 않는다.
- 특정 제품을 광고하듯 추천하지 않는다.
- 금액은 원화로만 표시한다.
- 본문 마지막에 '함께 읽으면 좋은 글', 'SEO 정보', '출처', '신뢰율'을 포함한다.
- 쇼츠, 릴스, 유튜브, SNS 대본은 넣지 않는다.
- 'GPT 판단', 사용자에게 하는 설명, 작업 과정 설명은 넣지 않는다.
- 자연스러운 한국어로 쓰고 AI 특유의 상투적인 문장을 피한다.
""".strip()


def stock_prompt(today: str) -> str:
    return f"""
오늘 날짜는 {today}, 대한민국 기준이다.
한국 주식 투자자가 개인 참고용으로 볼 프리미엄 증권가 일일 리포트를 작성하라.
현재 시각이 한국 시장 개장 전이라면 가장 최근 완료된 한국 거래일과 직전 미국 거래일 데이터를 기준으로 삼고, 이를 명확히 표시한다.

필수 구성:
- 첫 줄 '# YYYY-MM-DD 증권가 일일 리포트'
- 핵심 요약
- 코스피·코스닥 및 주요 미국 지수, 환율, 금리, 유가 등 시장 스냅샷
- 국내외 주요 이슈와 섹터 방향성
- 단기·중기 기본/상승/하락 시나리오
- 최근 완료된 한국 거래일에서 급등한 종목 3개: 종목명·코드·등락률·거래량 변화·공시/뉴스 원인·지속 가능성·위험
- 다음 거래일 확인 항목
- 투자 위험 고지
- 출처와 신뢰율

검증 규칙:
- 웹 검색을 사용한다.
- 한국거래소, DART, 한국은행, 금융위원회, 회사 공시, 중앙은행 등 공식 자료를 우선한다.
- 급등률과 가격은 최소 2개 신뢰 가능한 자료로 교차 확인한다.
- 아직 발생하지 않은 당일 장중 급등 종목을 지어내지 않는다.
- 사실과 해석을 분리한다.
- 매수·매도 지시, 목표수익 보장, 과장 표현을 금지한다.
- 확인하지 못한 항목은 '답변 보류: 추가 근거 필요'로 쓴다.
- 설명 없이 리포트 자체만 출력한다.
""".strip()


def create_text(client: OpenAI, prompt: str) -> str:
    model = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.2")
    response = client.responses.create(
        model=model,
        input=prompt,
        tools=[
            {
                "type": "web_search",
                "search_context_size": "high",
                "user_location": {
                    "type": "approximate",
                    "country": "KR",
                    "city": "Seoul",
                    "timezone": "Asia/Seoul",
                },
            }
        ],
        tool_choice="auto",
        reasoning={"effort": "medium"},
        max_output_tokens=10000,
    )
    text = response.output_text.strip()
    if len(text) < 500:
        raise RuntimeError("생성된 본문이 지나치게 짧습니다.")
    return text


def create_image(client: OpenAI, topic: str, output_path: Path) -> None:
    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
    prompt = f"""
한국 자취·원룸 생활지식 블로그의 대표 이미지.
주제: {topic}
현실적인 한국 원룸 내부 또는 해당 생활 문제를 보여주는 깨끗한 에디토리얼 사진 스타일.
밝고 정돈된 자연광, 과장되지 않은 생활감, 광고처럼 보이지 않는 구성.
사람 얼굴, 브랜드 로고, 제품 상표, 워터마크, 글자, 숫자는 넣지 않는다.
블로그 가로 대표 이미지에 맞는 16:9 구성, 핵심 피사체가 중앙에 너무 붙지 않도록 여백을 둔다.
""".strip()
    result = client.images.generate(
        model=model,
        prompt=prompt,
        size="1536x1024",
        quality="medium",
        output_format="webp",
    )
    image_base64 = result.data[0].b64_json
    if not image_base64:
        raise RuntimeError("이미지 데이터가 없습니다.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(image_base64))


def update_index(record: dict) -> None:
    index = load_json(
        INDEX_PATH,
        {"project": "JJaept", "version": 1, "updatedAt": None, "content": []},
    )
    content = index.setdefault("content", [])
    content.append(record)
    index["updatedAt"] = datetime.now(KST).isoformat(timespec="seconds")
    save_json(INDEX_PATH, index)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type",
        required=True,
        choices=["stock", "lifestyle_am", "lifestyle_pm"],
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY 환경변수가 없습니다.")

    client = OpenAI()
    now = datetime.now(KST)
    date_text = now.strftime("%Y-%m-%d")
    state = load_json(
        STATE_PATH,
        {"lifestyle_am_index": 0, "lifestyle_pm_index": 0, "last_runs": {}},
    )

    if args.type == "stock":
        topic = f"{date_text} 증권가 일일 리포트"
        markdown = create_text(client, stock_prompt(date_text))
        relative_markdown = Path("content") / "stock-reports" / now.strftime("%Y") / now.strftime("%m") / f"{date_text}-stock-report.md"
        image_relative = None
        topic_id = "stock"
    else:
        topics = LIFESTYLE_TOPICS[args.type]
        index_key = f"{args.type}_index"
        topic_index = int(state.get(index_key, 0)) % len(topics)
        topic = topics[topic_index]
        topic_id = f"{args.type}-{topic_index + 1:02d}"
        markdown = create_text(client, lifestyle_prompt(topic, date_text))
        relative_markdown = Path("content") / "lifestyle" / now.strftime("%Y") / now.strftime("%m") / f"{date_text}-{topic_id}.md"
        image_relative = Path("images") / now.strftime("%Y") / now.strftime("%m") / f"{date_text}-{topic_id}.webp"
        try:
            create_image(client, topic, ROOT / image_relative)
        except Exception as error:  # 본문은 보존하고 이미지 실패만 기록합니다.
            print(f"이미지 생성 실패: {error}", file=sys.stderr)
            image_relative = None
        state[index_key] = (topic_index + 1) % len(topics)

    title = extract_title(markdown, topic)
    frontmatter = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f'date: "{now.isoformat(timespec="seconds")}"',
        f'type: "{args.type}"',
        f'topic_id: "{topic_id}"',
        'status: "draft"',
        f'image: "{image_relative.as_posix() if image_relative else ""}"',
        "---",
        "",
    ]
    document = "\n".join(frontmatter) + markdown.rstrip() + "\n"
    output_path = ROOT / relative_markdown
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")

    state.setdefault("last_runs", {})[args.type] = now.isoformat(timespec="seconds")
    save_json(STATE_PATH, state)
    update_index(
        {
            "id": f"{date_text}-{topic_id}",
            "title": title,
            "type": args.type,
            "topic": topic,
            "status": "draft",
            "createdAt": now.isoformat(timespec="seconds"),
            "contentPath": relative_markdown.as_posix(),
            "imagePath": image_relative.as_posix() if image_relative else None,
        }
    )

    print(f"생성 완료: {relative_markdown.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
