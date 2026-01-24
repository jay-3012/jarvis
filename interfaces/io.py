from typing import Protocol, AsyncGenerator, Any

class STTProvider(Protocol):
    """Protocol for Speech-to-Text providers."""
    async def transcribe(self, audio_chunk: Any) -> str:
        """Convert audio data to text."""
        ...

class TTSProvider(Protocol):
    """Protocol for Text-to-Speech providers."""
    async def synthesize(self, text: str) -> Any:
        """Convert text to audio data."""
        ...
