"""Preserve CSS match semantics without retrying every offset of inline assets."""
import random
import re

from validate_source import CSS_BLOCK


def test_css_boundaries_preserve_the_existing_matches():
    previous = re.compile(r"(?P<selectors>[^{}]+)\{(?P<body>[^{}]*)\}", re.DOTALL)
    rng = random.Random(7109)
    for _ in range(500):
        source = "".join(rng.choice("ab{}:; \n") for _ in range(100))
        assert [m.groupdict() for m in CSS_BLOCK.finditer(source)] == [
            m.groupdict() for m in previous.finditer(source)
        ]


def test_large_braceless_inline_asset_is_not_a_css_block():
    assert list(CSS_BLOCK.finditer("A" * 200_000)) == []
