from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from .event_store import EventStore
from .models import deterministic_id, money, score


class OrderSide(str, Enum):
    BID = "bid"
    ASK = "ask"


class OrderRequest(BaseModel):
    asset_id: str
    ownership_percentage: Decimal = Field(gt=0, le=100)
    price_per_percentage_point: Decimal = Field(gt=0)


class Order(BaseModel):
    order_id: str
    tenant_id: str
    side: OrderSide
    asset_id: str
    ownership_percentage: Decimal
    price_per_percentage_point: Decimal
    remaining_percentage: Decimal
    sequence: int


class SimulatedMatch(BaseModel):
    bid_id: str
    ask_id: str
    ownership_percentage: Decimal
    price_per_percentage_point: Decimal
    total_price: Decimal


class AuctionBook(BaseModel):
    asset_id: str
    bids: list[Order]
    asks: list[Order]
    simulated_matches: list[SimulatedMatch]
    historical_transactions: list[SimulatedMatch]


class AuctionBookService:
    def __init__(self, store: EventStore) -> None:
        self.store = store

    def add(self, tenant_id: str, side: OrderSide, request: OrderRequest) -> Order:
        ordinal = (
            len(
                [
                    event
                    for event in self.store.read(tenant_id)
                    if event["event_type"] == "auction.order_placed"
                ]
            )
            + 1
        )
        order_id = deterministic_id(
            side.value,
            {
                "tenant_id": tenant_id,
                "side": side.value,
                "request": request,
                "ordinal": ordinal,
            },
        )
        order = Order(
            order_id=order_id,
            tenant_id=tenant_id,
            side=side,
            asset_id=request.asset_id,
            ownership_percentage=score(request.ownership_percentage),
            price_per_percentage_point=money(request.price_per_percentage_point),
            remaining_percentage=score(request.ownership_percentage),
            sequence=ordinal,
        )
        self.store.append(tenant_id, "auction.order_placed", order_id, order)
        return order

    def book(self, tenant_id: str, asset_id: str) -> AuctionBook:
        orders = [
            Order.model_validate(event["payload"])
            for event in self.store.read(tenant_id)
            if event["event_type"] == "auction.order_placed"
            and event["payload"]["asset_id"] == asset_id
        ]
        bids = sorted(
            [item for item in orders if item.side == OrderSide.BID],
            key=lambda item: (-item.price_per_percentage_point, item.sequence),
        )
        asks = sorted(
            [item for item in orders if item.side == OrderSide.ASK],
            key=lambda item: (item.price_per_percentage_point, item.sequence),
        )
        remaining_bids = {item.order_id: item.ownership_percentage for item in bids}
        remaining_asks = {item.order_id: item.ownership_percentage for item in asks}
        matches: list[SimulatedMatch] = []
        for bid in bids:
            for ask in asks:
                if bid.price_per_percentage_point < ask.price_per_percentage_point:
                    continue
                quantity = min(
                    remaining_bids[bid.order_id], remaining_asks[ask.order_id]
                )
                if quantity <= 0:
                    continue
                price = money(
                    (bid.price_per_percentage_point + ask.price_per_percentage_point)
                    / Decimal("2")
                )
                matches.append(
                    SimulatedMatch(
                        bid_id=bid.order_id,
                        ask_id=ask.order_id,
                        ownership_percentage=score(quantity),
                        price_per_percentage_point=price,
                        total_price=money(price * quantity),
                    )
                )
                remaining_bids[bid.order_id] -= quantity
                remaining_asks[ask.order_id] -= quantity
        return AuctionBook(
            asset_id=asset_id,
            bids=bids,
            asks=asks,
            simulated_matches=matches,
            historical_transactions=self._history(tenant_id, asset_id),
        )

    def record_simulation(self, tenant_id: str, asset_id: str) -> list[SimulatedMatch]:
        matches = self.book(tenant_id, asset_id).simulated_matches
        existing_ids = {
            event["aggregate_id"]
            for event in self.store.read(tenant_id)
            if event["event_type"] == "auction.match_simulated"
        }
        for index, match in enumerate(matches, 1):
            match_id = deterministic_id(
                "match", {"asset_id": asset_id, "match": match, "index": index}
            )
            if match_id not in existing_ids:
                self.store.append(tenant_id, "auction.match_simulated", match_id, match)
        return matches

    def _history(self, tenant_id: str, asset_id: str) -> list[SimulatedMatch]:
        order_ids = {
            event["aggregate_id"]
            for event in self.store.read(tenant_id)
            if event["event_type"] == "auction.order_placed"
            and event["payload"]["asset_id"] == asset_id
        }
        return [
            SimulatedMatch.model_validate(event["payload"])
            for event in self.store.read(tenant_id)
            if event["event_type"] == "auction.match_simulated"
            and event["payload"]["bid_id"] in order_ids
        ]
