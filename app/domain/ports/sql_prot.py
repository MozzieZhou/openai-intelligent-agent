
from abc import ABC, abstractmethod


class SqlPort(ABC):
    @abstractmethod
    async def query(self,sql:str) -> list[dict]:
        """
        执行SQL查询并返回结果
        """
        raise NotImplementedError("Subclasses must implement this method")


        

