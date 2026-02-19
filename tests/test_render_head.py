"""Unit tests for render_head helper function"""

import pytest
from fasthtml.common import Script, to_xml

from render.common import render_head


@pytest.mark.unit
class TestRenderHead:
    """Tests for render_head function"""

    def test_render_head_includes_viewport_meta(self):
        """render_head should include a viewport meta tag for mobile"""
        head = render_head("Test", "body{}")
        html = to_xml(head)
        assert 'name="viewport"' in html
        assert "width=device-width" in html

    def test_render_head_includes_charset(self):
        """render_head should include a charset meta tag"""
        head = render_head("Test", "body{}")
        html = to_xml(head)
        assert 'charset="UTF-8"' in html or 'charset="utf-8"' in html.lower()

    def test_render_head_includes_title(self):
        """render_head should include the page title"""
        head = render_head("My Page Title", "body{}")
        html = to_xml(head)
        assert "My Page Title" in html

    def test_render_head_includes_htmx(self):
        """render_head should include the HTMX script"""
        head = render_head("Test", "body{}")
        html = to_xml(head)
        assert "htmx.org" in html

    def test_render_head_includes_favicon(self):
        """render_head should include a favicon link"""
        head = render_head("Test", "body{}")
        html = to_xml(head)
        assert "favicon.svg" in html

    def test_render_head_with_extra_scripts(self):
        """render_head should include extra elements passed via *extra"""
        extra = Script(src="https://cdn.jsdelivr.net/npm/chart.js")
        head = render_head("Test", "body{}", extra)
        html = to_xml(head)
        assert "chart.js" in html
