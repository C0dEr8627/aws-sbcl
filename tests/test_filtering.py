from sbcl_scraper.models import Builder


def make_builder(**changes):
    data = {
        "alias": "example",
        "display_name": "Example Builder",
        "location": "Maharashtra, India",
        "followers": 0,
        "following": 0,
        "profile_url": "https://builder.aws.com/community/@example",
    }
    data.update(changes)
    return Builder(**data)


def test_indian_zero_profile_is_target():
    assert make_builder().is_target


def test_non_indian_profile_is_not_target():
    assert not make_builder(location="London, United Kingdom").is_target


def test_followers_disqualify_profile():
    assert not make_builder(followers=1).is_target


def test_following_disqualifies_profile():
    assert not make_builder(following=1).is_target
