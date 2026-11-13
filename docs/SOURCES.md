# Implementation references

Reviewed on 2026-11-13. Exact installed framework APIs were also checked against Home Assistant 2026.10.4 and 2026.11.1 during development.

- [Config flows](https://contributors.home-assistant.io/core/integrations/config-flow/): UI setup, verification before creating an entry, unique IDs and duplicate protection.
- [Fetching data](https://contributors.home-assistant.io/core/integrations/fetching-data/): `DataUpdateCoordinator`, first refresh during setup, runtime data, coordinator entities, unavailable on failures and rate-limit retry intervals.
- [Options flows](https://contributors.home-assistant.io/core/integrations/options-flow/): options UI and applying changes through an entry update listener.
- [Custom integration publishing](https://contributors.home-assistant.io/marketplace/guides/integrations/): repository structure, manifests, translations and validation workflows.
- [Integration brands](https://contributors.home-assistant.io/core/integrations/brands/): local `brand/` icons, dimensions and custom integration identity.
- [Marketplace validation](https://contributors.home-assistant.io/marketplace/reference/validation/) and [catalog submission](https://contributors.home-assistant.io/marketplace/guides/catalog/): HACS/hassfest checks and release-before-submission sequence.
- [HACS and the Marketplace](https://www.hacs.xyz/docs/marketplace/): the 2026.11 transition retains the catalog and `hacs.json` format.
- [Home Assistant's test tools](https://github.com/home-assistant/core/tree/2026.11.1/packages/pytest-homeassistant): official helpers for the current test environment; the earlier compatibility environment uses its matching Custom Component test package.

## Observed DHL behavior

The HTTP paths and fields were verified by actual responses and by inspecting DHL's website application. They are observations, not a documented third-party service contract.

- [DHL Standortfinder](https://www.dhl.de/de/privatkunden/dhl-standorte-finden.html?address=67141%3A189&locationType=packstationen).
- [Website application configuration](https://www.dhl.de/int-postfinder/webservice/spa-config), then its versioned JavaScript bundle: location resolution, detail request and the `liveStatus` field names.
- [Location lookup](https://www.dhl.de/int-postfinder/webservice/rest/v1/nearbySearch?address=67141%3A189&maxResults=1): returns a `primaryKeyPF` for a matching station. The result must be checked for exact postal code, number and type.
- [Station detail](https://www.dhl.de/int-postfinder/webservice/rest/v1/locationByPrimaryKeyPF/1-67141189): includes `freeCompartmentsS`, `freeCompartmentsM`, `freeCompartmentsL`, `freeCompartmentsXl` and `sourceTimestamp` within `liveStatus` when available.

The 15-minute poll interval, configurable 60-minute default maximum data age and five-minute future clock-skew allowance are project policies. DHL did not provide documented polling quotas, a guaranteed update interval, or a reservation promise.

## Bundled dashboard cards (0.2.0b1)

- [Custom card lifecycle and sizing](https://contributors.home-assistant.io/frontend/custom-ui/card/): web components receive `hass` and configuration, can open more-info, and supply sizing hints.
- [Card editor and picker](https://contributors.home-assistant.io/frontend/custom-ui/card-editor/): `window.customCards`, configuration editor, `config-changed`, and stub configuration.
- [Static registration in HA 2026.11.1](https://github.com/home-assistant/core/blob/2026.11.1/homeassistant/components/http/server.py): `StaticPathConfig` and `async_register_static_paths`.
- [Frontend module helper in HA 2026.11.1](https://github.com/home-assistant/core/blob/2026.11.1/homeassistant/components/frontend/__init__.py): `add_extra_js_url` loads the included module without changing dashboard storage.

The cards display public station metadata from the integration's authenticated entity states. The static path contains code only. No third-party script host or external frontend library is used at runtime.

- [CSS container queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries): card-local responsive lengths and breakpoints; verified in Chromium and WebKit.
