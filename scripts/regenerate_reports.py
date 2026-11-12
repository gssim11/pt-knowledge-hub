#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 리포트를 현재 프롬프트(PROMPT_VERSION)로 다시 생성한다.
- manifest.json 의 각 항목을 PMID로 PubMed 초록을 다시 받아 Gemini로 재작성
- 발행일·파일 경로·id는 그대로 두고 본문 HTML, 제목, 요약, 태그만 교체
- 이미 현재 버전인 항목은 건너뛰므로 중간에 멈춰도 다시 실행하면 남은 것만 처리
- 성공할 때마다 manifest.json 을 저장한다
GitHub Actions의 'Regenerate Reports' 워크플로(수동 실행)에서 돌린다.
"""
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import auto_generate_daily as g  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
M_PATH = ROOT / "manifest.json"
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "100") or "100")
CFG_BY_STREAM = {c["stream"]: c for c in g.STREAM_CONFIGS}


def save(manifest):
    M_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def gemini_with_retry(cfg, paper, date_str):
    last = None
    for attempt in range(4):
        try:
            out = g.call_gemini(cfg, paper, date_str)
            html = out.get("html_code", "")
            if "<body" not in html.lower() or len(html) < 2000:
                raise ValueError(f"HTML이 비정상적으로 짧거나 <body>가 없음 ({len(html)}자)")
            return out
        except Exception as e:  # 429·5xx·JSON 오류 모두 재시도
            last = e
            wait = 20 * (attempt + 1)
            print(f"    재시도 {attempt + 1}/4 — {e} ({wait}초 대기)")
            time.sleep(wait)
    raise last


def main():
    if not g.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 없습니다.")
    manifest = json.loads(M_PATH.read_text(encoding="utf-8"))
    todo = [x for x in manifest if x.get("prompt_version") != g.PROMPT_VERSION and x.get("pmid")]
    print(f"재생성 대상 {len(todo)}건 (이번 실행 최대 {MAX_ITEMS}건)")
    done = failed = 0
    for x in todo[:MAX_ITEMS]:
        cfg = CFG_BY_STREAM.get(x["stream"])
        if not cfg:
            print(f"[건너뜀] {x['id']} — 알 수 없는 stream {x['stream']}")
            continue
        print(f"[{x['id']}] PMID {x['pmid']}")
        paper = g.fetch_paper(x["pmid"])
        if not paper:
            print("    초록을 받지 못해 건너뜀(기존 리포트 유지)")
            failed += 1
            continue
        try:
            out = gemini_with_retry(cfg, paper, x["date"])
        except Exception as e:
            print(f"    실패 — 기존 리포트 유지: {e}")
            failed += 1
            continue
        (ROOT / x["path"]).write_text(g.add_notice(out["html_code"]), encoding="utf-8")
        x["title"] = out["title"]
        x["summary"] = out["summary"]
        x["tags"] = [t for t in out["tags"] if t in g.ALLOWED_TAGS][:4] or ["#RCT저널브리핑"]
        x["prompt_version"] = g.PROMPT_VERSION
        save(manifest)
        done += 1
        print(f"    완료 ({done})")
        time.sleep(7)  # Gemini 분당 요청 한도 여유
    remaining = sum(1 for x in manifest if x.get("prompt_version") != g.PROMPT_VERSION and x.get("pmid"))
    print(f"재생성 {done}건 성공, {failed}건 실패, 남은 대상 {remaining}건")


if __name__ == "__main__":
    main()
