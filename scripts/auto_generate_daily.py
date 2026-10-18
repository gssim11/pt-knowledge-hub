#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
TODAY_STR = datetime.now(KST).strftime("%Y-%m-%d")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

STREAM_CONFIGS = [
    {"stream": "NEURO", "folder": "neuro", "pubmed_query": "(neuroplasticity[Title/Abstract] OR transcranial[Title/Abstract] OR motor imagery[Title/Abstract]) AND (rehabilitation[Title/Abstract])", "focus": "뇌과학 및 신경생리학(대뇌피질 흥분성, 시냅스 가소성, tSMS/tDCS, 거울시각피드백, EEG-MI) 기전 분석"},
    {"stream": "CLINICAL", "folder": "clinical", "pubmed_query": "(spinal cord injury[Title/Abstract] OR stroke rehabilitation[Title/Abstract] OR central sensitization[Title/Abstract]) AND (physical therapy[Title/Abstract])", "focus": "임상 물리치료(척수손상 자율신경 반사이상증, 신경근 질환, 중추감작 통증 기전, 심폐·로봇 재활 프로토콜) 심층 분석"},
    {"stream": "PILATES", "folder": "pilates", "pubmed_query": "(Pilates[Title/Abstract] OR core stabilization[Title/Abstract] OR multifidus[Title/Abstract]) AND (proprioception[Title/Abstract] OR balance[Title/Abstract])", "focus": "재활 필라테스 및 임상운동학(심부 분절 안정화, 다열근·복횡근 고유수용성 감각, 피드포워드 운동제어) 기전과 임상 적용"},
    {"stream": "POLICY_EBP", "folder": "policy", "pubmed_query": "(randomized controlled trial[Publication Type]) AND (physical therapy modalities[MeSH Terms] OR neurological rehabilitation[MeSH Terms])", "focus": "근거중심 물리치료(EBP) 최신 RCT 비평 및 재활 보건의료 정책 시사점"}
]

def fetch_pubmed(query, used_pmids):
    try:
        u1 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "term": query, "retmode": "json", "retmax": "10", "sort": "date"})
        with urllib.request.urlopen(u1, timeout=15) as r:
            ids = json.loads(r.read().decode("utf-8")).get("esearchresult", {}).get("idlist", [])
        pmid = next((i for i in ids if i not in used_pmids), ids[0] if ids else None)
        if not pmid: return {}
        u2 = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "id": pmid, "retmode": "xml"})
        with urllib.request.urlopen(u2, timeout=15) as r:
            root = ET.fromstring(r.read())
        title = "".join(root.find(".//ArticleTitle").itertext()) if root.find(".//ArticleTitle") is not None else ""
        abs_text = "\n".join("".join(e.itertext()) for e in root.findall(".//AbstractText"))
        journal = root.findtext(".//Journal/Title") or "Rehabilitation Journal"
        return {"pmid": pmid, "title": title, "abstract": abs_text, "journal": journal}
    except Exception as e:
        print("PubMed warning:", e)
        return {}

def call_gemini(cfg, paper):
    prompt = f"""당신은 물리치료학과 교수이자 신경물리치료·임상운동학·재활필라테스 시니어 전문가입니다.
아래 최신 PubMed 근거를 바탕으로 '{cfg['stream']}' 영역의 일일 심층 학술 브리핑 리포트를 한국어로 작성하십시오.
[분석 초점] {cfg['focus']}
[학술 근거] PMID: {paper.get('pmid','N/A')} | 저널: {paper.get('journal','N/A')} | 제목: {paper.get('title','최신 연구')} | 초록: {paper.get('abstract','해당 분야 핵심 생리학 기전 중심 서술')}
[규칙]
1. 대학원 수준의 엄밀함을 유지하되 평이한 문장으로 작성하고, 숫자와 단위는 LaTeX 없이 '10 Hz', '70% HRR'처럼 일반 텍스트로 표기하십시오.
2. html_code에는 <!DOCTYPE html>부터 </html>까지 완결된 모던 카드 스타일의 독립형 HTML 전체 코드를 작성하십시오.
3. tags에는 ["#신경가소성", "#고유수용성감각", "#운동제어_운동학습", "#중추감작_통증기전", "#자율신경계", "#비침습뇌자극(tSMS)", "#거울시각피드백(MVF)", "#뇌파_운동심상(EEG-MI)", "#로봇_보행재활", "#코어_분절안정화", "#심폐재활_CPET", "#임상응급_프로토콜", "#RCT저널브리핑"] 중 2~4개를 선택하십시오."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
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
    return json.loads(res["candidates"][0]["content"]["parts"][0]["text"])

def main():
    if not GEMINI_API_KEY: raise RuntimeError("GEMINI_API_KEY missing")
    root = Path(__file__).resolve().parent.parent
    m_path = root / "manifest.json"
    manifest = json.loads(m_path.read_text(encoding="utf-8")) if m_path.exists() else []
    used = {x.get("pmid") for x in manifest if x.get("pmid")}
    for cfg in STREAM_CONFIGS:
        rid = f"{TODAY_STR}-{cfg['stream'].lower()}"
        if any(x.get("id") == rid for x in manifest): continue
        paper = fetch_pubmed(cfg["pubmed_query"], used)
        if paper.get("pmid"): used.add(paper["pmid"])
        out = call_gemini(cfg, paper)
        f_dir = root / "reports" / cfg["folder"]
        f_dir.mkdir(parents=True, exist_ok=True)
        rel = f"reports/{cfg['folder']}/{rid}.html"
        (root / rel).write_text(out["html_code"], encoding="utf-8")
        manifest.insert(0, {"id": rid, "stream": cfg["stream"], "status": "PENDING", "date": TODAY_STR, "title": out["title"], "summary": out["summary"], "tags": out["tags"], "pmid": paper.get("pmid", ""), "path": rel})
    m_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
