import asyncio
from core.config import get_settings
from memory.memory_layer import MemoryLayer
from agents.ceo_agent import CEOAgent


async def main():
    settings = get_settings()
    memory = MemoryLayer(settings)
    ceo = CEOAgent(memory, settings)

    response = await ceo.invoke(
        user_id="test_user_001",
        message="We're deciding between raising a $500K seed round now vs staying bootstrapped for 12 more months. Revenue is $8K MRR, growing 15% month over month. What's your read?",
        history=[]
    )
    print("\n--- CEO RESPONSE ---\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())