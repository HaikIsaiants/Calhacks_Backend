## Goal
Pull fresh research data from the web, clean it up, and load it into our Letta agent’s vector memory so the agent can cite the newest findings.

## Steps
- Use Bright Data to crawl the target sites we list (start with the top journals and databases in the shared spreadsheet).
- Extract the useful text: title, authors, abstract/summary, key data points. Skip ads or navigation fluff.
- Normalize everything into a simple JSON shape: `{source_url, fetched_at, title, summary, tags, full_text}`.
- Call our ingestion script to push those JSON chunks into Letta’s vector store (we’ll expose a CLI for you).
- Confirm the agent can retrieve a few samples by running the test command and checking the logs.

## Notes
- Respect robots.txt and rate limits. If Bright Data flags a domain, stop and tell us.
- Tag each chunk with the data source so we can filter later.
- Keep a short daily log of what was fetched in Notion so we can audit updates.
