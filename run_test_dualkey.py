"""
PAGie accuracy test — dual-key, single-threaded, rate-limit aware.
Key 1 (OqqmdzQw): rag_pipeline (PAGie answers via .env GOOGLE_API_KEY)
Key 2 (ZgwH1qGA): judge scoring (separate genai instance)
15s gap per question -> safely under 5 RPM on each key.
"""
import os, re, json, time
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag_pipeline import query_pagie

JUDGE_KEY = "AIzaSyDga8oc9iFaq6TQ2bUMnPqLD9aZgwH1qGA"
genai.configure(api_key=JUDGE_KEY)
judge = genai.GenerativeModel("gemini-2.0-flash-lite")

EVAL_PROMPT = """You are an impartial evaluator scoring a RAG chatbot answer.

Question: {question}
Ground-Truth: {expected}
Chatbot Answer: {actual}

Score as one of: PERFECT / GOOD / PARTIAL / INCORRECT
- PERFECT: correct and complete
- GOOD: correct main points, minor gaps
- PARTIAL: some correct info but key details missing
- INCORRECT: wrong, irrelevant, or failed to retrieve

Reply ONLY with valid JSON (no markdown): {{"score": "GOOD", "justification": "one sentence"}}"""

def load_questions():
    with open("pagie_test_questions.txt") as f:
        content = f.read()
    return [{"number": int(n), "text": t.strip()}
            for n, t in re.findall(r'^\s*(\d+)\.\s*(.*)', content, re.MULTILINE)]

def load_answers():
    with open("pagie_test_answers.txt") as f:
        content = f.read()
    content = content.split("ACCURACY SCORING GUIDE:")[0]
    matches = re.findall(r'(?s)(\d+)\..*?ANSWER:\s*(.*?)(?=\n\n\d+\.|\Z)', content)
    return {int(n): t.strip() for n, t in matches}

def judge_answer(question, expected, actual, retries=3):
    if any(x in actual for x in ["couldn't find", "Failed to connect", "unexpected error"]):
        return {"score": "INCORRECT", "justification": "PAGie failed to retrieve context."}
    for attempt in range(retries):
        try:
            resp = judge.generate_content(
                EVAL_PROMPT.format(question=question, expected=expected, actual=actual)
            )
            text = resp.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"score": "PARTIAL", "justification": f"Judge parse error: {resp.text[:80]}"}
        except Exception as e:
            if "429" in str(e):
                print(f"    WARNING: Judge rate limited, waiting 70s...")
                time.sleep(12)
            else:
                return {"score": "ERROR", "justification": str(e)[:120]}
    return {"score": "ERROR", "justification": "Max retries exceeded"}

def main():
    questions = load_questions()
    answers = load_answers()
    print(f"Loaded {len(questions)} questions, {len(answers)} answers")
    print(f"Estimated time: ~{len(questions) * 26 // 60} min (26s/question)\n")

    results = []
    for i, q in enumerate(questions):
        n, text = q["number"], q["text"]
        expected = answers.get(n, "N/A")
        print(f"[{i+1:02d}/50] Q{n}: {text[:65]}...")

        pagie_result = query_pagie(text)
        actual = pagie_result.get("answer", "")
        sources = pagie_result.get("sources", [])
        print(f"       PAGie: {actual[:80].replace(chr(10),' ')}...")
        time.sleep(5)

        eval_result = judge_answer(text, expected, actual)
        score = eval_result.get("score", "ERROR").upper()
        justification = eval_result.get("justification", "")
        print(f"       Score: {score} -- {justification[:70]}")

        results.append({"number": n, "question": text, "expected": expected,
                        "actual": actual, "sources": sources,
                        "score": score, "justification": justification})

        if i < len(questions) - 1:
            time.sleep(5)

    results.sort(key=lambda x: x["number"])
    score_counts = Counter(r["score"] for r in results)
    total = len(results)
    accuracy = (score_counts.get("PERFECT", 0) + score_counts.get("GOOD", 0)) / total * 100

    with open("accuracy_report.md", "w") as f:
        f.write(f"# PAGie Accuracy Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Questions:** {total}\n")
        f.write(f"**Overall Accuracy (Perfect + Good):** `{accuracy:.2f}%`\n\n")
        f.write("## Summary\n\n| Score | Count | % |\n|-------|-------|---|\n")
        for s in ["PERFECT", "GOOD", "PARTIAL", "INCORRECT", "ERROR"]:
            c = score_counts.get(s, 0)
            f.write(f"| {s} | {c} | {c/total*100:.1f}% |\n")
        f.write("\n## Detailed Results\n\n")
        for r in results:
            f.write(f"### Q{r['number']}: {r['question']}\n\n")
            f.write(f"**Score: `{r['score']}`** -- {r['justification']}\n\n")
            f.write(f"<details><summary>Details</summary>\n\n")
            f.write(f"**Expected:**\n> {r['expected'][:400]}\n\n")
            f.write(f"**PAGie's Answer:**\n> {r['actual'][:600]}\n\n")
            f.write(f"**Sources:** {', '.join(r['sources'][:3]) or 'None'}\n\n")
            f.write(f"</details>\n\n---\n")

    print(f"\n{'='*50}")
    print(f"DONE! Overall Accuracy: {accuracy:.1f}%")
    print(f"PERFECT:{score_counts.get('PERFECT',0)} GOOD:{score_counts.get('GOOD',0)} PARTIAL:{score_counts.get('PARTIAL',0)} INCORRECT:{score_counts.get('INCORRECT',0)} ERROR:{score_counts.get('ERROR',0)}")

if __name__ == "__main__":
    main()
