"""Browser tests for the match page.

Every test here exists because a unit test could not have caught the bug:

- drag-and-drop used to navigate the whole page away and back
- the drag listeners were bound twice, and were lost whenever HTMX replaced
  the pitch markup
- the captain dropdowns stretched the full page width

Measuring scroll needs care in both directions:

- Playwright's ``click()`` scrolls the target into view first, which would move
  the page before the code under test runs. ``click_in_place`` parks the element
  in view *first*, so the later click cannot scroll anything.
- Clicking through ``evaluate("el => el.click()")`` avoids that problem but
  never gives the element focus, and focus is exactly what made the page jump.
  Anything asserting about scrolling has to use a real click.
"""

import pytest

pytestmark = pytest.mark.e2e


# Reads the slots of one pitch. Both teams render the same position codes
# (GK, LB, ...), so a document-wide lookup would mix the two sides up.
PITCH_SLOTS = """(index) => {
    const pitch = document.querySelectorAll('.single-pitch-container')[index];
    return [...pitch.querySelectorAll('.position-slot')].map(el => ({
        position: el.dataset.position,
        playerId: el.dataset.playerId || null,
    }));
}"""

# HTML5 drag-and-drop cannot be driven by mouse movement alone -- the events
# have to be dispatched with a shared DataTransfer.
DRAG = """([from, to]) => {
    const slots = document.querySelectorAll('.position-slot.draggable-player');
    const transfer = new DataTransfer();
    const fire = (el, type) => el.dispatchEvent(
        new DragEvent(type, {bubbles: true, cancelable: true, dataTransfer: transfer}));
    fire(slots[from], 'dragstart');
    fire(slots[to], 'dragenter');
    fire(slots[to], 'dragover');
    fire(slots[to], 'drop');
    fire(slots[from], 'dragend');
}"""


def swaps_so_far(page):
    return page.evaluate("window.__htmxSettles || 0")


def wait_for_swap(page, before):
    """Block until one more HTMX swap has settled.

    Waiting on the actual event rather than a fixed duration keeps these tests
    honest on a slow CI runner and quick on a fast laptop.
    """
    page.wait_for_function(
        "before => (window.__htmxSettles || 0) > before", arg=before, timeout=15000
    )


def click_in_place(page, selector, viewport_y=350):
    """Really click an element, with the page scrolled down and nothing moving.

    The element is parked `viewport_y` pixels down the viewport first. That
    matters twice over: the element is already visible so Playwright's click
    cannot scroll to reach it, and the page is genuinely scrolled down, which is
    the only situation where a stray scroll is visible at all. At the very top
    the page has nowhere to jump to and any bug hides.

    A real click also leaves focus on the element -- driving it through
    ``evaluate("el => el.click()")`` skips focus entirely and hides the very
    thing these tests exist to catch.

    Returns:
        int: window.scrollY at the moment of the click
    """
    element = page.locator(selector)
    element.scroll_into_view_if_needed()
    box = element.bounding_box()
    page.evaluate(f"window.scrollBy(0, {box['y'] - viewport_y})")

    before = swaps_so_far(page)
    scroll_at_click = page.evaluate("window.scrollY")
    element.click()
    wait_for_swap(page, before)
    return scroll_at_click


def drag(page, from_index, to_index):
    """Drag one pitch slot onto another and wait for the swap to land"""
    before = swaps_so_far(page)
    page.evaluate(DRAG, [from_index, to_index])
    wait_for_swap(page, before)


def allocate(page):
    click_in_place(page, "text=Allocate Teams")


def by_position(slots):
    return {slot["position"]: slot["playerId"] for slot in slots}


def pick_other_captain(page):
    """Choose a captain option other than the current one, and return its value"""
    return page.evaluate("""() => {
        const select = document.querySelector('select[name="captain_id"]');
        return [...select.options].find(
            o => o.value && o.value !== select.value).value;
    }""")


def park_at(page, locator, viewport_y=350):
    """Scroll so an element sits `viewport_y` px down the viewport"""
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    page.evaluate(f"window.scrollBy(0, {box['y'] - viewport_y})")


class TestDragAndDrop:
    def test_swapping_players_does_not_reload_the_page(self, page):
        allocate(page)
        page.evaluate("window.__stillHere = true")

        before = swaps_so_far(page)
        page.evaluate(DRAG, [0, 3])
        wait_for_swap(page, before)

        assert page.evaluate("window.__stillHere") is True, "page navigated away"

    def test_swapping_players_exchanges_their_positions(self, page):
        allocate(page)
        slots = page.evaluate(PITCH_SLOTS, 0)
        source, target = slots[0], slots[3]

        drag(page, 0, 3)

        after = by_position(page.evaluate(PITCH_SLOTS, 0))
        assert after[source["position"]] == target["playerId"]
        assert after[target["position"]] == source["playerId"]

    def test_drag_still_works_after_the_pitch_is_replaced(self, page):
        """Regression: listeners were bound per element and lost on every swap"""
        allocate(page)
        drag(page, 0, 3)

        slots = page.evaluate(PITCH_SLOTS, 0)
        source, target = slots[1], slots[4]
        drag(page, 1, 4)

        after = by_position(page.evaluate(PITCH_SLOTS, 0))
        assert after[source["position"]] == target["playerId"]
        assert after[target["position"]] == source["playerId"]

    def test_drag_does_not_move_the_page(self, page):
        allocate(page)
        page.evaluate("window.scrollTo(0, 700)")
        scroll_before = page.evaluate("window.scrollY")

        drag(page, 0, 3)

        assert page.evaluate("window.scrollY") == scroll_before


class TestAllocateAndReset:
    def test_allocate_fills_both_teams(self, page):
        allocate(page)
        pitches = page.locator(".single-pitch-container")
        assert pitches.count() == 2
        occupied = page.evaluate(
            "() => document.querySelectorAll('.position-slot[data-player-id]').length"
        )
        assert occupied > 0

    def test_allocate_does_not_reload_the_page(self, page):
        page.evaluate("window.__stillHere = true")
        allocate(page)
        assert page.evaluate("window.__stillHere") is True

    def test_allocate_does_not_move_the_page(self, page):
        """Regression: the clicked button kept focus while the swap deleted it,
        so the browser went hunting for a focus target and scrolled 1800px."""
        allocate(page)
        before = click_in_place(page, "text=Allocate Teams")

        assert page.evaluate("window.scrollY") == before

    def test_reset_does_not_move_the_page(self, page):
        allocate(page)
        before = click_in_place(page, "text=Reset Teams")

        assert page.evaluate("window.scrollY") == before

    def test_reset_empties_the_teams(self, page):
        allocate(page)
        click_in_place(page, "text=Reset Teams")

        occupied = page.evaluate(
            "() => document.querySelectorAll('.position-slot[data-player-id]').length"
        )
        assert occupied == 0

    def test_allocating_twice_produces_different_teams(self, page):
        """The whole point of the allocation rewrite: no more identical teams"""
        seen = set()
        for _ in range(6):
            allocate(page)
            slots = page.evaluate(PITCH_SLOTS, 0)
            seen.add(frozenset(s["playerId"] for s in slots if s["playerId"]))

        assert len(seen) > 1


class TestCaptainSelection:
    def test_both_teams_have_a_captain_after_allocating(self, page):
        """Regression: re-allocating left one team's dropdown empty"""
        allocate(page)
        values = page.evaluate(
            "() => [...document.querySelectorAll('select[name=\"captain_id\"]')]"
            ".map(s => s.value)"
        )
        assert len(values) == 2
        assert all(v for v in values), f"a team has no captain: {values}"

    def test_captain_badge_shows_on_the_pitch(self, page):
        allocate(page)
        badges = page.evaluate(
            "() => [...document.querySelectorAll('.position-slot div')]"
            ".filter(d => d.textContent.trim() === 'C').length"
        )
        assert badges >= 2

    def test_dropdowns_sit_side_by_side(self, page):
        allocate(page)
        boxes = page.locator('select[name="captain_id"]').all()
        assert len(boxes) == 2

        first, second = boxes[0].bounding_box(), boxes[1].bounding_box()
        assert abs(first["y"] - second["y"]) < 5, "not on the same row"
        assert abs(first["width"] - second["width"]) < 5, "different widths"

        page_width = page.evaluate("document.documentElement.clientWidth")
        assert first["width"] < page_width * 0.55, "still spanning the page"

        left_gap = first["x"]
        right_gap = page_width - (second["x"] + second["width"])
        assert abs(left_gap - right_gap) < 6, "not symmetric"

    def test_dropdowns_stack_on_a_narrow_screen(self, page):
        allocate(page)
        page.set_viewport_size({"width": 420, "height": 900})
        # Wait for the reflow rather than guessing at how long it takes: the
        # dropdown has to be narrower than the old desktop column before the
        # positions below mean anything.
        page.wait_for_function(
            "() => document.querySelector('select[name=\"captain_id\"]')"
            ".getBoundingClientRect().width < 420"
        )

        boxes = page.locator('select[name="captain_id"]').all()
        first, second = boxes[0].bounding_box(), boxes[1].bounding_box()
        assert second["y"] > first["y"] + 20, "should stack vertically"

    def test_choosing_a_captain_does_not_move_the_page(self, page):
        """Same focus trap as the buttons: the select holds focus when the user
        picks an option, and the swap that follows deletes it."""
        allocate(page)
        select = page.locator('select[name="captain_id"]').first
        park_at(page, select)
        scroll_before = page.evaluate("window.scrollY")

        chosen = pick_other_captain(page)
        swap_before = swaps_so_far(page)
        # select_option focuses the element, the way a real user does
        select.select_option(chosen)
        wait_for_swap(page, swap_before)

        assert page.evaluate("window.scrollY") == scroll_before
        assert (
            page.evaluate("document.querySelector('select[name=\"captain_id\"]').value")
            == chosen
        )


class TestSwapKeepsTheViewStill:
    """The mechanism behind the scroll jumps, asserted directly.

    Whether a stray scroll is *visible* depends on how much page is left below
    the element -- a control near the bottom has nowhere to jump to, so a
    position-based test quietly passes even when the bug is present. Checking
    that focus is gone before the swap holds regardless of page geometry.
    """

    WATCH_FOCUS = """() => {
        window.__focusedInsideTarget = null;
        // Registered after the app's own listener, so it sees the state the
        // browser will actually face when the swap runs.
        document.addEventListener('htmx:beforeSwap', function(event) {
            var active = document.activeElement;
            window.__focusedInsideTarget = !!(
                active && active !== document.body &&
                event.detail.target.contains(active)
            );
        });
    }"""

    def test_button_focus_is_dropped_before_the_swap(self, page):
        allocate(page)
        page.evaluate(self.WATCH_FOCUS)

        click_in_place(page, "text=Allocate Teams")

        assert page.evaluate("window.__focusedInsideTarget") is False, (
            "the clicked button still held focus when the swap deleted it"
        )

    def test_select_focus_is_dropped_before_the_swap(self, page):
        allocate(page)
        page.evaluate(self.WATCH_FOCUS)

        select = page.locator('select[name="captain_id"]').first
        select.scroll_into_view_if_needed()
        chosen = pick_other_captain(page)
        swap_before = swaps_so_far(page)
        # Opening a dropdown focuses it; select_option on its own does not
        select.focus()
        select.select_option(chosen)
        wait_for_swap(page, swap_before)

        assert page.evaluate("window.__focusedInsideTarget") is False, (
            "the captain select still held focus when the swap deleted it"
        )


class TestPageHealth:
    def test_match_page_has_no_console_errors_or_failed_requests(self, page):
        allocate(page)
        assert page.console_errors == []
        assert page.failed_requests == []
