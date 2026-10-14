# christopherlarsencpa.com — Christopher Larsen, CPA

Static marketing site for a California CPA practice focused on small business
accounting and personal tax preparation, with additional services including real estate
accounting: lease compliance reviews, CAM audits, and lease accounting advisory.

No build step is required to serve it: the repository root **is** the site.
GitHub Pages serves the root of `main`.

## Layout

```
index.html            Home
small-business-accounting.html   Small Business Accounting
real-estate-accounting.html      Real Estate Accounting (additional service, reachable from Other Services)
personal-tax-preparation.html    Personal Tax Preparation
other-services.html              Additional Services
about.html            About + Person JSON-LD (CA CPA licence 151422)
contact.html          Contact + form
privacy.html          Privacy
thanks.html           Contact-form confirmation (noindex)
services.html         Redirect stub -> real-estate-accounting.html
robots.txt            Crawler policy + sitemap pointer
sitemap.xml           Eight URLs
llms.txt              Summary for AI answer engines
favicon.ico/.png      Cropped from the licensed brand monogram
assets/style.css      Design system — plus style-v2.css (no JS, no third-party
                      requests)
assets/fonts/         Source Serif 4 + Inter, self-hosted, text-subset (SIL OFL)
assets/img/           Logo (downscaled), hero band (JPEG + WebP), and the
                      About-page headshot (JPEG + WebP, plus the full-size
                      source JPEG)
build/                RETIRED generators (do not run — see "Editing content")
                      and the render/accessibility audit harness
```

## Editing content

**The `.html` files at the repository root are the source of truth.** They are
hand-maintained and edited directly. There is no build step; never regenerate
the site from `build/`.

An earlier page generator (`build/build_html.py`) and its asset builder
(`build/build_assets.py`) are **retired**. They no longer reproduce the live
site — `build_html.py` emits five pages from an older positioning where nine
pages exist, with a different nav, footer, and hero band — and running them
would silently revert current work, today's headshot included. `build_html.py`
now refuses to run and exits with a message; `build_assets.py` is superseded
(see its docstring). They are kept only for historical reference.

To change copy, edit the relevant `.html` file directly. The shared header, nav,
and footer are duplicated in each file, so keep them consistent by hand.

Fonts: the self-hosted webfont subsets are built to exactly the characters the
site renders. If new copy introduces a character outside `U+0020-007E` plus
`© · —`, extend the subsets by hand; do not run `build/build_assets.py`.

## Verifying a change

```sh
python3 -m http.server 8123 --bind 127.0.0.1 --directory site   # or the repo root
# in another shell, with a headless Chrome on --remote-debugging-port=9333:
ORIGIN=http://127.0.0.1:8123 node build/audit.mjs
```

`build/audit.mjs` renders every page at 390 / 834 / 1440 CSS px and reports
horizontal overflow, heading-order violations, text contrast composited over the
real backgrounds, failed requests, console errors, and broken images.

## Contact form

The form posts to a FormSubmit relay key (not a mailto, and not the mailbox
address) and delivers to the practice mailbox. The key is activated per origin;
both `christopherlarsencpa.com` and the Pages origin are activated. Changing the delivery
address means re-activating the relay for the new address and swapping the action.

## Licensing

- Photograph: Tuxyso / Wikimedia Commons, CC BY-SA 3.0 (cropped and toned).
  Attribution is carried in the footer, as the licence requires. This covers
  the home-page hero band only. The About-page headshot of Mr. Larsen is the
  practice's own photograph and carries no third-party licence.
- Fonts: Source Serif 4 and Inter, SIL Open Font Licence, self-hosted subsets.
- Logo: supplied by the practice; the favicon is a crop of the monogram.
