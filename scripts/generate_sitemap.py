"""Generate sitemap.xml with accurate last modified dates."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

# (loc, path, changefreq, priority)
ROUTES = [
    ("https://www.falowen.app/", "public/index.html", "weekly", "1.0"),
    ("https://www.falowen.app/login", "pages/login.py", "monthly", "0.9"),
    ("https://www.falowen.app/register", "public/index.html", "monthly", "0.9"),
    (
        "https://www.falowen.app/payment-agreement",
        "public/index.html",
        "monthly",
        "0.8",
    ),
    (
        "https://register.falowen.app/#privacy-policy",
        "public/index.html",
        "monthly",
        "0.8",
    ),
    (
        "https://register.falowen.app/#terms-of-service",
        "public/index.html",
        "monthly",
        "0.8",
    ),
    (
        "https://www.falowen.app/about-us",
        "public/index.html",
        "yearly",
        "0.6",
    ),
    (
        "https://www.falowen.app/contact",
        "public/index.html",
        "yearly",
        "0.6",
    ),
]


def last_modified(path: str) -> str:
    """Return last commit date for *path* in ISO-8601 format."""
    try:
        result = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", path],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return result.split("T")[0]
    except subprocess.CalledProcessError:
        # Fallback to current date if file is not tracked.
        return datetime.utcnow().date().isoformat()


def generate_sitemap(destination: Path) -> None:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for loc, path, changefreq, priority in ROUTES:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = loc
        ET.SubElement(url, "lastmod").text = last_modified(path)
        ET.SubElement(url, "changefreq").text = changefreq
        ET.SubElement(url, "priority").text = priority

    rough_string = ET.tostring(urlset, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="UTF-8")
    destination.write_bytes(pretty_xml)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    generate_sitemap(base_dir / "public" / "sitemap.xml")


if __name__ == "__main__":
    main()
