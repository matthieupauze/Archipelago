# pylint: disable=missing-class-docstring, missing-function-docstring, missing-module-docstring, fixme
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from BaseClasses import Item, ItemClassification, Location, Region
from worlds.AutoWorld import World

PATH_ITEMS = Path("worlds", "celeste", "data", "items.csv")


class CelesteItemType(Enum):
    CASSETTE = auto()
    COMPLETION = auto()
    GEMHEART = auto()
    STRAWBERRY = auto()


class CelesteItem(Item):
    game: str = "Celeste"
    item_type: CelesteItemType
    level: int
    side: int

    def __init__(
        self,
        name: str,
        classification: ItemClassification,
        code: Optional[int],
        player: int,
        item_type: CelesteItemType,
        level: int,
        side: int,
    ):
        super().__init__(name, classification, code, player)
        self.item_type = item_type
        self.level = level
        self.side = side

    @staticmethod
    def create_from_pandas(world: World, row: pd.Series) -> "CelesteItem":
        item_type = CelesteItemType[row["type"].upper()]
        if item_type == CelesteItemType.STRAWBERRY and world.options.berries_required == 0:
            classification = ItemClassification.filler
        else:
            classification = ItemClassification.progression

        return CelesteItem(
            f"ITEM_{row['name']}",
            classification,
            row["id"],
            world.player,
            item_type,
            row["level"],
            row["side"],
        )


class CelesteLocation(Location):
    game: str = "Celeste"
    level: int
    side: int

    # override constructor to automatically mark event locations as such
    def __init__(
        self,
        player: int,
        level: int,
        side: int,
        name: str = "",
        code: Optional[int] = None,
        parent: Optional[Region] = None,
    ):
        super().__init__(player, name, code, parent)
        self.level = level
        self.side = side
        self.event = code is None

    @staticmethod
    def create_from_pandas(world: World, row: pd.Series) -> "CelesteLocation":
        code = row["id"] if row["level"] < 9 else None
        location = CelesteLocation(world.player, row["level"], row["side"], f"LOC_{row['name']}", code)
        if location.level == 8:
            if location.side == 0:
                location.access_rule = lambda state: state.has_group("gemhearts", world.player, 4)
            elif location.side == 1:
                location.access_rule = lambda state: state.has_group("gemhearts", world.player, 15)
            elif location.side == 2:
                location.access_rule = lambda state: state.has_group("gemhearts", world.player, 23)
        if location.level == 9:
            location.access_rule = (
                lambda state: state.has_group("gemhearts", world.player, world.options.hearts_required)
                and state.has_group("strawberries", world.player, world.options.berries_required)
                and state.has_group("completions", world.player, world.options.levels_required)
                and state.has_group("cassettes", world.player, world.options.cassettes_required)
            )
        return location


class CelesteItemFactory:
    _table: List[CelesteItem]
    _map: Dict[str, CelesteItem]
    _loaded: bool = False
    _world: World

    @classmethod
    def _load_table(cls, world: World, force: bool = False) -> None:
        if force or not cls._loaded or cls._world != world:
            df = pd.read_csv(PATH_ITEMS, usecols=["name", "id", "type", "level", "side"])
            cls._table = [CelesteItem.create_from_pandas(world, row) for _, row in df.iterrows() if row["level"] < 9]
            cls._map = {item.name: item for item in cls._table}
            cls._world = world
            cls._loaded = True

    @classmethod
    def get_name_to_id(cls) -> Dict[str, int]:
        df = pd.read_csv(PATH_ITEMS, usecols=["name", "id", "level"])
        return {f"ITEM_{row['name']}": row["id"] for _, row in df.iterrows() if row["level"] < 9}

    @classmethod
    def create_item(cls, item: str) -> CelesteItem:
        cls._load_table(cls._world)
        return deepcopy(cls._map[item])

    @classmethod
    def get_table(cls, world: World) -> List[CelesteItem]:
        cls._load_table(world)
        return cls._table


class CelesteLocationFactory:
    _table: List[CelesteLocation]
    _map: Dict[str, CelesteLocation]
    _loaded: bool = False

    @classmethod
    def _load_table(cls, world: World, force: bool = False) -> None:
        if force or not cls._loaded:
            df = pd.read_csv(PATH_ITEMS, usecols=["name", "id", "type", "level", "side"])
            cls._table = [CelesteLocation.create_from_pandas(world, row) for _, row in df.iterrows()]
            cls._map = {item.name: item for item in cls._table}
            cls._loaded = True

    @classmethod
    def get_name_to_id(cls) -> Dict[str, int]:
        df = pd.read_csv(PATH_ITEMS, usecols=["name", "id"])
        return {f"LOC_{row['name']}": int(row["id"]) for _, row in df.iterrows()}

    @classmethod
    def get_table(cls, world: World) -> List[CelesteLocation]:
        cls._load_table(world)
        return cls._table
