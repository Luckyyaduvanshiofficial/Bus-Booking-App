"""
Postman Test Runner - Automated API Testing
Executes critical test flows after recent bug fixes.
"""

import json
import requests
import time
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_RESULTS = []


class TestRunner:
    def __init__(self):
        self.tokens = {
            'customer': None,
            'operator': None,
            'admin': None
        }
        self.ids = {
            'bus': None,
            'booking': None,
            'payment': None
        }
        
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        result = {
            'test': test_name,
            'status': '✅ PASS' if passed else '❌ FAIL',
            'time': datetime.now().isoformat(),
            'details': details
        }
        TEST_RESULTS.append(result)
        print(f"{result['status']} - {test_name}: {details}")
        
    def run_all_tests(self):
        print("=" * 80)
        print("🧪 POSTMAN TEST RUNNER - Bus Booking Platform")
        print("=" * 80)
        print(f"Start Time: {datetime.now()}")
        print(f"Base URL: {BASE_URL}")
        print("=" * 80)
        
        try:
            # Phase 1: Authentication
            print("\n📌 PHASE 1: Authentication & Setup")
            self.test_auth_flow()
            
            # Phase 2: Bus Creation
            print("\n📌 PHASE 2: Bus Creation & Management")
            self.test_bus_creation()
            
            # Phase 3: Booking Creation (CRITICAL)
            print("\n📌 PHASE 3: Booking Creation (Race Condition Tests)")
            self.test_booking_creation()
            
            # Phase 4: Payment Flows (CRITICAL)
            print("\n📌 PHASE 4: Payment Flows")
            self.test_payment_flows()
            
            # Phase 5: Operator Actions (CRITICAL)
            print("\n📌 PHASE 5: Operator Accept/Reject")
            self.test_operator_actions()
            
            # Phase 6: Notifications
            print("\n📌 PHASE 6: Notification System")
            self.test_notifications()
            
        except Exception as e:
            self.log_result("Test Suite", False, f"Fatal Error: {str(e)}")
        
        # Print Summary
        self.print_summary()
        
    def test_auth_flow(self):
        """Test authentication flows."""
        # Test 1: Send OTP
        try:
            resp = requests.post(
                f"{BASE_URL}/users/auth/send-otp/",
                json={"phone": "+919876543210"}
            )
            self.log_result(
                "Send OTP",
                resp.status_code in [200, 201],
                f"Status: {resp.status_code}"
            )
        except Exception as e:
            self.log_result("Send OTP", False, str(e))
            
        # Test 2: Verify OTP (use test OTP: 123456)
        try:
            resp = requests.post(
                f"{BASE_URL}/users/auth/verify-otp/",
                json={"phone": "+919876543210", "otp": "123456"}
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.tokens['customer'] = data.get('token')
                self.log_result("Verify OTP", True, f"Token acquired: {self.tokens['customer'][:20]}...")
            else:
                self.log_result("Verify OTP", False, f"Status: {resp.status_code}")
        except Exception as e:
            self.log_result("Verify OTP", False, str(e))
            
        # Test 3: Register Customer
        if self.tokens['customer']:
            try:
                resp = requests.post(
                    f"{BASE_URL}/users/auth/register/",
                    headers={"Authorization": f"Token {self.tokens['customer']}"},
                    json={
                        "phone": "+919876543210",
                        "full_name": "Test Customer",
                        "email": "customer@test.com",
                        "role": "customer"
                    }
                )
                self.log_result(
                    "Register Customer",
                    resp.status_code in [200, 201],
                    f"Status: {resp.status_code}"
                )
            except Exception as e:
                self.log_result("Register Customer", False, str(e))
                
    def test_bus_creation(self):
        """Test bus creation by operator."""
        # Note: This requires an operator account - skipping if no operator token
        if not self.tokens.get('operator'):
            self.log_result(
                "Bus Creation",
                False,
                "No operator token - create operator account manually first"
            )
            return
            
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
            resp = requests.post(
                f"{BASE_URL}/buses/buses/",
                headers={"Authorization": f"Token {self.tokens['operator']}"},
                json={
                    "name": "Test Bus",
                    "registration_number": "TEST123",
                    "capacity": 40,
                    "bus_type": "ac_sleeper",
                    "base_price_per_km": "15.00",
                    "available_from": tomorrow
                }
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.ids['bus'] = data.get('id')
                self.log_result("Create Bus", True, f"Bus ID: {self.ids['bus']}")
            else:
                self.log_result("Create Bus", False, f"Status: {resp.status_code}, {resp.text}")
        except Exception as e:
            self.log_result("Create Bus", False, str(e))
            
    def test_booking_creation(self):
        """Test booking creation with race condition prevention."""
        if not self.tokens.get('customer') or not self.ids.get('bus'):
            self.log_result(
                "Booking Creation",
                False,
                "Missing customer token or bus ID"
            )
            return
            
        # Test 1: Create valid booking
        try:
            pickup_date = (datetime.now() + timedelta(days=7)).date().isoformat()
            resp = requests.post(
                f"{BASE_URL}/bookings/bookings/",
                headers={"Authorization": f"Token {self.tokens['customer']}"},
                json={
                    "bus": self.ids['bus'],
                    "pickup_date": pickup_date,
                    "pickup_location": "City Center",
                    "drop_location": "Airport",
                    "passenger_count": 2,
                    "payment_mode": "online_full"
                }
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.ids['booking'] = data.get('id')
                self.log_result(
                    "Create Booking (Valid)",
                    True,
                    f"Booking ID: {self.ids['booking']}, Amount: {data.get('total_amount')}"
                )
            else:
                self.log_result(
                    "Create Booking (Valid)",
                    False,
                    f"Status: {resp.status_code}, {resp.text}"
                )
        except Exception as e:
            self.log_result("Create Booking (Valid)", False, str(e))
            
        # Test 2: Try to book same date (should fail with BOK-SERV-CONFLICT-001)
        try:
            resp = requests.post(
                f"{BASE_URL}/bookings/bookings/",
                headers={"Authorization": f"Token {self.tokens['customer']}"},
                json={
                    "bus": self.ids['bus'],
                    "pickup_date": pickup_date,
                    "pickup_location": "Downtown",
                    "drop_location": "Airport",
                    "passenger_count": 3,
                    "payment_mode": "online_full"
                }
            )
            # Should fail with 400 and error code BOK-SERV-CONFLICT-001
            if resp.status_code == 400:
                error = resp.json()
                has_correct_code = 'BOK-SERV-CONFLICT-001' in str(error)
                self.log_result(
                    "Race Condition Prevention",
                    has_correct_code,
                    f"Correctly rejected: {error}"
                )
            else:
                self.log_result(
                    "Race Condition Prevention",
                    False,
                    f"Expected 400, got {resp.status_code}"
                )
        except Exception as e:
            self.log_result("Race Condition Prevention", False, str(e))
            
        # Test 3: Try to book past date (should fail)
        try:
            past_date = (datetime.now() - timedelta(days=1)).date().isoformat()
            resp = requests.post(
                f"{BASE_URL}/bookings/bookings/",
                headers={"Authorization": f"Token {self.tokens['customer']}"},
                json={
                    "bus": self.ids['bus'],
                    "pickup_date": past_date,
                    "pickup_location": "Downtown",
                    "drop_location": "Airport",
                    "passenger_count": 2,
                    "payment_mode": "online_full"
                }
            )
            passed = resp.status_code == 400
            self.log_result(
                "Past Date Validation",
                passed,
                f"Status: {resp.status_code}"
            )
        except Exception as e:
            self.log_result("Past Date Validation", False, str(e))
            
    def test_payment_flows(self):
        """Test payment creation and webhooks."""
        if not self.ids.get('booking'):
            self.log_result("Payment Flows", False, "No booking ID available")
            return
            
        # Test 1: Create payment
        try:
            resp = requests.post(
                f"{BASE_URL}/bookings/payments/",
                headers={"Authorization": f"Token {self.tokens['customer']}"},
                json={
                    "booking": self.ids['booking'],
                    "amount": "1000.00",
                    "payment_method": "upi"
                }
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                self.ids['payment'] = data.get('id')
                self.log_result(
                    "Create Payment",
                    True,
                    f"Payment ID: {self.ids['payment']}"
                )
            else:
                self.log_result(
                    "Create Payment",
                    False,
                    f"Status: {resp.status_code}, {resp.text}"
                )
        except Exception as e:
            self.log_result("Create Payment", False, str(e))
            
    def test_operator_actions(self):
        """Test operator accept/reject booking."""
        if not self.ids.get('booking') or not self.tokens.get('operator'):
            self.log_result(
                "Operator Actions",
                False,
                "Missing booking ID or operator token"
            )
            return
            
        # Test: Accept booking
        try:
            resp = requests.post(
                f"{BASE_URL}/bookings/bookings/{self.ids['booking']}/accept/",
                headers={"Authorization": f"Token {self.tokens['operator']}"}
            )
            self.log_result(
                "Accept Booking",
                resp.status_code in [200, 201],
                f"Status: {resp.status_code}"
            )
        except Exception as e:
            self.log_result("Accept Booking", False, str(e))
            
    def test_notifications(self):
        """Test notification system."""
        if not self.tokens.get('customer'):
            self.log_result("Notifications", False, "No customer token")
            return
            
        try:
            resp = requests.get(
                f"{BASE_URL}/users/notifications/",
                headers={"Authorization": f"Token {self.tokens['customer']}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get('results', []))
                self.log_result(
                    "List Notifications",
                    True,
                    f"Found {count} notifications"
                )
            else:
                self.log_result(
                    "List Notifications",
                    False,
                    f"Status: {resp.status_code}"
                )
        except Exception as e:
            self.log_result("List Notifications", False, str(e))
            
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total = len(TEST_RESULTS)
        passed = sum(1 for r in TEST_RESULTS if '✅' in r['status'])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in TEST_RESULTS:
                if '❌' in r['status']:
                    print(f"  - {r['test']}: {r['details']}")
                    
        print("\n" + "=" * 80)
        print(f"End Time: {datetime.now()}")
        print("=" * 80)
        
        # Save results to file
        with open('postman_test_results.json', 'w') as f:
            json.dump(TEST_RESULTS, f, indent=2)
        print("\n💾 Results saved to: postman_test_results.json")


if __name__ == "__main__":
    print("""
    ⚠️  PREREQUISITES:
    1. Django server running on http://localhost:8000
    2. Database with test data
    3. Create operator account manually and update operator token in script
    4. Brevo integration configured (optional for notification tests)
    
    Press CTRL+C to cancel, or press Enter to continue...
    """)
    
    input()
    
    runner = TestRunner()
    runner.run_all_tests()
