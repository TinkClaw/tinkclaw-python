"""
Test script for TinkClaw SDK

Run this to verify the SDK works with the live TinkClaw API.
"""

from tinkclaw import TinkClawClient

# Initialize client with test key
client = TinkClawClient(api_key="openclaw_builder_94e48d5e6c667e3f71de7bfa5b32e920")

print("=" * 60)
print("TinkClaw SDK Test")
print("=" * 60)

# Test 1: Health check
print("\n1. Health Check")
try:
    health = client.health()
    print(f"   API Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"   Error: {str(e)}")

# Test 2: Get confluence for BTC
print("\n2. Get Confluence (BTC)")
try:
    confluence = client.get_confluence("BTC")
    print(f"   Symbol: {confluence.get('symbol')}")
    print(f"   Score: {confluence.get('score')}")
    print(f"   Signal: {confluence.get('signal')}")
    print(f"   Setup: {confluence.get('setup_type')}")
    print(f"   Regime: {confluence.get('regime')}")
    print(f"   Success")
except Exception as e:
    print(f"   Error: {str(e)}")

# Test 3: Get indicators
print("\n3. Get Indicators (ETH)")
try:
    indicators = client.get_indicators("ETH", range_days=30)
    print(f"   Symbol: {indicators.get('symbol')}")
    print(f"   Hurst: {indicators.get('hurst_exponent')}")
    print(f"   Autocorr: {indicators.get('autocorrelation')}")
    print(f"   Success")
except Exception as e:
    print(f"   Error: {str(e)}")

# Test 4: Get top signals
print("\n4. Get Top Signals")
try:
    top_signals = client.get_top_signals(min_score=70, limit=5)
    print(f"   Found {len(top_signals)} signals")
    for signal in top_signals[:3]:
        print(f"   - {signal.get('symbol')}: {signal.get('score')}")
    print(f"   Success")
except Exception as e:
    print(f"   Error: {str(e)}")

# Test 5: Multi-timeframe
print("\n5. Multi-Timeframe Analysis (BTC)")
try:
    mtf = client.get_confluence("BTC", timeframes=[7, 30, 90, 365])
    print(f"   Symbol: {mtf.get('symbol')}")
    print(f"   Timeframes: {mtf.get('timeframes', 'N/A')}")
    print(f"   Success")
except Exception as e:
    print(f"   Error: {str(e)}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
