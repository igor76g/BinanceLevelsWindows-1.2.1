"""Geometry of the mini chart (pure functions, no tkinter): candles, cascades and the current price.

A cascade is drawn as a plain line (ray) that starts at its OLDEST extreme and runs to the right edge, with a small
circle on every extreme that forms it. The line is the level: the most extreme price of the cascade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .binance_api import Candle
from .levels import Level


@dataclass
class LineScene:
    y: float                  # the level
    price: float
    side: str
    score: float
    touches: int
    x_start: float            # x of the oldest extreme (the ray starts here)
    points: list = field(default_factory=list)   # (x, y) of every extreme that is visible
    nearest: bool = False     # the cascade closest to the current price


@dataclass
class Scene:
    low: float = 0.0
    high: float = 0.0
    candles: list = field(default_factory=list)   # (x, y_high, y_low, y_open, y_close, is_up)
    lines: list = field(default_factory=list)     # LineScene
    price_y: float | None = None
    body_width: float = 4.0


def build_scene(
    candles: Sequence[Candle],
    levels: Sequence[Level],
    price: float | None,
    width: float,
    height: float,
    margin_left: float = 8.0,
    margin_right: float = 130.0,
    margin_y: float = 10.0,
) -> Scene:
    """Map candles / cascades / price to canvas coordinates (y grows downwards).

    The vertical range covers the candles and the current price (plus 3 % padding); cascades outside it are not drawn."""
    scene = Scene()
    candles = list(candles)
    if not candles or width <= margin_left + margin_right or height <= 2 * margin_y:
        return scene
    low = min(c.low for c in candles)
    high = max(c.high for c in candles)
    if price:
        low, high = min(low, price), max(high, price)
    pad = (high - low) * 0.03 or high * 0.001
    low, high = low - pad, high + pad
    scene.low, scene.high = low, high

    def y_of(value: float) -> float:
        return margin_y + (high - value) / (high - low) * (height - 2 * margin_y)

    slot = (width - margin_left - margin_right) / len(candles)
    scene.body_width = max(1.0, min(slot * 0.7, 12.0))
    x_by_time: dict[int, float] = {}
    for i, c in enumerate(candles):
        x = margin_left + slot * (i + 0.5)
        x_by_time[c.open_time] = x
        scene.candles.append((x, y_of(c.high), y_of(c.low), y_of(c.open), y_of(c.close), c.close >= c.open))

    first_x = margin_left
    for level in levels:
        if not (low <= level.price <= high):
            continue
        points = [(x_by_time[t], y_of(p)) for t, p in level.points if t in x_by_time]
        scene.lines.append(LineScene(
            y=y_of(level.price), price=level.price, side=level.side, score=level.score, touches=level.touches,
            x_start=min((x for x, _y in points), default=first_x),
            points=points,
        ))
    if price:
        scene.price_y = y_of(price)
        if scene.lines:
            min(scene.lines, key=lambda ln: abs(ln.y - scene.price_y)).nearest = True
    return scene
