"""
ask.py
Interactive CLI for querying the RAG system.

Usage:
    python ask.py "What is RAG?"
    python ask.py --interactive        # REPL mode
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt

sys.path.insert(0, str(Path(__file__).parent))
console = Console()


def main():
    parser = argparse.ArgumentParser(description="Ask My Docs — RAG Query CLI")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("-i", "--interactive", action="store_true", help="REPL mode")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress pipeline steps")
    args = parser.parse_args()

    console.print("[bold cyan]Loading RAG pipeline...[/bold cyan]")
    from src.pipeline import RAGPipeline
    pipeline = RAGPipeline()

    verbose = not args.quiet

    if args.interactive:
        console.print("\n[bold]Ask My Docs[/bold] — type [dim]'exit'[/dim] to quit\n")
        while True:
            question = Prompt.ask("[bold blue]>[/bold blue]")
            if question.lower() in ("exit", "quit", "q"):
                break
            if not question.strip():
                continue
            pipeline.query(question, verbose=verbose)
            console.print()

    elif args.question:
        pipeline.query(args.question, verbose=verbose)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
