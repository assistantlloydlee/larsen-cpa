# larsen-cpa.com — Christopher Larsen, CPA

Static marketing site for a California CPA practice focused on real estate
accounting: lease compliance reviews, CAM audits, and lease accounting advisory.

No build step is required to serve it: the repository root **is** the site.
GitHub Pages serves the root of `main`.

## Layout

```
index.html            Home
services.html         Services + FAQ (FAQPage JSON-LD)
about.html            About + Person JSON-LD (CA CPA licence 151422)
contact.html          Contact + form
privacy.html          Privacy
robots.txt            Crawler policy + sitemap pointer
sitemap.xml           Five URLs
llms.txt              Summary for AI answer engines
favicon.ico/.png      Cropped from the licensed brand monogram
assets/style.css      Design system (no JS, no third-party requests)
assets/fonts/         Source Serif 4 + Inter, self-hosted, text-subset (SIL OFL)
assets/img/           Logo (downscaled) and hero band (JPEG + WebP)
build/                Generators and the render/accessibility audit harness
```

## Editing content

The five pages are generated so the header, footer, and navigation cannot drift
apart. Edit `build/build_html.py` and regenerate:

```sh
python3 build/build_html.py      # writes the five .html files
python3 build/build_assets.py    # rebuilds images + the subset webfonts
```

`build/build_assets.py` re-reads the generated HTML to work out which characters
to subset the webfonts to. If new copy introduces a character outside
`U+0020-007E` plus `© · —`, run it again so the glyph is present.

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
both `larsen-cpa.com` and the Pages origin are activated. Changing the delivery
address means re-activating the relay for the new address and swapping the action.

## Licensing

- Photograph: Tuxyso / Wikimedia Commons, CC BY-SA 3.0 (cropped and toned).
  Attribution is carried in the footer, as the licence requires.
- Fonts: Source Serif 4 and Inter, SIL Open Font Licence, self-hosted subsets.
- Logo: supplied by the practice; the favicon is a crop of the monogram.
