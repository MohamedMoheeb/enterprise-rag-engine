import os
import requests
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision

# Ground Ragas metrics evaluation models locally
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-key-here")

# Define our static Golden Dataset for system alignment verification
golden_dataset = [
    {
        "question": "What is the mandatory protocol for handling identified data breaches?",
        "ground_truth": "All security incidents must be reported to the Infosec team via portal within 24 hours. High severity items require immediate mitigation within 4 hours."
    }
]

def run_evaluation_suite():
    print("Initiating Pipeline Verification Against Target Container Platform...")
    api_url = "http://localhost:8000/query"
    
    prepared_eval_records = []
    
    for row in golden_dataset:
        # Direct execution over exposed local network gateway ports
        response = requests.post(api_url, json={"query": row["question"]})
        if response.status_code != 200:
            print(f"API Target communication failure: {response.text}")
            continue
            
        payload_data = response.json()
        
        prepared_eval_records.append({
            "question": row["question"],
            "answer": payload_data["answer"],
            "contexts": payload_data["retrieved_chunks"],
            "ground_truth": row["ground_truth"]
        })
        
    # Standardize schema into Hugging Face formats expected natively by Ragas framework
    dataset = Dataset.from_list(prepared_eval_records)
    
    print("Computing Mathematical Ragas Alignment Metrics via LLM-As-A-Judge...")
    evaluation_output = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision
        ]
    )
    
    print("\n--- PERFORMANCE METRICS MATRIX ---")
    print(evaluation_output)
    
    # Save the deep analytics to disk for pipeline comparison
    metrics_df = evaluation_output.to_pandas()
    metrics_df.to_csv("eval_output_log.csv", index=False)
    print("Metrics written successfully to disk: 'eval_output_log.csv'")

if __name__ == "__main__":
    run_evaluation_suite()