"""Real-browser smoke checks. Start Streamlit, then run this script."""

import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []
    screenshots = ROOT / "docs"
    screenshots.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200}, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:8501")
        classify = page.get_by_role("button", name="Classify ticket", exact=True)
        expect(classify).to_be_visible(timeout=30000)
        classify.click()
        expect(page.get_by_text("Top model score", exact=True)).to_be_visible(timeout=30000)
        expect(page.get_by_test_id("stMetricValue").first).to_contain_text("%")
        expect(page.get_by_text("Card arrival", exact=True)).to_be_visible()
        page.screenshot(path=str(screenshots / "triage-desktop.png"), full_page=True)
        checks.append("Single-ticket classification, real result and desktop screenshot")

        combo = page.get_by_role("combobox").first
        combo.focus()
        combo.press("ArrowDown")
        expect(page.get_by_role("listbox")).to_be_visible()
        combo.press("Escape")
        checks.append("Example select opens by keyboard and closes with Escape")
        page.get_by_role("button", name="Add to review queue", exact=True).click()
        expect(
            page.get_by_text("Added to review queue. Open Review queue in the sidebar.")
        ).to_be_visible()
        page.get_by_test_id("stSidebar").get_by_text("Review queue", exact=True).click()
        expect(page.get_by_role("button", name="Save review")).to_be_visible()
        page.get_by_role("button", name="Save review").click()
        expect(
            page.get_by_text("All queued tickets have been reviewed. Export the feedback below.")
        ).to_be_visible()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Export review records").click()
        assert download_info.value.suggested_filename == "supportflow_reviews.csv"
        checks.append("Review record saved and CSV export starts")

        page.get_by_test_id("stSidebar").get_by_text("Triage ticket", exact=True).click()
        field = page.get_by_role("textbox", name="Customer message")
        field.fill("help")
        page.get_by_role("button", name="Classify ticket", exact=True).click()
        expect(
            page.get_by_text("Enter at least three words so the model has enough context.")
        ).to_be_visible()
        checks.append("Invalid short input shows corrective error")

        page.get_by_test_id("stSidebar").get_by_text("Batch desk", exact=True).click()
        expect(
            page.get_by_text(
                "Choose a CSV to begin. Only the text column is used; other columns are ignored."
            )
        ).to_be_visible()
        uploader = page.locator('input[type="file"]')
        uploader.set_input_files(
            {"name": "invalid.csv", "mimeType": "text/csv", "buffer": b"message\nhello"}
        )
        expect(
            page.get_by_text(
                "The CSV needs a column named text. Download the sample to get started."
            )
        ).to_be_visible()
        uploader.set_input_files(
            {
                "name": "tickets.csv",
                "mimeType": "text/csv",
                "buffer": b'text\nWhere is my card\n""\nI was charged twice at a shop\n',
            }
        )
        page.get_by_role("button", name="Classify batch", exact=True).click()
        expect(page.get_by_text("Invalid tickets", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Download all results")).to_be_visible()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Download all results").click()
        assert download_info.value.suggested_filename == "supportflow_predictions.csv"
        page.screenshot(path=str(screenshots / "batch-desktop.png"), full_page=True)
        checks.append("CSV empty/error/success states, invalid row preservation and export")

        page.get_by_test_id("stSidebar").get_by_text("Model report", exact=True).click()
        expect(page.get_by_text("Test macro-F1", exact=True)).to_be_visible()
        expect(page.get_by_text("Model comparison", exact=True)).to_be_visible()
        page.screenshot(path=str(screenshots / "report-desktop.png"), full_page=True)
        assert page.locator("html").evaluate("el => getComputedStyle(el).scrollbarColor") != "auto"
        checks.append("Evaluation page, global scrollbar theme and reduced-motion mode")

        mobile = browser.new_page(viewport={"width": 390, "height": 1000}, reduced_motion="reduce")
        mobile.goto("http://127.0.0.1:8501")
        expect(mobile.get_by_role("button", name="Classify ticket", exact=True)).to_be_visible(
            timeout=30000
        )
        mobile.get_by_role("button", name="Classify ticket", exact=True).click()
        expect(mobile.get_by_text("Top model score", exact=True)).to_be_visible(timeout=30000)
        mobile.get_by_role(
            "button", name="Add to review queue", exact=True
        ).scroll_into_view_if_needed()
        expect(
            mobile.get_by_role("button", name="Add to review queue", exact=True)
        ).to_be_in_viewport()
        mobile.get_by_test_id("stMain").evaluate("el => el.scrollTo(0, 0)")
        assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        mobile.screenshot(path=str(screenshots / "triage-mobile.png"), full_page=True)
        checks.append("390px viewport has no page-width overflow; lower action remains reachable")
        assert not errors, errors
        browser.close()
    report = {
        "passed": checks,
        "page_errors": errors,
        "browser": "Microsoft Edge (Chromium)",
        "viewports": ["1440x1200", "390x1000"],
        "reduced_motion": True,
    }
    (ROOT / "reports" / "browser_checks.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
