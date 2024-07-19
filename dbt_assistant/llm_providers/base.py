# stdlib
import os
from abc import ABC, abstractmethod

# third party
from langchain_core.messages import BaseMessage


class BaseProvider(ABC):
    API_KEY_ENV_VAR = None

    def __init__(self, model: str, temperature: float, max_tokens: int, **kwargs):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        try:
            self.api_key = os.environ[self.API_KEY_ENV_VAR]
        except KeyError:
            raise Exception(
                f"{self._provider_name} API key not found. Please set the "
                f"{self.API_KEY_ENV_VAR} environment variable."
            )
        self.kwargs = kwargs
        self.llm = self.get_llm_model()

    @property
    def _provider_name(self):
        return self.__class__.__name__.replace("Provider", "")

    @abstractmethod
    def get_llm_model(self):
        raise NotImplementedError

    async def get_chat_response(
        self, messages: list[BaseMessage], stream: bool, websocket=None
    ):
        if not stream:
            output = await self.llm.ainvoke(messages)
            return output.content

        return await self.stream_response(messages, websocket)

    async def stream_response(self, messages: list[BaseMessage], websocket=None):
        response = ""
        paragraph = ""

        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content is not None:
                response += content
                paragraph += content
                if "\n" in paragraph:
                    if websocket is not None:
                        await websocket.send_json(
                            {"type": "report", "output": paragraph}
                        )
                    else:
                        print(paragraph)
                    paragraph = ""

        return response
