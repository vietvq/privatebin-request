# -*- coding: utf-8 -*-

"""This module provides functions and constants used in other modules in this package."""

import asyncio
import json
from typing import Union

import httpx
import requests

from pbrequest.exceptions import BadServerResponseError, PrivateBinAPIError

__all__ = ('get_loop', 'verify_response')

request_headers = None

def initialize_default_headers(initial_value = None):
    """Initializes the default headers for the requests."""
    if (initial_value is None):
        initial_value = {'X-Requested-With': 'JSONHttpRequest', 'User-Agent': 'PrivateBinRequest/1.0.0'}
    global request_headers
    request_headers = initial_value

def set_headers(headers: dict) -> dict:
    """Sets the default headers for the requests."""
    global request_headers
    request_headers = {**request_headers, **headers}
    return request_headers

def get_headers() -> dict:
    """Returns the default headers for the requests."""
    global request_headers
    return request_headers
    

def verify_response(response: Union[requests.Response, httpx.Response]) -> dict:
    """Checks a response to see it it contains JSON.

    :param response: An HTTP response from a PrivateBin host.
    :return: The JSON data included in the response.
    """
    try:
        data = response.json()
    except json.JSONDecodeError as error:
        raise BadServerResponseError('Unable to parse response from %s' % response.url) from error
    if data['status'] != 0:
        raise PrivateBinAPIError(data['message'])

    return data


def get_loop():
    """Returns the running event loop

    If Python 3.6 is running, it falls back to asyncio.get_event_loop()

    :return: The currently running event loop
    """
    try:
        return asyncio.get_running_loop()
    except AttributeError:
        return asyncio.get_event_loop()
