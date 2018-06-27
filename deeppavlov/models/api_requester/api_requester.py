import requests
import asyncio

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component


@register('api_requester')
class ApiRequester(Component):
    def __init__(self, url: str, out: [int, list], param_names=(), debatchify=False, *args,
                 **kwargs):
        self.url = url
        self.param_names = param_names
        self.out_count = out if isinstance(out, int) else len(out)
        self.debatchify = debatchify

    def __call__(self, *args, **kwargs):
        data = kwargs or dict(zip(self.param_names, args))

        if self.debatchify:
            for v in data.values():
                batch_size = len(v)
                break

            async def collect():
                return [j async for j in self.get_async_response(data, batch_size)]

            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(collect())

        else:
            response = requests.post(self.url, json=data).json()

        if self.out_count > 1:
            response = list(zip(*response))

        return response

    async def get_async_response(self, data, batch_size):
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                None,
                requests.post,
                self.url,
                None,
                {k: v[i] for k, v in data.items()}
            )
            for i in range(batch_size)
        ]
        for r in await asyncio.gather(*futures):
            yield r.json()
