"""
eval.py
Phase 3: Offline RAG evaluation script using RAGAS.

Measures faithfulness — whether claims in the generated answer are actually
supported by the retrieved chunks. Runs against the golden dataset and
fails with exit code 1 if scores drop below the configured threshold.

Usage:
    python3 scripts/eval.py                        # full eval (all 50 questions)
    python3 scripts/eval.py --sample 10            # quick run on 10 random questions
    python3 scripts/eval.py --domain aws_security  # filter by domain
    python3 scripts/eval.py --fail-threshold 0.75  # override pass threshold
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track

console = Console()

# ── RAGAS imports ──────────────────────────────────────────────────────────────
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# ── Config ─────────────────────────────────────────────────────────────────────
GOLDEN_DATASET_PATH = "evaluation/golden_dataset.json"
RESULTS_DIR = Path("evaluation/results")
FAITHFULNESS_THRESHOLD = 0.75  # build fails below this


def load_golden_dataset(
    domain_filter: str | None = None,
    sample: int | None = None,
    seed: int = 42,
) -> list[dict]:
    """Load and optionally filter/sample the golden dataset."""
    with open(GOLDEN_DATASET_PATH) as f:
        dataset = json.load(f)

    if domain_filter:
        dataset = [d for d in dataset if d["domain"] == domain_filter]
        console.print(f"[dim]Filtered to domain '{domain_filter}': {len(dataset)} questions[/dim]")

    if sample and sample < len(dataset):
        random.seed(seed)
        dataset = random.sample(dataset, sample)
        console.print(f"[dim]Sampled {sample} questions[/dim]")

    return dataset


def run_rag_pipeline(questions: list[dict]) -> list[dict]:
    """
    Run each question through the full RAG pipeline and collect:
    - question, answer, contexts (retrieved chunks), ground_truth
    """
    console.print("\n[bold cyan]Running RAG pipeline on evaluation questions...[/bold cyan]")

    from src.pipeline import RAGPipeline
    pipeline = RAGPipeline()

    # Check vector store is populated
    if pipeline.vector_store.count() == 0:
        console.print("[bold red]❌ Vector store is empty — run 'python3 ingest.py' first.[/bold red]")
        sys.exit(1)

    results = []
    declined_count = 0

    for item in track(questions, description="Evaluating"):
        question = item["question"]

        try:
            result = pipeline.query(question, verbose=False)

            if result["declined"]:
                declined_count += 1
                results.append({
                    "question": question,
                    "answer": result["answer"],
                    "contexts": ["No context retrieved — answer was declined."],
                    "ground_truth": item["ground_truth"],
                    "domain": item["domain"],
                    "difficulty": item["difficulty"],
                    "id": item["id"],
                    "declined": True,
                })
            else:
                # Use source excerpts as contexts for RAGAS
                contexts = [src["excerpt"] for src in result.get("sources", [])]
                if not contexts:
                    contexts = ["Context not available."]

                results.append({
                    "question": question,
                    "answer": result["answer"],
                    "contexts": contexts,
                    "ground_truth": item["ground_truth"],
                    "domain": item["domain"],
                    "difficulty": item["difficulty"],
                    "id": item["id"],
                    "declined": False,
                })

        except Exception as e:
            console.print(f"[red]  Error on '{question[:50]}': {e}[/red]")
            results.append({
                "question": question,
                "answer": f"ERROR: {e}",
                "contexts": ["Pipeline error."],
                "ground_truth": item["ground_truth"],
                "domain": item["domain"],
                "difficulty": item["difficulty"],
                "id": item["id"],
                "declined": False,
            })

        time.sleep(0.3)

    if declined_count:
        console.print(f"[yellow]  ⚠ {declined_count}/{len(questions)} questions were declined[/yellow]")

    return results


def score_with_ragas(pipeline_results: list[dict]) -> dict:
    """
    Score results using RAGAS faithfulness metric.
    Faithfulness = fraction of answer claims supported by retrieved context.
    """
    console.print("\n[bold cyan]Scoring with RAGAS faithfulness...[/bold cyan]")

    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY not set — required for RAGAS evaluation.")

    # Build RAGAS dataset
    ragas_data = {
        "question": [r["question"] for r in pipeline_results],
        "answer":   [r["answer"]   for r in pipeline_results],
        "contexts": [r["contexts"] for r in pipeline_results],
        "ground_truth": [r["ground_truth"] for r in pipeline_results],
    }
    dataset = Dataset.from_dict(ragas_data)

    # Wrap LLM and embeddings correctly for ragas 0.1.21
    llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", api_key=openai_key))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(api_key=openai_key))

    result = evaluate(
        dataset,
        metrics=[faithfulness],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False,
    )

    return result


def build_report(pipeline_results, ragas_scores, threshold) -> dict:
    """Build a structured evaluation report."""
    df = ragas_scores.to_pandas()
    per_question = df["faithfulness"].tolist()
    overall = float(df["faithfulness"].mean())

    # Per-domain breakdown
    domain_scores: dict[str, list[float]] = {}
    for result, score in zip(pipeline_results, per_question):
        domain_scores.setdefault(result["domain"], []).append(score)
    domain_averages = {d: sum(s)/len(s) for d, s in domain_scores.items()}

    # Per-difficulty breakdown
    diff_scores: dict[str, list[float]] = {}
    for result, score in zip(pipeline_results, per_question):
        diff_scores.setdefault(result["difficulty"], []).append(score)
    diff_averages = {d: sum(s)/len(s) for d, s in diff_scores.items()}

    # Worst performers
    scored = list(zip(pipeline_results, per_question))
    worst = sorted(scored, key=lambda x: x[1])[:5]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_faithfulness": overall,
        "threshold": threshold,
        "passed": overall >= threshold,
        "total_questions": len(pipeline_results),
        "declined_count": sum(1 for r in pipeline_results if r.get("declined")),
        "per_domain": domain_averages,
        "per_difficulty": diff_averages,
        "worst_performers": [
            {"id": r["id"], "question": r["question"][:80], "score": s}
            for r, s in worst
        ],
        "per_question_scores": [
            {"id": r["id"], "score": s, "domain": r["domain"]}
            for r, s in scored
        ],
    }


def print_report(report: dict):
    """Pretty-print the evaluation report."""
    passed = report["passed"]
    score  = report["overall_faithfulness"]
    color  = "green" if passed else "red"
    status = "[bold green]✅ PASSED[/bold green]" if passed else "[bold red]❌ FAILED[/bold red]"

    console.print(Panel(
        f"{status}\n\n"
        f"Faithfulness Score: [bold]{score:.3f}[/bold] "
        f"(threshold: {report['threshold']:.2f})\n"
        f"Questions: {report['total_questions']} "
        f"({report['declined_count']} declined)",
        title="RAGAS Evaluation Results",
        style=color,
    ))

    domain_table = Table(title="Faithfulness by Domain")
    domain_table.add_column("Domain", style="bold")
    domain_table.add_column("Score", justify="right")
    domain_table.add_column("Status")
    for domain, avg in sorted(report["per_domain"].items()):
        domain_table.add_row(domain, f"{avg:.3f}", "✅" if avg >= report["threshold"] else "⚠️")
    console.print(domain_table)

    diff_table = Table(title="Faithfulness by Difficulty")
    diff_table.add_column("Difficulty", style="bold")
    diff_table.add_column("Score", justify="right")
    for diff, avg in sorted(report["per_difficulty"].items()):
        diff_table.add_row(diff, f"{avg:.3f}")
    console.print(diff_table)

    worst_table = Table(title="Lowest Scoring Questions")
    worst_table.add_column("ID", style="dim")
    worst_table.add_column("Question")
    worst_table.add_column("Score", justify="right")
    for item in report["worst_performers"]:
        worst_table.add_row(item["id"], item["question"], f"{item['score']:.3f}")
    console.print(worst_table)


def save_report(report: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"eval_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    with open(RESULTS_DIR / "latest.json", "w") as f:
        json.dump(report, f, indent=2)
    return path


def main():
    parser = argparse.ArgumentParser(description="RAG Faithfulness Evaluation")
    parser.add_argument("--sample", type=int, help="Evaluate N random questions")
    parser.add_argument("--domain", type=str, help="Filter to specific domain")
    parser.add_argument("--fail-threshold", type=float, default=FAITHFULNESS_THRESHOLD)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    console.print(Panel(
        "[bold cyan]RAG Evaluation Pipeline — Phase 3[/bold cyan]\n"
        "Metric: Faithfulness (claims grounded in retrieved context)\n"
        f"Threshold: {args.fail_threshold}",
        style="cyan"
    ))

    questions = load_golden_dataset(
        domain_filter=args.domain,
        sample=args.sample,
        seed=args.seed,
    )
    console.print(f"[dim]Loaded {len(questions)} evaluation questions[/dim]")

    pipeline_results = run_rag_pipeline(questions)
    ragas_scores     = score_with_ragas(pipeline_results)
    report           = build_report(pipeline_results, ragas_scores, args.fail_threshold)

    print_report(report)
    path = save_report(report)
    console.print(f"\n[dim]Report saved to {path}[/dim]")

    if not report["passed"]:
        console.print(
            f"\n[bold red]BUILD FAILED:[/bold red] "
            f"Faithfulness {report['overall_faithfulness']:.3f} < threshold {args.fail_threshold}"
        )
        sys.exit(1)
    else:
        console.print(
            f"\n[bold green]BUILD PASSED:[/bold green] "
            f"Faithfulness {report['overall_faithfulness']:.3f} >= threshold {args.fail_threshold}"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
