# token_scraper_improved.py
import csv
import yaml
import time
import random
from datetime import datetime
from http_utils import get_json
from collections import defaultdict
from config_loader import get_config, get_config_bool

# Dynamic config loading
def get_token_scraper_config():
    """Get current configuration values dynamically"""
    return {
        'TELEGRAM_ENABLED': not get_config_bool("test_mode", True),
        'TELEGRAM_BOT_TOKEN': get_config("telegram_bot_token"),
        'TELEGRAM_CHAT_ID': get_config("telegram_chat_id")
    }

# === Enhanced Filters for TRADING ===
EXCLUDED_KEYWORDS = ["INU", "PEPE", "DOGE", "SHIBA", "SAFE", "ELON"]  # Removed "AI" and "MOON" for more opportunities
ENFORCE_KEYWORDS = True  # Re-enable keyword filtering for better quality

# Enhanced promotional content filters
PROMOTIONAL_KEYWORDS = [
    "appstore", "playstore", "download", "available", "marketplace", "app", "quotes", 
    "motivation", "inspiration", "mindset", "growth", "success", "productivity",
    "trending", "viral", "explore", "positive", "selfimprovement", "nevergiveup",
    "daily", "best", "for", "you", "creators", "memes", "defi", "tba", "launch",
    "presale", "airdrop", "whitelist", "ico", "ido", "fairlaunch", "stealth"
]

# Enhanced API sources for better diversity
PRIMARY_URLS = [
    "https://api.dexscreener.com/latest/dex/search/?q=trending",
    "https://api.dexscreener.com/latest/dex/search/?q=hot",
    "https://api.dexscreener.com/latest/dex/search/?q=gaining",
    "https://api.dexscreener.com/latest/dex/search/?q=volume",
    "https://api.dexscreener.com/latest/dex/search/?q=liquidity",
    "https://api.dexscreener.com/latest/dex/search/?q=new",
    "https://api.dexscreener.com/latest/dex/search/?q=rising",
    "https://api.dexscreener.com/latest/dex/search/?q=popular",
    "https://api.dexscreener.com/latest/dex/search/?q=active",
    "https://api.dexscreener.com/latest/dex/search/?q=top",
    "https://api.dexscreener.com/latest/dex/search/?q=moon",
    "https://api.dexscreener.com/latest/dex/search/?q=pump",
    "https://api.dexscreener.com/latest/dex/search/?q=surge",
]

FALLBACK_URLS = [
    "https://api.dexscreener.com/latest/dex/search/?q=trending",
    "https://api.dexscreener.com/latest/dex/search/?q=hot",
    "https://api.dexscreener.com/latest/dex/search/?q=new",
    "https://api.dexscreener.com/latest/dex/search/?q=volume",
]

CSV_PATH = "trending_tokens.csv"
CSV_FIELDS = [
    "fetched_at", "symbol", "address", "dex", "chainId",
    "priceUsd", "volume24h", "liquidity"
]

def send_telegram_message(message):
    config = get_token_scraper_config()
    if not config['TELEGRAM_ENABLED']:
        return
    import requests
    url = f"https://api.telegram.org/bot{config['TELEGRAM_BOT_TOKEN']}/sendMessage"
    payload = {"chat_id": config['TELEGRAM_CHAT_ID'], "text": message}
    try:
        requests.post(url, data=payload, timeout=8)
    except Exception as e:
        print("⚠️ Telegram error:", e)

def is_promotional_content(symbol, description=""):
    """Enhanced check if content is promotional/spam rather than a real token"""
    if not symbol:
        return True
    
    # Check for promotional keywords in symbol
    symbol_lower = symbol.lower()
    for keyword in PROMOTIONAL_KEYWORDS:
        if keyword in symbol_lower:
            return True
    
    # Check for very long symbols (likely promotional text)
    if len(symbol) > 20:  # Increased from 15 to 20 for more opportunities
        return True
    
    # Check for symbols with too many spaces (likely sentences)
    if symbol.count(' ') > 3:  # Increased from 2 to 3 for more opportunities
        return True
    
    # Check for symbols with hashtags or special characters
    if any(char in symbol for char in ['#', '@', 'http', 'www', '.com', '.io']):
        return True
    
    # Check for symbols that look like URLs or app descriptions
    if any(word in symbol_lower for word in ['http', 'www', 'app', 'download', 'available', 'launch']):
        return True
    
    # Check for symbols that are just numbers or very short
    if len(symbol) < 2 or symbol.isdigit():
        return True
    
    return False

def is_valid_token_data(symbol, address, volume24h, liquidity):
    """Enhanced validation that we have real token data with strict liquidity requirements"""
    if not symbol or not address:
        return False
    
    # Must have some trading activity
    if volume24h <= 0 or liquidity <= 0:
        return False
    
    # Address should be a valid format (not empty or obviously wrong)
    if len(address) < 10:
        return False
    
    # STRICT minimum requirements to prevent trading on low liquidity tokens
    # These match the config.yaml thresholds to ensure consistency
    if volume24h < 50000:  # Minimum $50k volume (increased from 10)
        return False
    
    if liquidity < 50000:  # Minimum $50k liquidity (increased from 50)
        return False
    
    return True

def calculate_token_score(symbol, volume24h, liquidity, chain_id):
    """Calculate a quality score for token filtering with updated thresholds"""
    score = 0
    
    # Volume scoring (0-3 points) - updated for higher thresholds
    if volume24h >= 500000:  # $500k+ volume
        score += 3
    elif volume24h >= 200000:  # $200k+ volume
        score += 2
    elif volume24h >= 100000:  # $100k+ volume
        score += 1
    
    # Liquidity scoring (0-3 points) - updated for higher thresholds
    if liquidity >= 500000:  # $500k+ liquidity
        score += 3
    elif liquidity >= 200000:  # $200k+ liquidity
        score += 2
    elif liquidity >= 100000:  # $100k+ liquidity
        score += 1
    
    # Symbol quality scoring (0-2 points)
    symbol_lower = symbol.lower()
    
    # Penalize common spam symbols
    spam_indicators = ['hot', 'moon', 'safe', 'elon', 'inu', 'doge', 'shiba', 'pepe']
    if any(indicator in symbol_lower for indicator in spam_indicators):
        score -= 1
    
    # Bonus for unique/interesting symbols
    if len(symbol) >= 4 and len(symbol) <= 8:
        score += 1
    
    # Chain-specific adjustments
    if chain_id == "ethereum":
        score += 1  # Bonus for Ethereum tokens
    elif chain_id in ["solana", "base"]:
        score += 0  # Neutral for other major chains
    else:
        score -= 1  # Penalty for less common chains
    
    return max(0, score)  # Ensure non-negative

def ensure_symbol_diversity(tokens, max_same_symbol=3):
    """Ensure we don't get too many tokens with the same symbol"""
    symbol_counts = defaultdict(int)
    diverse_tokens = []
    
    for token in tokens:
        symbol = token.get("symbol", "").upper()
        if symbol_counts[symbol] < max_same_symbol:
            diverse_tokens.append(token)
            symbol_counts[symbol] += 1
        else:
            print(f"🔄 Skipping duplicate symbol: {symbol} (already have {symbol_counts[symbol]})")
    
    return diverse_tokens

def _append_all_to_csv(rows):
    write_header = False
    try:
        with open(CSV_PATH, "r", newline="") as _:
            pass
    except FileNotFoundError:
        write_header = True

    try:
        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if write_header:
                writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"📁 Appended {len(rows)} rows to {CSV_PATH}")
    except Exception as e:
        print("⚠️ Failed to append CSV:", e)

def fetch_trending_tokens(limit=100):
    """Enhanced token discovery with better diversity and quality filtering"""
    headers = {"User-Agent": "Mozilla/5.0 (bot)"}
    all_pairs = []

    # Try multiple primary sources with randomization
    primary_urls = PRIMARY_URLS.copy()
    random.shuffle(primary_urls)  # Randomize order to avoid bias
    
    for u in primary_urls:
        try:
            data = get_json(u, headers=headers, timeout=10, retries=3, backoff=0.7)
            if data and data.get("pairs"):
                pairs = data.get("pairs", [])
                all_pairs.extend(pairs)
                print(f"✅ Fetched {len(pairs)} tokens from {u}")
                
                # Add small delay between requests
                time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Primary fetch failed ({u}): {e}")

    # If no primary sources worked, try fallbacks
    if not all_pairs:
        for u in FALLBACK_URLS:
            try:
                data = get_json(u, headers=headers, timeout=10, retries=3, backoff=0.7)
                if data and data.get("pairs"):
                    pairs = data.get("pairs", [])
                    all_pairs.extend(pairs)
                    print(f"🔁 Used fallback source: {u} - {len(pairs)} tokens")
                break
            except Exception as e:
                print(f"⚠️ Fallback fetch failed ({u}): {e}")

    if not all_pairs:
        print("❌ Error: all trending sources failed.")
        return []

    # Remove duplicates based on pair address
    unique_pairs = []
    seen_addresses = set()
    for pair in all_pairs:
        addr = pair.get("pairAddress")
        if addr and addr not in seen_addresses:
            unique_pairs.append(pair)
            seen_addresses.add(addr)
    
    print(f"🔍 Found {len(unique_pairs)} unique trending tokens from {len(all_pairs)} total...")

    # Load supported chains from config early
    supported_chains = get_config("supported_chains", ["ethereum"])
    
    print(f"🔗 Supported chains: {supported_chains}")
    
    # Enhanced filtering and scoring
    fetched_at = datetime.utcnow().isoformat()
    all_rows = []
    valid_tokens_count = 0
    unsupported_chain_count = 0
    
    for pair in unique_pairs:
        symbol = (pair.get("baseToken", {}) or {}).get("symbol") or ""
        addr = pair.get("pairAddress")
        dex = pair.get("dexId")
        chain = pair.get("chainId") or ""
        price = float(pair.get("priceUsd") or 0)
        vol24 = float((pair.get("volume", {}) or {}).get("h24") or 0)
        liq = float((pair.get("liquidity", {}) or {}).get("usd") or 0)
        
        # Early chain filtering - skip unsupported chains immediately
        if chain.lower() not in supported_chains:
            unsupported_chain_count += 1
            continue
        
        # Enhanced promotional content filtering
        if is_promotional_content(symbol):
            print(f"🚫 Skipping promotional content: {symbol[:50]}...")
            continue
        
        # Reject tokens with suspiciously low prices (likely scams)
        if price < 0.000001:  # Less than $0.000001
            print(f"🚫 Skipping suspiciously low price token: {symbol} (${price})")
            continue
        
        # Reject tokens with extremely low volume/liquidity ratios (manipulation indicators)
        if liq > 0 and vol24 > 0:
            vol_liq_ratio = vol24 / liq
            if vol_liq_ratio < 0.1:  # Volume less than 10% of liquidity (suspicious)
                print(f"🚫 Skipping low volume/liquidity ratio: {symbol} (ratio: {vol_liq_ratio:.2f})")
                continue
            
        # Enhanced token data validation
        if not is_valid_token_data(symbol, addr, vol24, liq):
            print(f"🚫 Skipping invalid token data: {symbol} (vol: ${vol24}, liq: ${liq})")
            continue
        
        valid_tokens_count += 1
        all_rows.append({
            "fetched_at": fetched_at,
            "symbol": symbol,
            "address": addr,
            "dex": dex,
            "chainId": chain,
            "priceUsd": price,
            "volume24h": vol24,
            "liquidity": liq
        })
    
    print(f"✅ Found {valid_tokens_count} valid tokens out of {len(unique_pairs)} total pairs")
    print(f"⛔ Skipped {unsupported_chain_count} tokens from unsupported chains")

    if all_rows:
        _append_all_to_csv(all_rows)
    else:
        print("ℹ️ No pairs found to log.")

    # Enhanced trading token selection with scoring
    tokens_for_trading = []
    
    scored_tokens = []
    
    for row in all_rows:
        chain = (row["chainId"] or "").lower()
        
        symbol = (row["symbol"] or "").upper()
        volume24h = row["volume24h"]
        liquidity = row["liquidity"]
        
        # Calculate quality score
        score = calculate_token_score(symbol, volume24h, liquidity, chain)
        
        # Keyword filtering
        blocked = any(k in symbol for k in EXCLUDED_KEYWORDS)
        if blocked and ENFORCE_KEYWORDS:
            print(f"⛔ {symbol} — blocked keyword.")
            continue
        
        print(f"🧪 {symbol} | Vol: ${volume24h:,.0f} | LQ: ${liquidity:,.0f} | Score: {score}/8 | Chain: {chain}")
        
        # Only include tokens with good scores (increased minimum for quality)
        if score >= 2:  # Minimum score of 2 for quality tokens (increased from 0)
            scored_tokens.append({
                "symbol": symbol,
                "address": row["address"],
                "dex": row["dex"],
                "chainId": row["chainId"],
                "priceUsd": row["priceUsd"],
                "volume24h": volume24h,
                "liquidity": liquidity,
                "score": score
            })
        else:
            print(f"⛔ {symbol} rejected - score too low: {score}/8")
    
    # Sort by score (highest first) and ensure diversity
    scored_tokens.sort(key=lambda x: x["score"], reverse=True)
    
    # Ensure symbol diversity
    diverse_tokens = ensure_symbol_diversity(scored_tokens, max_same_symbol=5)  # Increased from 2 to 5 for more opportunities
    
    # Take top tokens up to limit
    tokens_for_trading = diverse_tokens[:limit]
    
    # Remove score from final output
    for token in tokens_for_trading:
        token.pop("score", None)
    
    print(f"🎯 Selected {len(tokens_for_trading)} high-quality, diverse tokens for trading")
    
    if not tokens_for_trading:
        print("⚠️ No tokens passed enhanced filtering. Will try alternative sources...")
        return []

    return tokens_for_trading

if __name__ == "__main__":
    fetch_trending_tokens()
