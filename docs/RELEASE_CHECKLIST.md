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
- [x] Run GitHub Actions on the exact release commit; hassfest and HACS validation passed with no `ignore` settings: [0.2.0 validation](https://github.com/TimMixedIt/dhl-packstation/actions/runs/44558665600).
- [x] Publish a full, non-prerelease GitHub release matching `manifest.json`: [0.2.0](https://github.com/TimMixedIt/dhl-packstation/releases/tag/0.2.0). A successful automated release check alone does not satisfy the stable-release review requirement.
- [ ] Check a fresh Marketplace/HACS catalog install and update.

## Catalog submission

- [x] Meet the [Marketplace catalog requirements](https://contributors.home-assistant.io/marketplace/guides/catalog/) for the approved submission.
- [x] Fork `hacs/default`, make a separate branch from `master`, and insert `TimMixedIt/dhl-packstation` alphabetically into the `integration` JSON list.
- [x] Fill in the PR template truthfully with the full release and successful hassfest/HACS run links.
- [x] Submit as repository owner/major contributor: [#14061](https://github.com/hacs/default/pull/14061).
- [x] Address the stable-release review request, update release/validation links, comment as requested and mark the existing draft ready for review.
- [x] HACS maintainer approval and merge: [#14061](https://github.com/hacs/default/pull/14061), merged on 2026-11-19.
- [x] Update the English and German installation instructions after catalog admission, as requested in the approval review.

Stable release 0.2.0 passed automated validation and was accepted into the default catalog. The full field-test plan and a fresh installation/update check remain open; catalog acceptance does not complete them.
