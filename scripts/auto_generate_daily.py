#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신경물리치료·필라테스·뇌과학 무인 일일 학술 브리핑 생성 엔진
매일 아침 07:15 KST GitHub Actions에 의해 자동 실행됩니다.
"""
import json, os, urllib.parse, urllib.request, re
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

[분석 초점]
{cfg['focus']}

[실제 학술 근거]
- PMID: {paper['pmid']}
- 학술지: {paper['journal']}
- 원문 제목: {paper['title']}
- 원문 초록:
{paper['abstract']}

[작성 및 출력 규칙]
1. 반드시 제공된 초록의 사실에만 근거하여 작성하고, 확인되지 않은 수치나 기전을 자의적으로 날조하지 마십시오.
2. 대학원 수준의 엄밀한 학술 용어를 구사하되 평이한 문장으로 서술하고, 숫자와 단위는 LaTeX 수식 없이 '10 Hz', '70% HRR'처럼 일반 텍스트로 표기하십시오.
3. html_code에는 <!DOCTYPE html>부터 </html>까지 완결된, 모바일 반응형 및 현대적 카드 스타일(Pretendard 글꼴 및 깔끔한 CSS 포함)의 독립형 HTML 전체 코드를 작성하십시오.
4. tags에는 ["#신경가소성", "#고유수용성감각", "#운동제어_운동학습", "#중추감작_통증기전", "#자율신경계", "#비침습뇌자극(tSMS)", "#거울시각피드백(MVF)", "#뇌파_운동심상(EEG-MI)", "#로봇_보행재활", "#코어_분절안정화", "#심폐재활_CPET", "#임상응급_프로토콜", "#RCT저널브리핑"] 중 2~4개를 선택하십시오."""

    # 최신 공식 엔드포인트: gemini-2.0-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
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
            print(f"[{cfg['stream']}] Gemini 2.0 Flash 분석 브리핑 생성 중... (PMID: {paper['pmid']})")
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
            print(f"[{cfg['stream']}] 브리핑 생성 완료 -> {rel}")
        except Exception as e:
            print(f"[{cfg['stream']}] 리포트 생성 중 예외 발생 (건너뜀): {e}")

    if generated_count > 0:
        m_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"총 {generated_count}건의 새 리포트가 manifest.json에 등록되었습니다.")
    else:
        print("금일 새로 생성된 리포트가 없습니다.")

if __name__ == "__main__":
    main()
