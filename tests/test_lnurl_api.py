import secrets

import pytest

from lnbits.core.crud import get_wallet
from lnbits.extensions.atmbitbit.crud import get_atmbitbit_lnurl
from lnbits.extensions.atmbitbit.helpers import (
    generate_atmbitbit_lnurl_signature,
    query_to_signing_payload,
)
from lnbits.settings import get_wallet_class, settings
from tests.helpers import credit_wallet, is_regtest

WALLET = get_wallet_class()


@pytest.mark.asyncio
async def test_atmbitbit_lnurl_api_missing_secret(client):
    response = await client.get("/atmbitbit/u")
    assert response.status_code == 200
    assert response.json() == {"status": "ERROR", "reason": "Missing secret"}


@pytest.mark.asyncio
async def test_atmbitbit_lnurl_api_invalid_secret(client):
    response = await client.get("/atmbitbit/u?k1=invalid-secret")
    assert response.status_code == 200
    assert response.json() == {"status": "ERROR", "reason": "Invalid secret"}


@pytest.mark.asyncio
async def test_atmbitbit_lnurl_api_unknown_api_key(client):
    query = {
        "id": "does-not-exist",
        "nonce": secrets.token_hex(10),
        "tag": "withdrawRequest",
        "minWithdrawable": "1",
        "maxWithdrawable": "1",
        "defaultDescription": "",
        "f": "EUR",
    }
    payload = query_to_signing_payload(query)
    signature = "xxx"  # not checked, so doesn't matter
    response = await client.get(f"/atmbitbit/u?{payload}&signature={signature}")
    assert response.status_code == 200
    assert response.json() == {"status": "ERROR", "reason": "Unknown API key"}


@pytest.mark.asyncio
async def test_atmbitbit_lnurl_api_invalid_signature(client, atmbitbit):
    query = {
        "id": atmbitbit.api_key_id,
        "nonce": secrets.token_hex(10),
        "tag": "withdrawRequest",
        "minWithdrawable": "1",
        "maxWithdrawable": "1",
        "defaultDescription": "",
        "f": "EUR",
    }
    payload = query_to_signing_payload(query)
    signature = "invalid"
    response = await client.get(f"/atmbitbit/u?{payload}&signature={signature}")
    assert response.status_code == 200
    assert response.json() == {"status": "ERROR", "reason": "Invalid API key signature"}


@pytest.mark.asyncio
async def test_atmbitbit_lnurl_api_valid_signature(client, atmbitbit):
    query = {
        "id": atmbitbit.api_key_id,
        "nonce": secrets.token_hex(10),
        "tag": "withdrawRequest",
        "minWithdrawable": "1",
        "maxWithdrawable": "1",
        "defaultDescription": "test valid sig",
        "f": "EUR",  # tests use the dummy exchange rate provider
    }
    payload = query_to_signing_payload(query)
    signature = generate_atmbitbit_lnurl_signature(
        payload=payload,
        api_key_secret=atmbitbit.api_key_secret,
        api_key_encoding=atmbitbit.api_key_encoding,
    )
    response = await client.get(f"/atmbitbit/u?{payload}&signature={signature}")
    assert response.status_code == 200
    data = response.json()
    assert data["tag"] == "withdrawRequest"
    assert data["minWithdrawable"] == 1000
    assert data["maxWithdrawable"] == 1000
    assert data["defaultDescription"] == "test valid sig"
    assert data["callback"] == f"http://{settings.host}:{settings.port}/atmbitbit/u"
    k1 = data["k1"]
    lnurl = await get_atmbitbit_lnurl(secret=k1)
    assert lnurl


@pytest.mark.asyncio
@pytest.mark.skipif(is_regtest, reason="this test is only passes in fakewallet")
async def test_atmbitbit_lnurl_api_action_insufficient_balance(client, lnurl):
    atmbitbit = lnurl["atmbitbit"]
    secret = lnurl["secret"]
    pr = "lntb500n1pseq44upp5xqd38rgad72lnlh4gl339njlrsl3ykep82j6gj4g02dkule7k54qdqqcqzpgxqyz5vqsp5h0zgewuxdxcl2rnlumh6g520t4fr05rgudakpxm789xgjekha75s9qyyssq5vhwsy9knhfeqg0wn6hcnppwmum8fs3g3jxkgw45havgfl6evchjsz3s8e8kr6eyacz02szdhs7v5lg0m7wehd5rpf6yg8480cddjlqpae52xu"
    WALLET.pay_invoice.reset_mock()
    response = await client.get(f"/atmbitbit/u?k1={secret}&pr={pr}")
    assert response.status_code == 200
    assert response.json()["status"] == "ERROR"
    assert ("Insufficient balance" in response.json()["reason"]) or (
        "fee" in response.json()["reason"]
    )
    wallet = await get_wallet(atmbitbit.wallet)
    assert wallet, not None
    assert wallet.balance_msat == 0
    atmbitbit_lnurl = await get_atmbitbit_lnurl(secret)
    assert atmbitbit_lnurl, not None
    assert atmbitbit_lnurl.has_uses_remaining() is True
    WALLET.pay_invoice.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.skipif(is_regtest, reason="this test is only passes in fakewallet")
async def test_atmbitbit_lnurl_api_action_success(client, lnurl):
    atmbitbit = lnurl["atmbitbit"]
    secret = lnurl["secret"]
    pr = "lntb500n1pseq44upp5xqd38rgad72lnlh4gl339njlrsl3ykep82j6gj4g02dkule7k54qdqqcqzpgxqyz5vqsp5h0zgewuxdxcl2rnlumh6g520t4fr05rgudakpxm789xgjekha75s9qyyssq5vhwsy9knhfeqg0wn6hcnppwmum8fs3g3jxkgw45havgfl6evchjsz3s8e8kr6eyacz02szdhs7v5lg0m7wehd5rpf6yg8480cddjlqpae52xu"
    await credit_wallet(
        wallet_id=atmbitbit.wallet,
        amount=100000,
    )
    wallet = await get_wallet(atmbitbit.wallet)
    assert wallet, not None
    assert wallet.balance_msat == 100000
    WALLET.pay_invoice.reset_mock()
    response = await client.get(f"/atmbitbit/u?k1={secret}&pr={pr}")
    assert response.json() == {"status": "OK"}
    wallet = await get_wallet(atmbitbit.wallet)
    assert wallet, not None
    assert wallet.balance_msat == 50000
    atmbitbit_lnurl = await get_atmbitbit_lnurl(secret)
    assert atmbitbit_lnurl, not None
    assert atmbitbit_lnurl.has_uses_remaining() is False
    WALLET.pay_invoice.assert_called_once_with(pr, 2000)
