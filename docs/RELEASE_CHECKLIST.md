# Release and Marketplace catalog checklist

## Prepared locally

- [x] One integration in `custom_components/dhl_packstation`.
- [x] Config flow, options, stable station/entity IDs, shared polling, unload cleanup.
- [x] English/German translations and original local brand icons.
- [x] Manifest with version, owner, documentation and issue tracker URLs.
- [x] `hacs.json`, MIT license, README and field test plan.
- [x] CI workflow for tests, Ruff, hassfest and HACS validation, without ignored catalog checks.

## Before making the repository public

- [ ] Complete the documented field tests and record HA versions and results.
- [ ] Review the exact publishable tree for credentials and personal station associations. Research responses and local HA configurations are not part of the repository.
- [ ] Create `TimMixedIt/dhl-packstation` (or change every project URL if choosing another name), with description, issues enabled and topics such as `home-assistant`, `hacs`, `dhl`, `packstation`.
- [ ] Confirm that the documentation and issue tracker links actually resolve after repository creation.
- [ ] Run GitHub Actions on the exact release commit; hassfest and HACS validation must pass with no `ignore` settings.
- [ ] Publish a full GitHub release matching `manifest.json`, not just a Git tag. Decide whether to distribute a beta as a custom repository before the stable release.
- [ ] Check a fresh Marketplace/HACS custom-repository install and update.

## Catalog submission

- [ ] Meet the current [Marketplace catalog requirements](https://contributors.home-assistant.io/marketplace/guides/catalog/).
- [ ] Fork `hacs/default`, make a separate branch from `master`, and insert `TimMixedIt/dhl-packstation` alphabetically into the `integration` JSON list.
- [ ] Fill in the PR template truthfully with the full release and successful hassfest/HACS run links.
- [ ] Submit as repository owner/major contributor, then address review feedback. Catalog acceptance is a maintainer decision, not a direct upload.

This checklist does not claim that GitHub validation, public publication, field testing, or catalog acceptance has already happened.
