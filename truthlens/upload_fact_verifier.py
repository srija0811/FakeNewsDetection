"""Additional source checks for configured Fake Articles claims."""

import re
from datetime import date, datetime, timedelta

from truthlens.scraper import extract_article_from_url


ICC_T20_2024_FINAL_URL = (
    "https://www.icc-cricket.com/tournaments/t20cricketworldcup/news/"
    "india-return-to-heroes-welcome-in-delhi-following-t20-world-cup-triumph"
)

_T20_2024_PATTERN = re.compile(
    r"\bt20\s+world\s+cup\b.{0,35}\b2024\b|\b2024\b.{0,35}\bt20\s+world\s+cup\b",
    re.IGNORECASE,
)
_FINAL_PATTERN = re.compile(r"\bfinal\b", re.IGNORECASE)
_INDIA_DEFEAT_PATTERN = re.compile(
    r"\bindia\b.{0,250}\b(?:beat|beats|defeated|defeating|won|victory\s+over)\b"
    r".{0,100}\bsouth\s+africa\b.{0,80}\bby\s+(?:seven|7)\s+runs\b",
    re.IGNORECASE,
)
_JUNE_29_PATTERN = re.compile(
    r"\b(?:june\s+29(?:th)?[,]?\s+2024|29(?:th)?\s+june[,]?\s+2024)\b",
    re.IGNORECASE,
)
_ANY_EXPLICIT_2024_DATE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s+2024\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|"
    r"july|august|september|october|november|december)[,]?\s+2024\b",
    re.IGNORECASE,
)
_TEAM = r"(?:South Africa|India)"
_WINNER_LOSER_PATTERN = re.compile(
    rf"\b(?P<winner>{_TEAM})\b.{{0,100}}\b(?:beat|beats|defeated|defeats|defeating|overcame|"
    rf"won\s+against)\b.{{0,80}}\b(?P<loser>{_TEAM})\b",
    re.IGNORECASE,
)
_LOSER_WINNER_PATTERN = re.compile(
    rf"\b(?P<loser>{_TEAM})\b.{{0,80}}\b(?:lost\s+to|were\s+beaten\s+by|"
    rf"was\s+beaten\s+by|were\s+defeated\s+by|was\s+defeated\s+by)\s+"
    rf"(?P<winner>{_TEAM})\b",
    re.IGNORECASE,
)
_GENERIC_WINNER_PATTERN = re.compile(
    rf"\b(?P<winner>{_TEAM})\b.{{0,100}}\b(?:won|wins|win|triumphed|"
    rf"clinched|claimed|secured|lifted|were\s+crowned|was\s+crowned)\b",
    re.IGNORECASE,
)
_PASSIVE_WINNER_PATTERN = re.compile(
    rf"\b(?:the\s+)?(?:final|title|trophy)\b.{{0,60}}\b(?:was|were)\s+won\s+by\s+"
    rf"(?P<winner>{_TEAM})\b",
    re.IGNORECASE,
)
_MARGIN_PATTERN = re.compile(
    r"\bby\s+(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"\s+(?P<unit>runs?|wickets?)\b",
    re.IGNORECASE,
)
_CHASE_TARGET_PATTERN = re.compile(
    r"\bchased\s+(?:a\s+target\s+of\s+)?(?P<target>\d{2,3})\b",
    re.IGNORECASE,
)
_SCORE_PATTERN = re.compile(
    rf"\b(?P<team>{_TEAM})\b.{{0,35}}\b(?:scored|posted|made|finished\s+on)?\s*"
    r"(?P<runs>\d{2,3})\s*/\s*(?P<wickets>\d{1,2})\b",
    re.IGNORECASE,
)
_RECORDS_CLAIM_PATTERN = re.compile(
    r"\b(?:removed|erased|deleted|struck)\b.{0,80}\b(?:records?|scorecards?|results?)\b"
    r"|\b(?:records?|scorecards?|results?)\b.{0,80}\b(?:removed|erased|deleted|struck)\b",
    re.IGNORECASE,
)
_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _sentences(text):
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+|\n+", text) if sentence.strip()]


def _published_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None


def _previous_saturday(published_date):
    days_since_saturday = (published_date.weekday() - 5) % 7
    return published_date - timedelta(days=days_since_saturday)


def verify_uploaded_t20_final_claim(text):
    """Verify separate 2024 final result claims against the ICC's official report."""
    article_text = text or ""
    event_context = _T20_2024_PATTERN.search(article_text) and _FINAL_PATTERN.search(article_text)
    if not event_context:
        return {
            "status": "Unverified",
            "summary": "",
            "evidence": [],
            "source_check_attempted": False,
        }

    extracted_claims = []
    for sentence in _sentences(article_text):
        pair = _WINNER_LOSER_PATTERN.search(sentence)
        if pair:
            extracted_claims.append({
                "kind": "winner",
                "winner": pair.group("winner").lower(),
                "claim": sentence,
                "statement": (
                    f"{pair.group('winner')} defeated {pair.group('loser')} in the final."
                ),
            })
            continue

        reversed_pair = _LOSER_WINNER_PATTERN.search(sentence)
        if reversed_pair:
            extracted_claims.append({
                "kind": "winner",
                "winner": reversed_pair.group("winner").lower(),
                "claim": sentence,
                "statement": (
                    f"{reversed_pair.group('winner')} defeated "
                    f"{reversed_pair.group('loser')} in the final."
                ),
            })
            continue

        winner = _GENERIC_WINNER_PATTERN.search(sentence) or _PASSIVE_WINNER_PATTERN.search(sentence)
        if winner:
            extracted_claims.append({
                "kind": "winner",
                "winner": winner.group("winner").lower(),
                "claim": sentence,
                "statement": f"{winner.group('winner')} won the final.",
            })

    for sentence in _sentences(article_text):
        margin = _MARGIN_PATTERN.search(sentence)
        if margin:
            count = margin.group("count").lower()
            extracted_claims.append({
                "kind": "margin",
                "count": _NUMBER_WORDS.get(count, int(count) if count.isdigit() else None),
                "unit": margin.group("unit").lower().rstrip("s"),
                "claim": sentence,
                "statement": (
                    f"The final margin was {margin.group('count')} "
                    f"{margin.group('unit')}."
                ),
            })
        target = _CHASE_TARGET_PATTERN.search(sentence)
        if target:
            extracted_claims.append({
                "kind": "score",
                "claim": sentence,
                "detail": f"chased {target.group('target')}",
            })
        for score in _SCORE_PATTERN.finditer(sentence):
            extracted_claims.append({
                "kind": "score",
                "claim": sentence,
                "detail": (
                    f"{score.group('team')} {score.group('runs')}/"
                    f"{score.group('wickets')}"
                ),
            })
        if _RECORDS_CLAIM_PATTERN.search(sentence):
            extracted_claims.append({
                "kind": "unsupported_secondary",
                "claim": sentence,
            })

    result_claims = [
        claim for claim in extracted_claims
        if claim["kind"] in {"winner", "margin"}
    ]
    if not result_claims:
        return {
            "status": "Unverified",
            "summary": "",
            "evidence": [],
            "source_check_attempted": False,
        }

    source_result = extract_article_from_url(ICC_T20_2024_FINAL_URL)
    if not source_result.get("success"):
        return {
            "status": "Unverified",
            "summary": "The official ICC report could not be retrieved, so the uploaded article remains unverified.",
            "evidence": [],
            "source_check_attempted": True,
        }

    source_title = source_result.get("title", "")
    source_text = source_result.get("text", "")
    source_content = f"{source_title}\n{source_text}"
    source_result_sentence = next(
        (
            sentence
            for sentence in _sentences(source_text)
            if _INDIA_DEFEAT_PATTERN.search(sentence)
            and _FINAL_PATTERN.search(sentence)
        ),
        "",
    )
    source_publication_date = _published_date(source_result.get("date"))
    source_claimed_winner = (
        "india"
        if source_result_sentence
        and _INDIA_DEFEAT_PATTERN.search(source_result_sentence)
        else ""
    )
    source_margin = 7 if source_result_sentence and re.search(
        r"\bby\s+seven\s+runs\b", source_result_sentence, re.IGNORECASE
    ) else None
    if (
        not _T20_2024_PATTERN.search(source_content)
        or not source_result_sentence
        or not source_publication_date
        or "saturday" not in source_result_sentence.lower()
        or not source_claimed_winner
        or source_margin is None
    ):
        return {
            "status": "Unverified",
            "summary": "The retrieved ICC page did not directly confirm the matching final result and date.",
            "evidence": [],
            "source_check_attempted": True,
        }

    event_date = _previous_saturday(source_publication_date)
    if event_date != date(2024, 6, 29):
        return {
            "status": "Unverified",
            "summary": "The ICC report's publication date did not establish the claimed final date.",
            "evidence": [],
            "source_check_attempted": True,
        }

    claimed_dates = _ANY_EXPLICIT_2024_DATE.findall(article_text)
    if claimed_dates and not _JUNE_29_PATTERN.search(article_text):
        return {
            "status": "Unverified",
            "summary": "The uploaded article gives a date that does not match the ICC-verified final date.",
            "evidence": [],
            "source_check_attempted": True,
        }

    excerpt = " ".join(source_result_sentence.split())[:400]
    evidence = []
    contradiction_found = False
    for claim in result_claims:
        if claim["kind"] == "winner":
            matches = claim["winner"] == source_claimed_winner
            status = "Supports" if matches else "Contradicts"
            contradiction_found = contradiction_found or not matches
        else:
            matches = claim["count"] == source_margin and claim["unit"] == "run"
            status = "Supports" if matches else "Contradicts"
            contradiction_found = contradiction_found or not matches
        claim["status"] = status
        evidence.append({
            "source": "International Cricket Council (ICC)",
            "url": ICC_T20_2024_FINAL_URL,
            "claim": claim["statement"],
            "excerpt": excerpt,
            "status": status,
        })

    for claim in extracted_claims:
        if "status" not in claim:
            claim["status"] = "Unverified"

    if contradiction_found:
        return {
            "status": "Contradicted",
            "summary": (
                "ICC's official report confirms India defeated South Africa by seven runs "
                "in the final, contradicting one or more of the article's result claims."
            ),
            "evidence": evidence,
            "source_check_attempted": True,
            "claim_assessments": extracted_claims,
        }

    return {
        "status": "Supported",
        "summary": (
            "ICC's official report confirms India defeated South Africa by seven runs in "
            "the T20 World Cup 2024 final; the report identifies the match as Saturday, "
            "June 29, 2024."
        ),
        "evidence": evidence,
        "source_check_attempted": True,
        "claim_assessments": extracted_claims,
    }
