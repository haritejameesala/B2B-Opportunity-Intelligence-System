import unittest

from app.signals import SIGNAL_DEFINITIONS, SignalAnalyzer


def blank_result():
    return {
        "signals": {
            name: {
                "detected": False,
                "confidence": 0,
                "brandhero_relevance": 0,
                "observation": "",
                "brandhero_reason": "",
                "evidence": [],
            }
            for name in SIGNAL_DEFINITIONS
        },
        "opportunity": {
            "likely_brandhero_need": False,
            "confidence": 0,
            "primary_need": "",
            "relevant_stakeholder": "",
            "why_now": "",
            "personalized_outreach_angle": "",
        },
    }


class SignalReasoningTests(unittest.TestCase):
    def test_only_matching_collector_evidence_reaches_each_signal(self):
        result = blank_result()
        result["signals"]["market_expansion"].update({
            "detected": True,
            "evidence": [{
                "claim": "Model-invented summary",
                "url": "https://example.test/changelog",
            }],
        })
        evidence = {
            "signal_evidence": {
                "product_change": [{
                    "claim": "We released a new editor.",
                    "source_url": "https://example.test/changelog",
                    "snippet": "We released a new editor.",
                    "source_type": "first_party_release",
                }],
                "market_expansion": [],
            }
        }

        constrained = SignalAnalyzer(None).constrain_to_signal_evidence(result, evidence)

        self.assertEqual(constrained["signals"]["market_expansion"]["evidence"], [])

    def test_generic_pages_are_not_used_when_signal_evidence_is_missing(self):
        prepared = SignalAnalyzer(None).prepare_company_evidence({
            "company_name": "Example",
            "domain": "example.test",
            "pages": [{
                "url": "https://example.test/",
                "text": "We launched a new product.",
            }],
        })

        self.assertTrue(all(not records for records in prepared["signal_evidence"].values()))

    def test_mobile_product_change_is_not_market_expansion_or_opportunity(self):
        result = blank_result()
        evidence = [{
            "claim": "Document editing is now available on iOS and Android.",
            "url": "https://example.test/changelog",
        }]
        result["signals"]["product_change"].update({
            "detected": True,
            "confidence": 0.9,
            "brandhero_relevance": 0.9,
            "evidence": evidence,
        })
        result["signals"]["market_expansion"].update({
            "detected": True,
            "confidence": 0.9,
            "brandhero_relevance": 0.8,
            "evidence": evidence,
        })

        validated = SignalAnalyzer(None).validate_result(
            result,
            allowed_urls={"https://example.test/changelog"},
        )

        self.assertTrue(validated["signals"]["product_change"]["detected"])
        self.assertFalse(validated["signals"]["market_expansion"]["detected"])
        self.assertFalse(validated["opportunity"]["likely_brandhero_need"])

    def test_two_relevant_signals_can_qualify_an_opportunity(self):
        result = blank_result()
        for name, claim in (
            ("product_change", "We launched a redesigned document editor."),
            ("design_product_hiring", "We are hiring a Product Designer."),
        ):
            result["signals"][name].update({
                "detected": True,
                "confidence": 0.8,
                "brandhero_relevance": 0.8,
                "observation": claim,
                "evidence": [{"claim": claim, "url": "https://example.test/updates"}],
            })

        validated = SignalAnalyzer(None).validate_result(
            result,
            allowed_urls={"https://example.test/updates"},
        )

        self.assertTrue(validated["opportunity"]["likely_brandhero_need"])


if __name__ == "__main__":
    unittest.main()
