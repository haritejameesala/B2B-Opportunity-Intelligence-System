import json
import os
import sys

from app.llm import LocalLlama
from app.brandhero import BrandheroResearcher
from app.researcher import Researcher
from app.signals import SignalAnalyzer
from app.scoring import OpportunityScorer


BRANDHERO_CACHE = "data/brandhero_profile.json"


def print_header(title):
    print("\n======================================")
    print(title)
    print("======================================")


def load_brandhero_profile(llm):
    """
    Load Brandhero profile from cache.

    If cache does not exist:
        1. Crawl Brandhero
        2. Extract capability profile with Llama
        3. Save profile
    """

    if os.path.exists(BRANDHERO_CACHE):

        print(
            f"[BRANDHERO] Loading cached profile: "
            f"{BRANDHERO_CACHE}"
        )

        try:
            with open(
                BRANDHERO_CACHE,
                "r",
                encoding="utf-8"
            ) as f:

                profile = json.load(f)

            print(
                "[BRANDHERO] Cached profile loaded."
            )

            return profile

        except (
            json.JSONDecodeError,
            OSError
        ) as e:

            print(
                f"[BRANDHERO] Cache could not be loaded: {e}"
            )

            print(
                "[BRANDHERO] Rebuilding profile..."
            )

    # ---------------------------------------------------------
    # Cache doesn't exist → research Brandhero
    # ---------------------------------------------------------

    print_header(
        "[BRANDHERO INTELLIGENCE]"
    )

    researcher = BrandheroResearcher()

    brandhero_data = researcher.research()

    if not brandhero_data.get("pages"):

        raise RuntimeError(
            "Could not collect Brandhero website data."
        )

    profile = researcher.extract_profile(
        brandhero_data
    )

    # ---------------------------------------------------------
    # Save profile
    # ---------------------------------------------------------

    os.makedirs(
        os.path.dirname(BRANDHERO_CACHE),
        exist_ok=True
    )

    with open(
        BRANDHERO_CACHE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            profile,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"[BRANDHERO] Profile cached at "
        f"{BRANDHERO_CACHE}"
    )

    return profile


def print_brandhero_profile(profile):

    print_header(
        "BRANDHERO PROFILE"
    )

    description = profile.get(
        "description",
        ""
    )

    if description:
        print(
            f"\nDescription:\n{description}"
        )

    capabilities = profile.get(
        "capabilities",
        []
    )

    if capabilities:

        print("\nCapabilities:")

        for capability in capabilities:

            name = capability.get(
                "name",
                ""
            )

            description = capability.get(
                "description",
                ""
            )

            print(
                f"\n  {name}"
            )

            if description:
                print(
                    f"  {description}"
                )


def print_signals(result):

    signals = result.get(
        "signals",
        {}
    )

    signal_names = {
        "product_change":
            "Product / Feature Change",

        "rebrand_or_positioning":
            "Rebrand / Positioning Change",

        "website_change":
            "Website / Digital Experience Change",

        "market_expansion":
            "Market / Audience Expansion",

        "design_product_hiring":
            "Design / Product Hiring",

        "growth_with_experience_pressure":
            "Growth with Experience Pressure",

        "observable_experience_problem":
            "Observable UX / Product Experience Problem",
    }

    for key, display_name in signal_names.items():

        signal = signals.get(
            key,
            {}
        )

        print(
            f"\n[{display_name}]"
        )

        detected = signal.get(
            "detected",
            False
        )

        confidence = signal.get(
            "confidence",
            0
        )

        relevance = signal.get(
            "brandhero_relevance",
            0
        )

        print(
            "Detected: "
            + (
                "YES"
                if detected
                else "NO"
            )
        )

        print(
            f"Confidence: {float(confidence):.2f}"
        )

        print(
            f"Brandhero Relevance: "
            f"{float(relevance):.2f}"
        )

        observation = signal.get(
            "observation",
            ""
        )

        if observation:
            print(
                f"Observation: {observation}"
            )

        reason = signal.get(
            "brandhero_reason",
            ""
        )

        if reason:
            print(
                f"Brandhero Reason: {reason}"
            )

        evidence = signal.get(
            "evidence",
            []
        )

        if evidence:

            print("Evidence:")

            for item in evidence:

                claim = item.get(
                    "claim",
                    ""
                )

                url = item.get(
                    "url",
                    ""
                )

                if claim:
                    print(
                        f"  - {claim}"
                    )

                if url:
                    print(
                        f"    Source: {url}"
                    )


def print_opportunity(result):

    opportunity = result.get(
        "opportunity",
        {}
    )

    print_header(
        "BRANDHERO OPPORTUNITY"
    )

    likely_need = opportunity.get(
        "likely_brandhero_need",
        False
    )

    print(
        "Likely Brandhero Need: "
        + (
            "YES"
            if likely_need
            else "NO"
        )
    )

    print(
        "Evidence-based Opportunity Tier: "
        + opportunity.get(
            "opportunity_tier",
            "No Opportunity"
        )
    )

    confidence = opportunity.get(
        "confidence",
        0
    )

    print(
        f"Confidence: {float(confidence):.2f}"
    )

    primary_need = opportunity.get(
        "primary_need",
        ""
    )

    if primary_need:
        print(
            f"Primary Need: {primary_need}"
        )

    stakeholder = opportunity.get(
        "relevant_stakeholder",
        ""
    )

    if stakeholder:
        print(
            f"Relevant Stakeholder: {stakeholder}"
        )

    why_now = opportunity.get(
        "why_now",
        ""
    )

    if why_now:
        print(
            f"Why Now: {why_now}"
        )

    outreach = opportunity.get(
        "personalized_outreach_angle",
        ""
    )

    if outreach:
        print(
            f"Personalized Outreach Angle: {outreach}"
        )


def print_score(score_result):

    print_header(
        "SCORING"
    )

    score = score_result.get(
        "score",
        0
    )

    tier = score_result.get(
        "tier",
        "Very Low"
    )

    print(
        f"Score: {score}/100"
    )

    print(
        f"Tier: {tier}"
    )

    breakdown = score_result.get(
        "breakdown",
        {}
    )

    if breakdown:

        print(
            "\nScore Breakdown:"
        )

        for name, item in breakdown.items():

            points = item.get(
                "points",
                0
            )

            maximum = item.get(
                "max_points",
                0
            )

            detected = item.get(
                "detected",
                False
            )

            relevance = item.get(
                "relevance",
                0
            )

            print(
                f"  {name}: "
                f"{points:.1f}/{maximum} | "
                f"{'YES' if detected else 'NO'} | "
                f"relevance={relevance:.2f}"
            )


def main():

    # Company evidence can contain legitimate Unicode characters (for example
    # arrows in a changelog).  Avoid crashing after analysis on Windows shells
    # that default to a legacy code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(
        "======================================"
    )

    print(
        "B2B OPPORTUNITY INTELLIGENCE SYSTEM"
    )

    print(
        "======================================"
    )

    # =========================================================
    # 1. INITIALIZE LLM
    # =========================================================

    llm = LocalLlama()

    # =========================================================
    # 2. LOAD BRANDHERO INTELLIGENCE
    # =========================================================

    brandhero_profile = load_brandhero_profile(
        llm
    )

    print_brandhero_profile(
        brandhero_profile
    )

    # =========================================================
    # 3. TARGET COMPANY
    # =========================================================

    print_header(
        "TARGET COMPANY"
    )

    domain = input(
        "Enter company domain: "
    ).strip()

    if not domain:

        print(
            "[ERROR] Company domain is required."
        )

        return

    company_name = input(
        "Enter company name: "
    ).strip()

    if not company_name:
        company_name = None

    # =========================================================
    # 4. RESEARCH TARGET
    # =========================================================

    print_header(
        "[RESEARCH]"
    )

    researcher = Researcher(
        domain=domain,
        company_name=company_name
    )

    research_data = researcher.research()

    # A score of zero is meaningful only when the company was actually
    # researched.  Do not send an empty data set to the analyzer, because it
    # inevitably returns seven false signals and looks like a valid result.
    if not research_data.get("research_completed"):
        print(
            "[ERROR] No first-party website evidence was collected. "
            "Check the domain or network access, then try again."
        )
        return

    research_data["domain"] = domain

    if company_name:

        research_data["company_name"] = (
            company_name
        )

    print(
        "\n[RESEARCH] Target research completed."
    )

    # =========================================================
    # 5. ANALYZE SIGNALS
    # =========================================================

    print_header(
        "[SIGNALS]"
    )

    analyzer = SignalAnalyzer(
        llm
    )

    signal_result = analyzer.analyze(
        research_data,
        brandhero_profile
    )

    print_signals(
        signal_result
    )

    # =========================================================
    # 6. OPPORTUNITY
    # =========================================================

    print_opportunity(
        signal_result
    )

    # =========================================================
    # 7. SCORE
    # =========================================================

    scorer = OpportunityScorer()

    score_result = scorer.calculate(
        signal_result
    )

    print_score(
        score_result
    )

    # =========================================================
    # 8. FINAL SUMMARY
    # =========================================================

    print_header(
        "FINAL SUMMARY"
    )

    print(
        f"Company: "
        f"{research_data.get('company_name', domain)}"
    )

    print(
        f"Domain: {domain}"
    )

    print(
        f"Opportunity Score: "
        f"{score_result.get('score', 0)}/100"
    )

    print(
        f"Opportunity Tier: "
        f"{score_result.get('tier', 'Very Low')}"
    )

    print(
        "Note: Score Tier is the raw weighted score; "
        "Evidence-based Opportunity Tier is reported separately."
    )

    opportunity = signal_result.get(
        "opportunity",
        {}
    )

    print(
        "\nBrandhero Opportunity: "
        + (
            "YES"
            if opportunity.get(
                "likely_brandhero_need",
                False
            )
            else "NO"
        )
    )

    print(
        "Primary Need: "
        + opportunity.get(
            "primary_need",
            ""
        )
    )

    print(
        "Stakeholder: "
        + opportunity.get(
            "relevant_stakeholder",
            ""
        )
    )

    print(
        "Why Now: "
        + opportunity.get(
            "why_now",
            ""
        )
    )

    print(
        "\nAnalysis completed."
    )


if __name__ == "__main__":
    main()
