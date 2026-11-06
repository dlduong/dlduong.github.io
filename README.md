# Duc-Lam Duong — personal research website

Public site: **https://dlduong.github.io/**

A static, responsive academic homepage. It uses HTML and CSS with no framework, package dependencies, analytics, external fonts, or JavaScript on the homepage. The MCMC tutorial is preserved from the original `dlduong/personalsite` repository, including its standalone interactive lab and Python examples.

## Updating the site

Edit `index.html` directly on GitHub (pencil icon), then commit to `main`. GitHub Pages automatically publishes changes, usually within a few minutes.

- **Biography, affiliation and contact:** the `about` and `contact` sections in `index.html`. Keep the description and Person structured data in the document head consistent.
- **Publications:** add or edit an `<li>` within `publication-list`. Each entry includes year, status, title, authors, venue, a short description, and links. The homepage intentionally shows selected work; Google Scholar links to the broader record.
- **Portrait:** replace `assets/portrait.jpg`. Update the image description if needed.
- **Design:** edit `assets/style.css`. Color and font settings are at the top.
- **New resources:** add files or a folder and link to them from the Resources section. Add substantial pages to `sitemap.xml`.
- **CV:** when a current PDF is available, add `assets/duc-lam-duong-cv.pdf` and a link in the profile strip. No placeholder CV is published.

The homepage works without JavaScript and is usable offline with its local assets. The tutorial uses its own JavaScript. Navigation, publication links, email, and downloads are native HTML links. External scholarly sites may impose their own access restrictions.

## Hosting

The repository must be named `dlduong.github.io` to serve the root user-site address. In **Settings → Pages**, select **Deploy from a branch**, branch **main**, folder **/(root)**. `.nojekyll` tells Pages to serve these static files directly. No custom domain is needed.

The former `personalsite` repository is retained separately, so its existing `/personalsite/mcmc/` links continue to work. This site also includes the same tutorial at `/mcmc/`. If the tutorial is updated later, decide whether to update both copies or make the old one redirect.

## Content sources

First version assembled on 6 November 2026 from the owner's confirmed name, role, and profile links, plus public research records:

- University profile and portrait: https://www.oulu.fi/en/researchers/duc-lam-duong (also served at https://www.oulu.fi/en/researchers/lam-duong).
- Google Scholar: https://scholar.google.com/citations?user=6i0ljA0AAAAJ
- ORCID: https://orcid.org/0000-0002-3139-7309
- Survey preprint: https://arxiv.org/abs/2611.01300
- Optical tomography paper (current v2 title and journal reference): https://arxiv.org/abs/2602.03449
- TMLR paper: https://openreview.net/forum?id=rU8erhXHPo
- Experimental design paper: https://arxiv.org/abs/2211.04399

No citation counts, employment dates, qualifications beyond the confirmed role, or unsupported CV details are inferred. Research summaries are short descriptions, not quotations of the abstracts.
