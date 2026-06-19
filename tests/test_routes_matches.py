"""Unit tests for routes/matches.py helper functions"""

from routes.matches import parse_recording_links


class TestParseRecordingLinks:
    """Tests for parse_recording_links function"""

    def test_single_url(self):
        """A single bare URL is parsed with no label"""
        result = parse_recording_links("https://youtu.be/abc")
        assert result == [("https://youtu.be/abc", None)]

    def test_multiple_urls(self):
        """Multiple lines produce multiple links, in order"""
        result = parse_recording_links(
            "https://youtu.be/1\nhttps://youtu.be/2\nhttps://youtu.be/3"
        )
        assert result == [
            ("https://youtu.be/1", None),
            ("https://youtu.be/2", None),
            ("https://youtu.be/3", None),
        ]

    def test_url_with_label(self):
        """A line using 'url | label' captures both parts, trimmed"""
        result = parse_recording_links("https://youtu.be/abc | First half")
        assert result == [("https://youtu.be/abc", "First half")]

    def test_empty_label_after_pipe_is_none(self):
        """A trailing pipe with no label yields a None label"""
        result = parse_recording_links("https://youtu.be/abc |   ")
        assert result == [("https://youtu.be/abc", None)]

    def test_blank_lines_are_skipped(self):
        """Blank and whitespace-only lines are ignored"""
        result = parse_recording_links(
            "https://youtu.be/1\n\n   \nhttps://youtu.be/2\n"
        )
        assert result == [
            ("https://youtu.be/1", None),
            ("https://youtu.be/2", None),
        ]

    def test_invalid_links_are_skipped(self):
        """Lines without a valid http(s) URL are dropped, valid ones kept"""
        result = parse_recording_links(
            "not-a-url\nhttps://youtu.be/ok\nftp://example.com/x"
        )
        assert result == [("https://youtu.be/ok", None)]

    def test_surrounding_whitespace_trimmed(self):
        """Leading/trailing whitespace around the URL is removed"""
        result = parse_recording_links("   https://youtu.be/abc   ")
        assert result == [("https://youtu.be/abc", None)]

    def test_mixed_labelled_and_bare(self):
        """A mix of labelled and bare links is handled"""
        result = parse_recording_links(
            "https://youtu.be/1 | Full match\nhttps://youtu.be/2"
        )
        assert result == [
            ("https://youtu.be/1", "Full match"),
            ("https://youtu.be/2", None),
        ]

    def test_empty_text(self):
        """Empty input yields an empty list"""
        assert parse_recording_links("") == []

    def test_none_text(self):
        """None input is tolerated and yields an empty list"""
        assert parse_recording_links(None) == []
