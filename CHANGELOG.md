# Changelog

## 0.4.0b2

- Support DeinFach lockers listed by DHL, including live compartment counts when DHL provides them.
- Start a persistent one-time package alarm for a mix of exact sizes from the overview card.
- Show total free compartments, Home Assistant long-term statistics, and a measured weekday trend.
- Add postal-code search for nearby lockers and show configured stations on the map.

## 0.3.0

- Set a custom station order in the overview card using the existing `stations` list or the up and down buttons in the visual editor.

## 0.2.0

- First stable release, promoting the tested 0.2.0b2 functionality without runtime changes.
- Regular GitHub release for installation without opting into prereleases.
- Updated version metadata and installation instructions; existing station entries, entity identities and dashboard configurations are retained.

## 0.2.0b2

- Size cards by their own width instead of the browser viewport, fixing stretched compartments and excessive padding in narrow Home Assistant dashboard columns.
- Keep compartment labels inside their yellow shapes with explicit line height, minimum shape height and stable grid rows, including Safari/WebKit.
- Test 280/320/360px cards inside both 400px and 1920px viewports, including label geometry and consistent sizing.
- Run the browser regression suite in both Chromium and WebKit.

## 0.2.0b1

First public beta, for field testing through a custom Marketplace/HACS repository.

- Included single-station dashboard card with yellow compartment shapes, availability icons, timestamp and help dialog.
- Included multi-station comparison card with independent availability and freshness per station.
- Automatic loading, card picker entries and visual editors; no separate frontend repository or manual resource configuration.
- Optional exact counts, light/dark themes, keyboard controls and responsive layouts.
- Stable discovery metadata keeps cards working after entity renames or language changes.
- HTTP serving, card logic, browser behavior and accessibility checks added to the existing HA integration tests.

The DHL endpoint remains an unofficial website interface. Long-running field validation and default catalog admission are not complete.

## 0.1.0b1

Local prototype: UI configuration, four compartment sensors, source timestamp, stale-data diagnostic, shared polling, configurable freshness threshold and unload cleanup. Not publicly released.
