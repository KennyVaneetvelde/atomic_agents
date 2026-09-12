# Serply Search Tool

## Overview
Searches Google web results, Google News, or Google Scholar through the [Serply](https://serply.io) API and returns each result's title, URL, and snippet, plus the publish date and source for news and the authors and citation count for papers. Requires a Serply API key.

## Prerequisites and Dependencies
- Python 3.12 or later
- `atomic-agents`
- `pydantic`
- `aiohttp`
- A Serply API key from [serply.io](https://serply.io)

## Installation
1. Use the Atomic Assembler CLI: run `atomic` and pick `serply_search`.
2. Or copy the `tool/` folder directly into your project.

## Configuration
- `api_key` (str): Serply API key. Falls back to the `SERPLY_API_KEY` environment variable when empty.
- `base_url` (str): API base URL (default `https://api.serply.io/v1`).
- `hl` (str): interface language code, e.g. `en` (default `en`).
- `gl` (str): country code for the search, e.g. `us` (default `us`).
- `user_agent` (str): user agent sent with each request.
- `timeout` (float): HTTP timeout in seconds (default 30).

## Input & Output Structure

### Input Schema
- `queries` (list[str]): search queries to run.
- `search_type` (str): `search` (Google web), `news` (Google News), or `scholar` (Google Scholar). Default `search`.
- `max_results_per_query` (int): 1-100 (default 10).

### Output Schema
A list of `SerplySearchResultItem` items. Each has `query`, `title`, `url`, and optional `description`, `position` (web search), `published` and `source` (news), `authors` and `citations` (scholar).

## Usage

```python
from tool.serply_search import SerplySearchTool, SerplySearchToolConfig, SerplySearchToolInputSchema

tool = SerplySearchTool(config=SerplySearchToolConfig(api_key="your-serply-api-key"))

output = tool.run(SerplySearchToolInputSchema(
    queries=["retrieval augmented generation"],
    search_type="scholar",
    max_results_per_query=3,
))

for item in output.results:
    print(item.title, "-", item.url)
    print(item.authors, item.citations)
```

The request and response formats for each endpoint are documented at [serply.io/docs](https://serply.io/docs).

## Contributing
PRs welcome. See the main repo `CONTRIBUTING.md`.

## License
Same as the main Atomic Agents project.
