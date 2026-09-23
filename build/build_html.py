#!/usr/bin/env python3
"""Generate the Larsen CPA site (static HTML) from the approved comps and the copy deck.

Fixes carried in from the copy review + the recorded owner decisions:
  1. About: firms named with their real roles; no unsupported client claims;
     no current employer; practice not presented as a continuation of Big Four work.
  2. Attest service (audits / reviews / compilations) removed from launch copy.
  3. Accessibility tokens fixed (gold and slate) and focus styles added.
  4. services.html heading order fixed; unused about-graded.jpg dropped; hero compressed.
  5. robots.txt, sitemap.xml, llms.txt, favicon, privacy page.
  6. Phone number removed site-wide including JSON-LD (owner decision 4:22 PM).
  7. "commercial real estate" -> "real estate" (owner decision 4:25 PM).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
BASE = "https://larsen-cpa.com/"
EMAIL = "contact@larsen-cpa.com"
# FormSubmit relay. The random-form key hides the delivery mailbox from the page source.
FORM_ACTION = "https://formsubmit.co/136244dd4948b0a2cc7d588909bc84ab"
LICENCE = "151422"

NAV = [("index.html", "Home"), ("services.html", "Services"),
       ("about.html", "About Us"), ("contact.html", "Contact")]


FORM_STATUS_JS = """
<script>
/* Progressive enhancement: keep the visitor on the page and confirm inline.
   Without JavaScript the form still posts to the relay and shows the relay's
   own confirmation screen. */
(function () {
  var form = document.getElementById('contact-form');
  if (!form || !window.fetch || !window.FormData) return;
  var note = '', original = form.getAttribute('action');
  note = original.replace('https://formsubmit.co/', 'https://formsubmit.co/ajax/');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var status = form.querySelector('.form-status');
    var button = form.querySelector('button[type=submit]');
    status.hidden = false;
    status.className = 'form-status';
    status.textContent = 'Sending your message.';
    button.disabled = true;
    fetch(note, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || String(d.success) === 'false') throw new Error('relay');
        form.reset();
        status.className = 'form-status ok';
        status.textContent = 'Thank you. Your message has been sent.';
      })
      .catch(function () {
        status.className = 'form-status bad';
        status.textContent = 'Sorry, the message could not be sent. Please write to ' +
          'contact@larsen-cpa.com instead.';
      })
      .then(function () { button.disabled = false; });
  });
})();
</script>
"""


def head(title, desc, canonical, schema, extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}{canonical}">
<meta name="theme-color" content="#0A2E5C">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Christopher Larsen, CPA">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE}{canonical}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="assets/fonts/fonts.css">
<link rel="stylesheet" href="assets/style.css">{extra}
<script type="application/ld+json">
{schema}
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<div class="topbar"><div class="wrap">
  <span class="lic">California CPA &middot; License No. {LICENCE}</span>
</div></div>

<header class="masthead"><div class="wrap">
  <a class="logo" href="index.html" aria-label="Christopher Larsen, CPA, home">
    <img src="assets/img/logo.png" alt="Christopher Larsen, CPA" width="731" height="160">
  </a>
  <nav class="main" aria-label="Primary">
    <a href="index.html"{' aria-current="page"' if canonical == 'index.html' else ''}>Home</a>
    <a href="services.html"{' aria-current="page"' if canonical == 'services.html' else ''}>Services</a>
    <a href="about.html"{' aria-current="page"' if canonical == 'about.html' else ''}>About Us</a>
    <a href="contact.html"{' aria-current="page"' if canonical == 'contact.html' else ''}>Contact</a>
  </nav>
</div></header>

<main id="main">
"""


FOOTER = f"""</main>

<footer class="site"><div class="wrap">
  <div class="cols">
    <div>
      <img src="assets/img/logo-reverse.png" alt="Christopher Larsen, CPA"
           width="914" height="200" loading="lazy">
      <p class="about">A California CPA practice focused on real estate accounting,
        lease compliance, and lease accounting advisory.</p>
    </div>
    <div>
      <h2 class="fh">Pages</h2>
      <ul>
        <li><a href="index.html">Home</a></li>
        <li><a href="services.html">Services</a></li>
        <li><a href="about.html">About Us</a></li>
        <li><a href="contact.html">Contact</a></li>
        <li><a href="privacy.html">Privacy</a></li>
      </ul>
    </div>
    <div>
      <h2 class="fh">Contact</h2>
      <ul>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        <li>Serving clients throughout California</li>
      </ul>
    </div>
  </div>
  <div class="licence">
    <strong>Christopher D. Larsen, CPA</strong> &middot; California CPA License No. {LICENCE}
    &middot; Based in Southern California, licensed and serving clients statewide.<br>
    &copy; 2026 Christopher Larsen, CPA. All rights reserved.
    &middot; <a href="privacy.html">Privacy</a>
    <p class="photo-credit">Photograph: Tuxyso / Wikimedia Commons, CC BY-SA 3.0
      (cropped and toned).</p>
  </div>
</div></footer>

</body>
</html>
"""

BIZ_SCHEMA = """{
  "@context":"https://schema.org",
  "@type":["LocalBusiness","ProfessionalService"],
  "@id":"https://larsen-cpa.com/#business",
  "name":"Christopher Larsen, CPA",
  "description":"California CPA practice providing lease compliance reviews, CAM audits, and lease accounting advisory for real estate tenants, owners, and operators.",
  "url":"https://larsen-cpa.com/",
  "email":"contact@larsen-cpa.com",
  "areaServed":{"@type":"State","name":"California"},
  "address":{"@type":"PostalAddress","addressRegion":"CA","addressCountry":"US"},
  "founder":{"@type":"Person","@id":"https://larsen-cpa.com/about.html#person"},
  "knowsAbout":["CAM audits","Lease compliance","Commercial lease accounting","ASC 842","Operating expense reconciliation"]
}"""

# ---------------------------------------------------------------- index
index = head(
    "Christopher Larsen, CPA &mdash; CAM Audits &amp; Lease Compliance, California",
    "A California CPA practice focused on real estate accounting: lease compliance "
    "reviews, CAM audits, and lease accounting advisory for tenants and owners statewide.",
    "index.html",
    BIZ_SCHEMA,
) + f"""
  <section class="hero"><div class="wrap">
    <p class="eyebrow">Lease compliance &amp; CAM audits</p>
    <h1>CAM audits and lease compliance reviews for commercial tenants</h1>
    <p class="lede">A California CPA practice for real estate accounting. We review lease
      reconciliations, CAM charges, and operating expense billings, and we document what
      the lease actually supports.</p>
    <div class="btn-row">
      <a class="btn" href="contact.html">Discuss an engagement</a>
      <a class="btn ghost" href="services.html">See the services</a>
    </div>
    <div class="hero-meta">
      <span>Licensed California CPA</span>
      <span>Big Four background</span>
      <span>Tenants, owners &amp; managers</span>
    </div>
  </div></section>

  <div class="band">
    <picture>
      <source srcset="assets/img/hero-band.webp" type="image/webp">
      <img src="assets/img/hero-band.jpg" width="1800" height="750"
           alt="Commercial office towers in downtown Los Angeles">
    </picture>
    <div class="scrim"></div>
    <div class="over"><div class="wrap">
      <p class="kicker">The practice</p>
      <p>The lease sets what you owe. The reconciliation says what you were charged.
        That difference is the work.</p>
    </div></div>
  </div>

  <section><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">The primary work</p>
      <h2>Lease compliance and CAM audits</h2>
      <p class="lede">For commercial tenants, we examine the annual reconciliation your
        landlord issues against the language of your lease and the underlying expense
        records. The work is documentary: every finding is tied to a specific lease
        provision and a specific supporting schedule, so it can be raised and answered on
        paper.</p>
    </div>
    <h3 class="list-head">What the review covers</h3>
    <ol class="services">
      <li>
        <h3>Overcharges</h3>
        <p>Charges that exceed what the lease permits, whether by amount, category, or the
          period in which they were billed.</p>
      </li>
      <li>
        <h3>Pro rata share errors</h3>
        <p>Denominator and numerator errors in your proportionate share, including changes
          to the rentable area of the building or the tenant mix.</p>
      </li>
      <li>
        <h3>Base year issues</h3>
        <p>Whether the base year was set and applied correctly, and whether expenses
          already captured in the base year were billed to you again.</p>
      </li>
      <li>
        <h3>Expense cap violations</h3>
        <p>Caps on controllable or aggregate operating expenses, including compounding and
          carry-over mechanics where the lease provides for them.</p>
      </li>
      <li>
        <h3>Gross-up errors</h3>
        <p>The gross-up of variable expenses to a full-occupancy basis, and whether the
          method used matches the method the lease requires.</p>
      </li>
      <li>
        <h3>Improperly billed capital costs</h3>
        <p>Capital items, replacements, and improvement costs that were amortized or passed
          through when the lease did not permit it.</p>
      </li>
    </ol>
  </div></section>

  <section class="alt"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Also available</p>
      <h2>Other real estate accounting services</h2>
      <p class="lede">For engagements that do not call for a CAM review, the practice also
        provides the following.</p>
    </div>
    <ol class="services teaser">
      <li><h3>Lease accounting advisory</h3><p>ASC 842 compliance, lease abstraction, and
        lease accounting cleanup.</p></li>
      <li><h3>Commercial lease audits beyond CAM</h3><p>Base rent verification and
        percentage rent audits.</p></li>
      <li><h3>Landlord-side accounting support</h3><p>Accounting support for landlords and
        property management teams.</p></li>
      <li><h3>Expense reconciliation and cleanup</h3><p>Reconciliation and financial
        cleanup for owners and operators.</p></li>
      <li><h3>Ad hoc CPA advisory</h3><p>Advisory on real estate transactions as questions
        arise.</p></li>
    </ol>
  </div></section>

  <section><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">How it runs</p>
      <h2>From documents to findings</h2>
    </div>
    <ol class="steps">
      <li><span class="n">01</span><h3>Scoping</h3><p>We identify the property, the lease,
        and the reconciliation period, and confirm what records are available.</p></li>
      <li><span class="n">02</span><h3>Document review</h3><p>We abstract the relevant
        lease provisions and reconcile the charges against them.</p></li>
      <li><span class="n">03</span><h3>Findings</h3><p>You receive a written memo with each
        item stated, quantified where the records allow, and supported by schedules.</p></li>
      <li><span class="n">04</span><h3>Follow-up</h3><p>We answer questions on the findings
        and support the discussion with your landlord or their accountant.</p></li>
    </ol>
  </div></section>

  <section class="cta"><div class="wrap">
    <h2>Start with the most recent reconciliation</h2>
    <p>Send the lease and the last reconciliation you received. That is usually enough to
      say whether a fuller review is worth doing.</p>
    <div class="btn-row">
      <a class="btn" href="contact.html">Contact the practice</a>
      <a class="btn ghost" href="services.html">Services and FAQ</a>
    </div>
  </div></section>
""" + FOOTER

# ---------------------------------------------------------------- services
faq = [
    ("What is a CAM audit?",
     "A CAM audit is a review of the common area maintenance and operating expenses a "
     "landlord has billed a commercial tenant over a period. It compares the charges on "
     "the annual reconciliation against the language of the tenant's lease. The output is "
     "a written record of what the lease supports and what it does not."),
    ("What does a lease compliance review cover?",
     "The review covers overcharges, pro rata share errors, base year issues, expense cap "
     "violations, gross-up errors, and improperly billed capital costs. Each item is tied "
     "to a specific lease provision and a specific supporting schedule. Broader lease "
     "audits can also verify base rent and percentage rent."),
    ("Do you work for tenants or for landlords?",
     "Both sides of a lease are served, but not on the same matter. Most of the practice "
     "is tenant-side lease compliance and CAM review. Separately, the practice provides "
     "accounting support to landlords and property management teams."),
    ("How much can a tenant recover from a lease audit?",
     "That depends entirely on the lease and the records, and no one can predict it before "
     "reviewing them. What can be stated at the outset is what each item is, which lease "
     "provision governs it, and what the supporting schedules show. Any amount is a "
     "conclusion drawn from the documents, not a figure promised at the start of the "
     "engagement."),
    ("What do you need in order to start?",
     "The lease and any amendments, the most recent reconciliation or CAM statement, and "
     "the expense schedules behind it. For lease accounting work, the lease file and the "
     "current accounting schedule are usually enough to scope the engagement."),
    ("Is the work billed on contingency?",
     "Not always. Engagements are scoped and priced on their own terms, and for many "
     "matters a fixed or hourly arrangement is the simpler fit. The fee basis is agreed in "
     "writing before work begins."),
]

qa_parts = []
for i, (q, a) in enumerate(faq):
    qa_parts.append('    {"@type":"Question","name":"%s","acceptedAnswer":'
                    '{"@type":"Answer","text":"%s"}}' % (q, a))
faq_schema = """{
  "@context":"https://schema.org",
  "@type":"FAQPage",
  "@id":"https://larsen-cpa.com/services.html#faq",
  "mainEntity":[
%s
  ]
}""" % (",\n".join(qa_parts))

svc_cards = [
    ("Lease accounting advisory",
     "Support for entities applying lease accounting standards to their own books.",
     ["ASC 842 compliance", "Lease abstraction", "Lease accounting cleanup"]),
    ("Commercial lease audits beyond CAM",
     "Lease reviews that go past operating expenses into the rent provisions themselves.",
     ["Base rent verification", "Percentage rent audits"]),
    ("Landlord-side and property management accounting support",
     "Accounting support for landlords and property management teams, including the "
     "reconciliation process from the other side of the lease.", []),
    ("Expense reconciliation and financial cleanup",
     "Reconciliation and cleanup work for real estate owners and operators, typically "
     "where records have drifted or a portfolio has grown faster than its bookkeeping.", []),
    ("Ad hoc CPA advisory for real estate transactions",
     "Advisory on specific real estate transactions and questions as they arise, scoped "
     "to the decision in front of you.", []),
]
cards_html = []
for h, p, items in svc_cards:
    lis = "".join("\n          <li>%s</li>" % i for i in items)
    ul = "\n        <ul>%s\n        </ul>" % lis if items else ""
    cards_html.append("""      <div class="svc">
        <h3>%s</h3>
        <p>%s</p>%s
      </div>""" % (h, p, ul))

faq_html = "\n".join("""      <div class="qa">
        <h3>%s</h3>
        <p>%s</p>
      </div>""" % (q, a) for q, a in faq)

services = head(
    "Services &mdash; Lease Compliance, CAM Audits &amp; Lease Accounting | Christopher Larsen, CPA",
    "Lease compliance and CAM audits for commercial tenants, plus lease accounting "
    "advisory, ASC 842 support, and accounting support for landlords and property "
    "managers in California.",
    "services.html",
    faq_schema,
) + f"""
  <section class="tight"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Services</p>
      <h1>What the practice does</h1>
      <p class="lede">The practice is built around lease compliance and CAM audits for
        commercial tenants. The remaining services support tenants, owners, and operators
        who need accounting work around a real estate asset.</p>
    </div>
  </div></section>

  <section class="pt0"><div class="wrap">
    <div class="featured">
      <p class="eyebrow">Primary service</p>
      <h2>Lease compliance and CAM audits</h2>
      <p>An examination of the operating expense and common area maintenance charges billed
        to a commercial tenant, measured against the tenant's own lease. The work is
        documentary by design: each finding is tied to a lease provision and a supporting
        schedule, so it can be raised with the landlord and answered on paper.</p>
      <h3 class="sub-label">What is examined</h3>
      <ul class="checks">
        <li>Overcharges</li>
        <li>Pro rata share errors</li>
        <li>Base year issues</li>
        <li>Expense cap violations</li>
        <li>Gross-up errors</li>
        <li>Improperly billed capital costs</li>
      </ul>
    </div>
  </div></section>

  <section class="alt"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Secondary services</p>
      <h2>Real estate accounting and advisory</h2>
    </div>
    <div class="svc-grid">
{chr(10).join(cards_html)}
    </div>
    <p class="quiet mt46">How the practice works, and who it is set up to serve, is set out
      on the <a href="about.html">About page</a>.</p>
  </div></section>

  <section><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Questions</p>
      <h2>Common questions</h2>
    </div>
    <div class="faq">
{faq_html}
    </div>
  </div></section>

  <section class="cta"><div class="wrap">
    <h2>Have a lease and a reconciliation?</h2>
    <p>Send both, and we will tell you plainly whether a review is worth undertaking.</p>
    <div class="btn-row">
      <a class="btn" href="contact.html">Contact the practice</a>
    </div>
  </div></section>
""" + FOOTER

# ---------------------------------------------------------------- about
person_schema = """{
  "@context":"https://schema.org",
  "@type":"Person",
  "@id":"https://larsen-cpa.com/about.html#person",
  "name":"Christopher D. Larsen",
  "jobTitle":"Certified Public Accountant",
  "url":"https://larsen-cpa.com/about.html",
  "email":"contact@larsen-cpa.com",
  "address":{"@type":"PostalAddress","addressRegion":"CA","addressCountry":"US"},
  "hasCredential":[
    {"@type":"EducationalOccupationalCredential","credentialCategory":"license",
     "name":"California Certified Public Accountant","identifier":"151422",
     "recognizedBy":{"@type":"Organization","name":"California Board of Accountancy"}}
  ],
  "alumniOf":[{"@type":"CollegeOrUniversity","name":"University of Southern California"}],
  "worksFor":{"@type":"ProfessionalService","@id":"https://larsen-cpa.com/#business",
    "name":"Christopher Larsen, CPA","url":"https://larsen-cpa.com/"}
}"""

about = head(
    f"About &mdash; Christopher D. Larsen, CPA (California License No. {LICENCE})",
    "Christopher D. Larsen, CPA is a California licensed CPA based in Southern California, "
    "with a Big Four consulting background, serving commercial tenants, owners, and "
    "operators statewide.",
    "about.html",
    person_schema,
) + f"""
  <section class="tight"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">About Us</p>
      <h1>A California CPA practice for real estate</h1>
      <p class="lede">The practice provides lease compliance reviews, CAM audits, and lease
        accounting work for commercial tenants, owners, and operators. It is based in
        Southern California and serves clients throughout the state.</p>
    </div>
  </div></section>

  <section class="pt0"><div class="wrap">
    <div class="grid-2">
      <div>
        <h2 class="mb22">Christopher D. Larsen, CPA</h2>
        <p>Christopher Larsen is a California licensed Certified Public Accountant,
          holding license No. {LICENCE}. He has prior experience in the Big Four, working in
          strategy and management consulting at Ernst &amp; Young (EY) and accounting and
          advisory at Deloitte. He also holds a CPA license in New York.</p>
        <p>His work sits where accounting and real estate documents meet. A lease is a
          contract written in rentable-area definitions, expense categories, and
          exclusions; an operating expense reconciliation is an accounting document built
          on top of it.</p>
        <p>He holds a Bachelor of Science in Accounting from the Leventhal School of
          Accounting at the University of Southern California, along with a Bachelor of
          Business Administration from the Marshall School of Business.</p>
        <p class="quiet mt26">The practice does not publish client names or testimonials.
          Client identities are confidential, and no engagement result is published without
          written permission.</p>
      </div>
      <div>
        <div class="creds">
          <h2 class="fh">Credentials</h2>
          <dl>
            <dt>Credential</dt><dd>Certified Public Accountant</dd>
            <div class="span"></div>
            <dt>License</dt><dd>California No. {LICENCE}</dd>
            <div class="span"></div>
            <dt>Practice focus</dt><dd>Real estate accounting</dd>
            <div class="span"></div>
            <dt>Service area</dt><dd>Statewide, California</dd>
            <div class="span"></div>
            <dt>Prior firms</dt><dd>EY &middot; Deloitte</dd>
            <div class="span"></div>
            <dt>Education</dt><dd>University of Southern California<br>B.S. Accounting,
              B.B.A.</dd>
          </dl>
        </div>
      </div>
    </div>
  </div></section>

  <div class="band-static"><div class="wrap">
    <p class="kicker">Who the practice serves</p>
    <p>Tenants who receive an operating expense reconciliation. Owners and operators whose
      books have outgrown their bookkeeping.</p>
  </div></div>

  <section class="alt"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">How it works</p>
      <h2>Direct, documentary, in writing</h2>
    </div>
    <div class="grid-3">
      <div>
        <h3 class="mb12">One accountant</h3>
        <p>The person you speak with is the person doing the work. There is no engagement
          team to be handed off to and no account manager in between.</p>
      </div>
      <div>
        <h3 class="mb12">Documentary method</h3>
        <p>Findings come out of the lease and the records. Where the documents do not
          support a conclusion, the finding says so rather than estimating around it.</p>
      </div>
      <div>
        <h3 class="mb12">Written findings</h3>
        <p>You receive the analysis in writing, with the reasoning and the supporting
          schedules, so it can be used in a conversation with your landlord or their
          accountant.</p>
      </div>
    </div>
  </div></section>

  <section><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Services</p>
      <h2>Where to start</h2>
      <p class="lede">Most engagements begin with a lease compliance or CAM review. The
        <a href="services.html">Services page</a> sets out the full list, including lease
        accounting advisory and support for owners and property managers.</p>
    </div>
    <div class="btn-row">
      <a class="btn" href="services.html">View services</a>
      <a class="btn ghost" href="contact.html">Contact the practice</a>
    </div>
  </div></section>
""" + FOOTER

# ---------------------------------------------------------------- contact
contact_schema = """{
  "@context":"https://schema.org",
  "@type":"ContactPage",
  "@id":"https://larsen-cpa.com/contact.html",
  "url":"https://larsen-cpa.com/contact.html",
  "mainEntity":{"@id":"https://larsen-cpa.com/#business"}
}"""

contact = head(
    "Contact &mdash; Christopher Larsen, CPA | contact@larsen-cpa.com",
    "Contact Christopher Larsen, CPA for lease compliance, CAM audits, and real estate "
    "accounting work in California. Email contact@larsen-cpa.com or send a message "
    "through the site.",
    "contact.html",
    contact_schema,
) + f"""
  <section class="tight"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Contact</p>
      <h1>Get in touch</h1>
      <p class="lede">Tell us about the property and the reconciliation in question. If you
        have the lease and the most recent CAM or operating expense statement, mention
        that, and we will tell you whether a review is worth undertaking.</p>
    </div>
  </div></section>

  <section class="pt0"><div class="wrap">
    <div class="grid-2">
      <div>
        <h2 class="mb26">Send a message</h2>
        <form class="form" id="contact-form" action="{FORM_ACTION}" method="post">
          <input type="hidden" name="_subject" value="Website enquiry: Christopher Larsen, CPA">
          <input type="hidden" name="_captcha" value="false">
          <input type="hidden" name="_template" value="table">
          <div class="hp" aria-hidden="true">
            <label for="_honey">Leave this field empty</label>
            <input id="_honey" name="_honey" type="text" tabindex="-1" autocomplete="off">
          </div>
          <div class="field">
            <label for="name">Name</label>
            <input id="name" name="name" type="text" autocomplete="name" required>
          </div>
          <div class="field">
            <label for="email">Email</label>
            <input id="email" name="email" type="email" autocomplete="email" required>
          </div>
          <div class="field">
            <label for="phone">Phone</label>
            <input id="phone" name="phone" type="tel" autocomplete="tel">
          </div>
          <div class="field">
            <label for="company">Company</label>
            <input id="company" name="company" type="text" autocomplete="organization"
                   placeholder="Optional">
          </div>
          <div class="field full">
            <label for="message">Message</label>
            <textarea id="message" name="message" required></textarea>
          </div>
          <div class="field full">
            <button class="btn" type="submit">Send message</button>
          </div>
          <p class="note">Messages are delivered to <a href="mailto:{EMAIL}">{EMAIL}</a>.
            Please do not include confidential documents in this form; we will send you a
            secure way to transmit the lease and records once we are in touch.</p>
          <p class="form-status" role="status" aria-live="polite" hidden></p>
        </form>
{FORM_STATUS_JS}
      </div>
      <div>
        <h2 class="mb26">Direct</h2>
        <dl class="detail">
          <dt>Email</dt>
          <dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>
          <dt>Location</dt>
          <dd>Southern California</dd>
          <dt>Service area</dt>
          <dd>Licensed in California, serving clients statewide</dd>
        </dl>
        <p class="quiet direct-note">Write with the property address and the period in
          question, and you will get a reply.</p>
      </div>
    </div>
  </div></section>

  <section class="alt"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Before you write</p>
      <h2>What helps us answer quickly</h2>
    </div>
    <ol class="services teaser">
      <li><h3>The property</h3><p>Building address, your rented square footage, and the
        type of space.</p></li>
      <li><h3>The lease</h3><p>Original lease and any amendments, particularly the
        operating expense and CAM provisions.</p></li>
      <li><h3>The reconciliation</h3><p>The most recent CAM or operating expense statement,
        and the expense schedules behind it if you have them.</p></li>
      <li><h3>The question</h3><p>What prompted the enquiry, and what outcome you are
        looking for.</p></li>
    </ol>
  </div></section>
""" + FOOTER

# ---------------------------------------------------------------- privacy
privacy = head(
    "Privacy &mdash; Christopher Larsen, CPA",
    "How Christopher Larsen, CPA handles information sent through this website and by "
    "email.",
    "privacy.html",
    BIZ_SCHEMA,
) + f"""
  <section class="tight"><div class="wrap">
    <div class="sec-head">
      <p class="eyebrow">Privacy</p>
      <h1>Privacy</h1>
      <p class="lede">This page explains what this website collects and what happens to it.
        It is written to be read, not to be survived.</p>
    </div>
  </div></section>

  <section class="pt0"><div class="wrap">
    <div class="prose">
      <h2>What the site collects</h2>
      <p>The site itself sets no cookies and runs no analytics, advertising, or tracking
        scripts. It loads no third-party fonts or resources, so simply reading these pages
        does not disclose your visit to anyone other than the host that serves them.</p>

      <h2>Messages you send</h2>
      <p>If you use the contact form, the fields you complete (name, email address, phone
        number if you give one, company if you give one, and your message) are sent to the
        practice. The form is relayed to the practice mailbox through a third-party form
        delivery service, which processes the submission in transit. Messages sent by email
        arrive at that mailbox directly.</p>
      <p>The information is used to answer your enquiry and to carry out work you ask for.
        It is not sold, rented, or used for marketing lists. It is kept for as long as it is
        needed for those purposes and for the period professional and legal requirements
        call for, and is then removed.</p>

      <h2>Confidential documents</h2>
      <p>Please do not send leases, reconciliations, or other confidential records through
        the contact form. Say what you have, and the practice will arrange a secure way to
        transfer it.</p>

      <h2>Requests about your information</h2>
      <p>To ask what information is held about you, to correct it, or to ask for it to be
        deleted, write to <a href="mailto:{EMAIL}">{EMAIL}</a>. The practice will respond
        within a reasonable period and will explain if a legal or professional obligation
        prevents immediate deletion.</p>

      <h2>Contact</h2>
      <p>Christopher Larsen, CPA &middot; California CPA License No. {LICENCE} &middot;
        Southern California &middot; <a href="mailto:{EMAIL}">{EMAIL}</a></p>
    </div>
  </div></section>
""" + FOOTER

pages = {
    "index.html": index,
    "services.html": services,
    "about.html": about,
    "contact.html": contact,
    "privacy.html": privacy,
}

for name, html in pages.items():
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(html)
    print("%-14s %6d bytes" % (name, len(html)))
print("pages done")
