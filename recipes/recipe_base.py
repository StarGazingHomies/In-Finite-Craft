import abc
from abc import ABC
from typing import Optional

RecipeResponse = Optional[tuple[str, str, bool]]


class RecipeBase(ABC):
    _next: Optional["RecipeBase"]
    _name: str = "RecipeBase"

    def __init__(self):
        self._next = None

    def __str__(self):
        return self.__class__.__name__

    def set_next(self, handler):
        self._next = handler
        return handler

    def set_name(self, name):
        self._name = name
        return self

    async def combine(self, a, b, *args, **kwargs) -> RecipeResponse:
        result = await self._combine(a, b, *args, **kwargs)
        if result:
            # print(f"{self._name}.combine({a}, {b})")
            return result

        # print(f"{self._name} -> ", end="")
        if self._next is None:
            return

        result = await self._next.combine(a, b, *args, **kwargs)

        if result:
            await self.update(a, b, result)
        return result

    @abc.abstractmethod
    async def _combine(self, a, b, *args, **kwargs) -> RecipeResponse:
        return None

    async def combine_batch(self, batch: list[tuple[str, str]], *args, **kwargs) \
            -> list[tuple[str, str, RecipeResponse]]:
        # print(f"{self._name}.combine_batch({batch})")
        result = await self._combine_batch(batch, *args, **kwargs)

        valid_results = []
        need_results = []
        for a, b, r in result:
            if r:
                valid_results.append((a, b, r))
            else:
                need_results.append((a, b))
        if len(need_results) == 0:
            return valid_results

        if self._next is None:
            return valid_results

        next_results = await self._next.combine_batch(need_results, *args, **kwargs)
        for a, b, r in next_results:
            if r:
                await self._update(a, b, r)
        return valid_results + next_results

    @abc.abstractmethod
    async def _combine_batch(self, batch: list[tuple[str, str]], *args, **kwargs) \
            -> list[tuple[str, str, RecipeResponse]]:
        return [(a, b, None) for a, b in batch]

    async def update(self, a, b, r):
        # print(f"{self._name}.update({a}, {b}, {r})")
        await self._update(a, b, r)

    @abc.abstractmethod
    async def _update(self, a, b, r):
        pass

