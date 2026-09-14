import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from app.llm import LocalLlama
from app.main import load_brandhero_profile
from app.researcher import Researcher
from app.signals import SignalAnalyzer
from app.scoring import OpportunityScorer

# Initialize backend components
llm = LocalLlama()
brandhero_profile = load_brandhero_profile(llm)
signal_analyzer = SignalAnalyzer(llm)
scorer = OpportunityScorer()


class OpportunityAPIHandler(BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ["/health", "/api/health"]:
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "brandhero_profile_cached": bool(brandhero_profile)}).encode("utf-8"))
            return

        if parsed.path in ["/brandhero-profile", "/api/brandhero-profile"]:
            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(brandhero_profile).encode("utf-8"))
            return

        self.send_response(404)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"detail": "Not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path in ["/analyze", "/api/analyze"]:
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                req_data = json.loads(body) if body else {}

                domain = str(req_data.get("domain", "")).strip()
                if not domain:
                    self.send_response(400)
                    self._set_cors_headers()
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "Domain is required"}).encode("utf-8"))
                    return

                company_name = req_data.get("company_name", "").strip() or None

                researcher = Researcher(domain=domain, company_name=company_name)
                research_data = researcher.research()

                if not research_data.get("website"):
                    self.send_response(422)
                    self._set_cors_headers()
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": f"Could not collect website content for domain: {domain}"}).encode("utf-8"))
                    return

                signal_result = signal_analyzer.analyze(research_data, brandhero_profile)
                score_result = scorer.calculate(signal_result)

                evidence_pages = []
                seen_urls = set()
                for records in research_data.get("signal_evidence", {}).values():
                    if not isinstance(records, list):
                        continue
                    for record in records:
                        if not isinstance(record, dict):
                            continue
                        url = record.get("source_url", "")
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        evidence_pages.append({
                            "title": record.get("claim", ""),
                            "url": url,
                        })

                response_data = {
                    "company_name": research_data.get("company_name", company_name or domain),
                    "domain": domain,
                    "website": research_data.get("website", ""),
                    "evidence_summary": {
                        "pages_count": len(evidence_pages),
                        "news_count": 0,
                        "pages": evidence_pages,
                    },
                    "signals": signal_result.get("signals", {}),
                    "opportunity": signal_result.get("opportunity", {}),
                    "scoring": score_result,
                }

                self.send_response(200)
                self._set_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))

            except Exception as e:
                traceback.print_exc()
                self.send_response(500)
                self._set_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"detail": "Not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[API] {args[0]} - {args[1]}")


def run_server(port=8000, host="0.0.0.0"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, OpportunityAPIHandler)
    print(f"[API SERVER] Running on http://127.0.0.1:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()

