"""Run the complete opportunity pipeline for a fixed verification cohort."""

import json
import sys

from app.llm import LocalLlama
from app.researcher import Researcher
from app.scoring import OpportunityScorer
from app.signals import SignalAnalyzer


COMPANIES = [
    ("Linear", "linear.app"),
    ("Ramp", "ramp.com"),
    ("Notion", "notion.so"),
    ("HubSpot", "hubspot.com"),
    ("Canva", "canva.com"),
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    with open("data/brandhero_profile.json", encoding="utf-8") as profile_file:
        brandhero_profile = json.load(profile_file)

    llm = LocalLlama()
    analyzer = SignalAnalyzer(llm)
    scorer = OpportunityScorer()

    for company_name, domain in COMPANIES:
        print(f"\n{'=' * 70}\nVERIFYING: {company_name} ({domain})\n{'=' * 70}")
        research_data = Researcher(domain, company_name).research()
        result = analyzer.analyze(research_data, brandhero_profile)
        score = scorer.calculate(result)

        summary = {
            "company": company_name,
            "evidence_counts": {
                signal: len(records)
                for signal, records in research_data.get("signal_evidence", {}).items()
            },
            "detected_signals": [
                signal
                for signal, details in result.get("signals", {}).items()
                if details.get("detected")
            ],
            "likely_brandhero_need": result.get("opportunity", {}).get(
                "likely_brandhero_need", False
            ),
            "score": score["score"],
            "tier": score["tier"],
        }
        print("[VERIFY SUMMARY] " + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
