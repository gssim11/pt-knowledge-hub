#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신경물리치료·필라테스·뇌과학 무인 일일 학술 브리핑 생성 엔진 (인포그래픽 강화 버전)
매일 아침 07:15 KST GitHub Actions에 의해 자동 실행됩니다.
"""
import json, os, urllib.parse, urllib.request, re, time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
TODAY_STR = datetime.now(KST).strftime("%Y-%m-%d")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

STREAM_CONFIGS = [
    {
        "stream": "NEURO",
        "folder": "neuro",
        "pubmed_query": "(neuroplasticity[Title/Abstract] OR transcranial magnetic[Title/Abstract] OR motor imagery[Title/Abstract]) AND (stroke OR rehabilitation[Title/Abstract])",
        "focus": "대뇌피질 흥분성, 시냅스 가소성, tSMS/tDCS/TMS, 거울시각피드백, EEG-MI 등 뇌과학 및 신경생리학적 기전과 정량적 신경재활 프로토콜 분석"
    },
    {
        "stream": "CLINICAL",
        "folder": "clinical",
        "pubmed_query": "(spinal cord injury[Title/Abstract] OR stroke rehabilitation[Title/Abstract] OR central sensitization[Title/Abstract]) AND (physical therapy[Title/Abstract] OR exercise[Title/Abstract])",
        "focus": "척수손상 자율신경 반사이상증, 중추감작 통증 기전, 신경근 질환, 로봇 보행 및 심폐 재활의 임상 프로토콜 및 생리학적 안전 가이드라인"
    },
    {
        "stream": "PILATES",
        "folder": "pilates",
        "pubmed_query": "(Pilates[Title/Abstract] OR core stabilization[Title/Abstract] OR lumbar multifidus[Title/Abstract]) AND (proprioception[Title/Abstract] OR postural balance[Title/Abstract])",
        "focus": "재활 필라테스 및 임상운동학: 심부 분절 안정화, 다열근·복횡근 고유수용성 감각, 피드포워드 운동제어, 척추 분절 중립 영역(Neutral Zone) 회복 기전"
    },
    {
        "stream": "POLICY_EBP",
        "folder": "policy",
        "pubmed_query": "(randomized controlled trial[Publication Type]) AND (physical therapy modalities[MeSH Terms] OR neurological rehabilitation[MeSH Terms])",
        "focus": "근거중심 물리치료(EBP) 최신 무작위대조시험(RCT) 연구방법론 비평, 비뚤림 위험(RoB) 및 보건의료 재활 정책 시사점"
    }
]

def fetch_pubmed(query, used_pmids):
    try:
        time.sleep(1.5)  # NCBI Rate Limit (초당 3회 이하) 준수
        u1 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode({
            "db": "pubmed", "term": query, "retmode": "json", "retmax": "15", "sort": "date"
        })
        req1 = urllib.request.Request(u1, headers={"User-Agent": "AutonomousAcademicHub/2.0"})
        with urllib.request.urlopen(req1, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            ids = data.get("esearchresult", {}).get("idlist", [])
        
        pmid = next((i for i in ids if i not in used_pmids), None)
        if not pmid:
            return None

        time.sleep(1.5)  # NCBI Fetch 요청 간격 유지
        u2 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode({
            "db": "pubmed", "id": pmid, "retmode": "xml"
        })
        req2 = urllib.request.Request(u2, headers={"User-Agent": "AutonomousAcademicHub/2.0"})
        with urllib.request.urlopen(req2, timeout=15) as r:
            root = ET.fromstring(r.read())

        title_elem = root.find(".//ArticleTitle")
        title = "".join(title_elem.itertext()).strip() if title_elem is not None else ""
        
        abs_nodes = root.findall(".//AbstractText")
        abs_text = "\n".join("".join(e.itertext()).strip() for e in abs_nodes) if abs_nodes else ""
        
        journal = root.findtext(".//Journal/Title") or "Rehabilitation Science Journal"
        
        if not title or not abs_text:
            return None

        return {"pmid": pmid, "title": title, "abstract": abs_text, "journal": journal}
    except Exception as e:
        print(f"[PubMed Fetch Warning] {e}")
        return None

def call_gemini(cfg, paper):
    prompt = f"""당신은 물리치료학과 교수이자 신경물리치료·임상운동학·재활필라테스 시니어 연구자입니다.
아래 실제로 검증된 PubMed 학술 논문 초록을 정밀하게 분석하여 '{cfg['stream']}' 영역의 일일 심층 학술 브리핑 리포트를 한국어로 작성하십시오.
이 리포트는 전문 임상가와 연구자가 한눈에 핵심을 파악할 수 있도록 '학술 인포그래픽 카드뉴스' 스타일의 시각적 컴포넌트를 반드시 포함해야 합니다.

[분석 초점]
{cfg['focus']}

[실제 학술 근거]
- PMID: {paper['pmid']}
- 학술지: {paper['journal']}
- 원문 제목: {paper['title']}
- 원문 초록:
{paper['abstract']}

[작성 및 시각화 필수 규칙]
1. 반드시 제공된 초록의 사실에만 근거하여 작성하고, 확인되지 않은 수치나 기전을 자의적으로 날조하지 마십시오.
2. 대학원 수준의 엄밀한 학술 용어를 구사하되 평이한 문장으로 서술하고, 숫자와 단위는 LaTeX 수식 없이 '10 Hz', '70% HRR'처럼 일반 텍스트로 표기하십시오.
3. html_code에는 <!DOCTYPE html>부터 </html>까지 완결된 반응형 HTML 코드를 작성하십시오.
   - 헤드에 Tailwind CSS CDN (<script src="https://cdn.tailwindcss.com"></script>) 및 Pretendard 글꼴 스타일을 로드할 것.
   - 전체 배경은 차분한 슬레이트톤(bg-slate-900 text-slate-100)으로 하되, 본문 컨테이너(max-w-4xl mx-auto p-6 md:p-10 space-y-8)로 여백을 줄 것.
   - [필수 시각화 1: 상단 4대 메트릭스 스탯 카드 그리드]
     <div class="grid grid-cols-2 md:grid-cols-4 gap-3"> 구조로:
       (1) 연구 설계 & 표본수 (예: RCT (N=42))
       (2) 중재 주기 및 용량 (예: 주 3회, 6주간)
       (3) 주요 측정 척도 (예: MEP / FMA-UE)
       (4) 핵심 결과 수치 (예: +38.2% (p<0.01))
     각 카드는 bg-slate-800/80 p-4 rounded-xl border border-slate-700 형태로 상단에 소제목, 중앙에 크고 강조된 수치(text-indigo-400 font-extrabold text-lg), 하단 요약을 배치할 것.
   - [필수 시각화 2: 4단계 생리학적 기전 흐름도 (Step Flowchart)]
     <div class="grid md:grid-cols-4 gap-2"> 또는 단계별 화살표(→)가 포함된 카드로:
       Step 1(중재 투입) → Step 2(세포막·신경세포 이온반응) → Step 3(신경망·하행로 흥분성 조절) → Step 4(임상 운동기능 개선)
       형태의 직관적인 프로세스 블록을 구성할 것.
   - [필수 시각화 3: 임상 의사결정 신호등 콜아웃 3종]
     <div class="grid md:grid-cols-3 gap-3"> 안에:
       🟢 초록 박스 (bg-emerald-950/40 border border-emerald-500/40 p-4 rounded-xl): [권고 및 최우선 적응증]
       🟡 노랑 박스 (bg-amber-950/40 border border-amber-500/40 p-4 rounded-xl): [임상 모니터링 주의사항]
       🔴 빨강 박스 (bg-rose-950/40 border border-rose-500/40 p-4 rounded-xl): [금기증 및 중단 기준]
   - [필수 시각화 4: 시각적 메트릭 비교 바 (Progress Metric Bar)]
     주요 임상 지표의 개선율이나 치료 효과 크기를 CSS 바(예: <div class="w-full bg-slate-800 rounded-full h-3.5"><div class="bg-indigo-500 h-3.5 rounded-full" style="width: 78%"></div></div>) 형태로 최소 2개 이상 시각화할 것.
4. summary는 목록에 표시될 2~3줄의 핵심 요약문(일반 텍스트)을 작성하십시오.
5. tags에는 ["#신경가소성", "#고유수용성감각", "#운동제어_운동학습", "#중추감작_통증기전", "#자율신경계", "#비침습뇌자극(tSMS)", "#거울시각피드백(MVF)", "#뇌파_운동심상(EEG-MI)", "#로봇_보행재활", "#코어_분절안정화", "#심폐재활_CPET", "#임상응급_프로토콜", "#RCT저널브리핑"] 중 2~4개를 선택하십시오."""

    # Google AI 공식 최신 고성능 모델: gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "summary": {"type": "STRING"},
                    "tags": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "html_code": {"type": "STRING"}
                },
                "required": ["title", "summary", "tags", "html_code"]
            }
        }
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        res = json.loads(r.read().decode("utf-8"))
    
    raw_text = res["candidates"][0]["content"]["parts"][0]["text"]
    raw_text = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.MULTILINE)
    raw_text = re.sub(r"```$", "", raw_text.strip(), flags=re.MULTILINE)
    return json.loads(raw_text)

def main():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
    
    root = Path(__file__).resolve().parent.parent
    m_path = root / "manifest.json"
    manifest = json.loads(m_path.read_text(encoding="utf-8")) if m_path.exists() else []
    used = {x.get("pmid") for x in manifest if x.get("pmid")}
    generated_count = 0

    for cfg in STREAM_CONFIGS:
        rid = f"{TODAY_STR}-{cfg['stream'].lower()}"
        if any(x.get("id") == rid for x in manifest):
            continue

        try:
            print(f"[{cfg['stream']}] PubMed 최신 논문 탐색 중...")
            paper = fetch_pubmed(cfg["pubmed_query"], used)
            if not paper:
                print(f"[{cfg['stream']}] 유효한 논문 검색 결과가 없어 허위 리포트 생성을 방지하고 건너뜁니다.")
                continue

            used.add(paper["pmid"])
            print(f"[{cfg['stream']}] Gemini 2.5 Flash 인포그래픽 브리핑 생성 중... (PMID: {paper['pmid']})")
            out = call_gemini(cfg, paper)

            f_dir = root / "reports" / cfg["folder"]
            f_dir.mkdir(parents=True, exist_ok=True)
            rel = f"reports/{cfg['folder']}/{rid}.html"
            (root / rel).write_text(out["html_code"], encoding="utf-8")

            manifest.insert(0, {
                "id": rid,
                "stream": cfg["stream"],
                "date": TODAY_STR,
                "title": out["title"],
                "summary": out["summary"],
                "tags": out["tags"],
                "pmid": paper["pmid"],
                "path": rel
            })
            generated_count += 1
            print(f"[{cfg['stream']}] 인포그래픽 브리핑 생성 완료 -> {rel}")
            time.sleep(2)  # 스트림 간 안정적 딜레이
        except Exception as e:
            print(f"[{cfg['stream']}] 리포트 생성 중 예외 발생 (건너뜀): {e}")

    if generated_count > 0:
        m_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"총 {generated_count}건의 새 인포그래픽 리포트가 manifest.json에 등록되었습니다.")
    else:
        print("금일 새로 생성된 리포트가 없습니다.")

if __name__ == "__main__":
    main()
