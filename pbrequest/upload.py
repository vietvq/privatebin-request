# -*- coding: utf-8 -*-

"""This module provides functions to upload pastes to PrivateBin hosts."""

import functools
import json
from concurrent.futures import Executor
from typing import Optional, Tuple, Union

import httpx
import requests
from pbincli.api import PrivateBin
from pbincli.format import Paste
import pbrequest.common
from pbrequest.common import get_loop, verify_response, get_headers
from pbrequest.exceptions import BadCompressionTypeError, BadExpirationTimeError, BadFormatError, \
    BadServerResponseError, PrivateBinAPIError

__all__ = ('send', 'send_async')

COMPRESSION_TYPES = ('zlib', None)
EXPIRATION_TIMES = ("5min", "10min", "1hour", "1day", "1week", "1month", "1year", "never")
FORMAT_TYPES = ('plaintext', 'syntaxhighlighting', 'markdown')

def prepare_upload(server: str, *, text: str = None, file: str = None, password: str = None, expiration: str = '1day',
                   compression: str = 'zlib', formatting: str = 'plaintext', burn_after_reading: bool = False,
                   discussion: bool = False) -> Tuple[dict, str]:
    """Creates the JSON data needed to upload a paste to a PrivateBin host.

    :param server: The home URL of the PrivateBin host.
    :param text: The text content of the paste.
    :param file: The path of a file to attach to the paste.
    :param password: A password to secure the paste.
    :param expiration: After how long the paste should expire.
    :param compression:What type of compression to use when uploading.
    :param formatting: What format the paste should be declared as.
    :param burn_after_reading: Whether or not the paste should delete itself immediately after being read.
    :param discussion: Whether or not to enable discussion on the paste.
    :return: A tuple of the JSON data to POST to the PrivateBin host and the paste's hash
    """
    if not any((text, file)):
        raise ValueError("text and file many not both be None")
    if formatting not in FORMAT_TYPES:
        raise BadFormatError('formatting %s must be in %s' % (repr(formatting), FORMAT_TYPES))
    if expiration not in EXPIRATION_TIMES:
        raise BadExpirationTimeError('expiration %s must be in %s' % (repr(expiration), EXPIRATION_TIMES))
    if compression not in COMPRESSION_TYPES:
        raise BadCompressionTypeError('compression %s must be in %s' % (repr(compression), COMPRESSION_TYPES))

    paste = Paste()
    settings = {
        'server': server,
        'proxy': None,
        'short_api': None,
        'short_url': None,
        'short_user': None,
        'short_pass': None,
        'short_token': None,
        'no_check_certificate': False,
        'no_insecure_warning': False
    }
    api_client = PrivateBin(settings)
    try:
        version = api_client.getVersion()
    except json.JSONDecodeError as error:
        raise BadServerResponseError("The host failed to respond with PrivateBin version information.") from error
    paste.setVersion(version)
    if version == 2 and compression:
        paste.setCompression(compression)
    else:
        paste.setCompression('none')

    paste.setText(text or '')
    if password:
        paste.setPassword(password)
    if file:
        paste.setAttachment(file)
    paste.encrypt(formatting, burn_after_reading, discussion, expiration)
    data = paste.getJSON()
    return data, paste.getHash()


def process_result(response: Union[requests.Response, httpx.Response], passcode: str):
    """Convert a response and passcode into a link and extract the delete token.

    :param response: The response from the PrivateBin host.
    :param passcode: The passcode of the paste.
    :return: A tuple containing the paste's URL and delete token.
    """
    data = verify_response(response)

    if data['status'] == 0:
        url = str(response.url)

        output = {
            **data,
            'full_url': url + '?' + data['id'] + '#' + passcode,
            'passcode': passcode
        }
        return output
        # return str(response.url) + '?' + data['id'] + '#' + passcode, data['deletetoken']
    raise PrivateBinAPIError("Error uploading paste: %s" % data['message'])


def send(server: str, *, text: str = None, file: str = None, password: str = None, expiration: str = '1day',
         compression: Optional[str] = 'zlib', formatting: str = 'plaintext', burn_after_reading: bool = False,
         proxies: dict = None, discussion: bool = False):
    """Upload a paste to a PrivateBin host.

    :param server: The home URL of the PrivateBin host.
    :param text: The text content of the paste.
    :param file: The path of a file to attach to the paste.
    :param password: A password to secure the paste.
    :param expiration: After how long the paste should expire.
    :param compression: What type of compression to use when uploading.
    :param formatting: What format the paste should be declared as.
    :param burn_after_reading: Whether or not the paste should delete itself immediately after being read.
    :param proxies: A dict of proxies to pass to a requests.Session object.
    :param discussion: Whether or not to enable discussion on the paste.
    :return: The link to the paste and the delete token.
    """
    data, passcode = prepare_upload(
        server, text=text, file=file, password=password, expiration=expiration, compression=compression,
        formatting=formatting, burn_after_reading=burn_after_reading, discussion=discussion
    )
    with requests.Session() as session:
        response = session.post(
            server,
            headers=get_headers(),
            proxies=proxies,
            data=data
        )
    return process_result(response, passcode)


async def send_async(server: str, *, text: str = None, file: str = None, password: str = None, expiration: str = '1day',
                     compression: str = 'zlib', formatting: str = 'plaintext', burn_after_reading: bool = False,
                     proxies: dict = None, discussion: bool = False, executor: Executor = None):
    """Asynchronously upload a paste to a PrivateBin host.

    :param server: The home URL of the PrivateBin host.
    :param text: The text content of the paste.
    :param file: The path of a file to attach to the paste.
    :param password: A password to secure the paste.
    :param expiration: After how long the paste should expire.
    :param compression: What type of compression to use when uploading.
    :param formatting: What format the paste should be declared as.
    :param burn_after_reading: Whether or not the paste should delete itself immediately after being read.
    :param proxies: A dict of proxies to pass to a requests.Session object.
    :param discussion: Whether or not to enable discussion on the paste.
    :param executor: A concurrent.futures.Executor instance used for decryption.
    :return: The link to the paste and the delete token.
    """
    func = functools.partial(
        prepare_upload, server, text=text, file=file, password=password, expiration=expiration, compression=compression,
        formatting=formatting, burn_after_reading=burn_after_reading, discussion=discussion
    )
    data, passcode = await get_loop().run_in_executor(executor, func)
    async with httpx.AsyncClient(proxies=proxies, headers=get_headers()) as client:
        response = await client.post(server, data=data)
    return process_result(response, passcode)
