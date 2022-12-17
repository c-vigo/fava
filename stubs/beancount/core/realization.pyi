# pylint: disable=missing-docstring,unused-argument,multiple-statements
from collections.abc import Iterable
from collections.abc import Iterator
from typing import TypeAlias

from beancount.core.data import Directive
from beancount.core.data import Entries
from beancount.core.data import Posting
from beancount.core.data import TxnPosting
from beancount.core.inventory import Inventory

TxnPostingList: TypeAlias = list[Directive | TxnPosting]

class RealAccount(dict[str, RealAccount]):
    account: str = ...
    txn_postings: TxnPostingList = ...
    balance: Inventory = ...
    # def __init__(
    #     self, account_name: Any, *args: Any, **kwargs: Any
    # ) -> None: ...
    # def __setitem__(self, key: Any, value: Any): ...
    # def copy(self): ...
    # def __eq__(self, other: Any) -> Any: ...
    # def __ne__(self, other: Any) -> Any: ...

def iter_children(
    real_account: RealAccount, leaf_only: bool = ...
) -> Iterator[RealAccount]: ...
def get(
    real_account: RealAccount,
    account_name: str,
    default: RealAccount | None = ...,
) -> RealAccount: ...
def get_or_create(
    real_account: RealAccount, account_name: str
) -> RealAccount: ...

# def contains(real_account: , account_name: ): ...
def realize(
    entries: Entries,
    min_accounts: Iterable[str] | None = ...,
    compute_balance: bool = ...,
) -> RealAccount: ...

# def postings_by_account(entries: ): ...
# def filter(real_account: , predicate: ): ...
def get_postings(real_account: RealAccount) -> TxnPostingList: ...
def iterate_with_balance(
    txn_postings: TxnPostingList,
) -> list[tuple[Directive, list[Posting], Inventory, Inventory]]: ...
def compute_balance(real_account: RealAccount) -> Inventory: ...
def find_last_active_posting(txn_postings: TxnPostingList) -> Directive: ...

# def index_key(sequence: , value: , key: , cmp: ): ...
# def dump(root_account: ): ...
#
# PREFIX_CHILD_1: str
# PREFIX_CHILD_C: str
# PREFIX_LEAF_1: str
# PREFIX_LEAF_C: str
#
# def dump_balances(
#     real_root: ,
#     dformat: ,
#     at_cost: bool = ...,
#     fullnames: bool = ...,
#     file: Optional[] = ...,
# ): ...
# def compute_postings_balance(txn_postings: ): ...
