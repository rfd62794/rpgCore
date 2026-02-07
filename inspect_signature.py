import inspect
from pydantic_ai.models.openai import OpenAIModel

sig = inspect.signature(OpenAIModel.__init__)
print(f"Signature: {sig}")
