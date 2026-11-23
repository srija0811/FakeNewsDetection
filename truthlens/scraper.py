"""
TruthLens AI - URL Scraper & Article Content Extractor
Safely parses web articles, extracting headline, body text, byline, date, and domain.
"""

import requests
from bs4 import BeautifulSoup
from truthlens.source_checker import extract_domain

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 TruthLensBot/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
}

def extract_article_from_url(url: str, timeout: int = 10) -> dict:
    """
    Fetches article URL and extracts headline, main body text, domain, author, and date.
    Returns structured dictionary or error explanation.
    """
    if not url or not url.strip():
        return {"success": False, "error": "No URL provided."}

    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    domain = extract_domain(clean_url)

    try:
        response = requests.get(
            clean_url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
            verify=True
        )

        if response.status_code == 403:
            return {
                "success": False,
                "error": "Access Forbidden (403): The publisher employs strict anti-scraping or paywall protection. Please copy and paste the text directly.",
                "domain": domain,
                "url": clean_url
            }

        if response.status_code == 404:
            return {
                "success": False,
                "error": "Article Not Found (404): The specified article link does not exist or has been removed.",
                "domain": domain,
                "url": clean_url
            }

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Server returned HTTP {response.status_code}. Please copy and paste the article text directly.",
                "domain": domain,
                "url": clean_url
            }

        soup = BeautifulSoup(response.text, "html.parser")

        # Strip unneeded tags
        for element in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form", "svg"]):
            element.decompose()

        # 1. Extract Headline
        title = ""
        # Try OpenGraph or Twitter meta
        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        elif soup.title:
            title = soup.title.get_text(strip=True)

        # 2. Extract Author / Byline
        author = "Editorial Desk / Unspecified"
        author_meta = (
            soup.find("meta", attrs={"name": "author"}) or
            soup.find("meta", property="article:author") or
            soup.find(class_=lambda c: c and any(k in c.lower() for k in ["author", "byline"]))
        )
        if author_meta:
            if hasattr(author_meta, "get") and author_meta.get("content"):
                author = author_meta["content"].strip()
            elif hasattr(author_meta, "get_text"):
                author = author_meta.get_text(strip=True)

        # 3. Extract Published Date
        date_str = "Recent"
        date_meta = (
            soup.find("meta", property="article:published_time") or
            soup.find("meta", attrs={"name": "date"}) or
            soup.find("time")
        )
        if date_meta:
            if hasattr(date_meta, "get") and date_meta.get("content"):
                date_str = date_meta["content"].strip()
            elif hasattr(date_meta, "get") and date_meta.get("datetime"):
                date_str = date_meta["datetime"].strip()
            elif hasattr(date_meta, "get_text"):
                date_str = date_meta.get_text(strip=True)

        # 4. Extract Main Body Text
        paragraphs = []
        # Target main article container if available
        article_elem = soup.find("article") or soup.find(class_=lambda c: c and any(k in c.lower() for k in ["article-body", "story-body", "entry-content", "post-content"]))
        
        target_container = article_elem if article_elem else soup
        for p in target_container.find_all("p"):
            text = p.get_text(strip=True)
            # Filter out short disclaimers, cookie notices, share prompts
            if len(text.split()) >= 8 and not any(cookie_w in text.lower() for cookie_w in ["cookie policy", "subscribe now", "sign up for", "advertisement", "all rights reserved"]):
                paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)

        if len(full_text.split()) < 30:
            # Fallback if few paragraphs matched
            body_text = soup.get_text(separator=" ", strip=True)
            # Remove excessive whitespace
            clean_body = " ".join(body_text.split())
            if len(clean_body.split()) >= 30:
                full_text = clean_body[:5000]
            else:
                return {
                    "success": False,
                    "error": "Could not extract sufficient article text from URL (article may be behind paywall or dynamic client-side rendering). Please paste the article text manually.",
                    "title": title,
                    "domain": domain,
                    "url": clean_url
                }

        return {
            "success": True,
            "url": clean_url,
            "domain": domain,
            "title": title,
            "author": author,
            "date": date_str,
            "text": full_text,
            "word_count": len(full_text.split()),
            "character_count": len(full_text)
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "The target website took too long to respond (Request Timeout). Please paste article text directly.",
            "domain": domain,
            "url": clean_url
        }
    except requests.exceptions.SSLError:
        return {
            "success": False,
            "error": "SSL Security certificate error on remote host. The connection is not secure.",
            "domain": domain,
            "url": clean_url
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve article: {str(e)}. Please paste article text directly.",
            "domain": domain,
            "url": clean_url
        }
