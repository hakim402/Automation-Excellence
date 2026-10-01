"""
HTML sanitisation for the rich-text fields.

Rich HTML is allowed on an explicit short list of long-form body fields
(BUILD_PROMPT.md). Everything reaching the database passes through here
first, because this is a security vendor's own site and the frontend renders
these fields with dangerouslySetInnerHTML.

Sanitising on save rather than on render means the database never holds
markup we would not serve, so a future reader that forgets to sanitise
cannot reintroduce the hole.
"""

import re
from collections import Counter

import nh3

# CLAUDE.md section 5. Everything not listed is stripped, including style,
# class, script and every inline event attribute.
ALLOWED_TAGS: set[str] = {
    "p",
    "h2",
    "h3",
    "h4",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "a",
    "blockquote",
    "code",
    "pre",
    "br",
    "hr",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "img",
    "figure",
    "figcaption",
}

ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    # "rel" is deliberately absent: nh3 sets it itself via link_rel below, and
    # refuses to do both. Having nh3 own it is stricter than honouring an
    # author-supplied rel, and still satisfies CLAUDE.md section 5.
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan"},
}

ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto", "tel"}

# FAQ answers take links and lists only — no headings, no images, no tables.
# A heading inside an accordion panel breaks the document outline, which is
# an SEO problem, not just a visual one.
FAQ_ALLOWED_TAGS: set[str] = {
    "p",
    "ul",
    "ol",
    "li",
    "strong",
    "em",
    "a",
    "br",
    "code",
}

FAQ_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {"a": {"href", "title", "target"}}


def clean_html(value: str | None, *, profile: str = "default") -> str:
    """
    Return `value` with every tag and attribute outside the allowlist removed.

    External links get rel="noopener noreferrer" added by nh3's link_rel.
    Passing an empty or None value returns an empty string, so a blank
    translation stays blank rather than becoming the string "None".
    """
    if not value:
        return ""

    tags, attributes = _profile(profile)

    return nh3.clean(
        value,
        tags=tags,
        attributes=attributes,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer",
        strip_comments=True,
    )


def _profile(name: str) -> tuple[set[str], dict[str, set[str]]]:
    if name == "faq":
        return FAQ_ALLOWED_TAGS, FAQ_ALLOWED_ATTRIBUTES
    if name == "default":
        return ALLOWED_TAGS, ALLOWED_ATTRIBUTES
    raise ValueError(f"Unknown sanitiser profile: {name!r}")


_TAG_RE = re.compile(r"<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9]*)")


def tag_signature(value: str | None) -> Counter[str]:
    """
    A multiset of the tags in `value`, e.g. Counter({"p": 3, "/p": 3}).

    The Groq translation pipeline must return exactly the markup it was
    given. Comparing signatures before and after is how we catch a model that
    helpfully reformatted the HTML, dropped a closing tag, or wrapped the
    whole answer in an extra <p> (CLAUDE.md section 5). Used in Phase 3.
    """
    if not value:
        return Counter()

    return Counter(
        f"{'/' if closing else ''}{name.lower()}" for closing, name in _TAG_RE.findall(value)
    )
