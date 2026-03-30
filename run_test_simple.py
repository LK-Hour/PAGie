"""
Simple single-threaded PAGie accuracy test.
Uses Gemini as judge (no OpenAI needed).
Runs sequentially to avoid ChromaDB threading issues.
"""
import os, re, json, time
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag_pipeline import query_pagie

import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
judge = genai.GenerativeModel("gemini-2.5-flash")

EVAL_PROMPT = """You are an impartial evaluator scoring a RAG chatbot answer.

Question: {question}
Ground-Truth: {expected}
Chatbot Answer: {actual}

Score the chatbot answer as one of: PERFECT, GOOD, PARTIAL, INCORRECT
- PERFECT: correct and complete
- GOOD: correct main points, minor gaps
- PARTIAL: some correct info but incomplete
- INCORRECT: wrong or irrelevant

Reply with ONLY a JSON object: {{"score": "PERFECT", "justification": "..."}}"""

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

def judge_answer(question, expected, actual):
    if "couldn't find" in actual or "Failed to connect" in actual:
        return {"score": "INCORRECT", "justification": "PAGie failed to retrieve relevant context."}
    try:
        time.sleep(3)  # rate limit buffer
        resp = judge.generate_content(
            EVAL_PROMPT.format(question=question, expected=expected, actual=actual)
        )
        text = resp.text.strip().lstrip("```json").rstrip("```").strip()
        return json.loads(text)
    except Exception as e:
        return {"score": "ERROR", "justification": str(e)[:120]}

def main():
    questions = load_questions()
    answers = load_answers()
    print(f"Loaded {len(questions)} questions, {len(answers)} answers")
    
    results = []
    for i, q in enumerate(questions):
        n, text = q["number"], q["text"]
        expected = answers.get(n, "N/A")
        print(f"[{i+1}/50] Q{n}: {text[:60]}...")
        
        time.sleep(4)  # pace requests to stay under 20 RPM
        pagie_result = query_pagie(text)
        actual = pagie_result.get("answer", "")
        sources = pagie_result.get("sources", [])
        
        eval_result = judge_answer(text, expected, actual)
        score = eval_result.get("score", "ERROR").upper()
        justification = eval_result.get("justification", "")
        
        print(f"  → {score}: {justification[:80]}")
        results.append({
            "number": n, "question": text,
            "expected": expected, "actual": actual,
            "sources": sources, "score": score,
            "justification": justification
        })
    
    # Write report
    results.sort(key=lambda x: x["number"])
    score_counts = Counter(r["score"] for r in results)
    total = len(results)
    accuracy = (score_counts.get("PERFECT", 0) + score_counts.get("GOOD", 0)) / total * 100
    
    nl = '\n'
    with open("accuracy_report.md", "w") as f:
        f.write(f"# PAGie Accuracy Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Questions:** {total}\n")
        f.write(f"**Overall Accuracy (Perfect + Good):** `{accuracy:.2f}%`\n\n")
        f.write("## Summary\n\n")
        f.write("| Score | Count | % |\n|-------|-------|---|\n")
        for s in ["PERFECT", "GOOD", "PARTIAL", "INCORRECT", "ERROR"]:
            c = score_counts.get(s, 0)
            f.write(f"| {s} | {c} | {c/total*100:.1f}% |\n")
        f.write("\n## Detailed Results\n\n")
        for r in results:
            f.write(f"### Q{r['number']}: {r['question']}\n\n")
            f.write(f"**Score: `{r['score']}`** — {r['justification']}\n\n")
            f.write(f"<details><summary>Details</summary>\n\n")
            f.write(f"**Expected:** {r['expected'][:300]}\n\n")
            f.write(f"**PAGie:** {r['actual'][:500]}\n\n")
            f.write(f"**Sources:** {', '.join(r['sources'][:3]) or 'None'}\n\n")
            f.write(f"</details>\n\n---\n")
    
    print(f"\n✅ Done! Accuracy: {accuracy:.1f}%")
    print(f"PERFECT: {score_counts.get('PERFECT',0)} | GOOD: {score_counts.get('GOOD',0)} | PARTIAL: {score_counts.get('PARTIAL',0)} | INCORRECT: {score_counts.get('INCORRECT',0)} | ERROR: {score_counts.get('ERROR',0)}")

if __name__ == "__main__":
    main()
