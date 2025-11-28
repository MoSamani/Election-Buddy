import json
import requests
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from openai import OpenAI

API_BASE = "http://localhost:8000"  # dein Backend
OPENAI_MODEL_JUDGE = "gpt-4o-mini"  # Judge-Modell

client = OpenAI()  # nutzt OPENAI_API_KEY aus ENV


@dataclass
class EvalSample:
    id: int
    question: str
    reference_answer: str


@dataclass
class EvalResult:
    id: int
    question: str
    answer_score: float
    answer_explanation: str
    context_score: float
    context_explanation: str


def load_samples(path: str) -> List[EvalSample]:
    samples: List[EvalSample] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            samples.append(
                EvalSample(
                    id=obj["id"],
                    question=obj["question"],
                    reference_answer=obj["reference_answer"],
                )
            )
    print(f"[INFO] {len(samples)} Samples geladen.")
    return samples


def call_rag(question: str, top_k: int = 5, peer_reviewed_only: bool = False) -> Dict[str, Any]:
    print(f"[RAG] Frage: {question!r}")
    try:
        resp = requests.post(
            f"{API_BASE}/rag_answer/",
            json={
                "question": question,
                "top_k": top_k,
                "peer_reviewed_only": peer_reviewed_only,
                "conversation_id": None,
            },
            timeout=60,
        )
    except Exception as e:
        print(f"[ERROR] Request zu /rag_answer/ fehlgeschlagen: {e}")
        raise

    print(f"[RAG] HTTP Status: {resp.status_code}")
    if not resp.ok:
        print("[RAG] Response-Text:", resp.text)
        resp.raise_for_status()

    try:
        data = resp.json()
    except Exception as e:
        print("[ERROR] Konnte JSON von /rag_answer/ nicht parsen:", resp.text)
        raise

    print("[RAG] Response JSON (gekürzt):", {k: (v if k != "answer" else v[:120] + " ...") for k, v in data.items() if k != "sources"})
    print(f"[RAG] #Sources: {len(data.get('sources', []))}")
    return data


def judge_answer(question: str, model_answer: str, reference_answer: str) -> Dict[str, Any]:
    system_prompt = (
        "Du bewertest die Qualität einer Antwort im Kontext von Wissenschaftsjournalismus.\n"
        "Bewerte auf einer Skala von 0 bis 1, wie gut die Modellantwort die Referenzantwort trifft.\n"
        "0 bedeutet: klar falsch oder am Thema vorbei.\n"
        "1 bedeutet: inhaltlich weitgehend deckungsgleich, keine gravierenden sachlichen Fehler.\n"
        "Antworte NUR im JSON-Format: {\"score\": <zahl>, \"explanation\": \"...\"}."
    )

    user_prompt = (
        f"Frage:\n{question}\n\n"
        f"Modellantwort:\n{model_answer}\n\n"
        f"Referenzantwort:\n{reference_answer}\n"
    )

    print("[JUDGE-ANSWER] Rufe OpenAI als Judge auf...")
    completion = client.chat.completions.create(
        model=OPENAI_MODEL_JUDGE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    content = completion.choices[0].message.content
    print("[JUDGE-ANSWER] Rohantwort:", content)

    try:
        result = json.loads(content)
        score = float(result.get("score", 0.0))
        explanation = result.get("explanation", "")
    except Exception:
        score = 0.0
        explanation = f"Parsing-Fehler, Rohantwort des Judges: {content}"

    score = max(0.0, min(1.0, score))
    return {"score": score, "explanation": explanation}


def judge_context_relevance(question: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    system_prompt = (
        "Du bewertest, wie relevant gegebene Textauszüge (Kontexte) für eine Frage sind.\n"
        "Bewerte auf einer Skala von 0 bis 1, wie hilfreich die Kontexte zur Beantwortung der Frage sind.\n"
        "0 bedeutet: größtenteils irrelevant.\n"
        "1 bedeutet: klar relevante, hilfreiche Passagen.\n"
        "Antworte NUR im JSON-Format: {\"score\": <zahl>, \"explanation\": \"...\"}."
    )

    parts = []
    for i, s in enumerate(sources):
        meta = s.get("meta") or {}
        title = s.get("title", f"Quelle {i+1}")
        year = meta.get("year", "unbekannt")
        journal = meta.get("journal") or meta.get("source") or "unbekannt"
        txt = s.get("chunk_text", "")
        parts.append(
            f"[Quelle {i+1}]\nTitel: {title}\nJahr: {year}, Quelle: {journal}\nTextauszug:\n{txt}\n"
        )

    context_block = "\n\n".join(parts) if parts else "Keine Kontexte."

    user_prompt = (
        f"Frage:\n{question}\n\n"
        f"Kontexte:\n{context_block}\n"
    )

    print("[JUDGE-CONTEXT] Rufe OpenAI als Judge auf...")
    completion = client.chat.completions.create(
        model=OPENAI_MODEL_JUDGE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    content = completion.choices[0].message.content
    print("[JUDGE-CONTEXT] Rohantwort:", content)

    try:
        result = json.loads(content)
        score = float(result.get("score", 0.0))
        explanation = result.get("explanation", "")
    except Exception:
        score = 0.0
        explanation = f"Parsing-Fehler, Rohantwort des Judges: {content}"

    score = max(0.0, min(1.0, score))
    return {"score": score, "explanation": explanation}


def run_evaluation(samples: List[EvalSample]) -> List[EvalResult]:
    results: List[EvalResult] = []

    for s in samples:
        print(f"\n=== Evaluating sample {s.id}: {s.question} ===")

        try:
            rag_resp = call_rag(s.question, top_k=5, peer_reviewed_only=False)
        except Exception as e:
            print(f"[ERROR] RAG-Aufruf fehlgeschlagen für Sample {s.id}: {e}")
            continue

        model_answer = rag_resp.get("answer", "")
        sources = rag_resp.get("sources", [])

        if not model_answer:
            print(f"[WARN] Leere oder fehlende Modellantwort für Sample {s.id}")
            continue

        ans_eval = judge_answer(
            question=s.question,
            model_answer=model_answer,
            reference_answer=s.reference_answer,
        )
        ctx_eval = judge_context_relevance(
            question=s.question,
            sources=sources,
        )

        result = EvalResult(
            id=s.id,
            question=s.question,
            answer_score=ans_eval["score"],
            answer_explanation=ans_eval["explanation"],
            context_score=ctx_eval["score"],
            context_explanation=ctx_eval["explanation"],
        )

        print(f"[RESULT] Answer score:  {result.answer_score:.2f}")
        print(f"[RESULT] Context score: {result.context_score:.2f}")

        results.append(result)

    return results


def save_results(path: str, results: List[EvalResult]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            obj = {
                "id": r.id,
                "question": r.question,
                "answer_score": r.answer_score,
                "answer_explanation": r.answer_explanation,
                "context_score": r.context_score,
                "context_explanation": r.context_explanation,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    samples = load_samples("eval_samples.jsonl")
    if not samples:
        print("[WARN] Keine Samples gefunden – eval_samples.jsonl leer?")
    results = run_evaluation(samples)
    save_results("eval_results.jsonl", results)

    if results:
        avg_answer = sum(r.answer_score for r in results) / len(results)
        avg_context = sum(r.context_score for r in results) / len(results)
        print("\n===== SUMMARY =====")
        print(f"Durchschnitt Answer-Score:  {avg_answer:.3f}")
        print(f"Durchschnitt Context-Score: {avg_context:.3f}")
    else:
        print("\n[INFO] Keine Eval-Resultate erzeugt.")
