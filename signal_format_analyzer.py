import re

def analyze_signal_format(message_text: str) -> dict:
    """Analyze different signal formats from various channels"""
    result = {
        'asset': None,
        'direction': None, 
        'duration': None,
        'detected_patterns': []
    }
    
    print(f"Analyzing message: {message_text[:100]}...")
    
    # Asset patterns (try multiple formats)
    asset_patterns = [
        (r'📈\s*Pair:\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)', 'Current format with emoji'),
        (r'Pair[:\s]*([A-Z]+/[A-Z]+(?:\s+OTC)?)', 'Pair: without emoji'),
        (r'Asset[:\s]*([A-Z]+/[A-Z]+(?:\s+OTC)?)', 'Asset: format'),
        (r'([A-Z]+/[A-Z]+(?:\s+OTC)?)', 'Just the pair'),
        (r'💱\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)', 'Currency emoji + pair'),
        (r'📊\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)', 'Chart emoji + pair')
    ]
    
    for pattern, description in asset_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            result['asset'] = match.group(1).strip()
            result['detected_patterns'].append(f"Asset: {description}")
            break
    
    # Duration patterns
    time_patterns = [
        (r'⌛[️]?\s*time:\s*(\d+)\s*min', 'Current format with emoji'),
        (r'time[:\s]*(\d+)\s*min', 'time: without emoji'),
        (r'duration[:\s]*(\d+)\s*min', 'duration: format'),
        (r'(\d+)\s*min(?:ute)?s?', 'Just minutes'),
        (r'⏰\s*(\d+)\s*min', 'Clock emoji + minutes'),
        (r'expire[s]?:\s*(\d+)\s*min', 'expire: format')
    ]
    
    for pattern, description in time_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            result['duration'] = int(match.group(1))
            result['detected_patterns'].append(f"Duration: {description}")
            break
    
    # Direction patterns
    direction_patterns = [
        (r'^(Buy|Sell)\s*$', 'Exact Buy/Sell'),
        (r'📈\s*(Buy|Call|Up)', 'Up direction with emoji'),
        (r'📉\s*(Sell|Put|Down)', 'Down direction with emoji'),
        (r'\b(Buy|Call|Up)\b', 'Buy/Call/Up anywhere'),
        (r'\b(Sell|Put|Down)\b', 'Sell/Put/Down anywhere'),
        (r'⬆️\s*(Buy|Call)', 'Up arrow + direction'),
        (r'⬇️\s*(Sell|Put)', 'Down arrow + direction')
    ]
    
    for pattern, description in direction_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE | re.MULTILINE)
        if match:
            direction = match.group(1).upper()
            # Normalize direction
            if direction in ['CALL', 'UP']:
                direction = 'BUY'
            elif direction in ['PUT', 'DOWN']:
                direction = 'SELL'
            result['direction'] = direction
            result['detected_patterns'].append(f"Direction: {description}")
            break
    
    return result

# Test with current format
current_message = """📈 Pair: GBP/JPY OTC
⌛️ time: 1 min"""

print("=== Testing Current Format ===")
result = analyze_signal_format(current_message)
print(f"Asset: {result['asset']}")
print(f"Duration: {result['duration']}")
print(f"Direction: {result['direction']}")
print(f"Patterns: {result['detected_patterns']}")

print("\n=== Testing Possible VIP Formats ===")

# Test different possible formats
test_formats = [
    "💱 EUR/USD OTC\n⏰ 5 minutes\n⬆️ BUY",
    "Pair: AUD/JPY OTC\nDuration: 3 min\n📈 CALL", 
    "📊 USD/CAD\n2 min\nSELL",
    "Asset: EUR/GBP OTC\nExpire: 1 min\nPUT"
]

for i, test_msg in enumerate(test_formats, 1):
    print(f"\n--- Test Format {i} ---")
    result = analyze_signal_format(test_msg)
    print(f"Message: {test_msg}")
    print(f"Asset: {result['asset']}")
    print(f"Duration: {result['duration']}")
    print(f"Direction: {result['direction']}")
    print(f"Detected: {result['detected_patterns']}")
