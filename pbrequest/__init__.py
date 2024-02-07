# -*- coding: utf-8 -*-

"""Wrapper for the PrivateBin API."""

from pbrequest.deletion import delete, delete_async
from pbrequest.download import get, get_async
from pbrequest.exceptions import BadCompressionTypeError, BadExpirationTimeError, BadFormatError, \
    PrivateBinAPIError, BadServerResponseError, UnsupportedFeatureError
from pbrequest.common import initialize_default_headers, set_headers, get_headers
from pbrequest.upload import send, send_async

initialize_default_headers()
print("initialize_default_headers")
set_headers({'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8', })

def set_headers(headers: dict) -> dict:
    """Sets the headers for the requests."""
    return set_headers(headers)

__all__ = (
    'delete', 'delete_async', 'get', 'get_async', 'send', 'send_async', 'BadCompressionTypeError',
    'BadExpirationTimeError', 'BadFormatError', 'BadServerResponseError', 'PrivateBinAPIError',
    'UnsupportedFeatureError'
)

__author__ = 'Pioverpie'
