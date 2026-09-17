from sbcl_scraper.profile import parse_profile_html, profile_url


PROFILE_HTML = """
<html>
  <body>
    <main>
      <h1>Example Builder</h1>
      <div>@example</div>
      <div>Cloud learner</div>
      <div>Maharashtra, India</div>
      <div>0 followers</div>
      <div>0 following</div>
      <div>About</div>
      <p>Hello from example@example.com</p>
    </main>
  </body>
</html>
"""


def test_profile_url():
    assert profile_url("example") == "https://builder.aws.com/community/@example"
    assert profile_url("@example") == "https://builder.aws.com/community/@example"


def test_parse_public_profile():
    builder = parse_profile_html(PROFILE_HTML, "example")

    assert builder.alias == "example"
    assert builder.display_name == "Example Builder"
    assert builder.location == "Maharashtra, India"
    assert builder.followers == 0
    assert builder.following == 0
    assert builder.email == "example@example.com"
    assert builder.is_target


def test_parse_non_target_profile():
    html = PROFILE_HTML.replace("0 followers", "2 followers")
    builder = parse_profile_html(html, "example")

    assert not builder.is_target
