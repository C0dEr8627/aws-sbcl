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


def test_extracts_profile_routes_from_embedded_page_data():
    html = r'''<script>
      window.__DATA__ = {"profile":"/community/@embedded_one","other":"/community\\/@embedded_two"};
    </script>'''

    candidates = extract_candidates(html)

    assert [candidate.alias for candidate in candidates] == ["embedded_one", "embedded_two"]


def test_extracts_encoded_profile_route():
    html = '<script>"url":"https://builder.aws.com/community/%40encoded_user"</script>'
    candidates = extract_candidates(html)

    assert candidates == [
        type(candidates[0])("encoded_user", "https://builder.aws.com/community/@encoded_user")
    ]
