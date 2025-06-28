#!/usr/bin/env python3
"""
Quick test to verify the 3-round configuration
"""

from config import Config

print("🔧 Current Configuration:")
print(f"MAX_ROUNDS = {Config.MAX_ROUNDS}")
print(f"Expected: 3")

if Config.MAX_ROUNDS == 3:
    print("✅ Configuration is correct!")
else:
    print("❌ Configuration needs fixing!")

print(f"\n🧠 Orchestrator: {Config.ORCHESTRATOR_MODEL.model}")
print(f"👥 Debaters: {[d.model for d in Config.DEBATER_MODELS]}")
