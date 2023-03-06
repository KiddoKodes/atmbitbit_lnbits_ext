import secrets
import time
from typing import List, Optional, Union
from uuid import uuid4

from . import db
from .helpers import generate_atmbitbit_lnurl_hash
from .models import AtmBitBit, AtmBitBitLnurl, CreateAtmBitBit


async def create_atmbitbit(data: CreateAtmBitBit, wallet_id: str) -> AtmBitBit:
    atmbitbit_id = uuid4().hex
    api_key_id = secrets.token_hex(8)
    api_key_secret = secrets.token_hex(32)
    api_key_encoding = "hex"
    await db.execute(
        """
        INSERT INTO atmbitbit.atmbitbits (id, wallet, api_key_id, api_key_secret, api_key_encoding, name, fiat_currency, exchange_rate_provider, fee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            atmbitbit_id,
            wallet_id,
            api_key_id,
            api_key_secret,
            api_key_encoding,
            data.name,
            data.fiat_currency,
            data.exchange_rate_provider,
            data.fee,
        ),
    )
    atmbitbit = await get_atmbitbit(atmbitbit_id)
    assert atmbitbit, "Newly created atmbitbit couldn't be retrieved"
    return atmbitbit


async def get_atmbitbit(atmbitbit_id: str) -> Optional[AtmBitBit]:
    row = await db.fetchone(
        "SELECT * FROM atmbitbit.atmbitbits WHERE id = ?", (atmbitbit_id,)
    )
    return AtmBitBit(**row) if row else None


async def get_atmbitbit_by_api_key_id(api_key_id: str) -> Optional[AtmBitBit]:
    row = await db.fetchone(
        "SELECT * FROM atmbitbit.atmbitbits WHERE api_key_id = ?", (api_key_id,)
    )
    return AtmBitBit(**row) if row else None


async def get_atmbitbits(wallet_ids: Union[str, List[str]]) -> List[AtmBitBit]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]
    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"SELECT * FROM atmbitbit.atmbitbits WHERE wallet IN ({q})", (*wallet_ids,)
    )
    return [AtmBitBit(**row) for row in rows]


async def update_atmbitbit(atmbitbit_id: str, **kwargs) -> Optional[AtmBitBit]:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE atmbitbit.atmbitbits SET {q} WHERE id = ?",
        (*kwargs.values(), atmbitbit_id),
    )
    row = await db.fetchone(
        "SELECT * FROM atmbitbit.atmbitbits WHERE id = ?", (atmbitbit_id,)
    )
    return AtmBitBit(**row) if row else None


async def delete_atmbitbit(atmbitbit_id: str) -> None:
    await db.execute("DELETE FROM atmbitbit.atmbitbits WHERE id = ?", (atmbitbit_id,))


async def create_atmbitbit_lnurl(
    *, atmbitbit: AtmBitBit, secret: str, tag: str, params: str, uses: int = 1
) -> AtmBitBitLnurl:
    atmbitbit_lnurl_id = uuid4().hex
    hash = generate_atmbitbit_lnurl_hash(secret)
    now = int(time.time())
    await db.execute(
        """
        INSERT INTO atmbitbit.atmbitbit_lnurls (id, atmbitbit, wallet, hash, tag, params, api_key_id, initial_uses, remaining_uses, created_time, updated_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            atmbitbit_lnurl_id,
            atmbitbit.id,
            atmbitbit.wallet,
            hash,
            tag,
            params,
            atmbitbit.api_key_id,
            uses,
            uses,
            now,
            now,
        ),
    )
    atmbitbit_lnurl = await get_atmbitbit_lnurl(secret)
    assert atmbitbit_lnurl, "Newly created atmbitbit LNURL couldn't be retrieved"
    return atmbitbit_lnurl


async def get_atmbitbit_lnurl(secret: str) -> Optional[AtmBitBitLnurl]:
    hash = generate_atmbitbit_lnurl_hash(secret)
    row = await db.fetchone(
        "SELECT * FROM atmbitbit.atmbitbit_lnurls WHERE hash = ?", (hash,)
    )
    return AtmBitBitLnurl(**row) if row else None
