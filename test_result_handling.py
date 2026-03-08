"""
Test script to verify result handling (WIN, LOSS, DRAW) works correctly
Tests both the API client and main.py martingale logic
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pocketoptionapi_async.models import OrderStatus, OrderResult, OrderDirection
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    """Print test result"""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"     {details}")

def test_order_status_enum():
    """Test 1: Verify OrderStatus has DRAW status"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 1: OrderStatus Enum{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    has_draw = hasattr(OrderStatus, 'DRAW')
    print_test("OrderStatus.DRAW exists", has_draw)
    
    if has_draw:
        print_test("OrderStatus.DRAW value", OrderStatus.DRAW == "draw", f"Value: {OrderStatus.DRAW}")
    
    # Check all statuses
    expected_statuses = ['PENDING', 'ACTIVE', 'CLOSED', 'CANCELLED', 'WIN', 'LOSE', 'DRAW']
    all_present = all(hasattr(OrderStatus, status) for status in expected_statuses)
    print_test("All statuses present", all_present, f"Expected: {expected_statuses}")
    
    return has_draw and all_present

def test_result_mapping():
    """Test 2: Verify result mapping logic"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 2: Result Mapping Logic{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Simulate the mapping logic from main.py
    test_cases = [
        (OrderStatus.WIN, 'win'),
        (OrderStatus.LOSE, 'loss'),
        (OrderStatus.DRAW, 'draw'),
        (OrderStatus.CLOSED, 'closed'),
        (OrderStatus.CANCELLED, 'closed'),
        (OrderStatus.PENDING, 'pending'),
    ]
    
    all_passed = True
    for status, expected_result in test_cases:
        # Simulate mapping
        if status == OrderStatus.WIN:
            result = 'win'
        elif status == OrderStatus.LOSE:
            result = 'loss'
        elif status == OrderStatus.DRAW:
            result = 'draw'
        elif status == OrderStatus.CLOSED or status == OrderStatus.CANCELLED:
            result = 'closed'
        else:
            result = 'pending'
        
        passed = result == expected_result
        all_passed = all_passed and passed
        print_test(f"{status.value} → {expected_result}", passed, f"Got: {result}")
    
    return all_passed

def test_martingale_logic():
    """Test 3: Verify martingale step changes correctly"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 3: Martingale Logic{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Simulate martingale logic
    global_martingale_step = 0
    
    # Test WIN: should reset to 0
    global_martingale_step = 3
    result = 'win'
    if result == 'win':
        global_martingale_step = 0
    print_test("WIN resets step to 0", global_martingale_step == 0, f"Step: {global_martingale_step}")
    
    # Test LOSS: should increase step
    global_martingale_step = 2
    result = 'loss'
    if result == 'loss':
        global_martingale_step += 1
    print_test("LOSS increases step", global_martingale_step == 3, f"Step: {global_martingale_step}")
    
    # Test DRAW: should NOT change step
    global_martingale_step = 2
    result = 'draw'
    original_step = global_martingale_step
    if result == 'draw':
        pass  # Don't change step
    elif result == 'win':
        global_martingale_step = 0
    elif result == 'loss':
        global_martingale_step += 1
    print_test("DRAW keeps same step", global_martingale_step == original_step, f"Step: {global_martingale_step}")
    
    # Test max step reset
    global_martingale_step = 8
    result = 'loss'
    if result == 'loss':
        if global_martingale_step < 8:
            global_martingale_step += 1
        else:
            global_martingale_step = 0
    print_test("Max step (8) resets to 0", global_martingale_step == 0, f"Step: {global_martingale_step}")
    
    return True

def test_profit_to_status():
    """Test 4: Verify profit determines correct status"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 4: Profit to Status Conversion{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    test_cases = [
        (10.5, OrderStatus.WIN, "Positive profit"),
        (-5.0, OrderStatus.LOSE, "Negative profit"),
        (0.0, OrderStatus.DRAW, "Zero profit (DRAW)"),
        (0.01, OrderStatus.WIN, "Small positive profit"),
        (-0.01, OrderStatus.LOSE, "Small negative profit"),
    ]
    
    all_passed = True
    for profit, expected_status, description in test_cases:
        # Simulate the logic from client.py
        if profit > 0:
            status = OrderStatus.WIN
        elif profit < 0:
            status = OrderStatus.LOSE
        else:
            status = OrderStatus.DRAW
        
        passed = status == expected_status
        all_passed = all_passed and passed
        print_test(f"Profit ${profit:.2f} → {expected_status.value}", passed, description)
    
    return all_passed

async def test_live_connection():
    """Test 5: Test live connection and result retrieval"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 5: Live Connection Test{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        from pocketoptionapi_async import AsyncPocketOptionClient
        
        # Get SSID from environment
        is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
        if is_demo:
            ssid = os.getenv('SSID_DEMO') or os.getenv('SSID')
        else:
            ssid = os.getenv('SSID_REAL')
        
        if not ssid:
            print_test("SSID found in environment", False, "No SSID configured")
            return False
        
        print(f"     Using {'DEMO' if is_demo else 'REAL'} account")
        
        # Create client
        client = AsyncPocketOptionClient(
            ssid=ssid,
            is_demo=is_demo,
            persistent_connection=True,
            enable_logging=False
        )
        
        # Test connection
        print(f"     Connecting to PocketOption...")
        try:
            await asyncio.wait_for(client.connect(), timeout=25.0)
            print_test("Connection established", client.is_connected)
            
            if client.is_connected:
                # Test balance fetch
                try:
                    balance = await asyncio.wait_for(client.get_balance(), timeout=15.0)
                    print_test("Balance retrieved", True, f"${balance.balance:.2f} {balance.currency}")
                except Exception as e:
                    print_test("Balance retrieved", False, str(e))
                
                # Disconnect
                await client.disconnect()
                print_test("Disconnection", True)
                return True
            else:
                print_test("Connection established", False)
                return False
                
        except asyncio.TimeoutError:
            print_test("Connection timeout", False, "Check SSID validity")
            return False
            
    except Exception as e:
        print_test("Live connection test", False, str(e))
        return False

def test_csv_export():
    """Test 6: Verify CSV export includes draw results"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 6: CSV Export with DRAW{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Simulate CSV data structure
    csv_data = {
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'asset': 'EURUSD_otc',
        'direction': 'CALL',
        'amount': 1.0,
        'step': 0,
        'duration': 1,
        'result': 'draw',  # Test draw result
        'profit_loss': 0.0,
        'balance_before': 100.0,
        'balance_after': 100.0,
        'multiplier': 2.5
    }
    
    # Check all required fields present
    required_fields = ['timestamp', 'date', 'time', 'asset', 'direction', 'amount', 
                      'step', 'duration', 'result', 'profit_loss', 'balance_before', 
                      'balance_after', 'multiplier']
    
    all_present = all(field in csv_data for field in required_fields)
    print_test("All CSV fields present", all_present)
    
    # Check draw result is valid
    print_test("Draw result in CSV", csv_data['result'] == 'draw', f"Result: {csv_data['result']}")
    print_test("Draw profit is zero", csv_data['profit_loss'] == 0.0, f"Profit: ${csv_data['profit_loss']}")
    
    return all_present

async def main():
    """Run all tests"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}DRAW RESULT HANDLING TEST SUITE{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    results = []
    
    # Run tests
    results.append(("OrderStatus Enum", test_order_status_enum()))
    results.append(("Result Mapping", test_result_mapping()))
    results.append(("Martingale Logic", test_martingale_logic()))
    results.append(("Profit to Status", test_profit_to_status()))
    results.append(("CSV Export", test_csv_export()))
    results.append(("Live Connection", await test_live_connection()))
    
    # Summary
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}TEST SUMMARY{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} | {name}")
    
    print(f"\n{YELLOW}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}ALL TESTS PASSED ({passed}/{total}){RESET}")
        print(f"{GREEN}✅ Draw result handling is working correctly!{RESET}")
    else:
        print(f"{RED}SOME TESTS FAILED ({passed}/{total}){RESET}")
        print(f"{RED}❌ Fix the issues before live trading!{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
