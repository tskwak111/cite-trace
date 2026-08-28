


class EmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

class FakeEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]
