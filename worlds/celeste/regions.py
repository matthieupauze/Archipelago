from typing import Callable, Optional

from BaseClasses import CollectionState, Region
from worlds.AutoWorld import World

SIDE_MAP = {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 1, 9: 3, 10: 1}
SIDE_LETTERS = ["A", "B", "C"]


class CelesteRegionFactory:
    _world: World

    def _add_region(self, region: Region) -> Region:
        self._world.multiworld.regions.append(region)
        return region

    def _construct_rule(self, level: int, side: int) -> Optional[Callable[[CollectionState], bool]]:
        if side == 0:
            if level == 1:
                return None
            return lambda state: state.has_any(
                {
                    f"Level {level - 1} A-Side Complete",
                    f"Level {level - 1} B-Side Complete",
                    f"Level {level - 1} C-Side Complete",
                },
                self._world.player,
            )
        elif side == 1:
            return lambda state: state.has(f"Level {level} A-Side Cassette", self._world.player)
        elif side == 2:
            return lambda state: state.has_all(
                {f"Level {level} A-Side Crystal Heart", f"Level {level} B-Side Crystal Heart"}, self._world.player
            )
        else:
            return None

    def activate(self, world: World) -> None:
        self._world = world

        menu_region = self._add_region(Region("Menu", self._world.player, self._world.multiworld))
        map_region = self._add_region(Region("Map", self._world.player, self._world.multiworld))
        menu_region.connect(map_region)

        location_table = world.location_factory.get_table(self._world)

        for level, count in SIDE_MAP.items():
            for side in range(count):
                level_name = f"Level {level} {SIDE_LETTERS[side]}-Side"
                level_region = self._add_region(Region(level_name, self._world.player, self._world.multiworld))
                map_region.connect(level_region, level_name, self._construct_rule(level, side))
                native_locations = [
                    location for location in location_table if location.level == level and location.side == side
                ]
                for location in native_locations:
                    level_region.locations.append(location)
                    location.parent_region = level_region
