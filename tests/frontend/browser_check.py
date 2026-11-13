"""Run the actual bundled web components in Chromium with HA state fixtures."""

import asyncio
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]


class QuietHandler(SimpleHTTPRequestHandler):
    """Serve only the repository fixture without noisy access logs."""

    def log_message(self, format, *args):
        pass


async def main():
    """Check layouts, state changes, keyboard controls, editor and accessibility."""
    artifact_dir = Path(os.environ.get("CARD_ARTIFACT_DIR", "/tmp/dhl-card-check"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietHandler, directory=ROOT)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    errors, checks = [], []
    try:
        async with async_playwright() as playwright:
            engine = os.environ.get("BROWSER_ENGINE", "chromium")
            assert engine in {"chromium", "webkit"}
            options = {"headless": True}
            if (channel := os.environ.get("BROWSER_CHANNEL")) and engine == "chromium":
                options["channel"] = channel
            browser = await getattr(playwright, engine).launch(**options)
            page = await browser.new_page(viewport={"width": 768, "height": 1400})
            page.on("pageerror", lambda error: errors.append(str(error)))
            await page.goto(
                f"http://127.0.0.1:{server.server_port}/tests/frontend/preview.html"
            )
            await page.evaluate("window.ready")
            single = page.locator("dhl-packstation-card")
            multi = page.locator("dhl-packstation-overview-card")
            assert await single.locator(".tile").count() == 4
            assert await multi.locator(".station").count() == 3
            assert await single.locator(".count").all_text_contents() == [
                "viele frei",
                "4 frei",
                "viele frei",
                "1 frei",
            ]
            assert "Daten veraltet" in await multi.locator("ha-card").inner_text()
            for theme in ["dark", "light"]:
                await page.evaluate(
                    "theme => document.body.classList.toggle('light', theme === 'light')",
                    theme,
                )
                for width in [320, 768, 1024, 1440]:
                    await page.set_viewport_size({"width": width, "height": 1600})
                    assert await page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                    for card in [single, multi]:
                        assert await card.evaluate(
                            "element => [...element.shadowRoot.querySelectorAll('.grid,.tile,.metric')].every(el => el.scrollWidth <= el.clientWidth + 1)"
                        )
                    checks.append(f"layout {theme} {width}px")
                await page.set_viewport_size({"width": 768, "height": 1600})
                await single.screenshot(path=str(artifact_dir / f"single-{theme}.png"))
                await multi.screenshot(path=str(artifact_dir / f"overview-{theme}.png"))
            await page.evaluate("document.body.classList.remove('light')")
            dimensions = {}
            for viewport in [400, 1920]:
                await page.set_viewport_size({"width": viewport, "height": 1600})
                for card_width in [280, 320, 360]:
                    await page.locator("main").evaluate(
                        "(el, width) => el.style.maxWidth = `${width}px`", card_width
                    )
                    geometry = await single.evaluate("""element => {
                        const root = element.shadowRoot;
                        const shapes = [...root.querySelectorAll('.shape')];
                        return {
                            contained: shapes.every(el => {
                                const shape = el.getBoundingClientRect();
                                const range = document.createRange();
                                range.selectNodeContents(el);
                                const label = range.getBoundingClientRect();
                                return label.top >= shape.top - 1 && label.bottom <= shape.bottom + 1
                                    && label.left >= shape.left - 1 && label.right <= shape.right + 1;
                            }),
                            tileHeight: root.querySelector('.tile').getBoundingClientRect().height,
                            shapeFont: getComputedStyle(shapes[0]).fontSize,
                            bodyPadding: getComputedStyle(root.querySelector('.body')).paddingLeft,
                        };
                    }""")
                    assert geometry["contained"], (
                        engine,
                        viewport,
                        card_width,
                        geometry,
                    )
                    if viewport == 400:
                        dimensions[card_width] = geometry
                    else:
                        assert geometry == dimensions[card_width], (
                            card_width,
                            geometry,
                            dimensions[card_width],
                        )
                checks.append(f"narrow cards 280/320/360px in {viewport}px viewport")
            await page.locator("main").evaluate("el => el.style.maxWidth = '360px'")
            await single.screenshot(path=str(artifact_dir / "single-narrow.png"))
            await page.locator("main").evaluate("el => el.style.maxWidth = '600px'")
            await single.locator("summary").focus()
            await page.keyboard.press("Enter")
            assert not await single.locator("details").get_attribute("open") == ""
            await page.evaluate("single.hass = {...demoHass}")
            assert await single.locator("summary").evaluate(
                "el => el === el.getRootNode().activeElement"
            )
            await page.keyboard.press("Enter")
            assert await single.locator("details").get_attribute("open") == ""
            await single.locator('[data-action="info"]').click()
            assert await single.locator("dialog").evaluate("el => el.open")
            await page.keyboard.press("Escape")
            assert not await single.locator("dialog").evaluate("el => el.open")
            checks.append("keyboard accordion and modal")
            await page.evaluate(
                "single.addEventListener('hass-more-info', e => window.moreInfo = e.detail.entityId)"
            )
            await single.locator(".tile").first.click()
            assert await page.evaluate("window.moreInfo") == "sensor.renamed_189_free_s"
            await page.evaluate(
                "single.setConfig({type:'custom:dhl-packstation-card',station:'1-67141189',show_exact:true})"
            )
            assert await single.locator(".count").first.inner_text() == "17 frei"
            await page.evaluate(
                "demoHass.states.sensor_ignored = {state:'0',attributes:{}}; single.hass={...demoHass}"
            )
            assert await single.locator(".tile").count() == 4
            await page.evaluate(
                "demoHass.states.sensor_ignored = undefined; delete demoHass.states.sensor_ignored; demoHass.states['sensor.renamed_189_stale_data'].state='on'; single.hass={...demoHass}"
            )
            assert await single.locator(".tile.unknown").count() == 4
            await page.evaluate(
                "demoHass.states['sensor.renamed_189_stale_data'].state='off'; single.hass={...demoHass}"
            )
            assert await single.locator(".tile.available").count() == 4
            await page.evaluate(
                "single.setConfig({type:'custom:dhl-packstation-card',station:'1-missing'})"
            )
            assert "nicht verfügbar" in await single.locator("ha-card").inner_text()
            await page.evaluate(
                "single.setConfig({type:'custom:dhl-packstation-card',title:'<img src=x onerror=alert(1)>'}); single.hass={states:{},locale:{language:'de'}}"
            )
            assert await single.locator("img").count() == 0
            assert "keine Packstation" in await single.locator("ha-card").inner_text()
            await page.evaluate(
                "single.hass=makeHass(); single.setConfig({type:'custom:dhl-packstation-card',station:'1-67141189'})"
            )
            await page.evaluate(
                "multi.setConfig({type:'custom:dhl-packstation-overview-card',stations:['1-67141189']})"
            )
            assert await multi.locator(".station").count() == 1
            checks.append(
                "selection, exact counts, stale, recovery, empty, escaped title and more-info"
            )
            await page.evaluate(
                "window.editor = document.createElement('dhl-packstation-card-editor'); editor.setConfig({type:'custom:dhl-packstation-card',station:'1-67141189'}); editor.hass=makeHass(); editor.addEventListener('config-changed',e=>window.edited=e.detail.config); document.querySelector('#editor').replaceChildren(editor)"
            )
            editor = page.locator("dhl-packstation-card-editor")
            await editor.locator('input[name="show_exact"]').check()
            assert await page.evaluate("window.edited.show_exact") is True
            await editor.locator('select[name="station"]').select_option("1-33104182")
            assert await page.evaluate("window.edited.station") == "1-33104182"
            await page.evaluate(
                "editor.setConfig({type:'custom:dhl-packstation-overview-card'})"
            )
            await editor.locator('input[name="stations"]').first.check()
            assert len(await page.evaluate("window.edited.stations")) == 1
            checks.append("visual editor station and overview selections")
            axe_path = os.environ.get("AXE_CORE_PATH")
            if axe_path:
                await page.add_script_tag(path=axe_path)
                violations = await page.evaluate(
                    "async () => (await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))"
                )
                assert not violations, json.dumps(violations)
                checks.append("axe WCAG 2.1 A/AA")
            assert not errors, errors
            await browser.close()
    finally:
        server.shutdown()
        server.server_close()
    result = {
        "engine": engine,
        "checks": checks,
        "console_errors": errors,
        "fixtures": True,
    }
    (artifact_dir / "browser-results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
