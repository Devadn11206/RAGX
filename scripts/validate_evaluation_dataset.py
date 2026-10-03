import json
import sys

def main():
    try:
        with open("data/evaluation/evaluation_dataset.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        questions = data.get("questions", [])
        if not questions:
            print("Error: No questions found.")
            sys.exit(1)
            
        ids = set()
        for q in questions:
            qid = q.get("question_id")
            if not qid:
                print("Error: Missing question_id.")
                sys.exit(1)
            if qid in ids:
                print(f"Error: Duplicate question_id {qid}.")
                sys.exit(1)
            ids.add(qid)
            
            if not q.get("question") or not q.get("reference_answer"):
                print(f"Error: Question or answer missing in {qid}.")
                sys.exit(1)
                
            if not q.get("expected_chunk_ids"):
                print(f"Error: No expected chunks in {qid}.")
                sys.exit(1)
                
        print("Dataset is valid.")
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
