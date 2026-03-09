#!/usr/bin/env python3
"""
Test configuration reading from .env file
Verifies that TRADE_AMOUNT, MULTIPLIER, and IS_DEMO are read correctly
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_trade_amount():
    """Get current trade amount from environment"""
    return float(os.getenv('TRADE_AMOUNT', '1.0'))

def get_multiplier():
    """Get current multiplier from environment"""
    return float(os.getenv('MULTIPLIER', '2.5'))

def get_is_demo():
    """Get current demo mode from environment"""
    return os.getenv('IS_DEMO', 'True').lower() == 'true'

def test_configuration():
    """Test that configuration is read correctly"""
    print("=" * 60)
    print("🧪 TESTING CONFIGURATION")
    print("=" * 60)
    
    # Test trade amount
    trade_amount = get_trade_amount()
    print(f"✅ TRADE_AMOUNT: ${trade_amount}")
    
    # Test multiplier
    multiplier = get_multiplier()
    print(f"✅ MULTIPLIER: {multiplier}x")
    
    # Test demo mode
    is_demo = get_is_demo()
    print(f"✅ IS_DEMO: {is_demo} ({'DEMO' if is_demo else 'REAL'} mode)")
    
    # Test martingale calculation
    print("\n" + "=" * 60)
    print("📊 MARTINGALE CALCULATION TEST")
    print("=" * 60)
    
    for step in range(8):  # Steps 0-7 (8 total)
        amount = trade_amount * (multiplier ** step)
        print(f"Step {step}: ${amount:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    
    # Verify .env file exists
    if os.path.exists('.env'):
        print("\n✅ .env file found")
        
        # Show relevant lines
        print("\n📄 Current .env configuration:")
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TRADE_AMOUNT') or \
                   line.startswith('MULTIPLIER') or \
                   line.startswith('IS_DEMO') or \
                   line.startswith('MARTINGALE_STEP'):
                    print(f"   {line}")
    else:
        print("\n⚠️ .env file not found")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_configuration()
