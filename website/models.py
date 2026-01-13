"""
数据库模型
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')
    payments = db.relationship('PaymentRecord', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_premium_active(self):
        """检查会员是否有效"""
        if not self.is_premium:
            return False
        
        active_subscription = self.subscriptions.filter(
            Subscription.end_date >= datetime.utcnow(),
            Subscription.status == 'active'
        ).first()
        
        return active_subscription is not None
    
    def __repr__(self):
        return f'<User {self.username}>'


class Subscription(db.Model):
    """订阅模型"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # monthly, quarterly, yearly
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, expired, cancelled
    price = db.Column(db.Float)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment_records.id'))
    
    def __repr__(self):
        return f'<Subscription {self.user_id} - {self.plan_type}>'


class PaymentRecord(db.Model):
    """支付记录模型"""
    __tablename__ = 'payment_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')  # USD, CNY, BTC
    payment_method = db.Column(db.String(20), nullable=False)  # alipay, bitcoin
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    transaction_id = db.Column(db.String(256))  # 第三方支付平台的交易ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    subscription = db.relationship('Subscription', backref='payment', uselist=False)
    
    def __repr__(self):
        return f'<Payment {self.user_id} - {self.amount} {self.currency}>'
