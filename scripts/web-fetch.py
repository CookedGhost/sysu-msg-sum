import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from difflib import unified_diff

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

TMP_DIR = Path(os.environ.get("WEB_TMP_DIR", Path.home() / ".web-tmp"))

def ensure_dirs():
  TMP_DIR.mkdir(parents=True, exist_ok=True)

def fetch_navi_content(url: str, headers: dict = None) -> str:
    """获取页面导航信息"""
    req_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) web-monitor/1.0"
    }
    if headers:
        req_headers.update(headers)

    req = Request(url, headers=req_headers)
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.reason}")
    except URLError as e:
        raise RuntimeError(f"Connection error: {e.reason}")

    # Basic text extraction without bs4
    if HAS_BS4:
        soup = BeautifulSoup(raw, "html.parser")
        # Remove script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        # 移除footer
        for div in soup.find_all('div', id='footer'):
            div.decompose()

        # 获取剩余跳转链接
        all_links = soup.find_all('a')
        content = []
        _url = url.rstrip("/") if url.endswith("/") else url
        for link in all_links:
            if(link.get_text(strip=True) == ""):
                continue
            text = link.get_text(strip=True)
            href = link.get('href', '')
            # 跳过非具体文章的链接
            if not href.endswith(tuple("0123456789")):
                continue
            if not href.startswith("http"):
                href = _url + "/" + href.lstrip("/")
            content.append(f"{text} ({href})")
        return "\n".join(content)
    else:
        # Crude fallback: strip HTML tags
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

def fetch_detail_content(url: str, headers: dict = None) -> str:
    """获取页面详细内容"""
    req_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) web-monitor/1.0"
    }
    if headers:
        req_headers.update(headers)

    req = Request(url, headers=req_headers)
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.reason}")
    except URLError as e:
        raise RuntimeError(f"Connection error: {e.reason}")


    if HAS_BS4:
        soup = BeautifulSoup(raw, "html.parser")
        # Remove script, style
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "li", "ul", "a"]):
            tag.decompose()
        print(soup.prettify())
        text = soup.get_text(separator="\n")

        return text
    else:
        # Crude fallback: strip HTML tags
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

def normalize_text(text: str) -> str:
    lines = text.split("\n")
    lines = [re.sub(r'\s+', ' ', line.strip()) for line in lines if line.strip()]
    return "\n".join(lines)

def save_fetch_content(url: str, output_filename: str, isdetail: bool):
    if isdetail:
        content = fetch_detail_content(url)
    else:
        content = fetch_navi_content(url)
    content = normalize_text(content)
    filename = TMP_DIR / f"{output_filename}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n")
        f.write(content)
    return filename

def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser = argparse.ArgumentParser(description="Fetch web page content")
    parser.add_argument("url", help="URL of the web page to fetch")
    parser.add_argument("--output", default=f"fetch_{timestamp}", help="Base name for output file (without extension)")
    parser.add_argument("--detail", action="store_true", help="Fetch detailed content instead of navigation")
    args = parser.parse_args()

    ensure_dirs()
    try:
        filename = save_fetch_content(args.url, args.output, args.detail)
        print(f"Content saved to: {filename}")
    except Exception as e:
        print(f"Error fetching content: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
