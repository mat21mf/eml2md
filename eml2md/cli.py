#!/usr/bin/env python3
# eml2md.py  –  usage: python eml2md.py input.eml [output.md]
import sys
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from markdownify import markdownify as md

def convert(src, dst=None):
    with open(src, "rb") as f:
        msg = BytesParser(policy=default).parse(f)

    html, text = None, None
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if "attachment" in str(part.get("Content-Disposition", "")):
                continue
            if ct == "text/html" and html is None:
                html = part.get_content()
            elif ct == "text/plain" and text is None:
                text = part.get_content()
    else:
        ct = msg.get_content_type()
        content = msg.get_content()
        html = content if ct == "text/html" else None
        text = content if ct == "text/plain" else None

    body = md(html) if html else (text or "")

    out = "\n".join([
        f"# {msg.get('Subject', '')}",
        f"- **From:** {msg.get('From', '')}",
        f"- **To:** {msg.get('To', '')}",
        f"- **Date:** {msg.get('Date', '')}",
        "\n---\n",
        body,
    ])

    dst = dst or Path(src).with_suffix(".md")
    Path(dst).write_text(out, encoding="utf-8")
    print(f"Written: {dst}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python eml2md.py input.eml [output.md]")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
