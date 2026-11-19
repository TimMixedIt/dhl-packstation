# Release and Marketplace catalog checklist

## Prepared locally

- [x] One integration in `custom_components/dhl_packstation`.
- [x] Config flow, options, stable station/entity IDs, shared polling, unload cleanup.
- [x] English/German translations and original local brand icons.
- [x] Manifest with version, owner, documentation and issue tracker URLs.
- [x] `hacs.json`, MIT license, README and field test plan.
- [x] CI workflow for tests, Ruff, hassfest and HACS validation, without ignored catalog checks.

## Publication and verification

- [ ] Complete the documented field tests and record HA versions and results.
- [x] Review the exact publishable tree for credentials and personal station associations. Research responses and local HA configurations are not part of the repository.
- [x] Public repository `TimMixedIt/dhl-packstation` with description, issue tracker and topics.
- [x] Confirm that the documentation and issue tracker links actually resolve after repository creation.
- [ ] Run GitHub Actions on the exact release commit; hassfest and HACS validation must pass with no `ignore` settings.
- [ ] Publish a full, non-prerelease GitHub release matching `manifest.json`, not just a Git tag. A successful automated release check alone does not satisfy the stable-release review requirement.
- [ ] Check a fresh Marketplace/HACS custom-repository install and update.

## Catalog submission

- [ ] Meet the current [Marketplace catalog requirements](https://contributors.home-assistant.io/marketplace/guides/catalog/).
- [x] Fork `hacs/default`, make a separate branch from `master`, and insert `TimMixedIt/dhl-packstation` alphabetically into the `integration` JSON list.
- [ ] Fill in the PR template truthfully with the full release and successful hassfest/HACS run links.
- [x] Submit as repository owner/major contributor: [#14061](https://github.com/hacs/default/pull/14061).
- [ ] Address the stable-release review request, update release/validation links, comment as requested and mark the existing draft ready for review.
- [ ] HACS maintainer approval and merge; catalog acceptance is a maintainer decision, not a direct upload.

Automated validation and public beta releases were completed before this stable-release preparation. The full field-test plan and catalog acceptance remain separate checks; do not infer them from a stable version number.
