# Portfolio & Research Site

A static site showing an active Investopedia paper-trading portfolio and
the research/reasoning behind each position.

## Structure
```
data/portfolio.json     # single source of truth — edit this, not the HTML
data/performance.json   # historical returns for the Performance page (empty until real data is added)
generate_site.py        # builds site/ from data/*.json
assets/styles.css       # design source (copied into site/assets/ on build)
site/                   # the deployable output — this is what you upload/host
  index.html            # portfolio overview
  allocation.html       # pie chart of position weights
  performance.html      # portfolio vs. benchmark (needs real data — see below)
  research/index.html   # research index
  research/<ticker>.html# one page per holding
```

## Updating the portfolio
1. Edit `data/portfolio.json` — add/update a holding, or fill in a `"thesis"`
   field with your reasoning for that position (plain text; blank lines
   become paragraph breaks).
2. Run `python3 generate_site.py` to regenerate every page in `site/`.
3. Re-deploy `site/` (see below).

Ask Claude to do steps 1–2 for you at any time: tell it the trade and the
reasoning, and it can update the JSON, rebuild, and (if you want) redeploy.

## Performance page
`data/performance.json` starts empty on purpose — the Performance tab
shows an honest "no data yet" state rather than a fabricated chart until
real historical portfolio values and a matching benchmark series are
added. See that file's `note` field for the exact shape it expects.

## Deploying — pick one

**Netlify Drop (fastest, no account needed to see it live):**
1. Go to https://app.netlify.com/drop
2. Drag the `site/` folder onto the page.
3. You get a real public URL immediately (e.g. `random-name.netlify.app`).
   Claim/rename it by creating a free Netlify account.

**GitHub Pages (best for a resume — shows on your GitHub profile):**
1. Create a new GitHub repo (e.g. `portfolio-research`).
2. Push the contents of `site/` to the repo's root.
3. In the repo Settings → Pages, enable Pages for that branch/folder.
4. Your site is live at `https://<your-username>.github.io/portfolio-research/`.
   You can later attach a custom domain in the same settings page.

Either way, once it's live, submitting the URL to Google Search Console
(free) gets it indexed faster than waiting for organic crawling.
