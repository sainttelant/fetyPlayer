"""
🎀 许可证管理系统
处理试用期和黄金会员
"""
import json
import os
import hashlib
from datetime import datetime, timedelta
from .config import PinkConfig

class LicenseManager:
   """许可证管理器"""
   def __init__(self):
       """初始化许可证管理器"""
       self.license_data = self.load_license()
   def load_license(self):
       """从加密文件加载许可证数据"""
       if os.path.exists(PinkConfig.LICENSE_FILE):
           try:
               with open(PinkConfig.LICENSE_FILE, 'rb') as f:
                   encrypted = f.read()
                   decrypted = self._decrypt(encrypted)
                   return json.loads(decrypted)
           except Exception as e:
               print(f"加载许可证失败: {e}")
               return self.create_trial_license()
       return self.create_trial_license()
   def save_license(self):
       """保存许可证数据到加密文件"""
       try:
           data_str = json.dumps(self.license_data)
           encrypted = self._encrypt(data_str)
           with open(PinkConfig.LICENSE_FILE, 'wb') as f:
               f.write(encrypted)
           return True
       except Exception as e:
           print(f"保存许可证失败: {e}")
           return False
   def _encrypt(self, data):
       """简单的XOR加密（生产环境应使用更强的加密）"""
       key = PinkConfig.ENCRYPTION_KEY
       data_bytes = data.encode('utf-8')
       encrypted = bytearray()
       for i, byte in enumerate(data_bytes):
           encrypted.append(byte ^ key[i % len(key)])
       return bytes(encrypted)
   def _decrypt(self, data):
       """简单的XOR解密"""
       key = PinkConfig.ENCRYPTION_KEY
       decrypted = bytearray()
       for i, byte in enumerate(data):
           decrypted.append(byte ^ key[i % len(key)])
       return decrypted.decode('utf-8')
   def create_trial_license(self):
       """创建新的试用许可证"""
       license_data = {
           "type": "trial",
           "start_date": datetime.now().isoformat(),
           "expiry_date": (datetime.now() + timedelta(days=PinkConfig.TRIAL_DAYS)).isoformat(),
           "golden_key": None
       }
       self.license_data = license_data
       self.save_license()
       return license_data
   def activate_golden_membership(self, key):
       """激活黄金会员"""
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
       """生成黄金会员密钥"""
       return hashlib.sha256(PinkConfig.DEMO_GOLDEN_KEY_SEED).hexdigest()[:16]
   def check_license(self):
       """检查许可证是否有效
       Returns:
           tuple: (is_valid: bool, message: str)
       """
       if self.license_data["type"] == "golden":
           return True, "💖 黄金会员已激活"
       if self.license_data["type"] == "trial":
           expiry = datetime.fromisoformat(self.license_data["expiry_date"])
           now = datetime.now()
           if now < expiry:
               days_left = (expiry - now).days
               return True, f"✨ 试用期: 还剩 {days_left} 天"
           else:
               return False, "试用期已过期"
       return False, "无效许可证"
   def get_golden_key_hint(self):
       """获取黄金密钥提示（用于演示）"""
       return self._generate_golden_key()
   def get_license_info(self):
       """获取详细许可证信息"""
       valid, message = self.check_license()
       license_type = self.license_data.get('type', 'Unknown')
       return {
           'valid': valid,
           'message': message,
           'type': license_type,
           'data': self.license_data
       }