import asyncio
import json

import pytest

import pbrequest
from pbrequest import common, deletion, download, upload
from tests import MESSAGE, RESPONSE_DATA, SERVERS_AND_FILES


@pytest.mark.parametrize("server, file", SERVERS_AND_FILES)
def test_full(server, file):
    send_data = pbrequest.send(
        server, text=MESSAGE, file=file, password='foobar', compression=None,
    )
    get_data = pbrequest.get(send_data['full_url'], password='foobar')
    assert get_data['text'] == MESSAGE
    if file:
        with open(file, 'rb') as file:
            assert get_data['attachment']['content'] == file.read()
    try:
        pbrequest.delete(send_data['full_url'], send_data['deletetoken'])
    except pbrequest.UnsupportedFeatureError:
        pass


def test_bad_compression():
    try:
        pbrequest.send('', text=MESSAGE, compression='clearly-fake-compression')
    except pbrequest.BadCompressionTypeError:
        pass


def test_bad_expiration():
    try:
        pbrequest.send('', text=MESSAGE, expiration='clearly-incorrect-expiration')
    except pbrequest.BadExpirationTimeError:
        pass


def test_bad_formatting():
    try:
        pbrequest.send('', text=MESSAGE, formatting='clearly-incorrect-format')
    except pbrequest.BadFormatError:
        pass


def test_send_nothing():
    try:
        pbrequest.send('')
    except ValueError:
        pass


@pytest.mark.parametrize("server, _", SERVERS_AND_FILES)
@pytest.mark.asyncio
async def test_async_full(server, _):
    send_data = await pbrequest.send_async(server, text=MESSAGE)
    get_data = await pbrequest.get_async(send_data['full_url'])
    assert get_data['text'] == MESSAGE
    try:
        await pbrequest.delete_async(send_data['full_url'], send_data['deletetoken'])
    except pbrequest.UnsupportedFeatureError:
        pass
    await asyncio.sleep(0.5)


def test_bad_server():
    try:
        pbrequest.send('https://example.com', text=MESSAGE)
    except pbrequest.BadServerResponseError:
        pass


class FakeResponse:
    url = ''

    def __init__(self, error=False):
        self.error = error

    def json(self):
        if self.error:
            raise json.JSONDecodeError('', '', 0)
        else:
            return RESPONSE_DATA


def test_bad_response_verification():
    try:
        common.verify_response(FakeResponse(error=True))  # noqa
    except pbrequest.BadServerResponseError:
        pass


def test_bad_process_result():
    try:
        upload.process_result(FakeResponse(), '')  # noqa
    except pbrequest.PrivateBinAPIError:
        pass


def test_bad_process_url():
    try:
        deletion.process_url('https://example.com')
    except ValueError:
        pass


def test_bad_status():
    try:
        common.verify_response(FakeResponse())  # noqa
    except pbrequest.PrivateBinAPIError:
        pass


def test_bad_extract_passphrase():
    try:
        download.extract_passphrase('https://www.example.com')
    except ValueError:
        pass
