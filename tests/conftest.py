import json
import secrets

import pytest_asyncio

from lnbits.core.crud import create_account, create_wallet
from lnbits.extensions.atmbitbit.crud import create_atmbitbit, create_atmbitbit_lnurl
from lnbits.extensions.atmbitbit.exchange_rates import exchange_rate_providers
from lnbits.extensions.atmbitbit.helpers import (
    generate_atmbitbit_lnurl_secret,
    generate_atmbitbit_lnurl_signature,
    prepare_lnurl_params,
    query_to_signing_payload,
)
from lnbits.extensions.atmbitbit.models import CreateAtmBitBit

exchange_rate_providers["dummy"] = {
    "name": "dummy",
    "domain": None,
    "api_url": None,
    "getter": lambda data, replacements: str(1e8),  # 1 BTC = 100000000 sats
}


@pytest_asyncio.fixture
async def atmbitbit():
    user = await create_account()
    wallet = await create_wallet(user_id=user.id, wallet_name="atmbitbit_test")
    data = CreateAtmBitBit(
        name="Test AtmBitBit",
        fiat_currency="EUR",
        exchange_rate_provider="dummy",
        fee="0",
    )
    atmbitbit = await create_atmbitbit(data=data, wallet_id=wallet.id)
    return atmbitbit


@pytest_asyncio.fixture
async def lnurl(atmbitbit):
    query = {
        "tag": "withdrawRequest",
        "nonce": secrets.token_hex(10),
        "tag": "withdrawRequest",
        "minWithdrawable": "50000",
        "maxWithdrawable": "50000",
        "defaultDescription": "test valid sig",
    }
    tag = query["tag"]
    params = prepare_lnurl_params(tag, query)
    payload = query_to_signing_payload(query)
    signature = generate_atmbitbit_lnurl_signature(
        payload=payload,
        api_key_secret=atmbitbit.api_key_secret,
        api_key_encoding=atmbitbit.api_key_encoding,
    )
    secret = generate_atmbitbit_lnurl_secret(atmbitbit.api_key_id, signature)
    params = json.JSONEncoder().encode(params)
    lnurl = await create_atmbitbit_lnurl(
        atmbitbit=atmbitbit, secret=secret, tag=tag, params=params, uses=1
    )
    return {
        "atmbitbit": atmbitbit,
        "lnurl": lnurl,
        "secret": secret,
    }
