#!/usr/bin/env python3
"""
下载功能测试脚本
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 模拟 fetyPlayer 环境
os.environ['APP_FOLDER'] = os.path.join(os.path.dirname(__file__), 'website')

import requests

BASE_URL = 'http://localhost:5000'

def test_download_feature():
    """测试下载功能"""
    print("🧪 下载功能测试")
    print("=" * 50)
    
    tests = [
        ('1. 访问下载页面', test_downloads_page),
        ('2. 测试API端点', test_api_endpoints),
        ('3. 测试下载文件', test_download_file),
        ('4. 测试下载计数', test_download_count),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 50)
        try:
            test_func()
            results.append((test_name, 'PASS', None))
            print(f"✅ 测试通过")
        except AssertionError as e:
            results.append((test_name, 'FAIL', str(e)))
            print(f"❌ 测试失败: {e}")
        except Exception as e:
            results.append((test_name, 'ERROR', str(e)))
            print(f"⚠️  测试错误: {e}")
    
    # 输出汇总
    print("\n" + "=" * 50)
    print("📊 测试汇总")
    print("=" * 50)
    
    for test_name, status, detail in results:
        status_icon = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'
        print(f"{status_icon} {test_name}")
        if detail and status != 'PASS':
            print(f"   {detail}")
    
    # 统计
    passed = sum(1 for _, status, _ in results if status == 'PASS')
    failed = sum(1 for _, status, _ in results if status == 'FAIL')
    errors = sum(1 for _, status, _ in results if status == 'ERROR')
    total = len(results)
    
    print()
    print(f"📈 统计: {passed}/{total} 通过，{failed} 失败，{errors} 错误")
    print()
    
    # 建议
    if failed > 0 or errors > 0:
        print("🎯 建议:")
        if failed > 0:
            print("   - 修复失败的测试用例")
        if errors > 0:
            print("   - 修复错误的测试用例")
    else:
        print("🎉 所有功能正常！")
        print()
        print("📋 下一步:")
        print("   1. 复制 exe 文件到 downloads/ 目录")
        print("   2. 访问 http://localhost:5000/downloads")
        print("   3. 测试下载 exe 文件")

def test_downloads_page():
    """测试下载页面"""
    print("   访问首页下载页面...")
    response = requests.get(f'{BASE_URL}/downloads', timeout=10)
    assert response.status_code == 200, f"下载页面返回错误: {response.status_code}"
    assert 'text/html' in response.headers.get('Content-Type', ''), "不是HTML响应"
    assert 'Banana Player' in response.text, "页面标题不匹配"
    print("   ✅ 下载页面加载成功")

def test_api_endpoints():
    """测试 API 端点"""
    print("   测试下载 API...")
    
    # 测试获取下载列表
    response = requests.get(f'{BASE_URL}/api/downloads', timeout=10)
    assert response.status_code == 200, f"API返回错误: {response.status_code}"
    
    data = response.json()
    assert 'success' in data, "响应缺少success标志"
    assert 'downloads' in data, "响应缺少downloads数据"
    assert 'total' in data, "响应缺少total字段"
    print(f"   ✅ API列表: {len(data['downloads'])} 个文件")
    
    # 测试下载文件（如果存在）
    if data['downloads']:
        filename = data['downloads'][0]['filename']
        print(f"   测试下载: {filename}")
        
        # 尝试下载（需要文件存在）
        response = requests.get(f'{BASE_URL}/download/{filename}', timeout=30)
        print(f"   下载状态: {response.status_code} (200表示成功）")

def test_download_file():
    """测试下载文件（需要先有exe文件）"""
    print("   测试下载文件（需要exe文件在downloads/目录）")
    
    # 检查下载目录
    downloads_folder = os.path.join(os.path.dirname(__file__), 'website/downloads')
    if not os.path.exists(downloads_folder):
        print("   ⚠️  downloads/ 目录为空，跳过文件下载测试")
        return
    
    # 查找 exe 文件
    exe_files = [f for f in os.listdir(downloads_folder) if f.endswith('.exe')]
    if not exe_files:
        print("   ⚠️  downloads/ 目录中没有exe文件，跳过文件下载测试")
        return
    
    filename = exe_files[0]
    print(f"   找到 exe 文件: {filename}")
    
    # 尝试下载
    response = requests.get(f'{BASE_URL}/download/{filename}', timeout=10)
    print(f"   下载状态: {response.status_code}")
    
    if response.status_code == 200:
        assert 'application/x-msdownload' in response.headers.get('Content-Type', ''), "不是下载文件"
        print(f"   ✅ 文件下载成功")
    elif response.status_code == 404:
        print(f"   ❌ 文件不存在")
    else:
        print(f"   ⚠️ 未知状态码: {response.status_code}")

def test_download_count():
    """测试下载计数"""
    print("   测试下载计数...")
    
    response = requests.get(f'{BASE_URL}/api/downloads', timeout=10)
    assert response.status_code == 200, f"API返回错误: {response.status_code}"
    
    data = response.json()
    assert 'total' in data, "响应缺少total字段"
    
    print(f"   ✅ 下载总数: {data['total']} 个")
    print(f"   ✅ 列表数量: {len(data['downloads'])} 个")
    
    if data['downloads']:
        download = data['downloads'][0]
        print(f"   第一个文件: {download['name'] v{download['version']}")
        print(f"   文件大小: {download['size_mb']} MB")

if __name__ == '__main__':
    test_download_feature()
