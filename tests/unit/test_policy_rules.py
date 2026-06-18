from aoa_4pda_connector.policy import is_url_allowed


def test_public_showtopic_route_is_allowed():
    assert is_url_allowed("https://4pda.to/forum/index.php?showtopic=000001")


def test_internal_search_route_is_denied():
    assert not is_url_allowed("https://4pda.to/forum/index.php?act=search&q=bootloop")
    assert not is_url_allowed("https://4pda.to/forum/index.php?act=Search&q=bootloop")


def test_attachment_route_is_denied():
    assert not is_url_allowed("https://4pda.to/forum/index.php?act=attach&type=post&id=1")

