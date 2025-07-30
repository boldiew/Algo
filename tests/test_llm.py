import asyncio
from trading.llm import MultiKeyManager

async def _rotate(manager):
    return [await manager.next_key() for _ in range(4)]

def test_multikey_rotation():
    m = MultiKeyManager("a,b,c")
    keys = asyncio.run(_rotate(m))
    assert set(keys[:3]) == {"a", "b", "c"}
    assert keys[3] == "a"
