# MakeGood Co. website

People. Culture. Possibilities.

Standalone MakeGood website: `index.html` lives at the repository root. Publishing this root serves MakeGood directly, without PAC content or a nested `makegood/` directory.

## Structure and local preview

16 HTML pages: six main pages, nine service pages in `services/`, and `privacy.html`. Assets live at the root. Current pages use `site.js` and `service-navigation.js`. Obsolete preview scripts and styles were removed during the public-sharing review. No build or npm install is required.

Run `python3 -m http.server 8000` from this directory and open http://localhost:8000. Check navigation, service filtering, mobile menu, portraits, privacy links, and links from service pages. Do not submit the production contact form during routine checks; intercept requests in automated tests.

## Publish

Open this repository's **Settings → Pages**. Choose **Deploy from a branch**, **main**, and **/ (root)**, then save. `.nojekyll` supports direct static publishing.

Current published site:
https://backwardssdrow-source.github.io/makegood-site/

The repository is public and GitHub Pages is enabled. The 16 pages and their assets were reviewed before sharing the standalone site link.

## Connect makegoodco.com

1. Enable and verify the standalone deployment.
2. In Pages settings, set the custom domain to `makegoodco.com`. GitHub should create the root `CNAME` file. Complete the current domain-verification instructions shown by GitHub.
3. In the domain DNS dashboard reached through Tailor Brands/GoDaddy, configure apex and `www` using GitHub's current custom-domain documentation. Remove only conflicting website records/forwarding. Preserve Google Workspace MX, SPF, DKIM, and DMARC records so email keeps working.
4. Wait for DNS verification and the HTTPS certificate, then enable **Enforce HTTPS**.
5. Change canonical and Open Graph URLs in all HTML pages from the GitHub preview base to `https://makegoodco.com/`. Update the approved indexing setting in HTML and `search_indexing`/`review_only` in `site-manifest.json` together. Verify the final domain before announcing it.
6. Redirect old PAC-hosted MakeGood pages to corresponding new pages, preserving query strings and hashes. Update email signatures and launch links.

Search visibility was enabled with founder approval on October 13, 2026. All 16 public pages allow indexing and have branded social-image metadata. `sitemap.xml` lists the current canonical URLs. The project-level `robots.txt` will apply when served at a custom-domain root; it does not control the parent github.io host. Canonical, sharing, image, sitemap, and robots URLs still use the active standalone GitHub Pages base. Update them together after verifying the custom domain. No custom-domain connection or completed search-engine indexing is claimed.

## Contact form and privacy

`site.js` contains an existing Google Apps Script `/exec` endpoint. Configuration is not proof of delivery. Confirm the private handler's deployment and readable response from the new origin, then verify an authorized test reaches **LT@makegoodco.com**, **Travis@makegoodco.com**, and the private inquiry tracker.

The UI shows success only after a readable acceptance response with the matching inquiry ID; acceptance does not prove inbox receipt. Retries with unchanged details reuse the inquiry ID after an uncertain response. Inquiry content remains in page memory rather than localStorage. The form includes a privacy notice, Privacy link, and public email fallback. Keep visitor-facing availability language accurate until delivery is verified.

Private tracker IDs, credentials, and notification configuration belong in the private Apps Script project, never here. Booking and payments are not connected.

## Migration status: October 12, 2026

- Site copied from `backwardssdrow-source/pac-site`, branch `gh-pages`, directory `makegood/`, to this repository's root.
- Canonical and sharing URLs updated to the standalone preview base.
- Original PAC deployment remains available during cutover.
- Hosting is active at the standalone GitHub Pages URL. The contact form is enabled and its handler responds to a health request; inbox delivery requires a separate check.
- Removed six unused preview scripts/styles, internal editorial comments, and obsolete preview manifest metadata.
- Indexing restrictions were removed with approval on October 13, 2026. Search-engine discovery is not instantaneous or guaranteed.
- Pending: domain DNS/HTTPS, final-domain metadata and sitemap URLs, old-URL redirects, and final-domain email signatures.

## Maintenance

Edit current HTML/CSS/JS directly. Preserve service scope, prices, and founding-rate terms unless a change is requested. Stylesheet order is intentional: inspect existing links before changing overrides. Check keyboard navigation, mobile reflow, enlarged text, and root/service-page relative links after changes. Do not regenerate current pages from old preview bundles.
