# Banana Player 用户登录和支付系统

## 功能特性

### 1. 用户认证系统
- 用户注册：支持用户名、邮箱、密码注册
- 用户登录：支持用户名/邮箱登录
- 用户登出：安全退出登录
- 会话管理：基于Flask-Login的安全会话管理

### 2. 会员系统
- 三种会员套餐：
  - 月度会员：¥9.9/月
  - 季度会员：¥28.9/季
  - 年度会员：¥98.9/年
- 会员权益：
  - 无限观看时长（非会员限制15秒）
  - 高清画质
  - 优先播放体验
  - 无广告干扰
  - 独家内容访问

### 3. 支付系统
- 支持两种支付方式：
  - **支付宝**：人民币支付
  - **比特币**：美元支付
- 模拟支付流程（可扩展为真实支付）
- 支付状态跟踪
- 自动激活会员权益

### 4. 用户权限集成
- 自动检测用户会员状态
- 会员用户无观看时长限制
- 非会员用户15秒观看限制
- 视频播放时实时权限验证

## 安装说明

### 1. 安装依赖

```bash
cd website
pip install -r requirements.txt
```

新增的依赖包：
- Flask-Login==0.6.3 - 用户会话管理
- Flask-SQLAlchemy==3.0.5 - 数据库ORM

### 2. 配置

配置文件已更新（`website/config.py`），新增配置项：
```python
# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 会员配置
PREMIUM_PRICES = {
    'monthly': {'price': 9.9, 'duration_days': 30, 'name': '月度会员'},
    'quarterly': {'price': 28.9, 'duration_days': 90, 'name': '季度会员'},
    'yearly': {'price': 98.9, 'duration_days': 365, 'name': '年度会员'}
}
```

### 3. 数据库初始化

数据库会在首次运行时自动创建（app.db文件）。

数据库模型：
- **User**：用户信息
  - id, username, email, password_hash
  - is_premium, created_at, last_login
- **Subscription**：订阅记录
  - user_id, plan_type, start_date, end_date
  - status, price, payment_id
- **PaymentRecord**：支付记录
  - user_id, amount, currency, payment_method
  - status, transaction_id, created_at, completed_at

### 4. 运行服务器

```bash
cd website
python app.py
```

服务器将在 `http://localhost:5000` 启动。

## 使用说明

### 用户注册

1. 访问 `http://localhost:5000/register`
2. 填写用户名、邮箱、密码
3. 点击"注册"按钮
4. 注册成功后自动跳转到登录页面

### 用户登录

1. 访问 `http://localhost:5000/login`
2. 输入用户名和密码
3. 点击"登录"按钮
4. 登录成功后返回首页

### 购买会员

1. 访问 `http://localhost:5000/premium`
2. 选择合适的会员套餐
3. 点击"立即购买"
4. 选择支付方式（支付宝/比特币）
5. 扫描二维码或复制地址完成支付
6. 点击"确认已支付"
7. 会员自动激活

### 观看视频

- **非会员**：每个视频只能观看前15秒
- **会员**：无限观看时长

### 会员状态查询

登录后可通过API查询会员状态：
```
GET /api/user/subscription
```

返回数据：
```json
{
  "is_premium": true,
  "plan_type": "monthly",
  "end_date": "2024-02-13T10:30:00",
  "days_remaining": 30
}
```

## API接口

### 用户认证

- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /logout` - 用户登出

### 会员和支付

- `GET /premium` - 会员套餐页面
- `GET /api/premium/plans` - 获取套餐信息
- `POST /payment/<plan_type>` - 支付页面
- `GET /payment/bitcoin/<payment_id>/<plan_type>` - 比特币支付页面
- `GET /payment/alipay/<payment_id>/<plan_type>` - 支付宝支付页面
- `POST /api/payment/confirm/<payment_id>` - 确认支付
- `GET /api/payment/status/<payment_id>` - 查询支付状态
- `GET /api/user/subscription` - 获取用户订阅信息

### 视频播放（已集成用户权限）

- `GET /api/video/<filename>/frame/<frame_idx>` - 获取单帧（带权限验证）
- `GET /api/video/<filename>/frames/<start>/<end>` - 批量获取帧（带权限验证）

## 文件结构

```
website/
├── app.py                          # 主应用（已更新）
├── config.py                       # 配置文件（已更新）
├── models.py                       # 数据库模型（新增）
├── requirements.txt                # 依赖列表（已更新）
├── templates/
│   ├── base.html                   # 基础模板（已更新）
│   ├── auth/
│   │   ├── login.html             # 登录页面（新增）
│   │   └── register.html          # 注册页面（新增）
│   ├── premium.html               # 会员套餐页面（新增）
│   ├── payment.html               # 支付选择页面（新增）
│   ├── payment_bitcoin.html       # 比特币支付页面（新增）
│   └── payment_alipay.html        # 支付宝支付页面（新增）
├── static/
│   └── css/
│       └── style.css              # 样式文件（已更新）
└── app.db                         # 数据库文件（自动创建）
```

## 安全说明

1. **密码加密**：使用Werkzeug的密码哈希功能，不存储明文密码
2. **会话安全**：使用Flask-Login的会话管理，支持CSRF保护
3. **SQL注入防护**：使用SQLAlchemy ORM，自动防止SQL注入
4. **文件上传安全**：使用secure_filename验证文件名
5. **权限验证**：所有需要权限的路由都使用@login_required装饰器

## 扩展建议

### 1. 真实支付集成

可以将模拟支付替换为真实的支付API：

**支付宝**：
- 使用支付宝开放平台API
- 需要申请APP ID和密钥
- 参考文档：https://opendocs.alipay.com/

**比特币**：
- 使用比特币支付网关（如Coinbase Commerce、BTCPay Server）
- 或者使用区块链API监控交易
- 需要设置比特币钱包

### 2. 功能扩展

- 邮箱验证
- 密码找回
- 用户个人中心
- 会员续费
- 支付历史查询
- 优惠券系统
- 推荐奖励

### 3. 数据库优化

对于生产环境，建议使用PostgreSQL替代SQLite：
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/dbname'
```

## 故障排除

### 数据库创建失败

确保有写入权限，或手动创建：
```bash
cd website
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 登录后没有会员权限

检查：
1. 支付是否成功完成
2. 订阅记录是否创建
3. 订阅end_date是否在当前时间之后

### 支付确认失败

检查：
1. network请求是否成功
2. API接口返回的错误信息
3. 浏览器控制台的错误日志

## 技术栈

- Flask 2.3.3 - Web框架
- Flask-Login 0.6.3 - 用户会话管理
- Flask-SQLAlchemy 3.0.5 - 数据库ORM
- Werkzeug 2.3.7 - 安全工具
- SQLite - 数据库（可升级为PostgreSQL）

## 许可证

本系统基于Banana Player项目开发，遵循相同的许可证。
