import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.llm import LocalLlama


class BrandheroResearcher:
    BASE_URL = "https://www.brandhero.design/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        })

        self.llm = LocalLlama()

    # ---------------------------------------------------------
    # FETCH
    # ---------------------------------------------------------

    def fetch_page(self, url):
        try:
            response = self.session.get(
                url,
                timeout=20,
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text

        except Exception as e:
            print(f"[BRANDHERO] Failed to fetch {url}: {e}")
            return ""

    # ---------------------------------------------------------
    # EXTRACT TEXT
    # ---------------------------------------------------------

    def extract_page(self, url):
        html = self.fetch_page(url)

        if not html:
            return {
                "url": url,
                "title": "",
                "description": "",
                "text": ""
            }

        soup = BeautifulSoup(html, "html.parser")

        for element in soup([
            "script",
            "style",
            "noscript",
            "svg"
        ]):
            element.decompose()

        title = ""

        if soup.title:
            title = soup.title.get_text(
                " ",
                strip=True
            )

        description = ""

        meta = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if meta:
            description = meta.get(
                "content",
                ""
            )

        text = soup.get_text(
            " ",
            strip=True
        )

        text = " ".join(text.split())

        return {
            "url": url,
            "title": title,
            "description": description,
            "text": text[:15000]
        }

    # ---------------------------------------------------------
    # FIND RELEVANT PAGES
    # ---------------------------------------------------------

    def find_relevant_pages(self, homepage_html):
        soup = BeautifulSoup(
            homepage_html,
            "html.parser"
        )

        candidates = []

        keywords = [
            "service",
            "work",
            "case",
            "about",
            "brand",
            "design",
            "product",
            "contact",
            "process",
            "journal",
            "blog"
        ]

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = link.get(
                "href",
                ""
            ).strip()

            if not href:
                continue

            full_url = urljoin(
                self.BASE_URL,
                href
            )

            if not full_url.startswith(
                self.BASE_URL
            ):
                continue

            text = link.get_text(
                " ",
                strip=True
            ).lower()

            href_lower = href.lower()

            if any(
                keyword in text
                or keyword in href_lower
                for keyword in keywords
            ):
                candidates.append(full_url)

        seen = set()
        result = []

        for url in candidates:

            if url not in seen:

                seen.add(url)
                result.append(url)

        return result[:8]

    # ---------------------------------------------------------
    # RESEARCH BRANDHERO
    # ---------------------------------------------------------

    def research(self):

        print(
            "[BRANDHERO] Researching Brandhero..."
        )

        print(
            f"[BRANDHERO] URL: {self.BASE_URL}"
        )

        homepage_html = self.fetch_page(
            self.BASE_URL
        )

        if not homepage_html:

            return {
                "company": "Brandhero",
                "website": self.BASE_URL,
                "pages": []
            }

        homepage = self.extract_page(
            self.BASE_URL
        )

        print(
            "[BRANDHERO] Homepage collected"
        )

        relevant_urls = self.find_relevant_pages(
            homepage_html
        )

        pages = [homepage]

        for url in relevant_urls:

            if url == self.BASE_URL:
                continue

            print(
                f"[BRANDHERO] Fetching: {url}"
            )

            page = self.extract_page(url)

            if page["text"]:
                pages.append(page)

        print(
            f"[BRANDHERO] Collected {len(pages)} pages"
        )

        return {
            "company": "Brandhero",
            "website": self.BASE_URL,
            "pages": pages
        }

    # ---------------------------------------------------------
    # BUILD COMPACT PROFILE
    # ---------------------------------------------------------

    def extract_profile(self, research_data):

        pages = research_data.get(
            "pages",
            []
        )

        if not pages:
            raise ValueError(
                "No Brandhero pages available."
            )

        evidence_blocks = []

        for page in pages:

            text = page.get(
                "text",
                ""
            )

            if not text:
                continue

            evidence_blocks.append(
                f"""
SOURCE URL:
{page.get("url", "")}

PAGE TITLE:
{page.get("title", "")}

PAGE DESCRIPTION:
{page.get("description", "")}

PAGE CONTENT:
{text[:7000]}
"""
            )

        evidence = "\n".join(
            evidence_blocks
        )

        system_prompt = """
You are analyzing Brandhero's own website.

Your task is to create a factual capability profile of Brandhero.

Use ONLY information supported by the supplied website evidence.

Do NOT invent services.
Do NOT assume services from generic design-agency knowledge.
Do NOT infer that Brandhero offers something unless the evidence supports it.

Distinguish clearly between:
1. What Brandhero explicitly offers
2. Who Brandhero appears to work with
3. Problems Brandhero explicitly solves
4. Capabilities demonstrated through case studies
5. Observable company situations that could make Brandhero relevant

For opportunity triggers, only include triggers that can reasonably be connected
to an actual Brandhero capability demonstrated in the evidence.

Every important item must include supporting evidence.

Return JSON with exactly this structure:

{
  "brandhero": {
    "name": "Brandhero",
    "website": "https://www.brandhero.design/"
  },
  "services": [
    {
      "item": "",
      "evidence": "",
      "source_url": ""
    }
  ],
  "target_customers": [
    {
      "item": "",
      "evidence": "",
      "source_url": ""
    }
  ],
  "problems_solved": [
    {
      "item": "",
      "evidence": "",
      "source_url": ""
    }
  ],
  "demonstrated_capabilities": [
    {
      "item": "",
      "evidence": "",
      "source_url": ""
    }
  ],
  "strong_opportunity_triggers": [
    {
      "trigger": "",
      "why_relevant_to_brandhero": "",
      "supporting_brandhero_capability": "",
      "source_url": ""
    }
  ],
  "weak_opportunity_triggers": [
    {
      "trigger": "",
      "why_weaker": "",
      "source_url": ""
    }
  ]
}
"""

        user_prompt = f"""
Here is the extracted content from Brandhero's website:

{evidence}

Build the Brandhero capability profile from this evidence.
"""

        print(
            "[BRANDHERO] Building capability profile with Llama..."
        )

        profile = self.llm.analyze_json(
            system_prompt,
            user_prompt
        )

        return profile