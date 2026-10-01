"""Validate generated text before it can touch a translated column."""

import re
from html.parser import HTMLParser

from apps.core.sanitize import clean_html, tag_signature

from .client import TranslationError


class Markup(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.events = []
        self.feed(value)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.events.append(("start", tag, tuple(sorted(attrs))))

    def handle_startendtag(self, tag, attrs):
        self.events.append(("empty", tag, tuple(sorted(attrs))))

    def handle_endtag(self, tag):
        self.events.append(("end", tag))

    def handle_comment(self, data):
        self.events.append(("comment", data))

    def handle_decl(self, decl):
        self.events.append(("decl", decl))


URL_RE = re.compile(r"(?:https?://|mailto:|tel:)[^\s<>\"']+")
NUMBER_RE = re.compile(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)")


def validate_translation(
    source, output, *, max_length=None, rich=False, profile="default", terms=()
):
    if not isinstance(output, str) or not output.strip() or "```" in output:
        raise TranslationError("invalid_text")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in output):
        raise TranslationError("invalid_text")
    if max_length and len(output) > max_length:
        raise TranslationError("length_exceeded")
    if rich:
        if (
            tag_signature(source) != tag_signature(output)
            or Markup(source).events != Markup(output).events
        ):
            raise TranslationError("html_changed")
        cleaned = clean_html(output, profile=profile)
        if Markup(cleaned).events != Markup(output).events:
            raise TranslationError("unsafe_html")
        output = cleaned
    elif Markup(output).events:
        raise TranslationError("unexpected_html")
    for term in terms:
        if term in source and source.count(term) != output.count(term):
            raise TranslationError("proper_noun_changed")
    if sorted(URL_RE.findall(source)) != sorted(URL_RE.findall(output)):
        raise TranslationError("url_changed")
    # ASCII numbers stay as supplied, including in Arabic; prevents invented metrics.
    if sorted(NUMBER_RE.findall(source)) != sorted(NUMBER_RE.findall(output)):
        raise TranslationError("number_changed")
    return output
