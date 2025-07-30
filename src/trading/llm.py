import os
import itertools
import asyncio
import openai

class MultiKeyManager:
    def __init__(self, keys: str | list[str]):
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.split(',') if k.strip()]
        if not keys:
            keys = [""]
        self._iter = itertools.cycle(keys)
        self._lock = asyncio.Lock()

    async def next_key(self) -> str:
        async with self._lock:
            return next(self._iter)

OPENAI_KEYS = os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY", "")
OPENAI_MANAGER = MultiKeyManager(OPENAI_KEYS)

async def chat(messages, **kwargs):
    key = await OPENAI_MANAGER.next_key()
    openai.api_key = key
    return await openai.ChatCompletion.acreate(messages=messages, **kwargs)

async def embed(text: str, model: str = "text-embedding-ada-002"):
    key = await OPENAI_MANAGER.next_key()
    openai.api_key = key
    resp = await openai.Embedding.acreate(input=text, model=model)
    return resp.data[0].embedding
