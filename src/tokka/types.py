from typing import Any
from typing import Literal
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import TypedDict

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.typings import _CollationIn


class FindKwargs(TypedDict, total=False):
    projection: dict[str, Any]
    skip: int
    limit: int
    no_cursor_timeout: bool
    cursor_type: Literal[0, 1]

    # see cursor.html#pymongo.cursor.Cursor.sort
    # at https://pymongo.readthedocs.io/en/stable/api/pymongo/
    sort: tuple[
        str
        | Sequence[str | Tuple[str, int | str | Mapping[str, Any]]]
        | Mapping[str, Any],
        int | str,
    ]
    allow_partial_results: bool
    oplog_replay: bool
    batch_size: int
    collation: _CollationIn
    hint: (
        str
        | Sequence[str | Tuple[str, int | str | Mapping[str, Any]]]
        | Mapping[str, Any]
    )
    max_scan: int
    max_time_ms: int
    max: Sequence[str | Tuple[str, int | str | Mapping[str, Any]]] | Mapping[str, Any]
    min: Sequence[str | Tuple[str, int | str | Mapping[str, Any]]] | Mapping[str, Any]
    return_key: bool
    show_record_id: bool
    snapshot: bool
    comment: Any
    session: AsyncIOMotorClient
    allow_disk_use: bool
