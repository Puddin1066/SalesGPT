"""
Start Background Queue Builder.

Continuously sources leads and generates emails for manual review.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from salesgpt.config import get_settings
from salesgpt.container import ServiceContainer


async def main():
    """Run background queue builder."""
    settings = get_settings()
    container = ServiceContainer(settings)
    
    print("🚀 Starting Background Queue Builder...")
    print(f"📍 Geography: {settings.default_geography}")
    print(f"🏥 Specialty: {settings.default_specialty}")
    print(f"📊 Batch Size: {settings.default_batch_size}")
    print("\nPress Ctrl+C to stop.\n")
    
    try:
        await container.queue_builder.run(
            geography=settings.default_geography,
            specialty=settings.default_specialty,
            batch_size=settings.default_batch_size,
            min_score=10
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopping queue builder...")
        container.close()
        print("✅ Queue builder stopped.")


if __name__ == "__main__":
    asyncio.run(main())

