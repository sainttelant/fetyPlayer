#!/usr/bin/env python3
"""
P0 阶段 - 后端API 测试脚本
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
import base64

BASE_URL = 'http://localhost:5000'
VIDEO_FILE = 'vis.ban'

def test_api():
    """测试 P0 API 功能"""
    print("🧪 P0 阶段 - 后端 API 测试")
    print("=" * 60)
    
    # 等待用户启动 Flask 服务器
    print("\n💡 请先在另一个终端运行:")
    print(f"   cd {os.path.dirname(__file__)}/website")
    print("   python3 app.py")
    print()
    
    print("✅ API 测试将在服务器启动后自动开始...")
    print("=" * 60)
    
    # 测试函数列表
    tests = [
        ('视频信息API', test_video_info),
        ('单帧获取API', test_single_frame),
        ('批量帧获取API', test_batch_frames),
        ('错误处理测试', test_error_handling),
    ]
    
    # 运行所有测试
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 测试: {test_name}")
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
    print("\n" + "=" * 60)
    print("📊 测试汇总")
    print("=" * 60)
    
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
    print("🎯 建议:")
    if failed > 0 or errors > 0:
        print("   - 修复失败的测试用例")
        print("   - 检查服务器日志获取详细信息")
    else:
        print("   - 所有API 路由工作正常")
        print("   - 可以开始前端播放器集成")

def test_video_info():
    """测试视频信息API"""
    print("1. 测试视频信息API...")
    
    response = requests.get(f'{BASE_URL}/api/video/{VIDEO_FILE}/info', timeout=10)
    assert response.status_code == 200, f"API返回错误: {response.status_code}"
    
    data = response.json()
    assert 'success' in data and data['success'], "响应缺少success标志"
    assert 'info' in data, "响应缺少info数据"
    assert 'is_ban_format' in data, "响应缺少is_ban_format标志"
    assert data['is_ban_format'] == True, "未识别为.ban格式"
    
    info = data['info']
    assert 'frame_count' in info, "视频信息缺少frame_count"
    assert 'fps' in info, "视频信息缺少fps"
    assert 'width' in info, "视频信息缺少width"
    assert 'height' in info, "视频信息缺少height"
    
    print(f"   ✅ 视频帧数: {info['frame_count']}")
    print(f"   ✅ 分辨率: {info['width']}x{info['height']}")
    print(f"   ✅ FPS: {info['fps']}")

def test_single_frame():
    """测试单帧获取API"""
    print("2. 测试单帧获取API...")
    
    test_frames = [0, 100, 250, 400, 499]
    
    for frame_idx in test_frames:
        response = requests.get(f'{BASE_URL}/api/video/{VIDEO_FILE}/frame/{frame_idx}', timeout=10)
        assert response.status_code == 200, f"API返回错误: {response.status_code}"
        
        data = response.json()
        assert 'success' in data and data['success'], f"帧 {frame_idx}: 缺少success标志"
        assert 'frame_idx' in data, f"帧 {frame_idx}: 缺少frame_idx"
        assert 'frame_data' in data, f"帧 {frame_idx}: 缺少frame_data"
        assert data['frame_idx'] == frame_idx, f"帧索引不匹配: {data['frame_idx']} != {frame_idx}"
        assert data['width'] > 0 and data['height'] > 0, f"无效的尺寸: {data['width']}x{data['height']}"
        assert 'frame_data' in data and data['frame_data'].startswith('data:image/jpeg;base64,'), f"无效的帧数据格式"
        
        print(f"   ✅ 帧 {frame_idx}: {data['width']}x{data['height']}, {data['size_kb']:.1f} KB")

def test_batch_frames():
    """测试批量帧获取API"""
    print("3. 测试批量帧获取API...")
    
    # 测试不同的批量大小
    batch_tests = [
        (0, 10),   # 10帧
        (100, 150), # 50帧
        (0, 20),   # 20帧
    ]
    
    for start, end in batch_tests:
        response = requests.get(f'{BASE_URL}/api/video/{VIDEO_FILE}/frames/{start}/{end}', timeout=30)
        assert response.status_code == 200, f"批量 {start}-{end}: API返回错误: {response.status_code}"
        
        data = response.json()
        assert 'success' in data and data['success'], f"批量 {start}-{end}: 缺少success标志"
        assert 'frames' in data, f"批量 {start}-{end}: 缺少frames数组"
        assert len(data['frames']) == end - start, f"帧数不匹配: {len(data[\"frames\"])} != {end-start}"
        
        # 验证每帧数据
        for i, frame_data in enumerate(data['frames']):
            assert 'frame_idx' in frame_data, f"批量 {start}-{end}: 帧 {i} 缺少frame_idx"
            assert 'frame_data' in frame_data, f"批量 {start}-{end}: 帧 {i} 缺少frame_data"
            assert frame_data['frame_idx'] == start + i, f"帧索引不匹配: {frame_data[\"frame_idx\"]} != {start+i}"
        
        print(f"   ✅ 批量 {start}-{end}: 获取 {len(data['frames']) 帧")

def test_error_handling():
    """测试错误处理"""
    print("4. 测试错误处理...")
    
    # 测试不存在的文件
    response = requests.get(f'{BASE_URL}/api/video/nonexistent.ban/frame/0', timeout=10)
    assert response.status_code == 404, f"不存在文件: 期望 404，得到 {response.status_code}"
    print("   ✅ 不存在的文件: 正确返回 404")
    
    # 测试超出的帧索引
    response = requests.get(f'{BASE_URL}/api/video/{VIDEO_FILE}/frame/9999', timeout=10)
    assert response.status_code == 400, f"超出范围帧索引: 期望 400，得到 {response.status_code}"
    print("   ✅ 超出范围帧索引: 正确返回 400")
    
    # 测试批量大小超限
    response = requests.get(f'{BASE_URL}/api/video/{VIDEO_FILE}/frames/0/200', timeout=10)
    assert response.status_code == 400, f"批量大小超限: 期望 400，得到 {response.status_code}"
    print("   ✅ 批量大小超限: 正确返回 400")


if __name__ == '__main__':
    test_api()
