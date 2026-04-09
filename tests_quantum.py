"""
Unit tests for Quantum Playground — DARPA Family Day 2026
GitHub Engineering Office — Tetrabolt LLC
"""
import os
import re
import pytest
from html.parser import HTMLParser

# ── Fixtures ──────────────────────────────────────────────────────────────────

HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")

@pytest.fixture(scope="session")
def html_content():
    with open(HTML_PATH, encoding="utf-8") as f:
        return f.read()


class StructureParser(HTMLParser):
    """Parse HTML into useful lookup structures."""

    def __init__(self):
        super().__init__()
        self.tags = []          # list of (tag, attrs_dict)
        self.buttons = []       # list of (attrs_dict, text)
        self._current_button_text = None
        self._in_button = False
        self.links = []         # all <a href> and <link href>
        self.scripts = []       # all <script src>
        self.title_text = ""
        self._in_title = False
        self.style_blocks = []  # inline <style> content
        self._current_style = ""
        self._in_style = False
        self.footer_text = ""
        self._in_footer = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        self.tags.append((tag, d))

        if tag == "button":
            self._in_button = True
            self._current_button_text = ""
            self.buttons.append([d, ""])  # will update text later

        if tag == "title":
            self._in_title = True

        if tag == "style":
            self._in_style = True
            self._current_style = ""

        if tag in ("a", "link"):
            self.links.append(d)

        if tag == "script":
            self.scripts.append(d)

        if tag == "footer":
            self._in_footer = True
            self._footer_buf = ""

    def handle_endtag(self, tag):
        if tag == "button":
            self._in_button = False
        if tag == "title":
            self._in_title = False
        if tag == "style":
            self.style_blocks.append(self._current_style)
            self._in_style = False
        if tag == "footer":
            self._in_footer = False
            self.footer_text = getattr(self, "_footer_buf", "")

    def handle_data(self, data):
        if self._in_button and self.buttons:
            self.buttons[-1][1] += data
        if self._in_title:
            self.title_text += data
        if self._in_style:
            self._current_style += data
        if self._in_footer:
            self._footer_buf = getattr(self, "_footer_buf", "") + data


@pytest.fixture(scope="session")
def parsed(html_content):
    p = StructureParser()
    p.feed(html_content)
    return p


# ── Structure Tests ───────────────────────────────────────────────────────────

class TestStructure:

    def test_file_exists(self):
        assert os.path.isfile(HTML_PATH), "index.html must exist"

    def test_file_over_500_lines(self):
        with open(HTML_PATH) as f:
            lines = f.readlines()
        assert len(lines) > 500, f"Expected >500 lines, got {len(lines)}"

    def test_five_tab_sections(self, html_content):
        # Tab panels are <div id="tab1"> … <div id="tab5">
        tab_ids = re.findall(r'id=["\']tab(\d)["\']', html_content)
        unique_tabs = set(tab_ids)
        # Should have tab1 through tab5
        assert unique_tabs == {"1", "2", "3", "4", "5"}, (
            f"Expected tabs 1-5, found IDs: {unique_tabs}"
        )

    def test_five_tab_buttons(self, html_content):
        """Tab bar should have exactly 5 tab buttons."""
        tab_buttons = re.findall(r'data-tab=["\'](\d)["\']', html_content)
        assert len(tab_buttons) == 5, f"Expected 5 tab buttons, got {len(tab_buttons)}"

    def test_tab_names_present(self, html_content):
        expected = ["How To Play", "Coin Flip", "Entanglement", "Quantum Race", "Code Breaker"]
        for name in expected:
            assert name in html_content, f"Tab name '{name}' not found in HTML"

    def test_header_quantum_playground(self, html_content):
        assert "QUANTUM PLAYGROUND" in html_content, "Header must contain 'QUANTUM PLAYGROUND'"

    def test_footer_tetrabolt(self, html_content):
        assert "Tetrabolt LLC" in html_content, "Footer/page must contain 'Tetrabolt LLC'"

    def test_footer_darpa_family_day(self, html_content):
        assert "DARPA Family Day 2026" in html_content, "Footer must contain 'DARPA Family Day 2026'"

    def test_canvas_starfield(self, parsed):
        canvases = [(t, a) for t, a in parsed.tags if t == "canvas"]
        assert any(a.get("id") == "starfield" for _, a in canvases), (
            "Must have <canvas id='starfield'>"
        )

    def test_page_title_set(self, parsed):
        assert parsed.title_text.strip() != "", "Page <title> must not be empty"


# ── Offline / Security Tests ──────────────────────────────────────────────────

class TestOfflineSecurity:

    # Strip HTML comments so we don't flag URLs that are only in comments
    @pytest.fixture(scope="class")
    def html_no_comments(self, html_content):
        return re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)

    def test_no_external_src_href(self, html_no_comments):
        """src= and href= attributes must not point to http(s):// URLs."""
        # Match src="http..." or href="http..."
        matches = re.findall(
            r'(?:src|href)\s*=\s*["\']https?://[^"\']+["\']',
            html_no_comments,
            re.IGNORECASE
        )
        assert matches == [], f"Found external src/href URLs: {matches}"

    def test_no_cdn_links(self, html_no_comments):
        cdn_patterns = [
            r'cdn\.jsdelivr', r'unpkg\.com', r'cdnjs\.cloudflare',
            r'fonts\.googleapis', r'ajax\.googleapis', r'stackpath\.bootstrapcdn',
            r'maxcdn\.bootstrapcdn', r'code\.jquery'
        ]
        for pat in cdn_patterns:
            matches = re.findall(pat, html_no_comments, re.IGNORECASE)
            assert matches == [], f"Found CDN reference ({pat}): {matches}"

    def test_no_external_font_imports(self, html_no_comments):
        """No @import url(...) or <link rel=stylesheet href=external>."""
        # CSS @import with http
        css_imports = re.findall(
            r'@import\s+url\s*\(["\']?https?://', html_no_comments, re.IGNORECASE
        )
        assert css_imports == [], f"Found external @import: {css_imports}"

        # <link rel="stylesheet" href="https://...">
        link_stylesheets = re.findall(
            r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']https?://[^"\']+["\']',
            html_no_comments, re.IGNORECASE
        )
        link_stylesheets += re.findall(
            r'<link[^>]+href=["\']https?://[^"\']+["\'][^>]+rel=["\']stylesheet["\']',
            html_no_comments, re.IGNORECASE
        )
        assert link_stylesheets == [], f"Found external stylesheet links: {link_stylesheets}"

    def test_no_external_script_src(self, html_no_comments):
        """<script src="https://..."> is forbidden."""
        matches = re.findall(
            r'<script[^>]+src=["\']https?://[^"\']+["\']',
            html_no_comments, re.IGNORECASE
        )
        assert matches == [], f"Found external script src: {matches}"

    def test_no_eval_calls(self, html_content):
        """eval() must not appear in JavaScript."""
        # Exclude occurrences inside HTML comments
        no_comments = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        matches = re.findall(r'\beval\s*\(', no_comments)
        assert matches == [], f"Found eval() calls: {matches}"

    def test_no_document_write(self, html_content):
        """document.write() must not be used."""
        no_comments = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        matches = re.findall(r'document\.write\s*\(', no_comments)
        assert matches == [], f"Found document.write() calls: {matches}"

    def test_no_string_based_event_handlers(self, html_content):
        """Inline event handlers must not call eval() with strings."""
        matches = re.findall(
            r'on\w+=["\'][^"\']*\beval\s*\([^)]*["\'][^"\']*["\']',
            html_content, re.IGNORECASE
        )
        assert matches == [], f"Found eval in inline handlers: {matches}"


# ── Feature Tests ─────────────────────────────────────────────────────────────

class TestFeatures:

    def test_coin_flip_prepare_qubit_button(self, html_content):
        # Button text contains "Prepare Qubit"
        assert "Prepare Qubit" in html_content, "Coin Flip: 'Prepare Qubit' button missing"

    def test_coin_flip_measure_button(self, html_content):
        assert "Measure" in html_content, "Coin Flip: 'Measure' button missing"

    def test_coin_flip_coin_div(self, html_content):
        # coins-row div is where coins are injected
        assert 'id="coins-row"' in html_content or "id='coins-row'" in html_content, (
            "Coin Flip: coins-row element missing"
        )

    def test_entanglement_entangle_button(self, html_content):
        assert "Entangle" in html_content, "Entanglement: 'Entangle' button missing"

    def test_entanglement_distance_slider(self, html_content):
        # input[type="range"] with id distance-slider
        assert 'id="distance-slider"' in html_content or "id='distance-slider'" in html_content, (
            "Entanglement: distance slider (input[type=range] #distance-slider) missing"
        )

    def test_entanglement_alice_element(self, html_content):
        assert "Alice" in html_content, "Entanglement: Alice element missing"

    def test_entanglement_bob_element(self, html_content):
        assert "Bob" in html_content, "Entanglement: Bob element missing"

    def test_quantum_race_maze_grid(self, html_content):
        assert "maze-grid" in html_content, "Quantum Race: maze-grid element missing"

    def test_quantum_race_race_button(self, html_content):
        assert "RACE" in html_content or "Race" in html_content, (
            "Quantum Race: Race button missing"
        )

    def test_quantum_race_classical_panel(self, html_content):
        assert "Classical" in html_content, "Quantum Race: Classical panel missing"

    def test_quantum_race_quantum_panel(self, html_content):
        # "Quantum" clearly appears throughout but specifically in race context
        assert 'id="classical-maze"' in html_content or "id='classical-maze'" in html_content, (
            "Quantum Race: classical-maze panel missing"
        )
        assert 'id="quantum-maze"' in html_content or "id='quantum-maze'" in html_content, (
            "Quantum Race: quantum-maze panel missing"
        )

    def test_code_breaker_vault_element(self, html_content):
        assert "vault" in html_content, "Code Breaker: vault element missing"

    def test_code_breaker_classical_crack_button(self, html_content):
        assert "Classical Crack" in html_content, "Code Breaker: 'Classical Crack' button missing"

    def test_code_breaker_quantum_crack_button(self, html_content):
        assert "Quantum Crack" in html_content, "Code Breaker: 'Quantum Crack' button missing"

    def test_code_breaker_quantum_safe_section(self, html_content):
        assert "quantum-safe" in html_content, "Code Breaker: quantum-safe section missing"

    def test_how_to_play_lets_play_button(self, html_content):
        # "Let's Play" may be encoded as "Let&#39;s Play" or "Let's Play"
        assert ("Let's Play" in html_content or
                "Let&#39;s Play" in html_content or
                "Let\u2019s Play" in html_content), (
            "How To Play: \"Let's Play\" button missing"
        )

    def test_wolfssl_mentioned(self, html_content):
        assert "wolfSSL" in html_content, "wolfSSL must be mentioned in the HTML"


# ── Accessibility / UX Tests ──────────────────────────────────────────────────

class TestAccessibilityUX:

    def test_all_buttons_have_text(self, parsed):
        empty_buttons = []
        for attrs, text in parsed.buttons:
            if text.strip() == "":
                empty_buttons.append(attrs)
        assert empty_buttons == [], f"Found buttons with no text content: {empty_buttons}"

    def test_no_tiny_font_size_on_buttons(self, html_content):
        """No button should have an inline style with font-size < 14px."""
        # Match inline style="...font-size: Xpx..." on button tags
        button_styles = re.findall(
            r'<button[^>]+style=["\'][^"\']*font-size\s*:\s*([\d.]+)px[^"\']*["\']',
            html_content, re.IGNORECASE
        )
        for size_str in button_styles:
            size = float(size_str)
            assert size >= 14, f"Button has font-size {size}px — below 14px minimum"

    def test_page_title_is_set(self, parsed):
        assert parsed.title_text.strip() != "", "Page <title> must be non-empty"
        assert len(parsed.title_text.strip()) > 3, (
            f"Page title too short: '{parsed.title_text.strip()}'"
        )
