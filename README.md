# Duc-Lam Duong — personal research website

Public site: **https://dlduong.github.io/**

A simple, static academic website with a homepage, publications page, and notes and code page. It uses HTML and CSS with no framework, package dependencies, analytics, external fonts, or JavaScript on the homepage. The MCMC tutorial is preserved from the original `dlduong/personalsite` repository, including its standalone interactive lab and Python examples.

## Updating the site

Edit `index.html` directly on GitHub (pencil icon), then commit to `main`. GitHub Pages automatically publishes changes, usually within a few minutes.

- **Biography and research:** edit the main content in `index.html`. Keep the description and Person structured data in the document head consistent.
- **Affiliation, contact and profile links:** edit the shared profile sidebar in `index.html`, `publications.html`, and `notes.html`.
- **Publications:** edit `publications.html`. Add an `<li>` under the appropriate year. Preserve titles, author order, venue, publication status, and paper links. The list is selected work; Google Scholar links to the broader record.
- **Portrait:** replace `assets/portrait.jpg`. Update the image description if needed.
- **Design:** edit `assets/basic.css`. Color and font settings are at the top.
- **Notes and code:** edit `notes.html`. Add each new set of material as a section with a descriptive heading, short description, and download links; store its files in a subfolder of `notes/`. Link substantial standalone pages from `sitemap.xml`. The homepage provides a short link to this collection.
- **PDE files:** the supplied lecture notes and six 2025 worksheets are in `notes/pdes/`; the ZIP there contains only these seven PDFs. Rebuild the ZIP if replacing individual files.
- **Software notes:** `notes/ode-pde-software-2021.pdf`, by Duc-Lam Duong and Anotida Madzvamuse (Spring 2021). PDFs are published unchanged; archive metadata files are excluded.
- **CV:** when a current PDF is available, add `assets/duc-lam-duong-cv.pdf` and a link in the profile sidebar on all three pages. No placeholder CV is published.

The homepage works without JavaScript and is usable offline with its local assets. The tutorial uses its own JavaScript. Navigation, publication links, email, and downloads are native HTML links. External scholarly sites may impose their own access restrictions.

## Design versions and restoring the original

The simpler academic design is live at the root address. The original design is preserved, with the dots after the name removed:

- Browse: https://dlduong.github.io/versions/original/
- Snapshot: Git tag `design-original` (commit `3b719f1`).
- Archived files: `versions/original/index.html` and `versions/original/style.css`. The archive uses shared portrait and favicon assets and is excluded from indexing. The exact snapshot is also retained by the Git tag.

To restore the original design at the homepage, run from a checkout of **dlduong/dlduong.github.io**:

```sh
git restore --source=design-original -- index.html 404.html
git add index.html 404.html
git commit -m "Restore original homepage design"
git push origin main
```

This restores the original homepage without deleting resources or rewriting history. Both stylesheets are retained independently (`assets/style.css` for the original and `assets/basic.css` for the simpler design), so the separate publications page remains usable.

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
