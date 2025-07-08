import pytest
from api_layer.rest_api import utils


def test_is_valid_eth_address():
    assert utils.is_valid_eth_address("0x2810f346088b6f9638a39b869a929e6eafb73398")
    assert not utils.is_valid_eth_address("badaddress")
    assert not utils.is_valid_eth_address("0x123")


def test_is_valid_token_id():
    assert utils.is_valid_token_id(1)
    assert utils.is_valid_token_id("abc")
    assert not utils.is_valid_token_id(-1)
    assert not utils.is_valid_token_id(" ")


def test_is_valid_uri():
    assert utils.is_valid_uri("http://example.com")
    assert utils.is_valid_uri("https://example.com")
    assert not utils.is_valid_uri("ftp://example.com")


def test_to_checksum():
    addr = "0x2810f346088b6f9638a39b869a929e6eafb73398"
    expected = "0x2810f346088B6F9638a39b869a929E6EaFb73398"
    assert utils.to_checksum(addr) == expected
    with pytest.raises(ValueError):
        utils.to_checksum("bad")
