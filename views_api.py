from http import HTTPStatus

from fastapi import Depends, Query
from loguru import logger
from starlette.exceptions import HTTPException

from lnbits.core.crud import get_user
from lnbits.decorators import WalletTypeInfo, require_admin_key

from . import atmbitbit_ext
from .crud import (
    create_atmbitbit,
    delete_atmbitbit,
    get_atmbitbit,
    get_atmbitbit_by_api_key_id,
    get_atmbitbits,
    update_atmbitbit,
)
from .exchange_rates import fetch_fiat_exchange_rate
from .models import CreateAtmBitBit


@atmbitbit_ext.get("/api/v1/atmbitbits")
async def api_atmbitbits(
    wallet: WalletTypeInfo = Depends(require_admin_key),
    all_wallets: bool = Query(False),
):
    wallet_ids = [wallet.wallet.id]

    if all_wallets:
        user = await get_user(wallet.wallet.user)
        wallet_ids = user.wallet_ids if user else []

    return [atmbitbit.dict() for atmbitbit in await get_atmbitbits(wallet_ids)]


@atmbitbit_ext.get("/api/v1/fetch_atm/{api_key_id}")
async def api_atmbitbits(
    api_key_id=Depends(require_admin_key)
):

    return (await get_atmbitbit_by_api_key_id(api_key_id)).dict()


@atmbitbit_ext.get("/api/v1/atmbitbit/{atmbitbit_id}")
async def api_atmbitbit_retrieve(
    atmbitbit_id, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    atmbitbit = await get_atmbitbit(atmbitbit_id)

    if not atmbitbit or atmbitbit.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="AtmBitBit configuration not found.",
        )

    return atmbitbit.dict()


@atmbitbit_ext.post("/api/v1/atmbitbit")
@atmbitbit_ext.put("/api/v1/atmbitbit/{atmbitbit_id}")
async def api_atmbitbit_create_or_update(
    data: CreateAtmBitBit,
    wallet: WalletTypeInfo = Depends(require_admin_key),
    atmbitbit_id=None,
):
    fiat_currency = data.fiat_currency
    exchange_rate_provider = data.exchange_rate_provider
    try:
        await fetch_fiat_exchange_rate(
            currency=fiat_currency, provider=exchange_rate_provider
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch BTC/{fiat_currency} currency pair from "{exchange_rate_provider}"',
        )

    if atmbitbit_id:
        atmbitbit = await get_atmbitbit(atmbitbit_id)
        if not atmbitbit or atmbitbit.wallet != wallet.wallet.id:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="AtmBitBit configuration not found.",
            )

        atmbitbit = await update_atmbitbit(atmbitbit_id, **data.dict())
    else:
        atmbitbit = await create_atmbitbit(wallet_id=wallet.wallet.id, data=data)

    assert atmbitbit
    return atmbitbit.dict()


@atmbitbit_ext.delete("/api/v1/atmbitbit/{atmbitbit_id}")
async def api_atmbitbit_delete(
    atmbitbit_id, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    atmbitbit = await get_atmbitbit(atmbitbit_id)

    if not atmbitbit or atmbitbit.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="AtmBitBit configuration not found.",
        )

    await delete_atmbitbit(atmbitbit_id)
    return "", HTTPStatus.NO_CONTENT
