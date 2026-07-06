"""
corpus_fetcher.py
Fetches real technical documents for the RAG corpus.
Supports both built-in datasets and custom URLs.
"""

import json
import time
import hashlib
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import track

console = Console()
MIN_CONTENT_LENGTH = 200

CORPUS_SOURCES = [
    {"url": "https://aws.amazon.com/iam/",                        "domain": "aws_core",     "title": "AWS IAM Overview"},
    {"url": "https://aws.amazon.com/iam/features/",               "domain": "aws_security", "title": "AWS IAM Features"},
    {"url": "https://aws.amazon.com/s3/",                         "domain": "aws_core",     "title": "Amazon S3 Overview"},
    {"url": "https://aws.amazon.com/s3/features/",                "domain": "aws_core",     "title": "Amazon S3 Features"},
    {"url": "https://aws.amazon.com/lambda/",                     "domain": "aws_core",     "title": "AWS Lambda Overview"},
    {"url": "https://aws.amazon.com/lambda/features/",            "domain": "aws_core",     "title": "AWS Lambda Features"},
    {"url": "https://aws.amazon.com/cloudwatch/",                 "domain": "aws_core",     "title": "Amazon CloudWatch Overview"},
    {"url": "https://aws.amazon.com/cloudwatch/features/",        "domain": "aws_core",     "title": "Amazon CloudWatch Features"},
    {"url": "https://aws.amazon.com/vpc/",                        "domain": "aws_core",     "title": "Amazon VPC Overview"},
    {"url": "https://aws.amazon.com/config/",                     "domain": "aws_core",     "title": "AWS Config Overview"},
    {"url": "https://aws.amazon.com/security/",                   "domain": "aws_security", "title": "AWS Security Overview"},
    {"url": "https://aws.amazon.com/guardduty/",                  "domain": "aws_security", "title": "Amazon GuardDuty Overview"},
    {"url": "https://aws.amazon.com/security-hub/",               "domain": "aws_security", "title": "AWS Security Hub Overview"},
    {"url": "https://aws.amazon.com/cloudtrail/",                 "domain": "aws_security", "title": "AWS CloudTrail Overview"},
    {"url": "https://aws.amazon.com/compliance/shared-responsibility-model/", "domain": "aws_security", "title": "AWS Shared Responsibility Model"},
    {"url": "https://aws.amazon.com/compliance/soc-faqs/",        "domain": "aws_security", "title": "AWS SOC Compliance FAQ"},
    {"url": "https://aws.amazon.com/compliance/iso-27001-faqs/",  "domain": "aws_security", "title": "AWS ISO 27001 FAQ"},
    {"url": "https://aws.amazon.com/blogs/security/the-aws-shared-responsibility-model-and-gdpr/", "domain": "aws_security", "title": "AWS Shared Responsibility and GDPR"},
    {"url": "https://aws.amazon.com/architecture/well-architected/", "domain": "aws_waf",   "title": "AWS Well-Architected Framework"},
    {"url": "https://aws.amazon.com/blogs/apn/the-5-pillars-of-the-aws-well-architected-framework/", "domain": "aws_waf", "title": "The 5 Pillars of AWS Well-Architected Framework"},
    {"url": "https://aws.amazon.com/sagemaker/",                  "domain": "aws_ml",       "title": "Amazon SageMaker Overview"},
    {"url": "https://docs.aws.amazon.com/sagemaker/latest/dg/how-it-works-training.html", "domain": "aws_ml", "title": "SageMaker Training Overview"},
    {"url": "https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html", "domain": "aws_ml", "title": "SageMaker Model Deployment"},
    {"url": "https://aws.amazon.com/compliance/gdpr-center/",     "domain": "grc",          "title": "AWS GDPR Compliance Center"},
    {"url": "https://aws.amazon.com/compliance/hipaa-compliance/","domain": "grc",          "title": "AWS HIPAA Compliance"},
    {"url": "https://aws.amazon.com/compliance/pci-dss-level-1-faqs/","domain": "grc",     "title": "AWS PCI DSS Compliance FAQ"},
    {"url": "https://owasp.org/www-project-top-ten/",             "domain": "grc",          "title": "OWASP Top 10 Overview"},
    {"url": "https://owasp.org/www-project-top-ten/2017/A1_2017-Injection", "domain": "grc","title": "OWASP Injection Attacks"},
    {"url": "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure", "domain": "grc", "title": "OWASP Sensitive Data Exposure"},
]


def fetch_page(url: str, timeout: int = 15) -> str | None:
    """
    Fetches a URL and returns cleaned text content.
    Uses a robust multi-strategy extraction approach that works across
    documentation sites, Wikipedia, MDN, AWS, GitHub, and custom URLs.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove obvious noise
        for tag in soup(["nav", "footer", "script", "style", "noscript",
                         "iframe", "svg", "img", "button", "form"]):
            tag.decompose()

        # Try semantic content containers in priority order
        content = None
        for selector in [
            {"name": "main"},
            {"name": "article"},
            {"attrs": {"role": "main"}},
            {"attrs": {"id": "content"}},
            {"attrs": {"id": "bodyContent"}},          # Wikipedia
            {"attrs": {"id": "mw-content-text"}},      # Wikipedia
            {"attrs": {"class": "content"}},
            {"attrs": {"class": "documentation"}},
            {"attrs": {"class": "docs-content"}},
            {"attrs": {"class": "markdown-body"}},     # GitHub
            {"attrs": {"class": "post-body"}},
        ]:
            found = soup.find(**selector)
            if found:
                text = found.get_text(separator="\n", strip=True)
                if len(text) >= MIN_CONTENT_LENGTH:
                    content = text
                    break

        # Fallback: use full body text
        if not content:
            body = soup.find("body")
            if body:
                content = body.get_text(separator="\n", strip=True)

        if not content or len(content) < MIN_CONTENT_LENGTH:
            return None

        # Clean up lines — keep anything non-empty (don't filter by length
        # since short lines like headers/labels are valid content)
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        result = "\n".join(lines)

        return result if len(result) >= MIN_CONTENT_LENGTH else None

    except Exception as e:
        console.print(f"[yellow]  ⚠ Skipped {url}: {e}[/yellow]")
        return None


def build_corpus(output_dir: str = "corpus") -> list[dict]:
    """Downloads all corpus sources and saves as JSON docs."""
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    docs = []
    console.print(f"\n[bold cyan]📥 Fetching {len(CORPUS_SOURCES)} corpus documents...[/bold cyan]")
    console.print("[dim]Domains: AWS Core | AWS Security | AWS Well-Architected | AWS ML/SageMaker | GRC/NIST/OWASP[/dim]\n")

    for source in track(CORPUS_SOURCES, description="Fetching docs"):
        doc_id = hashlib.md5(source["url"].encode()).hexdigest()[:8]
        cache_file = out / f"{doc_id}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                doc = json.load(f)
            docs.append(doc)
            continue

        text = fetch_page(source["url"])
        if not text:
            console.print(f"[yellow]  ⚠ Too short or empty: {source['title']}[/yellow]")
            continue

        doc = {
            "id": doc_id,
            "title": source["title"],
            "domain": source["domain"],
            "url": source["url"],
            "content": text,
            "char_count": len(text),
        }
        with open(cache_file, "w") as f:
            json.dump(doc, f, indent=2)

        docs.append(doc)
        time.sleep(0.5)

    by_domain: dict[str, int] = {}
    for d in docs:
        by_domain[d["domain"]] = by_domain.get(d["domain"], 0) + 1

    console.print(f"\n[green]✅ Fetched {len(docs)} documents ({sum(d['char_count'] for d in docs):,} chars total)[/green]")
    for domain, count in sorted(by_domain.items()):
        console.print(f"  [dim]{domain}: {count} docs[/dim]")

    return docs