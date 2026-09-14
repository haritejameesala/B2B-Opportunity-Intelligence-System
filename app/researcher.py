import re
import requests
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin, urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )
}


# Each collector has its own discovery vocabulary and proof requirement.  A
# URL is merely a candidate; it becomes evidence only when its extracted text
# contains one of the configured, signal-specific patterns.
SIGNAL_RESEARCH = {
    "product_change": {
        "query": "product launch feature release changelog",
        "url_hints": ("changelog", "release", "updates", "what-s-new", "product"),
        "fallback_paths": ("/changelog", "/product-releases", "/release-notes", "/updates"),
        "patterns": (r"\b(launched|released|introducing|introduced|new feature|now available|what['’]?s new)\b",),
    },
    "rebrand_or_positioning": {
        "query": "rebrand positioning brand identity",
        "url_hints": ("blog", "news", "press", "insights", "brand"),
        "fallback_paths": ("/news", "/press", "/blog"),
        "patterns": (r"\b(rebrand(?:ed|ing)?|new visual identity|brand refresh|reposition(?:ed|ing)?)\b",),
    },
    "website_change": {
        "query": "website redesign digital experience launch",
        "url_hints": ("blog", "news", "press", "insights", "design"),
        "fallback_paths": ("/news", "/press", "/blog"),
        "patterns": (r"\b(website redesign|redesigned (?:our )?website|new website|website relaunch|digital experience redesign)\b",),
    },
    "market_expansion": {
        "query": "expansion new market customer segment international",
        "url_hints": ("blog", "news", "press", "insights", "expansion"),
        "fallback_paths": ("/news", "/press", "/blog"),
        "patterns": (
            r"\b(expand(?:ing|ed)?\s+(?:into|to)\s+(?:a |the )?(?:new )?(?:market|country|region|geograph\w*|industry|vertical|segment|audience)|expansion\s+into\s+(?:a |the )?(?:new )?(?:market|country|region|geograph\w*|industry|vertical|segment|audience)|enter(?:ing|ed)?\s+(?:a |the )?(?:new )?(?:market|country|region|industry|vertical)|new\s+(?:customer\s+)?(?:market|segment|audience|industry|vertical)|now\s+serv(?:e|es|ing)\s+(?:a |the )?(?:new )?(?:market|segment|audience|industry))\b",
        ),
    },
    "design_product_hiring": {
        "query": "hiring product designer UX designer design researcher",
        "url_hints": ("careers", "career", "jobs", "job", "join"),
        "fallback_paths": ("/careers", "/jobs"),
        "patterns": (r"\b(product designer|ux designer|ui designer|design researcher|head of design|design lead|brand designer)\b",),
    },
    "growth_with_experience_pressure": {
        "query": "growth scaling customer experience complexity",
        "url_hints": ("blog", "news", "press", "insights", "growth"),
        "fallback_paths": ("/news", "/press", "/blog"),
        "patterns": (
            r"\b(grew|growing|growth|scaled|scaling|rapidly expanding)\b",
            r"\b(complexity|complex|workflow friction|usability|customer experience|user experience|overwhelming|at scale)\b",
        ),
    },
    "observable_experience_problem": {
        "query": "user experience problem usability friction customer feedback",
        "url_hints": ("blog", "news", "status", "support", "help", "insights"),
        "fallback_paths": ("/status", "/blog", "/news"),
        "patterns": (r"\b(usability issue|user experience problem|workflow friction|difficult to use|confusing|accessibility issue|customer complaint)\b",),
    },
}


class Researcher:

    def __init__(self, domain, company_name=None):
        """
        Initialize researcher.

        domain:
            Company domain such as linear.app

        company_name:
            Company name such as Linear
        """

        self.domain = domain.strip()

        if not self.domain.startswith("http://") and not self.domain.startswith(
            "https://"
        ):
            self.base_url = "https://" + self.domain
        else:
            self.base_url = self.domain

            # Extract domain without protocol
            self.domain = re.sub(
                r"^https?://",
                "",
                self.domain
            ).rstrip("/")

        self.company_name = company_name or self._derive_company_name()
        self._document_cache = {}

    # ============================================================
    # COMPANY NAME
    # ============================================================

    def _derive_company_name(self):
        """
        Derive a reasonable company name from the domain.
        """

        name = self.domain.split(".")[0]

        name = name.replace("-", " ")
        name = name.replace("_", " ")

        return name.title()

    # ============================================================
    # HTTP FETCH
    # ============================================================

    def fetch(self, url):

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            response.raise_for_status()

            return response.text

        except requests.RequestException as e:

            print(
                f"[WARN] Failed to fetch {url}: {e}"
            )

            return None

    def fetch_document(self, url):
        """Fetch a candidate and retain its final URL for provenance."""
        if url in self._document_cache:
            return self._document_cache[url]

        try:
            response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException:
            self._document_cache[url] = None
            return None

        final_url = response.url
        # Google News RSS redirect URLs are discovery-only.  They are never
        # evidence unless requests followed them through to the actual article.
        if "news.google.com" in urlparse(final_url).netloc.lower():
            self._document_cache[url] = None
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        text = self.html_to_text(response.text)
        document = {"url": final_url, "title": title, "text": text}
        self._document_cache[url] = document
        return document

    # ============================================================
    # HTML -> TEXT
    # ============================================================

    def html_to_text(self, html):

        if not html:
            return ""

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # Remove noisy elements
        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "iframe"
        ]):
            tag.decompose()

        text = soup.get_text(
            separator=" "
        )

        # Normalize whitespace
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return text

    # ============================================================
    # WEBSITE EXTRACTION
    # ============================================================

    def extract_website(self):

        print(f"[RESEARCH] Researching {self.company_name} ({self.domain})")

        html = self.fetch(
            self.base_url
        )

        if not html:
            return {}

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # ----------------------------
        # TITLE
        # ----------------------------

        title = ""

        if soup.title:
            title = soup.title.get_text(
                strip=True
            )

        # ----------------------------
        # META DESCRIPTION
        # ----------------------------

        description = ""

        meta = soup.find(
            "meta",
            attrs={
                "name": "description"
            }
        )

        if meta:
            description = meta.get(
                "content",
                ""
            )

        # ----------------------------
        # PAGE TEXT
        # ----------------------------

        text = self.html_to_text(
            html
        )

        # ----------------------------
        # LINKS
        # ----------------------------

        links = []

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = link.get(
                "href"
            )

            if not href:
                continue

            absolute_url = urljoin(
                self.base_url,
                href
            )

            # Only keep HTTP(S)
            if not absolute_url.startswith(
                "http://"
            ) and not absolute_url.startswith(
                "https://"
            ):
                continue

            links.append(
                absolute_url
            )

        # Remove duplicates
        links = list(
            dict.fromkeys(links)
        )

        print("[RESEARCH] Website collected")

        return {
            "url": self.base_url,
            "title": title,
            "description": description,
            "text": text[:6000],
            "links": links[:100],
        }

    # ============================================================
    # FIND RELEVANT PAGES
    # ============================================================

    def find_relevant_pages(
        self,
        website
    ):

        links = website.get(
            "links",
            []
        )

        categories = {
            "careers": [
                "career",
                "careers",
                "jobs",
                "join-us",
                "join"
            ],

            "updates": [
                "changelog",
                "release",
                "releases",
                "updates",
                "what's-new",
                "whats-new",
            ],

            "blog": [
                "blog",
                "insights",
                "articles",
                "news"
            ],

            "product": [
                "product",
                "products",
                "platform",
                "changelog",
                "features"
            ],

            "about": [
                "about",
                "company"
            ],
        }

        found = {}

        # A homepage commonly links to several posts, but the old code kept
        # just the first matching URL.  That made a generic blog landing page
        # the only source available to the signal engine and hid releases,
        # hiring pages, and other time-sensitive evidence.
        for category, keywords in categories.items():
            matches = []

            for link in links:
                lower_link = link.lower()
                if any(keyword in lower_link for keyword in keywords):
                    matches.append(link)

            # Keep a small, diverse set so requests remain bounded while the
            # analyzer has enough evidence to find a real signal.
            unique_matches = list(dict.fromkeys(matches))[:3]
            if unique_matches:
                found[category] = unique_matches

        # Many sites do not expose their changelog or careers page from the
        # homepage.  Probe conventional first-party paths as additional
        # sources; failed fetches are simply ignored.
        fallback_paths = {
            "updates": ["/changelog", "/updates", "/release-notes"],
            "careers": ["/careers", "/jobs"],
        }
        for category, paths in fallback_paths.items():
            candidates = found.setdefault(category, [])
            for path in paths:
                candidate = urljoin(self.base_url + "/", path)
                if candidate not in candidates:
                    candidates.append(candidate)
            found[category] = candidates[:3]

        print(f"[RESEARCH] Relevant pages found: {list(found.keys())}")

        return found

    # ============================================================
    # FETCH RELEVANT PAGES
    # ============================================================

    def fetch_relevant_pages(
        self,
        pages
    ):

        results = {}

        for page_type, urls in pages.items():
            if isinstance(urls, str):
                urls = [urls]

            if not isinstance(urls, list):
                continue

            for index, url in enumerate(urls, start=1):
                if not isinstance(url, str) or not url:
                    continue

                # Do not follow a homepage link to a third-party job board;
                # it would not be first-party evidence for this company.
                if urlparse(url).netloc and urlparse(url).netloc != urlparse(self.base_url).netloc:
                    continue

                print(f"[RESEARCH] Fetching {page_type}: {url}")
                html = self.fetch(url)
                if not html:
                    continue

                text = self.html_to_text(html)
                if text:
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.title.get_text(strip=True) if soup.title else ""
                    key = page_type if index == 1 else f"{page_type}_{index}"
                    results[key] = {
                        "url": url,
                        "title": title,
                        "text": text[:3000],
                    }

        return results

    # ============================================================
    # GOOGLE NEWS
    # ============================================================

    def google_news(
        self,
        query,
        limit=5
    ):

        encoded_query = quote(
            query
        )

        url = (
            "https://news.google.com/rss/search?"
            f"q={encoded_query}"
            "&hl=en-US"
            "&gl=US"
            "&ceid=US:en"
        )

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            response.raise_for_status()

        except requests.RequestException as e:

            print(
                f"[WARN] Google News failed: {e}"
            )

            return []

        try:

            root = ET.fromstring(
                response.content
            )

        except ET.ParseError:

            print(
                "[WARN] Could not parse Google News RSS"
            )

            return []

        results = []

        for item in root.findall(
            ".//item"
        ):

            title_element = item.find(
                "title"
            )

            link_element = item.find(
                "link"
            )

            date_element = item.find(
                "pubDate"
            )

            source_element = item.find(
                "source"
            )

            title = (
                title_element.text
                if title_element is not None
                else ""
            )

            link = (
                link_element.text
                if link_element is not None
                else ""
            )

            published = (
                date_element.text
                if date_element is not None
                else ""
            )

            source = ""

            if source_element is not None:
                source = (
                    source_element.text
                    or ""
                )

            results.append({
                "title": title,
                "url": link,
                "published": published,
                "source": source,
            })

            if len(results) >= limit:
                break

        return results

    # ============================================================
    # SIGNAL-SCOPED EVIDENCE COLLECTION
    # ============================================================

    def discover_sitemap_urls(self):
        """Discover first-party candidates without treating the sitemap as proof."""
        sitemap_url = urljoin(self.base_url + "/", "/sitemap.xml")
        try:
            response = requests.get(sitemap_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError):
            return []

        urls = []
        for loc in root.findall(".//{*}loc"):
            if loc.text and self._is_first_party_url(loc.text):
                urls.append(loc.text.strip())
            if len(urls) >= 250:
                break
        return list(dict.fromkeys(urls))

    def _is_first_party_url(self, url):
        candidate_host = urlparse(url).netloc.lower().split(":")[0]
        company_host = urlparse(self.base_url).netloc.lower().split(":")[0]
        return candidate_host == company_host or candidate_host.endswith("." + company_host)

    @staticmethod
    def _is_generic_url(url):
        path = urlparse(url).path.rstrip("/").lower()
        return (
            path in {"", "/", "/about", "/about-us", "/company"}
            or "/customers/" in path
            or "/case-stud" in path
        )

    def _signal_candidates(self, signal_name, discovered_urls):
        config = SIGNAL_RESEARCH[signal_name]
        hints = config["url_hints"]
        candidates = [
            url for url in discovered_urls
            if self._is_first_party_url(url)
            and not self._is_generic_url(url)
            and any(hint in url.lower() for hint in hints)
        ]
        candidates.extend(
            urljoin(self.base_url + "/", path)
            for path in config["fallback_paths"]
        )
        return list(dict.fromkeys(candidates))[:3]

    @staticmethod
    def _supporting_snippet(text, patterns):
        """Return an exact extracted-text window containing every requirement."""
        if not text:
            return ""
        matches = []
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                return ""
            matches.append(match)
        start = max(0, min(match.start() for match in matches) - 160)
        end = min(len(text), max(match.end() for match in matches) + 320)
        return text[start:end].strip()

    def _source_type(self, url, signal_name):
        host = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
        if not self._is_first_party_url(url):
            return "news_article"
        if signal_name == "design_product_hiring" or any(part in path for part in ("career", "job")):
            return "job_listing"
        if any(part in path for part in ("changelog", "release", "update")):
            return "first_party_release"
        return "first_party_article"

    def _evidence_from_document(self, signal_name, document):
        config = SIGNAL_RESEARCH[signal_name]
        snippet = self._supporting_snippet(document.get("text", ""), config["patterns"])
        if not snippet:
            return None
        return {
            "signal": signal_name,
            "claim": snippet,
            "source_url": document["url"],
            "snippet": snippet,
            "source_type": self._source_type(document["url"], signal_name),
        }

    def collect_signal_evidence(self, signal_name, discovered_urls):
        """Collect direct, signal-specific proof before Llama sees the data."""
        records = []
        seen_urls = set()

        for url in self._signal_candidates(signal_name, discovered_urls):
            document = self.fetch_document(url)
            if not document or document["url"] in seen_urls:
                continue
            seen_urls.add(document["url"])
            evidence = self._evidence_from_document(signal_name, document)
            if evidence:
                records.append(evidence)
            if len(records) >= 3:
                return records

        query = f'"{self.company_name}" {SIGNAL_RESEARCH[signal_name]["query"]}'
        for article in self.google_news(query, limit=2):
            document = self.fetch_document(article.get("url", ""))
            if not document or document["url"] in seen_urls:
                continue
            seen_urls.add(document["url"])
            # Require the extracted article itself to identify the target.
            article_text = f'{document.get("title", "")} {document.get("text", "")}'.lower()
            if self.company_name.lower() not in article_text and self.domain.split(".")[0].lower() not in article_text:
                continue
            evidence = self._evidence_from_document(signal_name, document)
            if evidence:
                records.append(evidence)
            if len(records) >= 3:
                break

        return records

    def print_signal_evidence(self, signal_evidence):
        print("[EVIDENCE] Signal-scoped sources collected:")
        for signal_name in SIGNAL_RESEARCH:
            records = signal_evidence.get(signal_name, [])
            print(f"\n[{signal_name}] {len(records)} evidence item(s)")
            for record in records:
                print(f"  - source_type: {record['source_type']}")
                print(f"    url: {record['source_url']}")
                # Safely encode claim and snippet to avoid UnicodeEncodeError on Windows console
                safe_claim = str(record.get('claim', '')).encode('ascii', errors='replace').decode('ascii')
                safe_snippet = str(record.get('snippet', '')).encode('ascii', errors='replace').decode('ascii')
                print(f"    claim: {safe_claim}")
                print(f"    snippet: {safe_snippet}")

    # ============================================================
    # BUSINESS SIGNAL SEARCH
    # ============================================================

    def search_business_signals(self):

        company = self.company_name

        queries = {

            "funding": (
                f'"{company}" "{self.domain}" '
                '(funding OR raised OR '
                '"Series A" OR "Series B" OR "Series C")'
            ),

            "product_launch": (
                f'"{company}" "{self.domain}" '
                '(launch OR launched OR '
                '"new product" OR "new platform")'
            ),

            "leadership": (
                f'"{company}" "{self.domain}" '
                '(CEO OR CMO OR "VP Marketing" OR '
                '"Chief Marketing Officer")'
            ),

            "expansion": (
                f'"{company}" "{self.domain}" '
                '(expansion OR "new market" OR '
                'enterprise OR international)'
            ),

            "repositioning": (
                f'"{company}" "{self.domain}" '
                '(rebrand OR rebranding OR '
                'repositioning OR "new brand")'
            ),

            "growth": (
                f'"{company}" "{self.domain}" '
                '(hiring OR "hiring spree" OR '
                '"growing team")'
            ),
        }

        results = {}

        for category, query in queries.items():

            print(f"[RESEARCH] Searching news: {category}")

            results[category] = self.google_news(
                query,
                limit=5
            )

        return results

    # ============================================================
    # COMPLETE RESEARCH
    # ============================================================

    def research(self):

        # ----------------------------
        # WEBSITE
        # ----------------------------

        website = self.extract_website()

        if not website:

            print(
                "[ERROR] Could not collect website."
            )

            return {}

        # The homepage is discovery-only.  Every signal gets an independent
        # candidate search and returns only concrete, extracted proof.
        discovered_urls = list(dict.fromkeys(website.get("links", []) + self.discover_sitemap_urls()))
        signal_evidence = {
            signal_name: self.collect_signal_evidence(signal_name, discovered_urls)
            for signal_name in SIGNAL_RESEARCH
        }
        self.print_signal_evidence(signal_evidence)

        return {
            "company_name": self.company_name,
            "domain": self.domain,
            "website": website.get("url", self.base_url) if website else self.base_url,
            "signal_evidence": signal_evidence,
            "research_completed": True,
        }
