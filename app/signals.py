import json
import re


SIGNAL_DEFINITIONS = {

    "product_change": {
        "name": "Product / Feature Change",
        "description": (
            "A recent, observable product launch, major feature release, "
            "redesign, or substantial product experience change."
        ),
        "brandhero_relevance": (
            "Product changes can create demand for product design, UX "
            "research, UX strategy, interaction design, and design systems."
        ),
    },

    "rebrand_or_positioning": {
        "name": "Rebrand / Positioning Change",
        "description": (
            "An actual recent change to brand identity, messaging, "
            "positioning, visual identity, or target audience."
        ),
        "brandhero_relevance": (
            "Brandhero provides branding, visual design, UX strategy, "
            "and product design services that can support a repositioning."
        ),
    },

    "website_change": {
        "name": "Website / Digital Experience Change",
        "description": (
            "A recent website redesign, major website launch, information "
            "architecture change, or significant digital experience update."
        ),
        "brandhero_relevance": (
            "Website changes can require UX/UI design, visual design, "
            "development, accessibility, and conversion-focused experience work."
        ),
    },

    "market_expansion": {
        "name": "Market / Audience Expansion",
        "description": (
            "A concrete expansion into a new geography, customer segment, "
            "industry, or materially different audience. It requires explicit "
            "evidence naming that new market or audience; a new platform, "
            "device, integration, or feature is a product change instead."
        ),
        "brandhero_relevance": (
            "New audiences can create demand for localized UX, research, "
            "brand adaptation, and product experience changes."
        ),
    },

    "design_product_hiring": {
        "name": "Design / Product Hiring",
        "description": (
            "Evidence of active hiring specifically for product design, "
            "UX, UI, research, brand, creative, or related design roles."
        ),
        "brandhero_relevance": (
            "Design hiring can indicate increased product/design workload "
            "or a need to scale design capacity."
        ),
    },

    "growth_with_experience_pressure": {
        "name": "Growth with Experience Pressure",
        "description": (
            "Concrete business or product growth combined with evidence "
            "that the company is undergoing a significant experience-related "
            "change or scaling challenge."
        ),
        "brandhero_relevance": (
            "Growth can increase the need to improve product experience, "
            "design systems, usability, and customer-facing digital experiences, "
            "but growth alone is insufficient."
        ),
    },

    "observable_experience_problem": {
        "name": "Observable UX / Product Experience Problem",
        "description": (
            "A specific, externally observable product or website experience "
            "problem supported by direct evidence."
        ),
        "brandhero_relevance": (
            "Direct UX problems are strongly relevant to Brandhero's UI/UX, "
            "product design, research, accessibility, and strategy capabilities."
        ),
    },
}


class SignalAnalyzer:

    def __init__(self, llm):
        self.llm = llm

    # =========================================================
    # BRANDHERO PROFILE
    # =========================================================

    def prepare_brandhero_profile(self, profile):

        if not isinstance(profile, dict):
            return {}

        result = {
            "name": profile.get(
                "name",
                "Brandhero"
            ),
            "description": profile.get(
                "description",
                ""
            ),
            "capabilities": [],
        }

        capabilities = profile.get(
            "capabilities",
            []
        )

        if isinstance(capabilities, list):

            for capability in capabilities:

                if not isinstance(
                    capability,
                    dict
                ):
                    continue

                name = capability.get(
                    "name",
                    ""
                )

                description = capability.get(
                    "description",
                    ""
                )

                if name or description:

                    result["capabilities"].append({
                        "name": name,
                        "description": description,
                    })

        return result

    # =========================================================
    # DETERMINISTIC NEWS FILTERING
    # =========================================================

    @staticmethod
    def is_relevant_news(article, company_name, domain):
        if not isinstance(article, dict):
            return False

        title = str(article.get("title", "")).strip()
        description = str(article.get("description", article.get("summary", ""))).strip()
        url = str(article.get("url", "")).strip()

        combined_text = f"{title} {description} {url}".lower()

        # Check domain name without tld (e.g. 'linear' from 'linear.app')
        domain_clean = re.sub(r"^https?://", "", domain.lower()).rstrip("/")
        domain_parts = domain_clean.split(".")
        root_domain = domain_parts[0] if domain_parts else ""

        # Match exact whole word for company name
        company_clean = company_name.strip().lower()
        if company_clean:
            # Word boundary match for company name
            if re.search(rf"\b{re.escape(company_clean)}\b", combined_text):
                return True

        if domain_clean and domain_clean in combined_text:
            return True

        if root_domain and len(root_domain) >= 3:
            if re.search(rf"\b{re.escape(root_domain)}\b", combined_text):
                return True

        return False

    # =========================================================
    # COMPANY EVIDENCE
    # =========================================================

    def prepare_company_evidence(
        self,
        research_data
    ):

        if not isinstance(
            research_data,
            dict
        ):
            return {}

        company_name = str(
            research_data.get(
                "company_name",
                research_data.get(
                    "company",
                    ""
                )
            )
        ).strip()

        domain = str(
            research_data.get(
                "domain",
                ""
            )
        ).strip()

        website_val = research_data.get(
            "website",
            ""
        )
        if isinstance(website_val, dict):
            website_url = website_val.get("url", "")
        else:
            website_url = str(website_val)

        company = {
            "company_name": company_name,
            "domain": domain,
            "website": website_url,
            "pages": [],
            "signal_evidence": {},
        }

        # The researcher supplies evidence already scoped to each signal. Do
        # not fall back to generic pages/news here: that would let a homepage
        # description leak back into classification as pseudo-evidence.
        raw_signal_evidence = research_data.get("signal_evidence", {})
        if not isinstance(raw_signal_evidence, dict):
            raw_signal_evidence = {}

        for signal_name in SIGNAL_DEFINITIONS:
            cleaned_records = []
            seen_urls = set()
            records = raw_signal_evidence.get(signal_name, [])
            if not isinstance(records, list):
                records = []

            for record in records:
                if not isinstance(record, dict):
                    continue
                claim = str(record.get("claim", "")).strip()
                url = str(record.get("source_url", "")).strip()
                snippet = str(record.get("snippet", "")).strip()
                source_type = str(record.get("source_type", "")).strip()
                if (
                    not claim
                    or not snippet
                    or not url
                    or "news.google.com" in url.lower()
                    or url in seen_urls
                ):
                    continue
                seen_urls.add(url)
                cleaned_records.append({
                    "signal": signal_name,
                    "claim": claim[:700],
                    "source_url": url,
                    "snippet": snippet[:900],
                    "source_type": source_type,
                })

                if not any(
                    page.get("url") == url
                    for page in company["pages"]
                ):
                    company["pages"].append({
                        "title": claim[:160],
                        "url": url,
                        "text": snippet,
                    })

            company["signal_evidence"][signal_name] = cleaned_records

        return company

        # -----------------------------------------------------
        # Website pages
        # -----------------------------------------------------

        collected_pages = []

        # 1. Check direct 'pages' list/dict
        raw_pages = research_data.get("pages", [])
        if isinstance(raw_pages, dict):
            raw_pages = list(raw_pages.values())
        if isinstance(raw_pages, list):
            collected_pages.extend(raw_pages)

        # 2. Check 'website' dict if not already included
        if isinstance(website_val, dict) and website_val.get("text"):
            collected_pages.append({
                "title": website_val.get("title", ""),
                "url": website_val.get("url", website_url),
                "text": website_val.get("text", "")
            })

        # 3. Check 'relevant_pages' dict
        rel_pages = research_data.get("relevant_pages", {})
        if isinstance(rel_pages, dict):
            for p_type, p_val in rel_pages.items():
                if isinstance(p_val, dict) and p_val.get("text"):
                    collected_pages.append({
                        "title": f"{company_name} - {p_type.title()}",
                        "url": p_val.get("url", ""),
                        "text": p_val.get("text", "")
                    })

        # Deduplicate pages by URL and clean
        seen_urls = set()
        for page in collected_pages:
            if not isinstance(page, dict):
                continue

            url = str(page.get("url", "")).strip()
            if not url or url in seen_urls:
                continue

            title = str(page.get("title", "")).strip()
            text = str(page.get("text", page.get("content", ""))).strip()

            if not text:
                continue

            seen_urls.add(url)
            # Limit page content to manageable size for compact prompt
            company["pages"].append({
                "title": title,
                "url": url,
                "text": text[:3500],
            })

        # -----------------------------------------------------
        # News (deterministic filtering)
        # -----------------------------------------------------

        raw_news = research_data.get("news", [])
        news_items = []
        if isinstance(raw_news, dict):
            for category_items in raw_news.values():
                if isinstance(category_items, list):
                    news_items.extend(category_items)
        elif isinstance(raw_news, list):
            news_items.extend(raw_news)

        seen_news_urls = set()
        for article in news_items:
            if not isinstance(article, dict):
                continue

            url = str(article.get("url", "")).strip()
            title = str(article.get("title", "")).strip()
            if not url or url in seen_news_urls or not title:
                continue

            # Deterministic relevance filter
            if not self.is_relevant_news(article, company_name, domain):
                continue

            seen_news_urls.add(url)
            description = str(article.get("description", article.get("summary", ""))).strip()
            source = str(article.get("source", "")).strip()
            date = str(article.get("date", article.get("published", ""))).strip()

            company["news"].append({
                "title": title,
                "description": description[:1000],
                "url": url,
                "source": source,
                "date": date,
            })

        return company

    # =========================================================
    # PROMPT
    # =========================================================

    def build_prompt(
        self,
        company_evidence,
        brandhero_profile
    ):

        signals_json = json.dumps(
            SIGNAL_DEFINITIONS,
            indent=2,
            ensure_ascii=False
        )

        brandhero_json = json.dumps(
            brandhero_profile,
            indent=2,
            ensure_ascii=False
        )

        company_json = json.dumps(
            company_evidence,
            indent=2,
            ensure_ascii=False
        )

        system_prompt = """
You are the evidence-based opportunity intelligence engine
for Brandhero, a design agency.

Your job is NOT to generate generic business opportunities.

Your ONLY task is to analyze the TARGET COMPANY using the supplied
signal-scoped evidence and determine whether any of the seven predefined
Brandhero opportunity signals are actually present.

CRITICAL:

1. Analyze ONLY the TARGET COMPANY.

2. Ignore unrelated companies mentioned in news articles.

3. Never invent facts.

4. Never use your general knowledge to add evidence.

5. Every detected signal MUST have at least one evidence item.

6. Every evidence item MUST contain a URL from the supplied evidence.

7. If there is insufficient evidence, detected MUST be false.

7a. For product_change, do not cite a generic changelog, release-notes,
updates, blog, or news index page. Cite a specific announcement or entry
with a concrete feature/update name and description; include its date when
the source provides one.

8. ARR, valuation, revenue, or company size are NOT funding events.

9. A company having a product is NOT a product launch.

10. A current homepage description is NOT evidence of a recent
positioning change.

11. A current website is NOT evidence of a recent website redesign.

12. Generic hiring is NOT design/product hiring.

13. Growth alone is NOT growth-with-experience-pressure.

14. Never claim that a website is cluttered, confusing, outdated,
bad, difficult, or poorly designed unless the supplied evidence
explicitly supports that observation.

15. A news article about another company is irrelevant even if
the article appears in the research results.

16. The signal must be relevant to an actual Brandhero capability.

17. Brandhero relevance is a value from 0.0 to 1.0.

18. Confidence is a value from 0.0 to 1.0.

19. Do NOT calculate the final numeric opportunity score.

20. It is completely acceptable for all seven signals to be false.

21. Do not manufacture an opportunity just because the company
is successful, large, funded, growing, or well known.

22. The final opportunity should only be YES when there is enough
evidence for at least one meaningful Brandhero-relevant signal.

23. Return EXACTLY the JSON structure requested by the user prompt.

24. Do not return:
- opportunities
- analysis
- analysisConclusion
- recommendations
- generic business ideas
- unrelated companies

25. MARKET EXPANSION is only a new geography, customer segment, industry,
or materially different audience stated in the evidence. Do NOT classify a
mobile app, iOS/Android support, integration, new feature, or product
availability on another platform as market expansion; those are product
changes unless the evidence separately names a new market or audience.

26. A detected signal is not automatically a Brandhero opportunity. Set
likely_brandhero_need=true only when the evidence shows either (a) two or
more corroborating, Brandhero-relevant signals, or (b) one direct high-impact
signal such as a rebrand, website redesign, or observable UX problem. A
single product release by itself is insufficient.

27. The supplied signal_evidence is the complete evidence set. It was
collected independently for each signal. Do not use a record from one signal
to detect another, and do not infer evidence from the company homepage,
company description, or general knowledge.
"""

        user_prompt = f"""
TARGET COMPANY
==============

{company_json}


BRANDHERO PROFILE
=================

{brandhero_json}


PREDEFINED SIGNALS
==================

{signals_json}


TASK
====

Evaluate the target company against EACH of the seven predefined signals using
only the records under that signal's signal_evidence key. An empty list means
there is no evidence for that signal and it must be false.

For every signal:

- detected: true or false
- confidence: 0.0 to 1.0
- brandhero_relevance: 0.0 to 1.0
- observation: concise factual observation
- brandhero_reason: why the observation is relevant to Brandhero
- evidence: list of supporting evidence

Evidence format:

[
  {{
    "claim": "Exact factual claim supported by the source",
    "url": "source_url from the matching signal_evidence record"
  }}
]

If there is no valid evidence:

"detected": false,
"confidence": 0,
"brandhero_relevance": 0,
"observation": "",
"brandhero_reason": "",
"evidence": []

Then produce an opportunity object.

The opportunity must contain:

- likely_brandhero_need
- confidence
- primary_need
- relevant_stakeholder
- why_now
- personalized_outreach_angle

The outreach angle must be based ONLY on detected evidence.
Do not invent company initiatives.

Return EXACTLY this structure:

{{
  "signals": {{
    "product_change": {{
      "detected": false,
      "confidence": 0,
      "brandhero_relevance": 0,
      "observation": "",
      "brandhero_reason": "",
      "evidence": []
    }},
    "rebrand_or_positioning": {{
      "detected": false,
      "confidence": 0,
      "brandhero_relevance": 0,
      "observation": "",
      "brandhero_reason": "",
      "evidence": []
    }},
    "website_change": {{
      "detected": false,
      "confidence": 0,
      "brandhero_relevance": 0,
      "observation": "",
      "brandhero_reason": "",
      "evidence": []
    }},
    "market_expansion": {{
      "detected": false,
      "confidence": 0,
      "brandhero_relevance": 0,
      "observation": "",
      "brandhero_reason": "",
      "evidence": []
    }},
    "design_product_hiring": {{
      "detected": false,
      "confidence": 0,
      "brandhero_relevance": 0,
      "observation": "",
      "brandhero_reason": "",
      "evidence": []
    }},
    "growth_with_experience_pressure": {{
      "detected": false,
      "confidence": 0,
      "brandhero_relevance": 0,
      "observation": "",
      "brandhero_reason": "",
      "evidence": []
    }},
    "observable_experience_problem": {{
      "detected": false,
      "confidence": 0,
      "brandhero_relevance": 0,
      "observation": "",
      "brandhero_reason": "",
      "evidence": []
    }}
  }},
  "opportunity": {{
    "likely_brandhero_need": false,
    "confidence": 0,
    "primary_need": "",
    "relevant_stakeholder": "",
    "why_now": "",
    "personalized_outreach_angle": ""
  }}
}}

IMPORTANT:
Return ONLY the JSON object.
"""

        return system_prompt, user_prompt

    # =========================================================
    # EVIDENCE BACKSTOP
    # =========================================================

    @staticmethod
    def _evidence_sentence(text, pattern):
        """Return a short, source-backed sentence matching ``pattern``."""
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            cleaned = re.sub(r"\s+", " ", sentence).strip()
            if re.search(pattern, cleaned, flags=re.IGNORECASE):
                return cleaned[:500]
        return ""

    def apply_evidence_backstop(self, result, company_evidence):
        """Preserve clear first-party signals if a small model misses them.

        This is intentionally narrow: a signal is added only when the crawled
        page itself contains a direct, relevant phrase.  It avoids turning a
        generic homepage description into an opportunity while preventing an
        all-zero result caused by an overly conservative model response.
        """
        rules = {
            "product_change": {
                "pattern": r"\b(new feature|new product|new platform|we (?:have )?launched|introduced|released|release(?:d)?|now available|changelog)\b",
                "confidence": 0.72,
                "relevance": 0.85,
                "reason": "Recent product changes can require product-design and UX support.",
            },
            "rebrand_or_positioning": {
                "pattern": r"\b(rebrand(?:ing|ed)?|new visual identity|refreshed brand|brand relaunch)\b",
                "confidence": 0.78,
                "relevance": 0.9,
                "reason": "A brand change is directly relevant to Brandhero's branding capability.",
            },
            "website_change": {
                "pattern": r"\b(website redesign|redesigned (?:our )?website|new website|website relaunch)\b",
                "confidence": 0.75,
                "relevance": 0.88,
                "reason": "A website change can create a need for UI/UX and conversion-focused design work.",
            },
            "market_expansion": {
                "pattern": r"\b(expanding (?:into|to)|expansion into|new market|now available in|international expansion)\b",
                "confidence": 0.7,
                "relevance": 0.72,
                "reason": "Serving a new audience can require research, localization, and experience adaptation.",
            },
            "design_product_hiring": {
                "pattern": r"\b(product designers?|ux designers?|ui designers?|design researchers?|head of design|design leads?)\b",
                "confidence": 0.8,
                "relevance": 0.82,
                "reason": "Active design hiring indicates product or design capacity is being expanded.",
            },
        }

        signals = result.get("signals", {})
        if not isinstance(signals, dict):
            return result

        for signal_name, rule in rules.items():
            current = signals.get(signal_name, {})
            if isinstance(current, dict) and current.get("detected") is True:
                continue

            # Prefer the researcher's already-qualified, signal-specific
            # records. This keeps a conservative model from discarding valid
            # evidence and preserves the exact collector URL and claim.
            for record in company_evidence.get("signal_evidence", {}).get(signal_name, []):
                if not isinstance(record, dict):
                    continue
                url = str(record.get("source_url", "")).strip()
                claim = str(record.get("claim", "")).strip()
                snippet = str(record.get("snippet", "")).strip()
                if not url or not claim or not snippet:
                    continue
                if (
                    signal_name == "product_change"
                    and not self._is_specific_product_update_page({
                        "title": claim,
                        "url": url,
                        "text": snippet,
                    })
                ):
                    continue
                signals[signal_name] = {
                    "detected": True,
                    "confidence": rule["confidence"],
                    "brandhero_relevance": rule["relevance"],
                    "observation": claim,
                    "brandhero_reason": rule["reason"],
                    "evidence": [{"claim": claim, "url": url}],
                }
                break

            current = signals.get(signal_name, {})
            if isinstance(current, dict) and current.get("detected") is True:
                continue

            for page in company_evidence.get("pages", []):
                if not isinstance(page, dict):
                    continue
                if signal_name == "product_change" and not self._is_specific_product_update_page(page):
                    continue
                claim = self._evidence_sentence(page.get("text", ""), rule["pattern"])
                url = str(page.get("url", "")).strip()
                if not claim or not url:
                    continue

                if signal_name == "product_change":
                    claim = self._product_update_claim(page, claim)
                    if not claim:
                        continue

                signals[signal_name] = {
                    "detected": True,
                    "confidence": rule["confidence"],
                    "brandhero_relevance": rule["relevance"],
                    "observation": claim,
                    "brandhero_reason": rule["reason"],
                    "evidence": [{"claim": claim, "url": url}],
                }
                break

        result["signals"] = signals
        return result

    @staticmethod
    def _is_specific_product_update_page(page):
        """Accept a concrete update entry, never a generic updates index."""
        url = str(page.get("url", "")).strip()
        parsed = re.sub(r"[?#].*$", "", url).rstrip("/")
        slug = parsed.rsplit("/", 1)[-1].lower()
        generic_slugs = {
            "changelog",
            "release",
            "releases",
            "release-notes",
            "product-releases",
            "product-updates",
            "product-announcements",
            "updates",
            "whats-new",
            "what-s-new",
            "news",
            "blog",
            "insights",
        }
        if not slug or slug in generic_slugs:
            return False

        text = str(page.get("text", ""))
        has_update_language = re.search(
            r"\b(changelog|release notes?|what['’]?s new|new feature|new product|"
            r"new platform|launched|introduced|released|now available)\b",
            text,
            flags=re.IGNORECASE,
        )
        has_description = len(text.split()) >= 12
        return bool(has_update_language and has_description)

    @staticmethod
    def _product_update_claim(page, fallback_claim):
        """Build a claim from a specific update's name and description."""
        text = re.sub(r"\s+", " ", str(page.get("text", ""))).strip()
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        update_pattern = re.compile(
            r"\b(new feature|new product|new platform|launched|introduced|released|"
            r"now available|changelog|release notes?)\b",
            flags=re.IGNORECASE,
        )
        matching = [sentence for sentence in sentences if update_pattern.search(sentence)]
        if not matching:
            return ""

        title = str(page.get("title", "")).strip()
        date_match = re.search(
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b",
            text,
            flags=re.IGNORECASE,
        )
        details = " ".join(matching[:2])[:700]
        parts = [part for part in [title, date_match.group(0) if date_match else "", details] if part]
        return ": ".join(parts)[:900]

    @staticmethod
    def _valid_market_expansion_evidence(evidence):
        """Require a stated market or audience, not merely a new platform."""
        market_pattern = re.compile(
            r"\b("
            r"expand(?:ing|ed)?\s+(?:into|to)\s+(?:a |the )?(?:new )?(?:market|country|region|geograph|industry|vertical|segment|audience)"
            r"|expansion\s+into\s+(?:a |the )?(?:new )?(?:market|country|region|geograph|industry|vertical|segment|audience)"
            r"|enter(?:ing|ed)?\s+(?:a |the )?(?:new )?(?:market|country|region|industry|vertical)"
            r"|new\s+(?:customer\s+)?(?:market|segment|audience|industry|vertical)"
            r"|now\s+serv(?:e|es|ing)\s+(?:a |the )?(?:new )?(?:market|segment|audience|industry)"
            r")\b",
            re.IGNORECASE,
        )
        return any(
            market_pattern.search(str(item.get("claim", "")))
            for item in evidence
            if isinstance(item, dict)
        )

    @staticmethod
    def _is_opportunity_supported(signals):
        """Return whether signal evidence supports a qualified opportunity."""
        supported = []
        for name, signal in signals.items():
            if not isinstance(signal, dict) or not signal.get("detected"):
                continue
            if not signal.get("evidence"):
                continue
            try:
                confidence = float(signal.get("confidence", 0))
                relevance = float(signal.get("brandhero_relevance", 0))
            except (TypeError, ValueError):
                continue
            if confidence >= 0.6 and relevance >= 0.7:
                supported.append((name, signal, confidence, relevance))

        # Multiple independent, relevant events corroborate a design need.
        if len(supported) >= 2:
            return True, supported

        # A single high-impact experience/brand event can stand on its own.
        high_impact = {
            "rebrand_or_positioning",
            "website_change",
            "observable_experience_problem",
        }
        if (
            len(supported) == 1
            and supported[0][0] in high_impact
            and supported[0][2] >= 0.75
            and supported[0][3] >= 0.75
        ):
            return True, supported

        return False, supported

    @staticmethod
    def _opportunity_tier(supporting_signals):
        """Classify evidence strength independently from the weighted score."""
        if not supporting_signals:
            return "No Opportunity"

        high_impact = {
            "rebrand_or_positioning",
            "website_change",
            "observable_experience_problem",
        }

        if len(supporting_signals) >= 2:
            return "Very High"

        signal_name, _, confidence, relevance = supporting_signals[0]
        if (
            signal_name in high_impact
            and confidence >= 0.75
            and relevance >= 0.75
        ):
            return "High"

        return "Qualified"

    @staticmethod
    def constrain_to_signal_evidence(result, company_evidence):
        """Keep model citations tied to the collector's matching signal.

        Llama decides detection and relevance, but never supplies new facts or
        moves a source gathered for one signal into another signal.
        """
        if not isinstance(result, dict) or not isinstance(result.get("signals"), dict):
            return result

        source_index = {}
        for signal_name, records in company_evidence.get("signal_evidence", {}).items():
            if not isinstance(records, list):
                continue
            source_index[signal_name] = {
                record.get("source_url"): record
                for record in records
                if isinstance(record, dict) and record.get("source_url")
            }

        for signal_name, signal in result["signals"].items():
            if not isinstance(signal, dict):
                continue
            allowed_records = source_index.get(signal_name, {})
            cited_urls = []
            for item in signal.get("evidence", []):
                if not isinstance(item, dict):
                    continue
                url = str(item.get("url", "")).strip()
                if url in allowed_records and url not in cited_urls:
                    cited_urls.append(url)

            # Use the collector's exact claim, not a model paraphrase.
            signal["evidence"] = [
                {"claim": allowed_records[url]["claim"], "url": url}
                for url in cited_urls
            ]

        return result

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate_result(
        self,
        result,
        allowed_urls=None,
        company_evidence=None
    ):

        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                "Signal analyzer did not return an object."
            )

        signals = result.get(
            "signals"
        )

        if not isinstance(
            signals,
            dict
        ):
            raise ValueError(
                "LLM returned invalid signal schema: missing 'signals' object."
            )

        required_signals = list(
            SIGNAL_DEFINITIONS.keys()
        )

        company_evidence = company_evidence or {}
        generic_product_urls = {
            page.get("url")
            for page in company_evidence.get("pages", [])
            if isinstance(page, dict)
            and page.get("url")
            and not self._is_specific_product_update_page(page)
            and re.search(
                r"/(?:changelog|release|releases|release-notes|product-releases|product-updates|product-announcements|updates|what['-]?s-new|news|blog|insights)(?:/|$)",
                str(page.get("url", "")),
                flags=re.IGNORECASE,
            )
        }

        for signal_name in required_signals:

            if signal_name not in signals:

                signals[signal_name] = {
                    "detected": False,
                    "confidence": 0,
                    "brandhero_relevance": 0,
                    "observation": "",
                    "brandhero_reason": "",
                    "evidence": [],
                }

            signal = signals[
                signal_name
            ]

            if not isinstance(
                signal,
                dict
            ):
                signals[signal_name] = {
                    "detected": False,
                    "confidence": 0,
                    "brandhero_relevance": 0,
                    "observation": "",
                    "brandhero_reason": "",
                    "evidence": [],
                }

                continue

            detected_value = signal.get("detected", False)
            detected = (
                detected_value
                if isinstance(detected_value, bool)
                else str(detected_value).strip().lower() in {"true", "1", "yes"}
            )

            try:
                confidence = float(
                    signal.get(
                        "confidence",
                        0
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                confidence = 0

            try:
                relevance = float(
                    signal.get(
                        "brandhero_relevance",
                        0
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                relevance = 0

            confidence = max(
                0,
                min(
                    1,
                    confidence
                )
            )

            relevance = max(
                0,
                min(
                    1,
                    relevance
                )
            )

            evidence = signal.get(
                "evidence",
                []
            )

            if not isinstance(
                evidence,
                list
            ):
                evidence = []

            cleaned_evidence = []

            for item in evidence:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                claim = str(
                    item.get(
                        "claim",
                        ""
                    )
                ).strip()

                url = str(
                    item.get(
                        "url",
                        ""
                    )
                ).strip()

                if claim and url:
                    # If allowed_urls is provided, verify the URL was part of supplied research
                    if allowed_urls is not None and url not in allowed_urls:
                        # Allow partial URL matches (e.g. without query string or protocol)
                        url_matches = any(url in u or u in url for u in allowed_urls)
                        if not url_matches:
                            continue

                    cleaned_evidence.append({
                        "claim": claim,
                        "url": url,
                    })

            # Positive signal without evidence is invalid.
            if detected and not cleaned_evidence:

                detected = False
                confidence = 0
                relevance = 0

                signal["observation"] = ""
                signal["brandhero_reason"] = ""

            # Platform availability is a product-change signal, not market
            # expansion.  Require the cited evidence to name a new market or
            # audience before allowing this specific signal to score.
            if (
                signal_name == "market_expansion"
                and detected
                and not self._valid_market_expansion_evidence(cleaned_evidence)
            ):
                detected = False
                confidence = 0
                relevance = 0
                signal["observation"] = ""
                signal["brandhero_reason"] = ""
                cleaned_evidence = []

            if (
                signal_name == "product_change"
                and detected
                and any(
                    item.get("url") in generic_product_urls
                    for item in cleaned_evidence
                )
            ):
                detected = False
                confidence = 0
                relevance = 0
                signal["observation"] = ""
                signal["brandhero_reason"] = ""
                cleaned_evidence = []

            signal["detected"] = detected
            signal["confidence"] = round(
                confidence,
                2
            )
            signal["brandhero_relevance"] = round(
                relevance,
                2
            )
            signal["evidence"] = (
                cleaned_evidence
            )

        # -----------------------------------------------------
        # Opportunity validation
        # -----------------------------------------------------

        opportunity = result.get(
            "opportunity",
            {}
        )

        if not isinstance(
            opportunity,
            dict
        ):
            opportunity = {}

        any_detected = any(
            signal.get(
                "detected",
                False
            )
            for signal in signals.values()
            if isinstance(
                signal,
                dict
            )
        )

        opportunity_supported, supporting_signals = self._is_opportunity_supported(signals)
        likely_need = opportunity_supported
        opportunity_tier = self._opportunity_tier(supporting_signals)

        if opportunity_supported:
            strongest_name, strongest_signal, confidence, _ = max(
                supporting_signals,
                key=lambda item: item[2] * item[3],
            )
            # Retain model-written reasoning when it is present, but make
            # every automatically completed field traceable to signal evidence.
            if not opportunity.get("primary_need"):
                opportunity["primary_need"] = SIGNAL_DEFINITIONS[strongest_name]["name"]
            if not opportunity.get("relevant_stakeholder"):
                opportunity["relevant_stakeholder"] = "Product or Design leader"
            if not opportunity.get("why_now"):
                opportunity["why_now"] = strongest_signal.get("observation", "")
            if not opportunity.get("personalized_outreach_angle"):
                opportunity["personalized_outreach_angle"] = strongest_signal.get("brandhero_reason", "")
            opportunity["confidence"] = confidence
        else:
            # Do not let a model's generic conclusion turn one isolated event
            # (especially a product release) into a sales opportunity.
            opportunity = {
                "likely_brandhero_need": False,
                "confidence": 0,
                "primary_need": "",
                "relevant_stakeholder": "",
                "why_now": "",
                "personalized_outreach_angle": "",
                "opportunity_tier": "No Opportunity",
            }

        # Cannot have an opportunity without
        # at least one detected signal.
        if likely_need and not any_detected:

            opportunity = {
                "likely_brandhero_need": False,
                "confidence": 0,
                "primary_need": "",
                "relevant_stakeholder": "",
                "why_now": "",
                "personalized_outreach_angle": "",
                "opportunity_tier": "No Opportunity",
            }

        else:

            try:
                opportunity_confidence = float(
                    opportunity.get(
                        "confidence",
                        0
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                opportunity_confidence = 0

            opportunity_confidence = max(
                0,
                min(
                    1,
                    opportunity_confidence
                )
            )

            opportunity["likely_brandhero_need"] = (
                likely_need
            )

            opportunity["opportunity_tier"] = opportunity_tier
            if not likely_need:
                opportunity["opportunity_tier"] = "No Opportunity"

            opportunity["confidence"] = round(
                opportunity_confidence,
                2
            )

            for field in [
                "primary_need",
                "relevant_stakeholder",
                "why_now",
                "personalized_outreach_angle",
            ]:

                value = opportunity.get(
                    field,
                    ""
                )

                if not isinstance(
                    value,
                    str
                ):
                    value = str(
                        value
                    )

                opportunity[field] = value.strip()

        result["signals"] = signals
        result["opportunity"] = opportunity

        return result

    # =========================================================
    # MAIN ANALYSIS
    # =========================================================

    def analyze(
        self,
        research_data,
        brandhero_profile
    ):

        company_evidence = (
            self.prepare_company_evidence(
                research_data
            )
        )

        # Debug summary
        signal_evidence = company_evidence.get("signal_evidence", {})
        evidence_sources = [
            item.get("source_url")
            for records in signal_evidence.values()
            if isinstance(records, list)
            for item in records
            if isinstance(item, dict) and item.get("source_url")
        ]
        print(f"[SIGNALS] Signal-scoped evidence items: {len(evidence_sources)}")
        if evidence_sources:
            print("[SIGNALS] Evidence sources:")
            for src in evidence_sources:
                print(f"- {src}")

        print(
            "[LLAMA EVIDENCE] Evidence payload by signal:\n"
            + json.dumps(
                signal_evidence,
                indent=2,
                ensure_ascii=False
            )
        )

        prepared_brandhero = (
            self.prepare_brandhero_profile(
                brandhero_profile
            )
        )

        system_prompt, user_prompt = (
            self.build_prompt(
                company_evidence,
                prepared_brandhero
            )
        )

        result = self.llm.analyze_json(
            system_prompt,
            user_prompt
        )

        print(
            "[LLAMA CLASSIFICATION] Before validation:\n"
            + json.dumps(
                result.get("signals", {}),
                indent=2,
                ensure_ascii=False
            )
        )

        # A conservative local model may return the requested all-false
        # schema even when the collector found direct, signal-specific proof.
        # Restore only those deterministic matches; this never invents a URL
        # or broadens evidence across signal categories.
        result = self.apply_evidence_backstop(
            result,
            company_evidence
        )

        allowed_urls = set(evidence_sources)

        result = self.constrain_to_signal_evidence(
            result,
            company_evidence,
        )

        validated = self.validate_result(
            result,
            allowed_urls=allowed_urls,
            company_evidence=company_evidence
        )

        print(
            "[VALIDATION] Final signals:\n"
            + json.dumps(
                validated.get("signals", {}),
                indent=2,
                ensure_ascii=False
            )
        )
        return validated
