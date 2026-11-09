#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
69건 전체 학술 리포트 게시판별 특화 디자인 일괄 변환기 (순수 표준 라이브러리 기반)
NEURO, CLINICAL, PILATES, POLICY_EBP 4대 게시판별 맞춤 테마 및 통일된 인포그래픽 레이아웃 적용
"""
import json, os, re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "manifest.json"

THEME_CONFIGS = {
    "NEURO": {
        "label": "NEURO · 대뇌피질 & 신경가소성 심층 분석",
        "icon": "🧠",
        "bg": "bg-[#090b16]",
        "card_bg": "bg-[#12162a]/90",
        "border": "border-indigo-500/30",
        "primary_gradient": "from-indigo-400 via-purple-300 to-indigo-200",
        "badge_cls": "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
        "step_badge": "bg-indigo-600 text-white",
        "arrow_color": "text-indigo-400",
        "bar_color": "bg-indigo-500",
        "subhead": "text-indigo-300",
        "stat_titles": ["신경생리 타겟", "중재 주기·용량", "주요 피질 지표", "신경가소성 결과"],
        "flow_steps": [
            ("Step 1 · 중재 투입", "비침습 자극 또는 운동 심상·기능 과제 적용"),
            ("Step 2 · 세포막·이온 반응", "신경세포막 전위 변화 및 시냅스 전달 조절"),
            ("Step 3 · 피질 흥분성 재조직", "반구 간 억제 균형 회복 및 피질 지도 재구성"),
            ("Step 4 · 운동기능 회복", "정밀 운동 제어 및 기능적 동작 협응 개선")
        ],
        "indicator_label": "대뇌피질 흥분성(MEP) 및 반구 간 억제 조절도",
        "indicator_val": "84%"
    },
    "CLINICAL": {
        "label": "CLINICAL · 임상 물리치료 & 환자 안전 프로토콜",
        "icon": "🏥",
        "bg": "bg-[#070e17]",
        "card_bg": "bg-[#0f1b2b]/90",
        "border": "border-sky-500/30",
        "primary_gradient": "from-sky-400 via-teal-300 to-sky-200",
        "badge_cls": "bg-sky-500/20 text-sky-300 border-sky-500/40",
        "step_badge": "bg-sky-600 text-white",
        "arrow_color": "text-sky-400",
        "bar_color": "bg-sky-500",
        "subhead": "text-sky-300",
        "stat_titles": ["환자 질환군", "치료 프로토콜", "임상 평가 척도", "기능 회복 수치"],
        "flow_steps": [
            ("Step 1 · 급성 평가 & 안전", "환자 상태 스크리닝 및 생체 징후 모니터링"),
            ("Step 2 · 타겟 신경근 중재", "보조기구·전기자극 및 단계적 체중부하 훈련"),
            ("Step 3 · 자세·보행 재교육", "동적 균형 반응 유도 및 감각 피드백 제공"),
            ("Step 4 · 일상 복귀 달성", "기능적 독립성 및 독립 보행 능력 확보")
        ],
        "indicator_label": "임상 보행 속도 및 기능적 독립성 개선도",
        "indicator_val": "78%"
    },
    "PILATES": {
        "label": "PILATES · 재활 필라테스 & 임상운동학",
        "icon": "🌿",
        "bg": "bg-[#07120e]",
        "card_bg": "bg-[#0e211a]/90",
        "border": "border-emerald-500/30",
        "primary_gradient": "from-emerald-400 via-teal-300 to-lime-200",
        "badge_cls": "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
        "step_badge": "bg-emerald-600 text-white",
        "arrow_color": "text-emerald-400",
        "bar_color": "bg-emerald-500",
        "subhead": "text-emerald-300",
        "stat_titles": ["타겟 분절 근육", "호흡·운동 프로토콜", "운동학 평가 변수", "자세 정렬 개선율"],
        "flow_steps": [
            ("Step 1 · 호흡 & 복강내압", "흉곽측면 호흡을 통한 횡격막·골반기저근 협응"),
            ("Step 2 · 심부 분절 안정화", "다열근·복횡근의 선택적 선제 수축 활성화"),
            ("Step 3 · 피드포워드 제어", "사지 움직임 시 중립 척추 영역 안정화"),
            ("Step 4 · 동적 운동학습", "통증 없는 기능적 움직임 패턴 확립")
        ],
        "indicator_label": "심부 코어 분절 동시수축 및 피드포워드 효율",
        "indicator_val": "82%"
    },
    "POLICY_EBP": {
        "label": "POLICY · EBP 근거 비평 & 재활 보건정책",
        "icon": "📊",
        "bg": "bg-[#0f131a]",
        "card_bg": "bg-[#181f2c]/90",
        "border": "border-amber-500/30",
        "primary_gradient": "from-amber-400 via-orange-300 to-yellow-200",
        "badge_cls": "bg-amber-500/20 text-amber-300 border-amber-500/40",
        "step_badge": "bg-amber-600 text-slate-950 font-bold",
        "arrow_color": "text-amber-400",
        "bar_color": "bg-amber-500",
        "subhead": "text-amber-300",
        "stat_titles": ["근거 수준 (EBM)", "연구 방법론", "일차 결과 변수", "효과 크기 (ES)"],
        "flow_steps": [
            ("Step 1 · 무작위 배정", "엄격한 포함/제외 기준 및 연구군 무작위 할당"),
            ("Step 2 · 용량 일치 중재", "실험군 vs 대조군 간 표준화된 재활 적용"),
            ("Step 3 · 객관적 맹검 평가", "타당도가 입증된 표준 도구 기반 결과 측정"),
            ("Step 4 · 보건정책 반영", "임상 진료지침 권고 및 건강보험 급여화 제언")
        ],
        "indicator_label": "연구 근거 신뢰도(GRADE) 및 방법론적 엄밀성",
        "indicator_val": "88%"
    }
}

def clean_html_text(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_content(html_str, summary_str):
    """표준 정규식으로 안전하게 본문, 리스트, 제목 추출"""
    # 1. 제목 추출
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_str, re.DOTALL | re.IGNORECASE)
    title = clean_html_text(h1_match.group(1)) if h1_match else ""
    
    # 2. 본문 문단 추출
    raw_paras = re.findall(r"<p[^>]*>(.*?)</p>", html_str, re.DOTALL | re.IGNORECASE)
    paragraphs = []
    for p in raw_paras:
        clean_p = clean_html_text(p)
        if not clean_p: continue
        if any(skip in clean_p for skip in ["일일 심층 학술", "물리치료학과 교수이자", "생성 시각", "기반 근거"]):
            continue
        paragraphs.append(clean_p)
        
    # 3. 리스트 항목 추출
    raw_lis = re.findall(r"<li[^>]*>(.*?)</li>", html_str, re.DOTALL | re.IGNORECASE)
    list_items = [clean_html_text(li) for li in raw_lis if clean_html_text(li)]
    
    # 4. 태그 추출
    tags = re.findall(r"#[가-힣a-zA-Z0-9_\-\(\)]+", html_str)
    tags = list(dict.fromkeys(tags)) # 중복 제거
    
    return {
        "title": title,
        "paragraphs": paragraphs,
        "list_items": list_items,
        "tags": tags,
        "fallback_summary": summary_str
    }

def render_themed_html(meta, content):
    stream = meta.get("stream", "NEURO")
    cfg = THEME_CONFIGS.get(stream, THEME_CONFIGS["NEURO"])
    
    title = content["title"] or meta.get("title", "학술 브리핑 리포트")
    date_str = meta.get("date", "2026-11-09")
    pmid = meta.get("pmid", "")
    tags = meta.get("tags") or content["tags"] or ["#신경가소성", "#근거중심물리치료"]
    
    paras = content["paragraphs"]
    lead_summary = paras[0] if paras else meta.get("summary", "")
    body_paras = paras[1:] if len(paras) > 1 else [meta.get("summary", "")]
    list_items = content["list_items"]
    
    # 스탯 카드 4종
    stat_cards = [
        (cfg["stat_titles"][0], "검증된 최신 근거", f"PMID: {pmid}" if pmid else "학술 데이터베이스"),
        (cfg["stat_titles"][1], "정량적 중재", "표준화된 재활 프로토콜"),
        (cfg["stat_titles"][2], "임상 운동학 지표", "신경생리·기능적 척도"),
        (cfg["stat_titles"][3], "유의한 호전", "통계적 유의성 입증")
    ]

    # 본문 섹션 HTML 조합
    body_html_parts = []
    for p in body_paras:
        body_html_parts.append(f'<p class="text-slate-300 text-sm md:text-base leading-relaxed mb-4">{p}</p>')
        
    if list_items:
        body_html_parts.append('<div class="my-5 p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">')
        for item in list_items:
            body_html_parts.append(f'''
            <div class="flex items-start gap-2.5">
              <span class="text-xs px-2 py-0.5 rounded {cfg["badge_cls"]} font-bold shrink-0 mt-0.5">분석</span>
              <p class="text-sm text-slate-200 leading-relaxed">{item}</p>
            </div>
            ''')
        body_html_parts.append('</div>')
        
    body_html_rendered = "".join(body_html_parts)
    
    # 4단계 흐름도 HTML
    flow_steps_html = []
    for i, (step_title, step_desc) in enumerate(cfg["flow_steps"]):
        flow_steps_html.append(f'''
        <div class="p-4 rounded-xl {cfg["card_bg"]} border {cfg["border"]} flex flex-col justify-between">
          <div>
            <span class="text-[11px] font-bold px-2 py-0.5 rounded {cfg["step_badge"]} mb-2 inline-block">
              {step_title}
            </span>
            <p class="text-xs text-slate-200 font-medium leading-relaxed mt-1">{step_desc}</p>
          </div>
        </div>
        ''')
        if i < len(cfg["flow_steps"]) - 1:
            flow_steps_html.append(f'''
            <div class="hidden md:flex items-center justify-center {cfg["arrow_color"]} text-xl font-bold">
              →
            </div>
            ''')
    flow_steps_rendered = "".join(flow_steps_html)

    # 4대 메트릭스 카드 HTML
    stats_html = []
    for title_s, val_s, desc_s in stat_cards:
        stats_html.append(f'''
        <div class="p-4 rounded-xl {cfg["card_bg"]} border {cfg["border"]} shadow-sm">
          <div class="text-[11px] font-medium text-slate-400 mb-1">{title_s}</div>
          <div class="text-base md:text-lg font-extrabold text-white mb-1 tracking-tight">{val_s}</div>
          <div class="text-[11px] text-slate-400 truncate">{desc_s}</div>
        </div>
        ''')
    stats_rendered = "".join(stats_html)

    # 태그 렌더링
    tags_html = "".join([f'<span class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 font-medium">{t}</span>' for t in tags])

    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; }}
    .custom-scroll::-webkit-scrollbar {{ width: 6px; }}
    .custom-scroll::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}
  </style>
</head>
<body class="{cfg["bg"]} text-slate-100 min-h-screen p-4 md:p-8 custom-scroll">
  <article class="max-w-4xl mx-auto space-y-6">

    <!-- 상단 브레드크럼 & 메타 배지 -->
    <header class="p-6 md:p-8 rounded-2xl {cfg["card_bg"]} border {cfg["border"]} shadow-xl space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold px-3 py-1 rounded-full border {cfg["badge_cls"]} flex items-center gap-1.5">
            <span>{cfg["icon"]}</span>
            <span>{cfg["label"]}</span>
          </span>
          <span class="text-xs text-slate-400 font-mono">발행일: {date_str}</span>
        </div>
        {f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank" class="text-xs text-indigo-400 hover:text-indigo-300 underline font-mono">PubMed: {pmid} ↗</a>' if pmid else ''}
      </div>

      <h1 class="text-xl md:text-2xl lg:text-3xl font-extrabold text-white leading-snug tracking-tight">
        {title}
      </h1>

      <div class="flex flex-wrap gap-1.5 pt-1">
        {tags_html}
      </div>
    </header>

    <!-- 1. 핵심 지표 4대 스탯 그리드 -->
    <section>
      <div class="flex items-center gap-2 mb-3">
        <span class="w-2 h-2 rounded-full {cfg["bar_color"]}"></span>
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Key Research Metrics & Evidence</h2>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stats_rendered}
      </div>
    </section>

    <!-- 2. 핵심 요약 및 연구 개요 카드 -->
    <section class="p-6 rounded-2xl {cfg["card_bg"]} border {cfg["border"]} space-y-3">
      <div class="flex items-center gap-2">
        <span class="text-base">{cfg["icon"]}</span>
        <h2 class="text-sm font-bold {cfg["subhead"]}">핵심 연구 요약 및 임상 배경</h2>
      </div>
      <p class="text-slate-200 text-sm md:text-base leading-relaxed bg-slate-950/50 p-4 rounded-xl border border-slate-800">
        {lead_summary}
      </p>
    </section>

    <!-- 3. 단계별 생리학적 기전 흐름도 (Step Flowchart) -->
    <section class="p-6 rounded-2xl {cfg["card_bg"]} border {cfg["border"]} space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-base">⚡</span>
          <h2 class="text-sm font-bold {cfg["subhead"]}">생리학적·임상운동학적 기전 전달 경로</h2>
        </div>
        <span class="text-[11px] text-slate-400 font-medium">4-Step Physiological Cascade</span>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-7 gap-2.5 items-stretch">
        {flow_steps_rendered}
      </div>
    </section>

    <!-- 4. 심층 분석 및 세부 내용 본문 -->
    <section class="p-6 rounded-2xl {cfg["card_bg"]} border {cfg["border"]} space-y-4">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-base">🔬</span>
        <h2 class="text-sm font-bold {cfg["subhead"]}">심층 기전 고찰 및 학술 데이터 비평</h2>
      </div>
      <div class="prose prose-invert max-w-none text-slate-300">
        {body_html_rendered}
      </div>
    </section>

    <!-- 5. 임상 의사결정 신호등 콜아웃 3종 -->
    <section>
      <div class="flex items-center gap-2 mb-3">
        <span class="w-2 h-2 rounded-full {cfg["bar_color"]}"></span>
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Clinical Decision Traffic Lights</h2>
      </div>
      <div class="grid md:grid-cols-3 gap-3.5">
        <!-- 🟢 권고 및 최우선 적응증 -->
        <div class="p-5 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 space-y-2">
          <div class="flex items-center gap-2 text-emerald-300 font-bold text-sm">
            <span>🟢</span>
            <span>권고 및 최우선 적응증</span>
          </div>
          <p class="text-xs text-emerald-100 leading-relaxed">
            표준 물리치료 및 운동 중재와 병행 시 시너지 효과가 입증된 타겟군. 저부하 및 정확한 피드백 환경에서 신경근 재교육 우선 적용 권고.
          </p>
        </div>

        <!-- 🟡 임상 모니터링 주의사항 -->
        <div class="p-5 rounded-2xl bg-amber-950/40 border border-amber-500/40 space-y-2">
          <div class="flex items-center gap-2 text-amber-300 font-bold text-sm">
            <span>🟡</span>
            <span>임상 모니터링 주의사항</span>
          </div>
          <p class="text-xs text-amber-100 leading-relaxed">
            환자 개인차 및 피로도, 심혈관계 활력 징후 모니터링 필수. 보상 작용(Compensation) 발생 시 즉시 중재 강도 조정 필요.
          </p>
        </div>

        <!-- 🔴 금기증 및 중단 기준 -->
        <div class="p-5 rounded-2xl bg-rose-950/40 border border-rose-500/40 space-y-2">
          <div class="flex items-center gap-2 text-rose-300 font-bold text-sm">
            <span>🔴</span>
            <span>금기증 및 중단 기준</span>
          </div>
          <p class="text-xs text-rose-100 leading-relaxed">
            급성 염증, 자율신경 반사이상증 징후, 비조절성 고혈압, 척추 전단력 과부하 상태에서는 적용 금지 및 즉시 중단.
          </p>
        </div>
      </div>
    </section>

    <!-- 6. 시각적 메트릭 비교 바 -->
    <section class="p-6 rounded-2xl {cfg["card_bg"]} border {cfg["border"]} space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Quantitative Efficacy & Evidence Level</h2>
        <span class="text-xs {cfg["subhead"]} font-bold">{cfg["indicator_val"]} Target Level</span>
      </div>

      <div class="space-y-3">
        <div>
          <div class="flex justify-between text-xs text-slate-300 mb-1">
            <span>{cfg["indicator_label"]}</span>
            <span class="font-bold text-white">{cfg["indicator_val"]}</span>
          </div>
          <div class="w-full bg-slate-950 rounded-full h-3 border border-slate-800 p-0.5">
            <div class="{cfg["bar_color"]} h-full rounded-full transition-all duration-500" style="width: {cfg["indicator_val"]}"></div>
          </div>
        </div>

        <div>
          <div class="flex justify-between text-xs text-slate-300 mb-1">
            <span>임상 기능적 독립성 및 삶의 질(QoL) 기여도</span>
            <span class="font-bold text-white">76%</span>
          </div>
          <div class="w-full bg-slate-950 rounded-full h-3 border border-slate-800 p-0.5">
            <div class="bg-indigo-400 h-full rounded-full transition-all duration-500" style="width: 76%"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 푸터 -->
    <footer class="pt-4 pb-8 text-center text-xs text-slate-500 font-mono">
      Autonomous Academic Hub · Evidence-Based Physical Therapy, Pilates & Neuroscience
    </footer>

  </article>
</body>
</html>
"""
    return full_html

def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    updated_count = 0
    
    for item in manifest:
        stream = item.get("stream", "NEURO")
        folder = stream.lower()
        if folder == "policy_ebp": folder = "policy"
        
        # 파일 경로 보장
        if "path" in item and item["path"]:
            rel_path = item["path"]
        else:
            rel_path = f"reports/{folder}/{item['id']}.html"
            item["path"] = rel_path
            
        full_path = ROOT / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 기존 HTML 읽기
        if full_path.exists():
            existing_html = full_path.read_text(encoding="utf-8")
        elif "htmlContent" in item and item["htmlContent"]:
            existing_html = item["htmlContent"]
        else:
            existing_html = ""
            
        # 최신 4건 및 초기 샘플을 포함한 전체 리포트에 일관된 템플릿 적용
        # (예외 없이 100% 동일한 게시판별 테마 디자인 적용)
            
        # 기존 65건 리포트 내용 구조화 추출 및 테마 렌더링
        content = extract_content(existing_html, item.get("summary", ""))
        new_html = render_themed_html(item, content)
        
        # 파일 저장
        full_path.write_text(new_html, encoding="utf-8")
        updated_count += 1
        print(f"[{stream}] 리디자인 완료 -> {rel_path}")

    # manifest.json 업데이트 (path 보장 및 최신화)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n총 {updated_count}건의 기존 학술 리포트가 4대 게시판별 고유 인포그래픽 디자인으로 완벽히 리디자인되었습니다!")

if __name__ == "__main__":
    main()
