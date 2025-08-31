#!/usr/bin/env python3
"""
Test Raydium Fallback Functionality
Tests the Raydium fallback when Jupiter fails
"""

from raydium_executor import get_raydium_executor

def test_raydium_liquidity_check():
    """Test Raydium liquidity checking"""
    print("🔍 Testing Raydium Liquidity Check")
    
    try:
        executor = get_raydium_executor()
        
        # Test with some known tokens
        test_tokens = [
            {
                "symbol": "BONK",
                "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "description": "BONK token (should have Raydium liquidity)"
            },
            {
                "symbol": "JUP",
                "address": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
                "description": "Jupiter token (should have Raydium liquidity)"
            },
            {
                "symbol": "MOON",
                "address": "4KeTt4e3vs9KKvRWttdzYQretUpZSkQhXs5y6QURzd7y",
                "description": "MOON token (from bot logs)"
            },
            {
                "symbol": "SOL",
                "address": "So11111111111111111111111111111111111111112",
                "description": "Wrapped SOL (should have Raydium liquidity)"
            },
            {
                "symbol": "USDC",
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "description": "USDC (should have Raydium liquidity)"
            }
        ]
        
        for token in test_tokens:
            print(f"\n🔍 Testing {token['symbol']}: {token['description']}")
            
            # Check liquidity
            liquidity_info = executor.check_raydium_liquidity(token["address"])
            
            if liquidity_info.get("has_liquidity"):
                print(f"   ✅ Has Raydium liquidity: ${liquidity_info['liquidity']:,.2f}")
                print(f"   📊 24h Volume: ${liquidity_info['volume_24h']:,.2f}")
                print(f"   🏊 Pool ID: {liquidity_info['pool_id']}")
            else:
                print(f"   ❌ No Raydium liquidity found")
                
    except Exception as e:
        print(f"   ❌ Raydium liquidity check error: {e}")

def test_raydium_quote():
    """Test Raydium quote functionality"""
    print("\n🔍 Testing Raydium Quote API")
    
    try:
        executor = get_raydium_executor()
        
        # Test USDC -> BONK quote
        print("\n📊 Testing USDC -> BONK quote:")
        quote = executor.get_raydium_quote(
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
            1000000  # 1 USDC
        )
        
        if quote:
            print(f"   ✅ Quote successful:")
            print(f"   💰 In: {quote['inAmount']}")
            print(f"   💰 Out: {quote['outAmount']}")
            print(f"   📈 Price Impact: {quote['priceImpact']}%")
        else:
            print(f"   ❌ Quote failed")
            
        # Test SOL -> USDC quote (should work better)
        print("\n📊 Testing SOL -> USDC quote:")
        quote2 = executor.get_raydium_quote(
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            1000000000  # 1 SOL
        )
        
        if quote2:
            print(f"   ✅ Quote successful:")
            print(f"   💰 In: {quote2['inAmount']}")
            print(f"   💰 Out: {quote2['outAmount']}")
            print(f"   📈 Price Impact: {quote2['priceImpact']}%")
        else:
            print(f"   ❌ Quote failed")
            
    except Exception as e:
        print(f"   ❌ Raydium quote error: {e}")

def test_raydium_executor():
    """Test Raydium executor initialization"""
    print("\n🔍 Testing Raydium Executor")
    
    try:
        executor = get_raydium_executor()
        print(f"   ✅ Raydium executor initialized")
        
        # Test tradeability check
        print("\n🔍 Testing tradeability check for BONK:")
        tradeable = executor.check_token_tradeable_on_raydium("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")
        print(f"   Result: {'✅ Tradeable' if tradeable else '❌ Not tradeable'}")
        
    except Exception as e:
        print(f"   ❌ Raydium executor error: {e}")

def main():
    """Run all Raydium tests"""
    print("🚀 Raydium Fallback Test Suite")
    print("=" * 50)
    
    # Test 1: Liquidity Check
    test_raydium_liquidity_check()
    
    # Test 2: Quote API
    test_raydium_quote()
    
    # Test 3: Executor
    test_raydium_executor()
    
    print("\n" + "=" * 50)
    print("🏁 Raydium Fallback Test Complete")

if __name__ == "__main__":
    main()
