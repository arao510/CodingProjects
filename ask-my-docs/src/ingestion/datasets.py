"""
datasets.py
Multi-dataset registry for the RAG comparison system.
Each dataset is a named collection of URLs that get fetched,
chunked, embedded, and indexed as a self-contained corpus.

Adding a new built-in dataset: add an entry to DATASETS dict below.
Custom datasets: users supply URLs via the UI which get stored in
  .custom_datasets.json at runtime.
"""

import json
from pathlib import Path

CUSTOM_DATASETS_PATH = ".custom_datasets.json"

# ── Built-in dataset registry ──────────────────────────────────────────────────
DATASETS: dict[str, dict] = {

    "aws_cloud": {
        "name": "AWS Cloud & Security",
        "description": "IAM, S3, Lambda, VPC, GuardDuty, CloudTrail, Well-Architected Framework",
        "icon": "☁️",
        "color": "#F59E0B",
        "sources": [
            {"url": "https://aws.amazon.com/iam/", "domain": "aws_security", "title": "AWS IAM Overview"},
            {"url": "https://aws.amazon.com/iam/features/", "domain": "aws_security", "title": "AWS IAM Features"},
            {"url": "https://aws.amazon.com/s3/", "domain": "aws_core", "title": "Amazon S3 Overview"},
            {"url": "https://aws.amazon.com/s3/features/", "domain": "aws_core", "title": "Amazon S3 Features"},
            {"url": "https://aws.amazon.com/lambda/", "domain": "aws_core", "title": "AWS Lambda Overview"},
            {"url": "https://aws.amazon.com/lambda/features/", "domain": "aws_core", "title": "AWS Lambda Features"},
            {"url": "https://aws.amazon.com/cloudwatch/features/", "domain": "aws_core", "title": "CloudWatch Features"},
            {"url": "https://aws.amazon.com/vpc/", "domain": "aws_core", "title": "Amazon VPC Overview"},
            {"url": "https://aws.amazon.com/security/", "domain": "aws_security", "title": "AWS Security Overview"},
            {"url": "https://aws.amazon.com/guardduty/", "domain": "aws_security", "title": "Amazon GuardDuty"},
            {"url": "https://aws.amazon.com/security-hub/", "domain": "aws_security", "title": "AWS Security Hub"},
            {"url": "https://aws.amazon.com/cloudtrail/", "domain": "aws_security", "title": "AWS CloudTrail"},
            {"url": "https://aws.amazon.com/compliance/shared-responsibility-model/", "domain": "aws_security", "title": "Shared Responsibility Model"},
            {"url": "https://aws.amazon.com/compliance/soc-faqs/", "domain": "aws_security", "title": "AWS SOC Compliance"},
            {"url": "https://aws.amazon.com/compliance/iso-27001-faqs/", "domain": "aws_security", "title": "AWS ISO 27001"},
            {"url": "https://aws.amazon.com/architecture/well-architected/", "domain": "aws_waf", "title": "Well-Architected Framework"},
            {"url": "https://aws.amazon.com/blogs/apn/the-5-pillars-of-the-aws-well-architected-framework/", "domain": "aws_waf", "title": "5 Pillars of Well-Architected"},
            {"url": "https://aws.amazon.com/sagemaker/", "domain": "aws_ml", "title": "Amazon SageMaker"},
            {"url": "https://aws.amazon.com/compliance/gdpr-center/", "domain": "grc", "title": "AWS GDPR Center"},
            {"url": "https://aws.amazon.com/compliance/hipaa-compliance/", "domain": "grc", "title": "AWS HIPAA Compliance"},
        ]
    },

    "cybersecurity": {
        "name": "Cybersecurity & GRC",
        "description": "OWASP Top 10, NIST framework, zero trust, vulnerability management",
        "icon": "🔐",
        "color": "#EF4444",
        "sources": [
            {"url": "https://owasp.org/www-project-top-ten/", "domain": "owasp", "title": "OWASP Top 10"},
            {"url": "https://owasp.org/www-project-top-ten/2017/A1_2017-Injection", "domain": "owasp", "title": "OWASP Injection"},
            {"url": "https://owasp.org/www-project-top-ten/2017/A2_2017-Broken_Authentication", "domain": "owasp", "title": "OWASP Broken Auth"},
            {"url": "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure", "domain": "owasp", "title": "OWASP Sensitive Data"},
            {"url": "https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration", "domain": "owasp", "title": "OWASP Misconfiguration"},
            {"url": "https://owasp.org/www-project-top-ten/2017/A7_2017-Cross-Site_Scripting_(XSS)", "domain": "owasp", "title": "OWASP XSS"},
            {"url": "https://www.nist.gov/cyberframework", "domain": "nist", "title": "NIST Cybersecurity Framework"},
            {"url": "https://aws.amazon.com/compliance/shared-responsibility-model/", "domain": "cloud_sec", "title": "Cloud Shared Responsibility"},
            {"url": "https://aws.amazon.com/security/", "domain": "cloud_sec", "title": "Cloud Security Overview"},
            {"url": "https://aws.amazon.com/guardduty/", "domain": "cloud_sec", "title": "Threat Detection"},
            {"url": "https://aws.amazon.com/compliance/gdpr-center/", "domain": "compliance", "title": "GDPR Compliance"},
            {"url": "https://aws.amazon.com/compliance/hipaa-compliance/", "domain": "compliance", "title": "HIPAA Compliance"},
            {"url": "https://aws.amazon.com/compliance/pci-dss-level-1-faqs/", "domain": "compliance", "title": "PCI DSS Compliance"},
            {"url": "https://aws.amazon.com/compliance/soc-faqs/", "domain": "compliance", "title": "SOC Compliance"},
            {"url": "https://aws.amazon.com/compliance/iso-27001-faqs/", "domain": "compliance", "title": "ISO 27001"},
        ]
    },

    "machine_learning": {
        "name": "Machine Learning & AI",
        "description": "SageMaker, ML pipelines, model training, deployment, MLOps",
        "icon": "🤖",
        "color": "#8B5CF6",
        "sources": [
            {"url": "https://aws.amazon.com/sagemaker/", "domain": "sagemaker", "title": "Amazon SageMaker"},
            {"url": "https://aws.amazon.com/sagemaker/features/", "domain": "sagemaker", "title": "SageMaker Features"},
            {"url": "https://docs.aws.amazon.com/sagemaker/latest/dg/how-it-works-training.html", "domain": "sagemaker", "title": "SageMaker Training"},
            {"url": "https://docs.aws.amazon.com/sagemaker/latest/dg/deploy-model.html", "domain": "sagemaker", "title": "SageMaker Deployment"},
            {"url": "https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html", "domain": "sagemaker", "title": "SageMaker Pipelines"},
            {"url": "https://aws.amazon.com/what-is/machine-learning/", "domain": "ml_concepts", "title": "What is Machine Learning"},
            {"url": "https://aws.amazon.com/what-is/deep-learning/", "domain": "ml_concepts", "title": "What is Deep Learning"},
            {"url": "https://aws.amazon.com/what-is/neural-network/", "domain": "ml_concepts", "title": "What is a Neural Network"},
            {"url": "https://aws.amazon.com/what-is/natural-language-processing/", "domain": "ml_concepts", "title": "What is NLP"},
            {"url": "https://aws.amazon.com/what-is/computer-vision/", "domain": "ml_concepts", "title": "What is Computer Vision"},
            {"url": "https://aws.amazon.com/rekognition/", "domain": "ai_services", "title": "Amazon Rekognition"},
            {"url": "https://aws.amazon.com/comprehend/", "domain": "ai_services", "title": "Amazon Comprehend"},
            {"url": "https://aws.amazon.com/bedrock/", "domain": "ai_services", "title": "Amazon Bedrock"},
            {"url": "https://aws.amazon.com/lambda/", "domain": "mlops", "title": "Serverless for ML"},
            {"url": "https://aws.amazon.com/cloudwatch/", "domain": "mlops", "title": "ML Model Monitoring"},
        ]
    },

    "web_development": {
        "name": "Web Development",
        "description": "React, APIs, databases, performance, frontend & backend concepts",
        "icon": "🌐",
        "color": "#10B981",
        "sources": [
            {"url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview", "domain": "web", "title": "HTTP Overview"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods", "domain": "web", "title": "HTTP Methods"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status", "domain": "web", "title": "HTTP Status Codes"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies", "domain": "web", "title": "HTTP Cookies"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API", "domain": "web", "title": "Fetch API"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction", "domain": "javascript", "title": "JavaScript Introduction"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions", "domain": "javascript", "title": "JavaScript Functions"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Promises", "domain": "javascript", "title": "JavaScript Promises"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout", "domain": "css", "title": "CSS Grid Layout"},
            {"url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout", "domain": "css", "title": "CSS Flexbox"},
            {"url": "https://aws.amazon.com/what-is/restful-api/", "domain": "apis", "title": "What is a REST API"},
            {"url": "https://aws.amazon.com/what-is/sql/", "domain": "databases", "title": "What is SQL"},
            {"url": "https://aws.amazon.com/nosql/", "domain": "databases", "title": "NoSQL Databases"},
            {"url": "https://aws.amazon.com/caching/", "domain": "performance", "title": "Web Caching"},
            {"url": "https://aws.amazon.com/cdn/", "domain": "performance", "title": "Content Delivery Networks"},
        ]
    },

    "devops": {
        "name": "DevOps & Cloud Infra",
        "description": "CI/CD, containers, Kubernetes, infrastructure as code, monitoring",
        "icon": "⚙️",
        "color": "#06B6D4",
        "sources": [
            {"url": "https://aws.amazon.com/devops/what-is-devops/", "domain": "devops", "title": "What is DevOps"},
            {"url": "https://aws.amazon.com/devops/continuous-integration/", "domain": "devops", "title": "Continuous Integration"},
            {"url": "https://aws.amazon.com/devops/continuous-delivery/", "domain": "devops", "title": "Continuous Delivery"},
            {"url": "https://aws.amazon.com/docker/", "domain": "containers", "title": "Docker on AWS"},
            {"url": "https://aws.amazon.com/kubernetes/", "domain": "containers", "title": "Kubernetes on AWS"},
            {"url": "https://aws.amazon.com/eks/", "domain": "containers", "title": "Amazon EKS"},
            {"url": "https://aws.amazon.com/ecs/", "domain": "containers", "title": "Amazon ECS"},
            {"url": "https://aws.amazon.com/what-is/infrastructure-as-code/", "domain": "iac", "title": "Infrastructure as Code"},
            {"url": "https://aws.amazon.com/cloudformation/", "domain": "iac", "title": "AWS CloudFormation"},
            {"url": "https://aws.amazon.com/cloudwatch/", "domain": "monitoring", "title": "CloudWatch Monitoring"},
            {"url": "https://aws.amazon.com/cloudwatch/features/", "domain": "monitoring", "title": "CloudWatch Features"},
            {"url": "https://aws.amazon.com/config/", "domain": "monitoring", "title": "AWS Config"},
            {"url": "https://aws.amazon.com/elasticloadbalancing/", "domain": "infra", "title": "Load Balancing"},
            {"url": "https://aws.amazon.com/autoscaling/", "domain": "infra", "title": "Auto Scaling"},
            {"url": "https://aws.amazon.com/what-is/microservices/", "domain": "architecture", "title": "Microservices"},
        ]
    },
}


def load_custom_datasets() -> dict:
    """Load user-created custom datasets from disk."""
    path = Path(CUSTOM_DATASETS_PATH)
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def save_custom_dataset(dataset_id: str, dataset: dict):
    """Save a custom dataset to disk."""
    custom = load_custom_datasets()
    custom[dataset_id] = dataset
    with open(CUSTOM_DATASETS_PATH, "w") as f:
        json.dump(custom, f, indent=2)


def get_all_datasets() -> dict:
    """Returns all built-in + custom datasets."""
    all_ds = {**DATASETS}
    custom = load_custom_datasets()
    for k, v in custom.items():
        v["is_custom"] = True
        all_ds[k] = v
    return all_ds


def get_dataset(dataset_id: str) -> dict | None:
    return get_all_datasets().get(dataset_id)
