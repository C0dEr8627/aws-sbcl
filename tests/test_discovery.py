from sbcl_scraper.discovery import extract_candidates


def test_extracts_unique_profile_candidates():
    html = '''
    <html><body>
      <a href="/community/@alpha">Alpha</a>
      <a href="https://builder.aws.com/community/@beta">Beta</a>
      <a href="/community/@alpha">Duplicate</a>
      <a href="/other/@gamma">Ignore</a>
    </body></html>
    '''

    candidates = extract_candidates(html)

    assert candidates == [
        # URL paths are normalized to the configured Builder Center host.
        type(candidates[0])("alpha", "https://builder.aws.com/community/@alpha"),
        type(candidates[0])("beta", "https://builder.aws.com/community/@beta"),
    ]


def test_ignores_nested_profile_paths():
    html = '<a href="/community/@alpha/posts">Ignore</a>'
    assert extract_candidates(html) == []
