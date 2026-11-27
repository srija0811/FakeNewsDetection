"""Source-backed verification for claims with a configured primary source."""

import logging
import re

from truthlens.scraper import extract_article_from_url


logger = logging.getLogger(__name__)
ISRO_CHANDRAYAAN3_URL = "https://www.isro.gov.in/ISRO_EN/Chandrayaan3.html"
_MISSION_PATTERN = re.compile(r"\bchandrayaan\s*[-–]?\s*3\b", re.IGNORECASE)
_LANDING_DATE_PATTERN = re.compile(
    r"\b(?:aug(?:ust)?\s+23(?:rd)?[,]?\s+2023|23(?:rd)?\s+aug(?:ust)?[,]?\s+2023)\b",
    re.IGNORECASE,
)
_LANDING_PATTERN = re.compile(
    r"\b(?:soft[\s-]?land(?:ed|ing)|(?:successfully\s+)?land(?:ed|ing)\s+(?:successfully\s+)?on\s+(?:the\s+)?moon|successful\s+(?:moon\s+)?landing)\b",
    re.IGNORECASE,
)
_NEGATED_LANDING_PATTERN = re.compile(
    r"\b(?:never|did\s+not|didn['’]t|failed\s+to|was\s+not|wasn['’]t|no)\b"
    r".{0,90}\b(?:reach(?:ed)?\s+(?:the\s+)?moon|soft[\s-]?land(?:ed|ing)|"
    r"land(?:ed|ing)|touch(?:ed)?\s+down|perform(?:ed)?\s+(?:a\s+)?landing)\b",
    re.IGNORECASE,
)
_CANCELLED_BEFORE_LAUNCH_PATTERN = re.compile(
    r"\b(?:cancelled|canceled|scrapped|aborted)\b.{0,60}\b"
    r"(?:before\s+(?:the\s+)?launch|prior\s+to\s+(?:the\s+)?launch|before\s+liftoff)\b",
    re.IGNORECASE,
)
_FALSE_REPORT_PATTERN = re.compile(
    r"\b(?:reports?|claims?)\b.{0,50}\b(?:are|were|is|was)?\s*(?:false|fabricated|untrue)\b"
    r"|\b(?:false|fabricated|untrue)\b.{0,50}\b(?:reports?|claims?)\b",
    re.IGNORECASE,
)
_LANDING_REPORT_PATTERN = re.compile(r"\b(?:landing|landed|soft[\s-]?land|moon)\b", re.IGNORECASE)
_LAUNCH_SOURCE_PATTERN = re.compile(
    r"\bsuccessfully\s+launched\s+chandrayaan\s*[-–]?\s*3\s+into\s+orbit\b",
    re.IGNORECASE,
)
_LANDING_SOURCE_PATTERN = re.compile(
    r"\bchandrayaan\s*[-–]?\s*3\b.{0,100}\bsuccessfully\s+soft[\s-]?landed\s+on\s+the\s+moon\b",
    re.IGNORECASE,
)


def _sentences(text):
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+|\n+", text) if sentence.strip()]


def _source_excerpt(text, fact_pattern, date_pattern=None):
    """Return bounded source context only when the source confirms the complete event."""
    for match in fact_pattern.finditer(text):
        start = max(0, match.start() - 150)
        end = min(len(text), match.end() + 100)
        excerpt = " ".join(text[start:end].split())
        if date_pattern and not date_pattern.search(excerpt):
            continue
        if not _MISSION_PATTERN.search(excerpt):
            continue
        return excerpt
    return ""


def _evidence(claim, excerpt, status):
    return {
        "source": "Indian Space Research Organisation (ISRO)",
        "url": ISRO_CHANDRAYAAN3_URL,
        "claim": claim,
        "excerpt": excerpt,
        "status": status,
    }


def _result(status, summary, evidence=None):
    return {
        "status": status,
        "summary": summary,
        "evidence": evidence or [],
    }


def verify_article_claims(text):
    """Compare configured article claims with authoritative primary sources."""
    article_text = text or ""
    extracted_claims = []
    retrieved_sources = []
    source_content = {}
    evidence_match = False
    contradiction_detected = False

    def finish(status, summary, evidence=None):
        logger.warning(
            "Fact-check diagnostics: %s",
            {
                "extracted_claim": extracted_claims,
                "retrieved_sources": retrieved_sources,
                "source_content": source_content,
                "evidence_match": evidence_match,
                "contradiction_detected": contradiction_detected,
                "fact_check_status": status,
            },
        )
        return _result(status, summary, evidence)

    if not _MISSION_PATTERN.search(article_text):
        from truthlens.upload_fact_verifier import verify_uploaded_t20_final_claim

        t20_result = verify_uploaded_t20_final_claim(article_text)
        if t20_result["status"] != "Unverified" or t20_result.get("source_check_attempted"):
            result = finish(
                t20_result["status"],
                t20_result["summary"],
                t20_result["evidence"],
            )
            result["source_check_attempted"] = t20_result.get("source_check_attempted", False)
            if "claim_assessments" in t20_result:
                result["claim_assessments"] = t20_result["claim_assessments"]
            return result
        return finish(
            "Unverified",
            "No configured trusted-source check directly corroborated this claim. "
            "The machine-learning prediction is kept separate from factual verification.",
        )

    sentences = _sentences(article_text)
    landing_claims = []
    contradicted_landing_claims = []
    cancelled_launch_claims = []
    false_report_claims = []

    for sentence in sentences:
        has_mission = bool(_MISSION_PATTERN.search(sentence))
        is_false_landing_report = bool(
            _FALSE_REPORT_PATTERN.search(sentence)
            and _LANDING_REPORT_PATTERN.search(sentence)
        )
        refers_to_mission = has_mission or bool(
            re.search(r"\b(?:spacecraft|vikram\s+lander|lander)\b", sentence, re.IGNORECASE)
        ) or (is_false_landing_report and bool(_MISSION_PATTERN.search(article_text)))
        if not refers_to_mission:
            continue

        if _CANCELLED_BEFORE_LAUNCH_PATTERN.search(sentence):
            cancelled_launch_claims.append(sentence)
            extracted_claims.append(sentence)
        if _NEGATED_LANDING_PATTERN.search(sentence):
            contradicted_landing_claims.append(sentence)
            extracted_claims.append(sentence)
        elif _LANDING_PATTERN.search(sentence):
            landing_claims.append(sentence)
            extracted_claims.append(sentence)
        if is_false_landing_report:
            false_report_claims.append(sentence)
            extracted_claims.append(sentence)

    if not any((landing_claims, contradicted_landing_claims, cancelled_launch_claims, false_report_claims)):
        return finish(
            "Unverified",
            "No configured trusted-source check directly corroborated this claim. "
            "The machine-learning prediction is kept separate from factual verification.",
        )

    source_result = extract_article_from_url(ISRO_CHANDRAYAAN3_URL)
    if not source_result.get("success"):
        return finish(
            "Unverified",
            "The official ISRO record could not be retrieved, so the claim remains unverified.",
        )

    retrieved_sources.append({
        "source": "Indian Space Research Organisation (ISRO)",
        "url": ISRO_CHANDRAYAAN3_URL,
    })
    source_text = source_result.get("text", "")
    landing_excerpt = _source_excerpt(
        source_text,
        _LANDING_SOURCE_PATTERN,
        _LANDING_DATE_PATTERN,
    )
    launch_excerpt = _source_excerpt(
        source_text,
        _LAUNCH_SOURCE_PATTERN,
        re.compile(r"\bjuly\s+14[,]?\s+2023\b", re.IGNORECASE),
    )
    source_content = {
        "landing_record": landing_excerpt[:240],
        "launch_record": launch_excerpt[:240],
    }
    evidence_match = bool(landing_excerpt or launch_excerpt)

    contradiction_evidence = []
    if contradicted_landing_claims or false_report_claims:
        if not landing_excerpt:
            return finish(
                "Unverified",
                "The retrieved ISRO page did not contain a matching dated landing statement.",
            )
        claim = (contradicted_landing_claims + false_report_claims)[0]
        contradiction_evidence.append(_evidence(claim, landing_excerpt, "Contradicts"))
    if cancelled_launch_claims:
        if not launch_excerpt:
            return finish(
                "Unverified",
                "The retrieved ISRO page did not confirm the launch details needed to assess this claim.",
            )
        contradiction_evidence.append(
            _evidence(cancelled_launch_claims[0], launch_excerpt, "Contradicts")
        )
    contradiction_detected = bool(contradiction_evidence)
    if contradiction_evidence and landing_claims:
        return finish(
            "Unverified",
            "The article contains conflicting claims about the Chandrayaan-3 mission; "
            "the available source evidence cannot establish the article's intended conclusion.",
            contradiction_evidence,
        )
    if contradiction_evidence:
        return finish(
            "Contradicted",
            "The article's claim conflicts with ISRO's official mission record, which confirms "
            "Chandrayaan-3 launched on July 14, 2023 and successfully soft-landed on the Moon "
            "on August 23, 2023.",
            contradiction_evidence,
        )

    if not landing_claims or not landing_excerpt:
        return finish(
            "Unverified",
            "The retrieved ISRO page did not contain a matching dated landing statement.",
        )

    claim = landing_claims[0]

    evidence_match = True
    return finish(
        "Supported",
        (
            "ISRO's official mission record confirms Chandrayaan-3 successfully "
            "soft-landed on the Moon on August 23, 2023."
        ),
        [_evidence(claim, landing_excerpt, "Supports")],
    )
