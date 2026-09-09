#!/usr/bin/env python3
# eml2md.py  –  usage: python eml2md.py input.eml [output.md]
import sys
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from markdownify import markdownify as md
from bs4 import BeautifulSoup

# Tags that HTML emails use purely for layout (nested tables to
# position content), not for real tabular data. markdownify flattens
# anything inside a <td> onto a single line so it fits a pipe-table
# cell, which mangles these layout tables into unreadable output.
# Unwrapping them before conversion keeps the text but drops the
# table semantics, so line breaks and paragraphs survive.
LAYOUT_TAGS = ["table", "tr", "td", "tbody", "thead", "tfoot"]

def html_to_md(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(LAYOUT_TAGS):
        tag.unwrap()
    return md(str(soup))

def iter_own_parts(msg):
    """Recursively yield the leaf parts that belong to this message's
    own content. A forwarded email attached as message/rfc822 is
    yielded as-is (not descended into): msg.walk() flattens straight
    through those, so the forwarded thread's text/html gets picked up
    instead of the sender's own top-level text, silently dropping
    whatever the sender actually wrote."""
    if msg.get_content_type() == "message/rfc822":
        yield msg
        return
    if msg.is_multipart():
        for part in msg.iter_parts():
            yield from iter_own_parts(part)
    else:
        yield msg

def extract_body(msg):
    """Return markdown for msg's own text/html content, ignoring any
    attached message/rfc822 parts (those are returned separately)."""
    html, text, forwarded = None, None, []
    for part in iter_own_parts(msg):
        ct = part.get_content_type()
        if ct == "message/rfc822":
            forwarded.append(part.get_content())
            continue
        if "attachment" in str(part.get("Content-Disposition", "")):
            continue
        if ct == "text/html" and html is None:
            html = part.get_content()
        elif ct == "text/plain" and text is None:
            text = part.get_content()

    body = html_to_md(html) if html else (text or "")

    for embedded in forwarded:
        fwd_body = extract_body(embedded)
        body += "\n\n---\n\n## Forwarded message\n"
        body += f"- **From:** {embedded.get('From', '')}\n"
        body += f"- **To:** {embedded.get('To', '')}\n"
        body += f"- **Date:** {embedded.get('Date', '')}\n"
        body += f"- **Subject:** {embedded.get('Subject', '')}\n\n"
        body += fwd_body

    return body

def convert(src, dst=None):
    with open(src, "rb") as f:
        msg = BytesParser(policy=default).parse(f)

    body = extract_body(msg)

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
