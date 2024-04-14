from typing import Any
from typing import Literal
from typing import Mapping
from typing import Sequence
from typing import Tuple
from typing import TypedDict
from typing import TypeAlias

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.typings import _CollationIn
from pydantic.main import IncEx


Sort: TypeAlias = tuple[
    str | Sequence[str | Tuple[str, int | str | Mapping[str, Any]]] | Mapping[str, Any],
    int | str,
]

MinMax: TypeAlias = (
    Sequence[str | Tuple[str, int | str | Mapping[str, Any]]] | Mapping[str, Any]
)

Hint: TypeAlias = (
    str | Sequence[str | Tuple[str, int | str | Mapping[str, Any]]] | Mapping[str, Any]
)


class FindKwargs(TypedDict, total=False):
    projection: dict[str, Any]
    skip: int
    limit: int
    no_cursor_timeout: bool
    cursor_type: Literal[0, 1]

    # see cursor.html#pymongo.cursor.Cursor.sort
    # at https://pymongo.readthedocs.io/en/stable/api/pymongo/
    sort: Sort
    allow_partial_results: bool
    oplog_replay: bool
    batch_size: int
    collation: _CollationIn
    hint: Hint
    max_scan: int
    max_time_ms: int
    max: MinMax
    min: MinMax
    return_key: bool
    show_record_id: bool
    snapshot: bool
    comment: Any
    session: AsyncIOMotorClient
    allow_disk_use: bool


class ModelDumpKwargs(TypedDict, total=False):
    mode: Literal["json", "python"]
    include: IncEx
    exclude: IncEx
    by_alias: bool
    exclude_unset: bool
    exclude_defaults: bool
    exclude_none: bool
    round_trip: bool
    warnings: bool