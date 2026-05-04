class AbstractNotifier:
    async def send(self, message: str) -> bool:
        raise NotImplementedError
