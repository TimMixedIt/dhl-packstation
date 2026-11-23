"""Run the actual bundled web components in Chromium with HA state fixtures."""

import asyncio
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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
            assert await multi.locator(".station").evaluate_all(
                "items => items.map(item => item.getAttribute('aria-label'))"
            ) == ["Packstation 182", "Packstation 101", "Packstation 189"]
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
                            "element => [...element.shadowRoot.querySelectorAll('.grid,.tile,.metric,.compare-row')].every(el => el.scrollWidth <= el.clientWidth + 1)"
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
            await page.evaluate(
                "multi.setConfig({type:'custom:dhl-packstation-overview-card',stations:['1-67141189','1-missing','1-33104182','1-67141189']})"
            )
            assert await multi.locator(".station").evaluate_all(
                "items => items.map(item => item.getAttribute('aria-label'))"
            ) == ["Packstation 189", "Packstation 182"]
            checks.append(
                "selection, exact counts, stale, recovery, empty, escaped title and more-info"
            )
            await page.evaluate(
                "window.editor = document.createElement('dhl-packstation-card-editor'); editor.setConfig({type:'custom:dhl-packstation-card',station:'1-67141189'}); editor.hass=makeHass(); editor.addEventListener('config-changed',e=>window.edited=e.detail.config); document.querySelector('#editor').replaceChildren(editor)"
            )
            editor = page.locator("dhl-packstation-card-editor")
            assert await editor.locator('input[name="show_station_map"]').count() == 0
            await editor.locator('input[name="show_exact"]').check()
            assert await page.evaluate("window.edited.show_exact") is True
            await editor.locator('select[name="station"]').select_option("1-33104182")
            assert await page.evaluate("window.edited.station") == "1-33104182"
            await page.evaluate(
                """() => {
                    editor.setConfig({type:'custom:dhl-packstation-overview-card'});
                    editor.addEventListener('config-changed', e => multi.setConfig(e.detail.config));
                }"""
            )
            await editor.locator('input[name="stations"]').first.check()
            assert len(await page.evaluate("window.edited.stations")) == 1
            await editor.locator('input[name="stations"][value="1-67141189"]').check()
            up = editor.get_by_role(
                "button", name="Nach oben verschieben: Packstation 189", exact=False
            )
            await up.focus()
            await page.keyboard.press("Enter")
            assert await page.evaluate("window.edited.stations") == [
                "1-67141189",
                "1-33104182",
            ]
            assert await multi.locator(".station").evaluate_all(
                "items => items.map(item => item.getAttribute('aria-label'))"
            ) == ["Packstation 189", "Packstation 182"]
            assert await up.evaluate("el => el === el.getRootNode().activeElement")
            assert await up.is_disabled()
            await page.keyboard.press("Enter")
            assert await page.evaluate("window.edited.stations") == [
                "1-67141189",
                "1-33104182",
            ]
            down = editor.get_by_role(
                "button", name="Nach unten verschieben: Packstation 189", exact=False
            )
            await down.click()
            assert await page.evaluate("window.edited.stations") == [
                "1-33104182",
                "1-67141189",
            ]
            await up.click()
            await page.evaluate(
                """() => {
                    const saved = JSON.parse(JSON.stringify(window.edited));
                    editor.setConfig(saved);
                    multi.setConfig(saved);
                    const hass = makeHass();
                    for (const entity of Object.keys(hass.states)) {
                        if (hass.states[entity].attributes.dhl_packstation_id === '1-67141189') delete hass.states[entity];
                    }
                    editor.hass = hass;
                    multi.hass = hass;
                }"""
            )
            assert await multi.locator(".station").count() == 1
            missing = editor.get_by_role(
                "checkbox", name="Station nicht verfügbar · 1-67141189"
            )
            assert await missing.is_checked()
            await editor.locator('input[name="stations"][value="1-35460101"]').check()
            assert await page.evaluate("window.edited.stations") == [
                "1-67141189",
                "1-33104182",
                "1-35460101",
            ]
            await missing.click()
            assert await page.evaluate("window.edited.stations") == [
                "1-33104182",
                "1-35460101",
            ]
            assert await missing.count() == 0
            await page.evaluate(
                """() => {
                    const config={...window.edited,stations:['1-67141189', ...window.edited.stations]};
                    editor.setConfig(config);
                    multi.setConfig(config);
                }"""
            )
            await page.evaluate("editor.hass=makeHass(); multi.hass=makeHass()")
            assert await multi.locator(".station").evaluate_all(
                "items => items.map(item => item.getAttribute('aria-label'))"
            ) == ["Packstation 189", "Packstation 182", "Packstation 101"]
            for station_id in ["1-67141189", "1-33104182", "1-35460101"]:
                await editor.locator(
                    f'input[name="stations"][value="{station_id}"]'
                ).uncheck()
            assert await page.evaluate("window.edited.stations") == []
            assert await multi.locator(".station").evaluate_all(
                "items => items.map(item => item.getAttribute('aria-label'))"
            ) == ["Packstation 182", "Packstation 101", "Packstation 189"]
            checks.append(
                "visual editor order, keyboard focus, reload, missing station recovery and reset"
            )
            await page.evaluate(
                """() => {
                    const config={type:'custom:dhl-packstation-overview-card',stations:['1-67141189','1-33104182','1-35460101']};
                    editor.setConfig(config);
                    multi.setConfig(config);
                }"""
            )
            await page.set_viewport_size({"width": 320, "height": 1400})
            assert await editor.locator("fieldset").evaluate_all(
                "groups => groups.every(el => el.scrollWidth <= el.clientWidth + 1)"
            )
            await page.evaluate("single.hass=makeHass(); multi.hass=makeHass()")
            assert await single.locator(".week li").count() == 7
            assert await single.locator(".week li.missing").count() == 2
            assert await single.locator(".week li.none").count() == 1
            assert await single.locator(".station-summary strong").inner_text() == "29"
            await single.locator(".week").screenshot(
                path=str(artifact_dir / "weekday-trend.png")
            )

            station_row = multi.get_by_role(
                "region", name="Packstation 189", exact=True
            )
            details = station_row.locator(".station-toggle")
            assert await details.get_attribute("aria-expanded") == "false"
            await details.click()
            assert await details.get_attribute("aria-expanded") == "true"
            for service, host in [
                ("Apple Karten", "maps.apple.com"),
                ("Google Maps", "www.google.com"),
            ]:
                route = urlparse(
                    await station_row.get_by_role(
                        "link", name=f"{service} · Packstation 189"
                    ).get_attribute("href")
                )
                assert route.hostname == host
                assert parse_qs(route.query)["destination"] == ["49.42,8.41"]
            await details.click()

            tools = multi.locator("dhl-packstation-tools")
            alarm_button = tools.locator('[data-panel="alarm"]')
            map_button = tools.locator('[data-panel="map"]')
            alarm_switch = editor.get_by_role("switch", name="Paketalarm anzeigen")
            map_switch = editor.get_by_role("switch", name="Standortkarte anzeigen")
            assert await alarm_switch.is_checked() and await map_switch.is_checked()
            await map_switch.focus()
            await page.keyboard.press("Space")
            assert await page.evaluate("window.edited.show_station_map") is False
            assert await map_button.count() == 0 and await alarm_button.count() == 1
            await alarm_switch.uncheck()
            assert await page.evaluate("window.edited.show_package_alarm") is False
            assert not await tools.is_visible()
            assert await multi.locator(".station").count() == 3
            await alarm_switch.check()
            assert await alarm_button.count() == 1 and await map_button.count() == 0
            await map_switch.check()
            await page.evaluate("editor.setConfig(structuredClone(window.edited))")
            assert await alarm_switch.is_checked() and await map_switch.is_checked()
            assert await map_button.count() == 1
            assert not await page.evaluate("Boolean(window.mapConfig)")
            await alarm_button.focus()
            await page.keyboard.press("Enter")
            assert await alarm_button.get_attribute("aria-expanded") == "true"
            await tools.locator('input[name="s"]').fill("1")
            await tools.locator('input[name="m"]').fill("2")
            assert (
                await multi.locator(".compare-result").inner_text()
                == "1 von 3 Stationen passen"
            )
            assert await multi.locator(".compare-label").all_text_contents() == [
                "Passt",
                "Fehlt 1× S",
                "Daten fehlen",
            ]
            assert await tools.locator(".station-fit").all_text_contents() == [
                "Passt",
                "Fehlt 1× S",
                "Daten fehlen",
            ]
            assert await tools.locator('input[name="m"]').evaluate(
                "el => el === el.getRootNode().activeElement"
            )
            assert (
                await tools.locator('option[value="none"]').inner_text()
                == "HA-Glocke (ohne Push)"
            )
            assert await tools.locator('select[name="notifier"]').evaluate(
                "el => el.getBoundingClientRect().height >= 44"
            )
            for width in (320, 1024):
                await page.set_viewport_size({"width": width, "height": 1400})
                assert await tools.locator(".alarm").evaluate(
                    "el => el.scrollWidth <= el.clientWidth + 1"
                )
            await page.set_viewport_size({"width": 320, "height": 1400})
            assert "Eigene Messungen" in await single.locator(".week").inner_text()
            await page.evaluate(
                """() => {
                    const hass=makeHass();
                    delete hass.states["sensor.renamed_189_free_total"];
                    const entity=hass.states["sensor.renamed_189_source_timestamp"];
                    entity.state="unknown";
                    entity.attributes.dhl_weekday_utilization={sun:2,mon:1,fri:3,sat:4};
                    single.hass=hass;
                }"""
            )
            forecast = single.locator(".forecast")
            assert await forecast.locator(".trend-value").all_text_contents() == [
                "1",
                "–",
                "–",
                "–",
                "3",
                "–",
                "2",
            ]
            assert (
                await forecast.locator("li.level-3").get_attribute("aria-label")
                == "Fr, Hohe Auslastung"
            )
            await forecast.screenshot(path=str(artifact_dir / "dhl-forecast.png"))
            await page.evaluate("single.hass=makeHass()")
            assert await single.locator(".forecast").count() == 0
            await multi.locator(".compare").screenshot(
                path=str(artifact_dir / "comparison.png")
            )
            await tools.locator('select[name="notifier"]').select_option(
                "mobile_app_test_phone"
            )
            await tools.screenshot(path=str(artifact_dir / "package-alarm.png"))
            await tools.get_by_role("button", name="Suche starten").click()
            call = await page.evaluate("window.lastCall")
            assert call == {
                "domain": "dhl_packstation",
                "action": "start_alarm",
                "data": {
                    "s": 1,
                    "m": 2,
                    "l": 0,
                    "xl": 0,
                    "stations": ["1-67141189", "1-33104182", "1-35460101"],
                    "notifier": "mobile_app_test_phone",
                },
            }, call
            await page.evaluate("""() => {
                const hass = makeHass();
                hass.states["sensor.renamed_189_free_total"].attributes.alarm = {
                    status: "waiting", sizes: {s:1,m:2}, stations: ["1-67141189"]
                };
                multi.hass = hass;
            }""")
            await tools.get_by_role("button", name="Suche stoppen").click()
            assert await page.evaluate("window.lastCall.action") == "stop_alarm"
            assert (
                await alarm_button.locator(".tool-state").inner_text() == "Suche läuft"
            )
            await map_button.click()
            assert await alarm_button.get_attribute("aria-expanded") == "false"
            assert await map_button.get_attribute("aria-expanded") == "true"
            await tools.locator(".map-content ha-card").wait_for()
            assert await page.evaluate("window.mapConfig.type") == "map"
            assert (
                await page.evaluate("window.mapConfig.entities[0].label_mode")
                == "state"
            )
            assert (
                await page.evaluate("window.mapConfig.entities[0].entity")
                == "sensor.renamed_189_free_total"
            )
            assert await tools.locator(".map").get_by_role("link").count() == 2
            await alarm_button.click()
            assert not await tools.locator(".map").is_visible()
            await map_button.click()
            await tools.locator(".map-content ha-card").wait_for()
            assert await tools.locator(".map-content ha-card").count() == 1
            await map_switch.uncheck()
            assert await tools.locator(".map-content").count() == 0
            assert (
                await multi.get_by_role("region", name="Packstation 189", exact=True)
                .locator(".directions a")
                .count()
                == 2
            )
            await map_switch.check()
            checks.append(
                "independent switches, keyboard toolbar, alarm actions, DHL weekday outlook and lazy HA map"
            )
            axe_path = os.environ.get("AXE_CORE_PATH")
            if axe_path:
                await page.evaluate("""() => {
                    const hass = makeHass();
                    hass.states["sensor.renamed_189_source_timestamp"].attributes.dhl_weekday_utilization = {mon:1,tue:2,sun:3};
                    single.hass = hass;
                    multi.hass = hass;
                }""")
                await (
                    multi.get_by_role("region", name="Packstation 189", exact=True)
                    .locator(".station-toggle")
                    .click()
                )
                assert await multi.locator(".forecast").is_visible()
                await page.add_script_tag(path=axe_path)
                for panel in (alarm_button, map_button):
                    await panel.click()
                    violations = await page.evaluate(
                        "async () => (await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))"
                    )
                    assert not violations, json.dumps(violations)
                checks.append("axe WCAG 2.1 A/AA")
            await page.set_viewport_size({"width": 520, "height": 1800})
            await editor.screenshot(
                path=str(artifact_dir / "overview-order-editor.png")
            )
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
