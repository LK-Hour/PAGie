"""
PAGie Accuracy Testing Pipeline
=================================

This script evaluates the accuracy of the PAGie RAG pipeline by comparing its answers
to a predefined set of questions and ground-truth answers.

Methodology:
1.  **Load Questions & Answers:** It reads from `pagie_test_questions.txt` and `pagie_test_answers.txt`.
2.  **Query PAGie:** For each question, it calls the `query_pagie` function to get the model's generated answer.
3.  **LLM-as-Judge Evaluation:** It uses the Google Gemini model as an impartial "judge" to semantically evaluate if PAGie's answer matches the ground-truth answer. This is more robust than simple string matching.
4.  **Scoring:** The judge assigns a score:
    - **PERFECT (100%):** Exact or semantically identical match.
    - **GOOD (70-99%):** Correct main points, minor details may differ.
    - **PARTIAL (40-69%):** Some correct elements but misses key information.
    - **INCORRECT (0-39%):** Wrong or no relevant information.
5.  **Reporting:** Generates a detailed `accuracy_report.md` with overall scores and a breakdown of each question's performance.

This "LLM-as-Judge" approach provides a more nuanced and human-like evaluation of the RAG system's performance.
"""
import os
import re
import json
import time # Import the time module
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

import google.generativeai as genai
from dotenv import load_dotenv
from tqdm import tqdm

# Ensure the script can find the rag_pipeline module
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag_pipeline import query_pagie

# --- Configuration ---
load_dotenv()
QUESTIONS_FILE = "pagie_test_questions.txt"
ANSWERS_FILE = "pagie_test_answers.txt"
REPORT_FILE = "accuracy_report.md"
MAX_WORKERS = 4 # Adjust based on your machine's capability

# Configure the Gemini API for the judge
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# Initialize the generative model for the judge
JUDGE_MODEL_NAME = "gemini-1.5-pro-latest"
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)
JUDGE_MODEL = genai.GenerativeModel(JUDGE_MODEL_NAME)

EVALUATION_PROMPT_TEMPLATE = """
You are an impartial AI evaluator. Your task is to assess the quality of a generated answer from a RAG (Retrieval-Augmented Generation) system against a ground-truth answer.

**INSTRUCTIONS:**
1.  Carefully read the user's **Question**.
2.  Review the **Ground-Truth Answer**, which is the ideal, correct response.
3.  Analyze the **Generated Answer** from the RAG system.
4.  Compare the **Generated Answer** to the **Ground-Truth Answer**.
5.  Determine if the **Generated Answer** contains the same key information as the **Ground-Truth Answer**. The phrasing does not need to be identical.
6.  Provide a score and a brief justification in JSON format.

**SCORING CRITERIA:**
- **PERFECT**: The generated answer is factually correct, complete, and aligns perfectly with the ground-truth.
- **GOOD**: The generated answer is factually correct and contains the most important information, but might be slightly less detailed or phrased differently.
- **PARTIAL**: The generated answer contains some correct information but is incomplete, missing key details, or contains minor inaccuracies.
- **INCORRECT**: The generated answer is factually wrong, irrelevant, or fails to answer the question.

**EVALUATION:**

**Question:**
{question}

**Ground-Truth Answer:**
{expected_answer}

**Generated Answer:**
{actual_answer}

**Your JSON Output:**
"""

JSON_REPAIR_PROMPT = """
The following text is a failed attempt to generate a JSON object. Please repair it.
Return ONLY the repaired JSON object, with no other text or explanation.

Failed Text:
{text}

Repaired JSON:
"""

# --- Data Loading Functions ---

def load_questions(filename: str) -> List[Dict[int, str]]:
    """Loads questions from the specified file."""
    print(f"Loading questions from {filename}...")
    questions = []
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to find numbered questions
    matches = re.findall(r'^\s*(\d+)\.\s*(.*)', content, re.MULTILINE)
    for num, text in matches:
        questions.append({"number": int(num), "text": text.strip()})
    print(f"Found {len(questions)} questions.")
    return questions

def load_answers(filename: str) -> Dict[int, str]:
    """Loads answers from the specified file."""
    print(f"Loading answers from {filename}...")
    answers = {}
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split content by question number headers like "1. What university..."
    # The regex looks for a number, a period, and then text until the next "ANSWER:"
    sections = re.split(r'\n(\d+)\.\s', content)
    
    answer_content = content.split("ACCURACY SCORING GUIDE:")[0]
    
    # Regex to find ANSWER blocks, associated with a preceding question number
    # This is a bit more complex because the question text is between the number and the ANSWER
    matches = re.findall(r'(?s)(\d+)\..*?ANSWER:\s*(.*?)(?=\n\n\d+\.|\Z)', answer_content)

    for num, text in matches:
        answers[int(num)] = text.strip()
        
    # A fallback for a different format if the above fails
    if not answers:
         # Regex to find a number and then the ANSWER block
        matches = re.findall(r'(?s)^\s*(\d+)\..*?ANSWER:\s*(.*?)(?=\n\s*\d+\.|\Z)', content, re.MULTILINE)
        for num, text in matches:
            answers[int(num)] = text.strip()

    print(f"Found {len(answers)} answers.")
    return answers

# --- Evaluation Functions ---

def get_llm_evaluation(question: str, expected_answer: str, actual_answer: str) -> Dict:
    """Uses an LLM to judge the actual answer against the expected one."""
    prompt = EVALUATION_PROMPT_TEMPLATE.format(
        question=question,
        expected_answer=expected_answer,
        actual_answer=actual_answer
    )
    
    response_text = ""
    try:
        response = JUDGE_MODEL.generate_content(prompt)
        response_text = response.text
        # Clean the response to extract only the JSON part
        json_text = response_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"Error decoding LLM response: {e}. Attempting to repair.")
        try:
            repair_prompt = JSON_REPAIR_PROMPT.format(text=response_text)
            repaired_response = JUDGE_MODEL.generate_content(repair_prompt)
            return json.loads(repaired_response.text)
        except (json.JSONDecodeError, Exception) as repair_e:
            print(f"JSON repair failed: {repair_e}")
            return {"score": "ERROR", "justification": f"Failed to parse LLM response: {response_text}"}
    except Exception as e:
        print(f"An unexpected error occurred during LLM evaluation: {e}")
        return {"score": "ERROR", "justification": f"API or other error during evaluation: {e}"}


def process_question(question_item: Dict, expected_answers: Dict) -> Dict:
    """
    Processes a single question: queries PAGie, gets evaluation, and returns the result.
    """
    q_num = question_item["number"]
    q_text = question_item["text"]
    
    expected_answer = expected_answers.get(q_num, "Answer not found.")
    
    # 1. Query PAGie
    # Add a delay to respect API rate limits
    time.sleep(2) # 2-second delay before the first API call
    pagie_result = query_pagie(q_text)
    actual_answer = pagie_result.get("answer", "PAGie returned no answer.")
    sources = pagie_result.get("sources", [])

    # 2. Get LLM-as-Judge evaluation
    # Add another delay before the second API call
    time.sleep(2) # 2-second delay
    evaluation = get_llm_evaluation(q_text, expected_answer, actual_answer)
    
    return {
        "number": q_num,
        "question": q_text,
        "expected_answer": expected_answer,
        "actual_answer": actual_answer,
        "sources": sources,
        "score": evaluation.get("score", "ERROR").upper(),
        "justification": evaluation.get("justification", "No justification provided.")
    }

# --- Reporting Functions ---

def generate_report(results: List[Dict]):
    """Generates a markdown report from the evaluation results."""
    print(f"Generating accuracy report to {REPORT_FILE}...")
    
    # Sort results by question number
    results.sort(key=lambda x: x["number"])
    
    # Calculate summary statistics
    score_counts = Counter(r['score'] for r in results)
    total_questions = len(results)
    
    perfect_count = score_counts.get("PERFECT", 0)
    good_count = score_counts.get("GOOD", 0)
    
    # Calculate accuracy score (Perfect + Good)
    accuracy = ((perfect_count + good_count) / total_questions) * 100 if total_questions > 0 else 0

    newline = '\n'

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# PAGie Accuracy Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Questions:** {total_questions}\n")
        f.write(f"**Overall Accuracy (Perfect + Good):** `{accuracy:.2f}%`\n\n")
        
        f.write("## Summary\n\n")
        f.write("| Score Category | Count | Percentage |\n")
        f.write("|----------------|-------|------------|\n")
        for score in ["PERFECT", "GOOD", "PARTIAL", "INCORRECT", "ERROR"]:
            count = score_counts.get(score, 0)
            percentage = (count / total_questions) * 100 if total_questions > 0 else 0
            f.write(f"| {score} | {count} | {percentage:.2f}% |\n")
        
        f.write("\n## Detailed Results\n\n")
        
        for res in results:
            f.write(f"### Question {res['number']}: {res['question']}\n\n")
            f.write(f"**Score: `{res['score']}`**\n\n")
            f.write(f"**Justification:** {res['justification']}\n\n")
            
            f.write("<details>\n<summary>Click to see details</summary>\n\n")
            f.write("**Ground-Truth Answer:**\n")
            f.write(f"> {res['expected_answer'].replace(newline, newline + '> ')}\n\n")
            f.write("**PAGie's Answer:**\n")
            f.write(f"> {res['actual_answer'].replace(newline, newline + '> ')}\n\n")
            f.write("**Sources Used:**\n")
            if res['sources']:
                for source in res['sources']:
                    f.write(f"- `{source}`\n")
            else:
                f.write("- *None*\n")
            f.write("\n</details>\n\n")
            f.write("---\n")
            
    print("Report generation complete.")

# --- Main Execution ---

def main():
    """Main function to run the accuracy test pipeline."""
    print("Starting PAGie Accuracy Test Pipeline...")
    
    questions = load_questions(QUESTIONS_FILE)
    expected_answers = load_answers(ANSWERS_FILE)
    
    if not questions or not expected_answers:
        print("Error: Could not load questions or answers. Exiting.")
        return

    results = []
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create a future for each question
        future_to_question = {executor.submit(process_question, q, expected_answers): q for q in questions}
        
        # Process as they complete
        for future in tqdm(as_completed(future_to_question), total=len(questions), desc="Evaluating Questions"):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                q_num = future_to_question[future]['number']
                print(f"Question {q_num} generated an exception: {exc}")
                results.append({
                    "number": q_num,
                    "question": future_to_question[future]['text'],
                    "expected_answer": expected_answers.get(q_num, "N/A"),
                    "actual_answer": f"Execution Error: {exc}",
                    "sources": [],
                    "score": "ERROR",
                    "justification": str(exc)
                })

    generate_report(results)
    print("PAGie Accuracy Test Pipeline finished.")

if __name__ == "__main__":
    main()
