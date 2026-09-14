# app/scoring.py


SIGNAL_WEIGHTS = {
    "product_change": 15,
    "rebrand_or_positioning": 20,
    "website_change": 20,
    "market_expansion": 10,
    "design_product_hiring": 10,
    "growth_with_experience_pressure": 10,
    "observable_experience_problem": 15,
}


SIGNAL_LABELS = {
    "product_change": "Product / Feature Change",
    "rebrand_or_positioning": "Rebrand / Positioning Change",
    "website_change": "Website / Digital Experience Change",
    "market_expansion": "Market / Audience Expansion",
    "design_product_hiring": "Design / Product Hiring",
    "growth_with_experience_pressure": (
        "Growth with Experience Pressure"
    ),
    "observable_experience_problem": (
        "Observable UX / Product Experience Problem"
    ),
}


class OpportunityScorer:

    def calculate(self, result):

        # The analyzer returns:
        #
        # {
        #   "signals": {...},
        #   "opportunity": {...}
        # }
        #
        # Accept either the complete analyzer result
        # or the signals dictionary for compatibility.

        if "signals" in result:
            signals = result.get(
                "signals",
                {}
            )
        else:
            signals = result

        total = 0.0

        breakdown = {}

        for signal_name, weight in SIGNAL_WEIGHTS.items():

            signal = signals.get(
                signal_name,
                {}
            )

            if not isinstance(signal, dict):
                signal = {}

            detected = bool(
                signal.get(
                    "detected",
                    False
                )
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
                confidence = 0.0

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
                relevance = 0.0

            # Keep values within valid bounds.
            confidence = max(
                0.0,
                min(
                    1.0,
                    confidence
                )
            )

            relevance = max(
                0.0,
                min(
                    1.0,
                    relevance
                )
            )

            # A signal only contributes when it is actually detected.
            #
            # Brandhero relevance is deliberately part of the score.
            # A generic company event should therefore not score highly
            # merely because the event itself is confidently detected.
            if detected:

                points = (
                    weight
                    * confidence
                    * relevance
                )

            else:

                points = 0.0

            points = round(
                points,
                2
            )

            total += points

            breakdown[signal_name] = {
                "label": SIGNAL_LABELS.get(
                    signal_name,
                    signal_name
                ),
                "weight": weight,
                "max_points": weight,
                "detected": detected,
                "confidence": round(
                    confidence,
                    2
                ),
                "relevance": round(
                    relevance,
                    2
                ),
                "points": points,
            }

        score = round(
            max(
                0.0,
                min(
                    100.0,
                    total
                )
            ),
            1
        )

        tier = self._get_tier(
            score
        )

        return {
            "score": score,
            "tier": tier,
            "breakdown": breakdown,
        }

    @staticmethod
    def _get_tier(score):

        if score >= 80:
            return "Very High"

        if score >= 65:
            return "High"

        if score >= 50:
            return "Medium"

        if score >= 30:
            return "Low"

        return "Very Low"