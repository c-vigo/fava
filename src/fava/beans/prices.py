"""Price helpers."""

from __future__ import annotations

import datetime
from bisect import bisect
from collections import Counter
from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable
    from collections.abc import Sequence
    from typing import TypeAlias

    from fava.beans.abc import Price

    BaseQuote: TypeAlias = tuple[str, str]
    PricePoint: TypeAlias = tuple[datetime.date, Decimal]

ZERO = Decimal()
ONE = Decimal(1)


class DateKeyWrapper(list[datetime.date]):
    """A class wrapping a list of prices for bisect.

    This is needed before Python 3.10, which adds the key argument.
    """

    __slots__ = ("inner",)

    def __init__(self, inner: list[PricePoint]) -> None:
        self.inner = inner

    def __len__(self) -> int:
        return len(self.inner)

    def __getitem__(self, k: int) -> datetime.date:  # type: ignore[override]
        return self.inner[k][0]


def _keep_last_per_day(
    prices: Sequence[PricePoint],
) -> Iterable[PricePoint]:
    """In a sorted non-empty list of prices, keep the last one for each day.

    Yields:
        The filtered prices.
    """
    prices_iter = iter(prices)
    last = next(prices_iter)
    for price in prices_iter:
        if price[0] > last[0]:
            yield last
        last = price
    yield last


class FavaPriceMap:
    """A Fava alternative to Beancount's PriceMap.

    By having some more methods on this class, fewer helper functions need to
    be imported. Also, this is fully typed and allows to more easily reproduce
    issues with the whole price logic.

    This behaves slightly differently than Beancount. Beancount creates a list
    for each currency pair and then merges the inverse rates. We just create
    both the lists in tandem and count the directions that prices occur in.

    Args:
        price_entries: A sorted list of price entries.
    """

    def __init__(self, price_entries: Iterable[Price]) -> None:
        raw_map: dict[BaseQuote, list[PricePoint]] = defaultdict(list)
        counts: Counter[BaseQuote] = Counter()

        # List of currencies
        self._currencies = set()

        for price in price_entries:
            self._currencies.add(price.currency)
            self._currencies.add(price.amount.currency)
            rate = price.amount.number
            base_quote = (price.currency, price.amount.currency)
            raw_map[base_quote].append((price.date, rate))
            counts[base_quote] += 1
            if rate != ZERO:
                raw_map[price.amount.currency, price.currency].append(
                    (price.date, ONE / rate),
                )
        self._forward_pairs = [
            (base, quote)
            for (base, quote), count in counts.items()
            if counts.get((quote, base), 0) < count
        ]
        self._map = {
            k: list(_keep_last_per_day(rates)) for k, rates in raw_map.items()
        }

    def commodity_pairs(
        self,
        operating_currencies: Sequence[str],
    ) -> list[BaseQuote]:
        """List pairs of commodities.

        Args:
            operating_currencies: A list of operating currencies.

        Returns:
            A list of pairs of commodities. Pairs of operating currencies will
            be given in both directions not just in the one most commonly found
            in the file.
        """
        forward_pairs = self._forward_pairs
        extra_operating_pairs = []
        for base, quote in forward_pairs:
            if base in operating_currencies and quote in operating_currencies:
                extra_operating_pairs.append((quote, base))
        return sorted(forward_pairs + extra_operating_pairs)

    def get_all_prices(self, base_quote: BaseQuote) -> list[PricePoint] | None:
        """Get all prices for the given currency pair."""
        return self._map.get(base_quote)

    def get_price(
        self,
        base_quote: BaseQuote,
        date: datetime.date | None = None,
    ) -> Decimal | None:
        """Get the price for the given currency pair."""
        return self.get_price_point(base_quote, date)[1]

    def get_price_point(
        self,
        base_quote: BaseQuote,
        date: datetime.date | None = None,
    ) -> PricePoint | tuple[None, Decimal] | tuple[None, None]:
        """Get the price point for the given currency pair."""
        base, quote = base_quote
        if base == quote:
            return None, ONE

        price_list = self._map.get(base_quote)

        # Direct conversion
        if price_list is not None:
            if date is None:
                return price_list[-1]

            index = bisect(DateKeyWrapper(price_list), date)
            if index == 0:
                return None, None
            return price_list[index - 1]

        # A price is unavailable, attempt to convert via another currency
        for currency in self._currencies:
            if currency in base_quote:
                continue
            price_list1 = self._map.get((base, currency))
            price_list2 = self._map.get((currency, quote))
            if price_list1 is None or price_list2 is None:
                continue

            # No date, get latest price
            if date is None:
                date1 = price_list1[-1][0]
                date2 = price_list2[-1][0]
                if date1 < date2:
                    return self.get_price_point((currency, quote), date1)
                else:
                    return self.get_price_point((base, currency), date2)

            # Date is given
            index = bisect(DateKeyWrapper(price_list1), date)
            if index == 0:
                return None, None
            return self.get_price_point((currency, quote), price_list1[index-1][0])

        return None, None
