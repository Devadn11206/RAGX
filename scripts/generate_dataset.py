import json
import os

questions = [
    # Factual (Direct extraction)
    {"q": "What are the standard working hours?", "type": "factual", "ans": "Standard working hours are 9 AM to 5 PM, Monday to Friday.", "docs": ["company_policies.md"]},
    {"q": "How many days of paid leave are employees entitled to per year?", "type": "factual", "ans": "Employees are entitled to 20 days of paid leave per year.", "docs": ["employee_handbook.md"]},
    {"q": "What is the maximum upload size for a file?", "type": "factual", "ans": "The maximum upload size is 25 MB per file.", "docs": ["product_guide.md"]},
    {"q": "How do I get IT support?", "type": "factual", "ans": "For IT support, you must open a ticket via the internal portal.", "docs": ["company_policies.md"]},
    {"q": "What file types can be processed by RAGX?", "type": "factual", "ans": "RAGX supports processing PDF, TXT, and Markdown files.", "docs": ["product_guide.md"]},
    {"q": "How many days of sick leave are allowed?", "type": "factual", "ans": "Sick leave is provided up to 10 days per year.", "docs": ["employee_handbook.md"]},
    {"q": "Do I need a certificate for 1 day sick leave?", "type": "factual", "ans": "No, a certificate is only required for exceeding 2 days.", "docs": ["employee_handbook.md"]},
    {"q": "What is the maximum upload size for tenant users?", "type": "factual", "ans": "The maximum file upload size is 50 MB for all standard tenant users.", "docs": ["product_guide.md"]},
    {"q": "What are core hours?", "type": "factual", "ans": "Core hours are 10:00 AM to 4:00 PM.", "docs": ["company_policies.md"]},
    {"q": "What happens after 30 minutes of inactivity?", "type": "factual", "ans": "Session timeouts occur after 30 minutes of inactivity.", "docs": ["product_guide.md"]},

    # Semantic (Paraphrased/synonyms)
    {"q": "At what time does my shift typically begin and end?", "type": "semantic", "ans": "Standard working hours are 9 AM to 5 PM, Monday to Friday.", "docs": ["company_policies.md"]},
    {"q": "If I am ill, what is the procedure?", "type": "semantic", "ans": "For sick leave exceeding 2 days, a medical certificate is required.", "docs": ["employee_handbook.md"]},
    {"q": "Where do I complain about my computer breaking?", "type": "semantic", "ans": "Open a ticket via the internal portal.", "docs": ["company_policies.md"]},
    {"q": "Is DOCX supported by the system?", "type": "semantic", "ans": "No, RAGX supports processing PDF, TXT, and Markdown files.", "docs": ["product_guide.md"]},
    {"q": "What is my annual vacation allowance?", "type": "semantic", "ans": "Employees are entitled to 20 days of paid leave per year.", "docs": ["employee_handbook.md"]},
    {"q": "Who approves remote work?", "type": "semantic", "ans": "Employees may work remotely up to 2 days per week upon manager approval.", "docs": ["employee_handbook.md"]},
    {"q": "Are company secrets allowed in Slack?", "type": "semantic", "ans": "No, company secrets must never be shared across communication channels.", "docs": ["employee_handbook.md"]},
    {"q": "What happens if I make 150 API calls in a minute?", "type": "semantic", "ans": "API rate limits are capped at 120 requests per minute.", "docs": ["product_guide.md"]},
    {"q": "When is everyone required to be online?", "type": "semantic", "ans": "During core hours from 10:00 AM to 4:00 PM.", "docs": ["company_policies.md"]},
    {"q": "Do I have to come to the office every single day?", "type": "semantic", "ans": "No, employees may work remotely up to 2 days per week upon manager approval.", "docs": ["employee_handbook.md"]},

    # Lexical (Keyword heavy, keyword matching)
    {"q": "Standard working hours 9 AM 5 PM Monday Friday", "type": "lexical", "ans": "Standard working hours are 9 AM to 5 PM, Monday to Friday.", "docs": ["company_policies.md"]},
    {"q": "IT support ticket internal portal", "type": "lexical", "ans": "For IT support, open a ticket via the internal portal.", "docs": ["company_policies.md"]},
    {"q": "20 days paid leave per year", "type": "lexical", "ans": "Employees are entitled to 20 days of paid leave per year.", "docs": ["employee_handbook.md"]},
    {"q": "maximum upload size 25 MB file", "type": "lexical", "ans": "The maximum upload size is 25 MB per file.", "docs": ["product_guide.md"]},
    {"q": "PDF TXT Markdown processing", "type": "lexical", "ans": "RAGX supports processing PDF, TXT, and Markdown files.", "docs": ["product_guide.md"]},
    {"q": "API rate limits 120 requests minute", "type": "lexical", "ans": "API rate limits are capped at 120 requests per minute.", "docs": ["product_guide.md"]},
    {"q": "medical certificate exceeding 2 days", "type": "lexical", "ans": "A medical certificate is required for sick leaves exceeding 2 days.", "docs": ["employee_handbook.md"]},
    {"q": "core hours 10:00 AM 4:00 PM", "type": "lexical", "ans": "Core hours are 10:00 AM to 4:00 PM.", "docs": ["company_policies.md"]},
    {"q": "flexible working arrangements department manager", "type": "lexical", "ans": "Flexible working arrangements must be approved by the department manager.", "docs": ["company_policies.md"]},
    {"q": "session timeouts 30 minutes", "type": "lexical", "ans": "Session timeouts occur after 30 minutes of inactivity.", "docs": ["product_guide.md"]},

    # Multi-hop (Requires connecting facts across documents or chunks)
    {"q": "If I am sick for 3 days and I want to upload my medical certificate, what is the maximum file size?", "type": "multi-hop", "ans": "For 3 days sick leave, a medical certificate is required. The maximum file upload size is 25 MB (or 50 MB for standard tenant users).", "docs": ["employee_handbook.md", "product_guide.md"]},
    {"q": "Can I upload a 40 MB PDF to open an IT support ticket?", "type": "multi-hop", "ans": "The maximum upload size is 25 MB (or 50 MB depending on the tenant). Standard IT support tickets are opened via the internal portal.", "docs": ["company_policies.md", "product_guide.md"]},
    {"q": "I want to work remotely next Monday, but also I want to take paid leave on Tuesday. Who approves my remote work and how many days of paid leave will I have left if I started with 20?", "type": "multi-hop", "ans": "The department manager approves remote work. You would have 19 days of paid leave left.", "docs": ["company_policies.md", "employee_handbook.md"]},
    {"q": "If I hit the API rate limit, and wait an hour, will my session still be active?", "type": "multi-hop", "ans": "No, session timeouts occur after 30 minutes of inactivity.", "docs": ["product_guide.md"]},
    {"q": "Are API keys allowed to be shared via the internal portal for IT support?", "type": "multi-hop", "ans": "No, API keys and company secrets must never be shared across communication channels.", "docs": ["employee_handbook.md", "company_policies.md"]},

    # Comparison
    {"q": "Is the number of paid leave days higher than the number of sick leave days?", "type": "comparison", "ans": "Yes, 20 (or 24) days of paid leave is higher than 10 days of sick leave.", "docs": ["employee_handbook.md"]},
    {"q": "Which is longer: standard working hours or core hours?", "type": "comparison", "ans": "Standard working hours (9 AM to 5 PM, 8 hours) is longer than core hours (10 AM to 4 PM, 6 hours).", "docs": ["company_policies.md"]},
    {"q": "Does Acme Corp give more annual leave than the standard 20 days?", "type": "comparison", "ans": "Yes, Acme Corp gives 24 days.", "docs": ["employee_handbook.md"]},

    # Policy
    {"q": "What happens if I commit a secret to GitHub?", "type": "policy", "ans": "Security credentials and company secrets must never be committed to source control.", "docs": ["employee_handbook.md"]},
    {"q": "What is the policy on taking 4 consecutive business days off?", "type": "policy", "ans": "Leave requests exceeding 3 consecutive business days must be submitted at least 2 weeks in advance.", "docs": ["employee_handbook.md"]},

    # Adversarial (Tricky wording, false premises)
    {"q": "How do I upload a 100 MB MP4 file to RAGX?", "type": "adversarial", "ans": "RAGX only supports PDF, TXT, and Markdown files, and the maximum file upload size is 50 MB.", "docs": ["product_guide.md"]},
    {"q": "Since I get 30 days of paid leave, can I take them all at once?", "type": "adversarial", "ans": "You do not get 30 days of paid leave; employees are entitled to 20 (or 24) days.", "docs": ["employee_handbook.md"]},
    {"q": "Is the internal portal the right place to share API keys?", "type": "adversarial", "ans": "No, API keys must never be shared across communication channels.", "docs": ["employee_handbook.md"]},
    {"q": "If I am sick for 1 day, do I need a medical certificate from the CEO?", "type": "adversarial", "ans": "No, a medical certificate is only required for sick leaves exceeding 2 days.", "docs": ["employee_handbook.md"]},
    {"q": "What time does the core hours sync happen on Saturday?", "type": "adversarial", "ans": "Standard working hours are Monday through Friday, so there are no core hours on Saturday.", "docs": ["company_policies.md"]},

    # Tenant-specific
    {"q": "For Acme Corporation, how many days of annual leave do I get?", "type": "tenant-specific", "ans": "Employees receive 24 days of annual leave.", "docs": ["employee_handbook.md"]},
    {"q": "At Acme Corp, what are the exact standard working hours?", "type": "tenant-specific", "ans": "Standard working hours are 9:00 AM to 6:00 PM.", "docs": ["employee_handbook.md"]},
    {"q": "For tenant users, what is the max file upload size?", "type": "tenant-specific", "ans": "The maximum file upload size is 50 MB for all standard tenant users.", "docs": ["product_guide.md"]},
    {"q": "How does role-based access control work for uploaded documents?", "type": "tenant-specific", "ans": "All documents uploaded are classified under tenant-level role-based access control (RBAC).", "docs": ["employee_handbook.md"]},
    {"q": "What is the company name mentioned in the employee handbook?", "type": "tenant-specific", "ans": "Acme Corporation.", "docs": ["employee_handbook.md"]}
]

os.makedirs("data/evaluation", exist_ok=True)
os.makedirs("reports/phase14", exist_ok=True)

dataset = {
    "dataset_version": "v1.0",
    "questions": []
}

for i, item in enumerate(questions):
    dataset["questions"].append({
        "question_id": f"q{i:03d}",
        "question": item["q"],
        "reference_answer": item["ans"],
        "source_documents": item["docs"],
        "question_type": item["type"]
    })

with open("data/evaluation/phase14_benchmark_dataset.json", "w") as f:
    json.dump(dataset, f, indent=2)

stats = {}
for q in dataset["questions"]:
    stats[q["question_type"]] = stats.get(q["question_type"], 0) + 1

profile = {
    "total_questions": len(dataset["questions"]),
    "types": stats,
    "documents": len(set(doc for q in dataset["questions"] for doc in q["source_documents"])),
    "multi_hop": stats.get("multi-hop", 0)
}

with open("reports/phase14/dataset_profile.json", "w") as f:
    json.dump(profile, f, indent=2)

md_content = f"""# Benchmark Dataset Profile

## Overview
- **Total Questions:** {profile['total_questions']}
- **Total Documents Referenced:** {profile['documents']}

## Question Categories
"""
for k, v in stats.items():
    md_content += f"- **{k.capitalize()}**: {v} questions\n"

with open("reports/phase14/dataset_profile.md", "w") as f:
    f.write(md_content)

print(f"Dataset generated with {len(dataset['questions'])} questions.")
