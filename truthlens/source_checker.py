"""
TruthLens AI - Source Credibility Explorer & Domain Intelligence Engine
Evaluates domain reputation, suspicious URL patterns, known media bias, and fact-checking links.
Strictly follows the principle: Never claim a source is fake simply because it is unfamiliar.
"""

import re
from urllib.parse import urlparse

# Verified Media Knowledge Base
KNOWN_SOURCES = {
    # Wire Services & High-Integrity Outlets
    "reuters.com": {
        "name": "Reuters News Agency",
        "category": "International Wire Service",
        "rating": "Very High Credibility",
        "bias": "Least Biased / Neutral",
        "trust_score": 98,
        "is_satire": False,
        "is_flagged": False,
        "established": "1851",
        "ownership": "Thomson Reuters",
        "description": "Global wire service adhering to the Trust Principles of independence, integrity, and freedom from bias."
    },
    "apnews.com": {
        "name": "Associated Press (AP)",
        "category": "International Wire Service",
        "rating": "Very High Credibility",
        "bias": "Least Biased / Neutral",
        "trust_score": 98,
        "is_satire": False,
        "is_flagged": False,
        "established": "1846",
        "ownership": "Not-for-profit news cooperative",
        "description": "Premier independent global news cooperative recognized worldwide for standard-setting factual reporting."
    },
    "bbc.com": {
        "name": "BBC News",
        "category": "Public Broadcaster",
        "rating": "High Credibility",
        "bias": "Center / Balanced",
        "trust_score": 94,
        "is_satire": False,
        "is_flagged": False,
        "established": "1922",
        "ownership": "Public Corporation (Royal Charter)",
        "description": "British public service broadcaster governed by strict editorial impartiality guidelines."
    },
    "bbc.co.uk": {
        "name": "BBC UK",
        "category": "Public Broadcaster",
        "rating": "High Credibility",
        "bias": "Center / Balanced",
        "trust_score": 94,
        "is_satire": False,
        "is_flagged": False,
        "established": "1922",
        "ownership": "Public Corporation",
        "description": "United Kingdom public service broadcasting headquarters."
    },
    "theguardian.com": {
        "name": "The Guardian",
        "category": "Major Newspaper",
        "rating": "High Credibility",
        "bias": "Left-Center",
        "trust_score": 88,
        "is_satire": False,
        "is_flagged": False,
        "established": "1821",
        "ownership": "Scott Trust Limited",
        "description": "British daily newspaper owned by an independent trust preserving financial and editorial independence."
    },
    "wsj.com": {
        "name": "The Wall Street Journal",
        "category": "Financial Daily",
        "rating": "High Credibility",
        "bias": "Right-Center (Editorial) / Center (News)",
        "trust_score": 90,
        "is_satire": False,
        "is_flagged": False,
        "established": "1889",
        "ownership": "Dow Jones & Company",
        "description": "Authoritative financial and international daily with rigorous fact-checking in news reporting."
    },
    "nytimes.com": {
        "name": "The New York Times",
        "category": "Major Newspaper",
        "rating": "High Credibility",
        "bias": "Left-Center",
        "trust_score": 89,
        "is_satire": False,
        "is_flagged": False,
        "established": "1851",
        "ownership": "The New York Times Company",
        "description": "Newspaper of record with 130+ Pulitzer Prizes and comprehensive investigative reporting."
    },
    "washingtonpost.com": {
        "name": "The Washington Post",
        "category": "Major Daily",
        "rating": "High Credibility",
        "bias": "Left-Center",
        "trust_score": 88,
        "is_satire": False,
        "is_flagged": False,
        "established": "1877",
        "ownership": "Nash Holdings",
        "description": "Major American daily newspaper celebrated for political and investigative accountability reporting."
    },
    "bloomberg.com": {
        "name": "Bloomberg News",
        "category": "Financial News & Data",
        "rating": "Very High Credibility",
        "bias": "Center / Neutral",
        "trust_score": 95,
        "is_satire": False,
        "is_flagged": False,
        "established": "1990",
        "ownership": "Bloomberg L.P.",
        "description": "Global financial, market, and geopolitical news agency with high evidentiary standards."
    },
    "nature.com": {
        "name": "Nature Scientific Journal",
        "category": "Peer-Reviewed Academic",
        "rating": "Gold Standard Credibility",
        "bias": "Scientific Consensus",
        "trust_score": 99,
        "is_satire": False,
        "is_flagged": False,
        "established": "1869",
        "ownership": "Springer Nature",
        "description": "World-leading multidisciplinary science journal with strict peer-review vetting."
    },
    "sciencemag.org": {
        "name": "Science / AAAS",
        "category": "Peer-Reviewed Academic",
        "rating": "Gold Standard Credibility",
        "bias": "Scientific Consensus",
        "trust_score": 99,
        "is_satire": False,
        "is_flagged": False,
        "established": "1880",
        "ownership": "AAAS",
        "description": "Peer-reviewed academic journal of the American Association for the Advancement of Science."
    },
    "npr.org": {
        "name": "National Public Radio (NPR)",
        "category": "Public Radio / News",
        "rating": "High Credibility",
        "bias": "Center / Lean Left",
        "trust_score": 91,
        "is_satire": False,
        "is_flagged": False,
        "established": "1970",
        "ownership": "Non-profit media organization",
        "description": "American public radio network with a comprehensive ethics handbook and corrections policy."
    },
    "aljazeera.com": {
        "name": "Al Jazeera English",
        "category": "International Broadcaster",
        "rating": "Moderate-High Credibility",
        "bias": "Lean Left / Middle East Focus",
        "trust_score": 82,
        "is_satire": False,
        "is_flagged": False,
        "established": "2006",
        "ownership": "Al Jazeera Media Network",
        "description": "Global news channel providing diverse regional coverage with strong field reporting."
    },
    "cnn.com": {
        "name": "CNN",
        "category": "Cable News Network",
        "rating": "Moderate-High Credibility",
        "bias": "Lean Left",
        "trust_score": 80,
        "is_satire": False,
        "is_flagged": False,
        "established": "1980",
        "ownership": "Warner Bros. Discovery",
        "description": "Pioneering 24-hour news network with reliable breaking news coverage and political commentary."
    },
    "foxnews.com": {
        "name": "Fox News",
        "category": "Cable News Network",
        "rating": "Mixed Credibility (Opinion vs News)",
        "bias": "Right / Conservative",
        "trust_score": 70,
        "is_satire": False,
        "is_flagged": False,
        "established": "1996",
        "ownership": "Fox Corporation",
        "description": "Major cable news channel; hard news desk is generally factual while prime-time opinion has high bias."
    },

    # Satire Outlets (Legitimate humor, not intended as disinformation)
    "theonion.com": {
        "name": "The Onion",
        "category": "Satire & Parody",
        "rating": "Verified Satire Publication",
        "bias": "Satirical Humor",
        "trust_score": 50,
        "is_satire": True,
        "is_flagged": False,
        "established": "1988",
        "ownership": "G/O Media",
        "description": "Prominent satirical publication. Articles are deliberately comedic and fictional."
    },
    "babylonbee.com": {
        "name": "The Babylon Bee",
        "category": "Satire & Parody",
        "rating": "Verified Satire Publication",
        "bias": "Conservative Satirical Humor",
        "trust_score": 50,
        "is_satire": True,
        "is_flagged": False,
        "established": "2016",
        "ownership": "Seth Dillon",
        "description": "Satirical news website publishing parodies on political, religious, and cultural events."
    },
    "clickhole.com": {
        "name": "ClickHole",
        "category": "Satire & Parody",
        "rating": "Verified Satire Publication",
        "bias": "Parody / Internet Culture",
        "trust_score": 50,
        "is_satire": True,
        "is_flagged": False,
        "established": "2014",
        "ownership": "Cards Against Humanity",
        "description": "Satirical website parodying viral clickbait media and sensational headlines."
    },

    # Known Disinformation / Questionable Sources
    "infowars.com": {
        "name": "InfoWars",
        "category": "Conspiracy / Alternative Media",
        "rating": "Extremely Low Credibility",
        "bias": "Extreme Right / Conspiracy",
        "trust_score": 12,
        "is_satire": False,
        "is_flagged": True,
        "established": "1999",
        "ownership": "Free Speech Systems LLC",
        "description": "Known propagator of debunked conspiracy theories, health hoaxes, and unverified allegations."
    },
    "naturalnews.com": {
        "name": "Natural News",
        "category": "Pseudoscience & Misinformation",
        "rating": "Extremely Low Credibility",
        "bias": "Conspiracy / Health Hoaxes",
        "trust_score": 10,
        "is_satire": False,
        "is_flagged": True,
        "established": "2005",
        "ownership": "Mike Adams",
        "description": "Website notorious for promoting vaccine misinformation, medical fraud, and conspiracy theories."
    },
    "beforeitsnews.com": {
        "name": "Before It's News",
        "category": "Unmoderated User Submissions",
        "rating": "Low Credibility",
        "bias": "Unvetted / Fringe Theories",
        "trust_score": 15,
        "is_satire": False,
        "is_flagged": True,
        "established": "2008",
        "ownership": "Citizen Journalist Platform",
        "description": "Platform allowing unverified citizen uploads with zero editorial fact-checking, frequently hosting hoaxes."
    },
    "worldnewsdailyreport.com": {
        "name": "World News Daily Report",
        "category": "Fabricated Hoaxes / Fake News",
        "rating": "Known Hoax Network",
        "bias": "Fabrication",
        "trust_score": 5,
        "is_satire": False,
        "is_flagged": True,
        "established": "2014",
        "ownership": "Disinformation network",
        "description": "Historically fabricated sensational hoax stories with fabricated quotes and non-existent authorities."
    },
    "thegatewaypundit.com": {
        "name": "The Gateway Pundit",
        "category": "Partisan Blog",
        "rating": "Low Credibility",
        "bias": "Extreme Right",
        "trust_score": 25,
        "is_satire": False,
        "is_flagged": True,
        "established": "2004",
        "ownership": "Jim Hoft",
        "description": "Blog frequently flagged by international fact-checkers for publishing false or misleading claims."
    }
}

# High-risk / suspicious TLDs frequently abused by ephemeral spam / phishing / fake news networks
HIGH_RISK_TLDS = {
    ".to", ".top", ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".buzz", ".click",
    ".work", ".date", ".racing", ".download", ".loan", ".win", ".bid"
}

# Famous domain names often typosquatted
WELL_KNOWN_DOMAINS = [
    "reuters", "bbc", "cnn", "nytimes", "washingtonpost", "apnews", "bloomberg",
    "theguardian", "wsj", "foxnews", "nbcnews", "cbsnews", "abcnews"
]

def extract_domain(input_str: str) -> str:
    """Extract clean domain name from URL or raw domain input."""
    if not input_str:
        return ""
    text = input_str.strip()
    if not re.match(r"^https?://", text, re.IGNORECASE):
        text = "https://" + text
    try:
        parsed = urlparse(text)
        host = parsed.netloc or parsed.path
        host = host.split(":")[0]  # strip port
        if host.startswith("www."):
            host = host[4:]
        return host.lower()
    except Exception:
        return input_str.lower()

def check_source_credibility(domain_or_url: str) -> dict:
    """
    Examines source credibility, forensic URL structure, known ratings, and fact-checking resources.
    Follows: 'Never claim a source is fake just because it is unfamiliar.'
    """
    domain = extract_domain(domain_or_url)
    if not domain:
        return {
            "domain": "",
            "status": "No Domain Provided",
            "trust_score": None,
            "rating": "Unknown",
            "flags": ["No domain provided for inspection"],
            "fact_check_links": []
        }

    # Step 1: Check known database
    known_info = KNOWN_SOURCES.get(domain)
    
    # Also check base domain if subdomain provided (e.g. news.bbc.co.uk -> bbc.co.uk)
    if not known_info:
        for k_domain, k_data in KNOWN_SOURCES.items():
            if domain.endswith("." + k_domain):
                known_info = k_data
                break

    flags = []
    suspicious_patterns = []
    
    # Step 2: URL Forensics
    # Check IP address as domain
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain):
        suspicious_patterns.append("IP Address used instead of verified registered domain name")
        flags.append("Numerical IP Host")

    # Check suspicious TLD
    for tld in HIGH_RISK_TLDS:
        if domain.endswith(tld):
            suspicious_patterns.append(f"Domain uses high-risk/unregulated TLD '{tld}' commonly associated with throwaway sites")
            flags.append("Uncommon TLD")
            break

    # Check typosquatting / clone patterns
    base_name = domain.split(".")[0]
    for brand in WELL_KNOWN_DOMAINS:
        if brand in domain and domain not in KNOWN_SOURCES and not domain.endswith(f".{brand}.com"):
            suspicious_patterns.append(f"Potential typosquatting/brand spoofing: contains '{brand}' but is not an official registered domain")
            flags.append("Brand Impersonation Risk")
            break

    # Check excessive hyphens (e.g. breaking-news-daily-update.com)
    if domain.count("-") >= 3:
        suspicious_patterns.append("Domain contains 3 or more hyphens, characteristic of algorithmic spam generation")
        flags.append("Hyphenated Domain")

    # Step 3: Determine reputation categorization
    if known_info:
        trust_score = known_info["trust_score"]
        rating = known_info["rating"]
        category = known_info["category"]
        bias = known_info["bias"]
        is_satire = known_info["is_satire"]
        is_flagged = known_info["is_flagged"]
        summary = known_info["description"]
        status = "Verified Source Index"
    else:
        # Source is UNKNOWN / UNINDEXED.
        # Strict rule: DO NOT label fake. Label as Unindexed / Corroboration Required.
        status = "Unindexed / Independent Source"
        is_satire = False
        is_flagged = len(suspicious_patterns) > 0
        category = "Independent / Regional Domain"
        bias = "Unindexed / Unknown"
        
        if suspicious_patterns:
            rating = "Caution — Suspicious Domain Indicators"
            trust_score = 45
            summary = "This domain exhibits unusual naming or registration characteristics. Exercise heightened scrutiny and verify claims through independent news agencies."
        else:
            rating = "Unindexed — Corroboration Recommended"
            trust_score = 65
            summary = "This source is not cataloged in the global primary index. An unindexed status does not mean the source is untruthful, but journalistic integrity standards advise cross-referencing significant claims."

    # Fact-checking query links for verification
    query = domain.replace(".", " ")
    fact_check_links = [
        {
            "name": "Reuters Fact Check",
            "url": f"https://www.reuters.com/site-search/?query={domain}",
            "description": "Cross-check Reuters global investigative database"
        },
        {
            "name": "AP Fact Check",
            "url": f"https://apnews.com/hub/ap-fact-check",
            "description": "Examine Associated Press verified debunks"
        },
        {
            "name": "Snopes Fact-Checking Archive",
            "url": f"https://www.snopes.com/?s={domain}",
            "description": "Search the oldest independent fact-checking archive"
        },
        {
            "name": "PolitiFact Truth-O-Meter",
            "url": f"https://www.politifact.com/search/?q={domain}",
            "description": "Cross-reference political claims and source ratings"
        },
        {
            "name": "FactCheck.org (Annenberg Public Policy)",
            "url": f"https://www.factcheck.org/?s={domain}",
            "description": "Nonpartisan consumer advocate for voters"
        }
    ]

    return {
        "domain": domain,
        "status": status,
        "name": known_info["name"] if known_info else domain,
        "rating": rating,
        "trust_score": trust_score,
        "category": category,
        "bias": bias,
        "is_satire": is_satire,
        "is_flagged": is_flagged,
        "summary": summary,
        "suspicious_patterns": suspicious_patterns,
        "flags": flags,
        "fact_check_links": fact_check_links,
        "established": known_info.get("established") if known_info else "Unindexed",
        "ownership": known_info.get("ownership") if known_info else "Private / Unindexed"
    }
