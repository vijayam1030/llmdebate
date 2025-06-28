#!/usr/bin/env python3
"""
Quick test to verify the reorganized system works
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all critical imports"""
    try:
        print("Testing system imports...")
        
        # Test main system
        from system.main import LLMDebateSystem
        print("✓ LLMDebateSystem import successful")
        
        # Test dynamic config
        from system.dynamic_config import create_small_model_config_only
        print("✓ Dynamic config import successful")
        
        # Test config
        from system.config import Config
        print("✓ Config import successful")
        
        # Test backend imports via system
        from backend.models import DebateResult, DebateStatus
        print("✓ Backend models import successful")
        
        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        print("✅ System is ready to use!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    test_imports()
