import asyncio
import sys
import time
import traceback
from typing import Optional

import aiohttp

import util
from recipes.recipe_base import RecipeBase, RecipeResponse


class RecipeRequests(RecipeBase):
    session: aiohttp.ClientSession

    request_addr: str = "https://neal.fun/api/infinite-craft/pair"
    last_request: float = 0
    request_cooldown: float = 0.5  # 0.5s is safe for this API
    request_lock: asyncio.Lock = asyncio.Lock()
    sleep_time: float = 1.0
    sleep_default: float = 1.0
    retry_exponent: float = 2.0
    local_only: bool = False
    trust_cache_nothing: bool = True  # Trust the local cache for "Nothing" results
    trust_first_run_nothing: bool = False  # Save as "Nothing" in the first run
    local_nothing_indication: str = "Nothing\t"  # Indication of untrusted "Nothing" in the local cache
    nothing_verification: int = 3  # Verify "Nothing" n times with the API
    batch_nothing_verification: int = 3  # Verify "Nothing" n times with the API while doing batch requests
    nothing_cooldown: float = 5.0  # Cooldown between "Nothing" verifications
    connection_timeout: float = 10.0  # Connection timeout
    batch_limit: int = 50  # Maximum number of requests in a batch
    error_retry: bool = True  # False = Nothing on error, True = Retry on error

    request_count = 0

    def __init__(self, session, *args, **kwargs):
        super(RecipeRequests, self).__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.session = session

    # async def __aenter__(self):
    #     return self
    #
    # async def __aexit__(self, exc_type, exc_val, exc_tb):
    #     await self.session.close()

    async def _combine(self, a, b, *args, **kwargs) -> RecipeResponse:
        if a > b:
            a, b = b, a

        # print(f"Requesting {a} + {b}", flush=True)
        r = await self.request_pair(self.session, a, b)

        if 'error' in r:
            r = {"result": "Nothing", "emoji": "", "isNew": False}

        nothing_count = 1
        while r['result'] == "Nothing" and nothing_count < self.nothing_verification:
            # Request again to verify, just in case...
            # Increases time taken on requests but should be worth it.
            await asyncio.sleep(self.nothing_cooldown)
            if self.print_new_recipes:
                print("Re-requesting Nothing result...", flush=True)

            r = await self.request_pair(self.session, a, b)
            if 'error' in r:
                r = {"result": "Nothing", "emoji": "", "isNew": False}
            nothing_count += 1

        return r['result'], r['emoji'], r['isNew']

    async def _combine_batch(self, batch: list[tuple[str, str]], check_local=True, *args, **kwargs) \
            -> list[tuple[str, str, RecipeResponse]]:

        # TODO: Request mistake counter
        final_results = [(a, b, None) for a, b in batch]
        need_request = batch
        batch_id: dict[tuple[str, str], int] = {}
        for i, e in enumerate(batch):
            a, b = e
            batch_id[(a, b)] = i

        for i in range(0, len(need_request), self.batch_limit):
            current_batch = need_request[i:i + self.batch_limit]
            # print(current_batch, flush=True)
            r = await self.request_batch(self.session, current_batch)
            for i, result in enumerate(r):
                a, b = current_batch[i]
                # print(a, b, result)
                if 'error' in result or result['result'] == "Nothing":
                    if 'error' in result:
                        print(f"Error {result['error']} in batch request: {a} + {b}", file=sys.stderr)
                    else:
                        pass
                        # print(f"Nothing result in batch request: {a} + {b}", flush=True)

                    result = {"result": "Nothing", "emoji": "", "isNew": False}
                final_results[batch_id[(a, b)]] = (a, b, (result['result'], result['emoji'], result['isNew']))

        return final_results

    async def request_batch(self, session: aiohttp.ClientSession, batch: list[tuple[str, str]]) -> list[dict]:
        async with self.request_lock:
            return await self._request_batch(session, batch)

    async def request_pair(self, session: aiohttp.ClientSession, a: str, b: str) -> dict:
        if len(a) > util.WORD_COMBINE_CHAR_LIMIT or len(b) > util.WORD_COMBINE_CHAR_LIMIT:
            return {"result": "Nothing", "emoji": "", "isNew": False}

        # Don't request too quickly. Have been 429'd way too many times
        async with self.request_lock:
            return await self._request_pair(session, a, b)

    async def _request_pair(self, session: aiohttp.ClientSession, a: str, b: str) -> dict:
        # Warning: To request from Neal's API, you must modify the code below.
        self.request_count += 1

        # Cooldown
        t = time.perf_counter()
        if (t - self.last_request) < self.request_cooldown:
            time.sleep(self.request_cooldown - (t - self.last_request))
        self.last_request = time.perf_counter()

        # a = urllib.parse.quote(a, safe=':/?&=, \'!@#$%^*(){}-+_')
        # b = urllib.parse.quote(b, safe=':/?&=, \'!@#$%^*(){}-+_')
        a = util.uriencode(a)
        b = util.uriencode(b)

        data = f'[["{a}", "{b}"]]'
        url = self.request_addr
        print(url, data)

        while True:
            try:
                async with session.post(url, data=data) as resp:
                    print(resp.status)
                    if resp.status == 200:
                        self.sleep_time = self.sleep_default
                        response = await resp.json(content_type=None)
                        # Single request, so take 1st element of the batch
                        response[0]['result'] = util.uridecode(response[0]['result'])
                        return response[0]
                    else:
                        time.sleep(self.sleep_time)
                        self.sleep_time *= self.retry_exponent
                        print("Retrying...", flush=True)
            except Exception as e:
                # Handling more than just that one error
                print("Unrecognized Error: ", e, file=sys.stderr)
                traceback.print_exc()
                time.sleep(self.sleep_time)
                self.sleep_time *= self.retry_exponent
                print("Retrying...", flush=True)

    async def _request_batch(self, session: aiohttp.ClientSession, batch):
        # Warning: No batch request exists for Neal's API. You must modify the code below for personal use.
        self.request_count += len(batch)

        # Formatting
        batch_uri_list = [
            (util.uriencode(a),
             util.uriencode(b))
            for (a, b) in batch]
        # batch_uri_list = [(a, b) for (a, b) in batch]
        batch_str_list = [f'["{a}", "{b}"]' for a, b in batch_uri_list]
        batch_data = "[" + ",".join(batch_str_list) + "]"

        url = self.request_addr

        while True:
            try:
                async with session.post(url, data=batch_data) as resp:
                    # print(resp.status)
                    if resp.status == 200:
                        self.sleep_time = self.sleep_default
                        response = await resp.json(content_type=None)
                        print(response)
                        for i, val in enumerate(response):
                            val["result"] = util.uridecode(val["result"])
                            response[i] = val
                        print(response)
                        return response
                    else:
                        print(f"Batch request of {len(batch)} items failed with status {resp.status}", file=sys.stderr)
                        print(f"Batch data: {batch_data}", file=sys.stderr)

                        if self.error_retry:
                            time.sleep(self.sleep_time)
                            self.sleep_time *= self.retry_exponent
                            print("Retrying...", flush=True)
                        else:
                            return [{"result": "Nothing", "emoji": "", "isNew": False}] * len(batch)
            except Exception as e:
                # Handling more than just that one error
                print("Unrecognized Error: ", e, file=sys.stderr)
                traceback.print_exc()
                time.sleep(self.sleep_time)
                self.sleep_time *= self.retry_exponent
                print("Retrying...", flush=True)

    # Literally nothing to do here...
    async def _update(self, a, b, r):
        pass
