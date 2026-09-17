# AWS Builder Center Profile Data Source Investigation

**Status:** Initial investigation complete  
**Date:** 2026-09-17  
**Scope:** Public AWS Builder Center builder profiles; local-only scraper for the SBCL workflow

## 1. Objective

The scraper needs to reduce the manual work of finding AWS Builder Center builders and collecting:

- `alias` — the Builder Center profile alias
- `full_name` / `display_name` — the public name shown on the profile
- `email` — optional, only if it is legitimately exposed as public data by Builder Center

The tool is intended to run locally for a single operator. No AWS deployment or hosted backend is planned.

## 2. Confirmed public profile source

AWS documents that a Builder Center alias is the unique identifier for a public profile and forms the profile URL:

`https://builder.aws.com/community/@<alias>`

The public profile page itself renders the builder's display name and alias. For example, a public profile inspected during this investigation displays:

- Display name: `Alias Here`
- Alias: `@aliasheree`

This establishes the most reliable public source for the two required fields: the public profile page.

## 3. What AWS says is public vs private

AWS Builder Center's FAQ explicitly states that public profile information includes:

- display name
- alias
- optionally headline
- interests
- about
- social media links
- display location

It separately identifies first name, last name, email, phone, and location as private information visible only to the profile owner.

### Implication for this project

The scraper **must not attempt to obtain private email addresses** from authenticated/private profile data, hidden application state, or unrelated AWS identity systems.

`email` should therefore be treated as an optional field that is normally `null` / blank unless the builder has independently published an email address in a genuinely public profile field or linked public content. The initial MVP should focus on alias + public display name.

## 4. Where the profile data appears in the site

### Public route

`/community/@<alias>`

This route is the canonical public profile page and is sufficient to resolve a known alias to its public profile information.

### Builder search

AWS states that builders can be searched without signing in. The Builder Center UI therefore has a public discovery/search mechanism that is relevant for discovering aliases before visiting individual profile routes.

The scraper should model discovery and profile extraction as two separate operations:

1. **Discovery:** obtain candidate builder/profile records from the public Builder Center search/discovery interface.
2. **Resolution:** visit the canonical `/community/@<alias>` page and normalize the public profile fields.

## 5. Important unresolved transport detail

The exact internal HTTP/API request used by the live Builder Center frontend to populate search results and/or profiles has **not yet been verified from browser network traffic in this environment**.

Search-engine indexing confirms the rendered public profile data and AWS documentation confirms the public/private boundary, but this is not enough evidence to claim a specific internal REST or GraphQL endpoint.

Therefore, implementation must **not hard-code an assumed API endpoint** at this stage.

### Next investigation step

Run Builder Center locally in a normal desktop browser and inspect DevTools → Network while:

1. opening `https://builder.aws.com/community`;
2. searching for a builder;
3. opening one search result;
4. opening the corresponding `/community/@alias` page.

Record the requests that return profile/search JSON, including:

- URL and HTTP method
- request parameters/body
- response JSON shape
- pagination fields
- authentication requirements
- rate-limit headers, if present
- whether the endpoint is same-origin or a separate AWS service domain

Only after this capture should the scraper choose direct HTTP/API extraction versus browser automation.

## 6. Data contract for the scraper

The normalized internal record should be:

```json
{
  "alias": "aliasheree",
  "display_name": "Alias Here",
  "profile_url": "https://builder.aws.com/community/@aliasheree",
  "email": null,
  "source": "builder_center_public_profile",
  "scraped_at": "2026-09-17T00:00:00Z"
}
```

`email` is deliberately nullable and must never be inferred from the alias, display name, social links, or external services.

## 7. Source-of-truth hierarchy

1. **Builder Center public profile page** — authoritative source for the displayed public name and alias.
2. **Builder Center public discovery/search response** — candidate discovery source, once its live transport is verified.
3. **Publicly displayed profile/contact field** — optional email source only if Builder Center actually exposes it publicly.
4. **Search-engine results** — useful for discovery/fallback diagnostics, but not the primary scraper source.

## 8. References

- AWS Builder Center FAQ: https://builder.aws.com/faq
- AWS Builder Center public profile example: https://builder.aws.com/community/@aliasheree
- AWS Builder Center community discovery: https://builder.aws.com/community

## 9. Current conclusion

The required alias and name are public Builder Center profile data. The canonical per-builder source is `/community/@<alias>`. AWS explicitly classifies email as private profile information, so email should not be a scraping target unless it is independently and explicitly published in a public field.

The remaining technical question is the exact network/API transport used by the current Builder Center frontend for **builder discovery/search**. That must be captured from the live browser before implementation so the scraper is based on the site's actual current architecture rather than an assumed endpoint.
