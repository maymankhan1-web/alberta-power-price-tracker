# Alberta Power Pool Price Tracker

A free, public tracker for Alberta's wholesale electricity pool price.

- `fetch_prices.py` (Python standard library only) downloads AESO's public reports and saves them to `data/`:
  - `data/latest.json`: projected pool price, system marginal price, and hourly pool prices for the last 7 days
  - `data/hourly_pool_price.csv` and `data/system_marginal_price.csv`
- `index.html` is a static GitHub Pages site showing the current projected price and a chart of recent hours.
- A GitHub Actions workflow refreshes the data every hour and commits it.

Run locally: `python3 fetch_prices.py`, then serve the folder (`python3 -m http.server`) and open http://localhost:8000.

## Data attribution
Data comes from AESO (Alberta Electric System Operator), http://ets.aeso.ca. This project is not affiliated with or endorsed by AESO.

## Support
If this tracker helps you, you can support it through [GitHub Sponsors](https://github.com/sponsors/maymankhan1-web). If this tracker is useful to you, starring the repo helps for now.

## License
MIT
