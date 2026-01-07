"""
License management system for Banana Player
Handles trial licenses and golden membership
"""
import json
import os
import hashlib
from datetime import datetime, timedelta
from .config import Config

class LicenseManager:
   """Manages trial and golden membership licenses"""
   def __init__(self):
       self.license_data = self.load_license()
   def load_license(self):
       """Load license data from encrypted file"""
       if os.path.exists(Config.LICENSE_FILE):
           try:
               with open(Config.LICENSE_FILE, 'rb') as f:
                   encrypted = f.read()
                   decrypted = self._decrypt(encrypted)
                   return json.loads(decrypted)
           except Exception as e:
               print(f"Error loading license: {e}")
               return self.create_trial_license()
       else:
           return self.create_trial_license()
   def save_license(self):
       """Save license data to encrypted file"""
       try:
           data_str = json.dumps(self.license_data)
           encrypted = self._encrypt(data_str)
           with open(Config.LICENSE_FILE, 'wb') as f:
               f.write(encrypted)
           return True
       except Exception as e:
           print(f"Error saving license: {e}")
           return False
   def _encrypt(self, data):
       """Simple XOR encryption (use proper encryption in production)"""
       key = Config.ENCRYPTION_KEY
       data_bytes = data.encode('utf-8')
       encrypted = bytearray()
       for i, byte in enumerate(data_bytes):
           encrypted.append(byte ^ key[i % len(key)])
       return bytes(encrypted)
   def _decrypt(self, data):
       """Simple XOR decryption"""
       key = Config.ENCRYPTION_KEY
       decrypted = bytearray()
       for i, byte in enumerate(data):
           decrypted.append(byte ^ key[i % len(key)])
       return decrypted.decode('utf-8')
   def create_trial_license(self):
       """Create new trial license"""
       license_data = {
           "type": "trial",
           "start_date": datetime.now().isoformat(),
           "expiry_date": (datetime.now() + timedelta(days=Config.TRIAL_DAYS)).isoformat(),
           "golden_key": None
       }
       self.license_data = license_data
       self.save_license()
       return license_data
   def activate_golden_membership(self, key):
       """Activate golden membership with key"""
       expected_hash = self._generate_golden_key()
       if key.upper() == expected_hash.upper():
           self.license_data = {
               "type": "golden",
               "activation_date": datetime.now().isoformat(),
               "golden_key": key
           }
           self.save_license()
           return True
       return False
   def _generate_golden_key(self):
       """Generate golden membership key"""
       return hashlib.sha256(Config.DEMO_GOLDEN_KEY_SEED).hexdigest()[:16]
   def check_license(self):
       """Check if license is valid
       Returns:
           tuple: (is_valid: bool, message: str)
       """
       if self.license_data["type"] == "golden":
           return True, "Golden Membership Active"
       elif self.license_data["type"] == "trial":
           expiry = datetime.fromisoformat(self.license_data["expiry_date"])
           now = datetime.now()
           if now < expiry:
               days_left = (expiry - now).days
               return True, f"Trial: {days_left} days remaining"
           else:
               return False, "Trial Expired"
       return False, "Invalid License"
   def get_golden_key_hint(self):
       """Get hint for golden key (for demo purposes)"""
       return f"Golden Key: {self._generate_golden_key()}"
   def get_license_info(self):
       """Get detailed license information"""
       valid, message = self.check_license()
       license_type = self.license_data.get('type', 'Unknown')
       info = {
           'valid': valid,
           'message': message,
           'type': license_type,
           'data': self.license_data
       }
       return info