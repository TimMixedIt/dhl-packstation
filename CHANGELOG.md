# Changelog

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
