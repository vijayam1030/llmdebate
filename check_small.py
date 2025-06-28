import asyncio
from dynamic_config import DynamicModelSelector

async def main():
    selector = DynamicModelSelector()
    await selector.scan_available_models()
    small_models = selector.get_models_under_size_limit(4.0)
    print(f"Models under 4GB ({len(small_models)}):")
    for model in small_models:
        print(f"  • {model}")

if __name__ == "__main__":
    asyncio.run(main())
