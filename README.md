# MOJOWAY website

Public source for the MOJOWAY marketing website — live at mojowaylife.com.

> Knowing and doing were never meant to be apart. **KNOW + DO = CHANGE**

## What lives here

- Website pages (`index.html`, `personal.html`, `coach.html`, `pricing.html`, legal pages, etc.)
- Public blog content (`blog-*.html`, `stories/`)
- Public assets (logo, images, front-end JS)

## What does NOT live here

This is a **public** repository. The following are deliberately excluded because they contain company, customer, or operational data:

- `config/company_info.json` — legal entity details, addresses, founder/reply emails, former company names
- `.htpasswd_admin` — admin password hashes
- `ops/`, `duns-apply/`, backend source, logs, deployment logs
- `交付物/` — internal reports, reviews, pricing analysis
- Any `.env` files or credentials

These belong in the private repository `mojoway-private`.

## Local production note

The live server is a self-contained single-file SPA. Deploy with care: the production `index.html` embeds 6 views, 5 Stripe payment links, and monthly/annual pricing JS. Never overwrite wholesale — use scoped CSS (`#view-home`) to change only the intended view.

## Related

- Knowledge base: [knowing-and-doing](https://github.com/brianmojoway/knowing-and-doing)

---

*MOJOWAY Spectrum Limited*
