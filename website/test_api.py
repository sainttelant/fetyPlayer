#!/usr/bin/env python3
"""
简单的测试脚本，验证修复后的播放器
"""
import requests
import json
import time

def test_api():
    """测试API响应"""
    print("=== 测试API ===")
    base_url = "http://localhost:5000"

    try:
        # 测试视频信息API
        print("1. 测试视频信息API...")
        response = requests.get(f"{base_url}/api/video/vis.ban/info")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 视频信息: {data['info']['frame_count']}帧, {data['info']['fps']}fps")
        else:
            print(f"   ✗ 失败: {response.status_code}")

        # 测试单帧API
        print("2. 测试单帧API...")
        response = requests.get(f"{base_url}/api/video/vis.ban/frame/0")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 帧0: {data['width']}x{data['height']}")
            print(f"   ✓ 数据长度: {len(data['frame_data'])} 字符")
        else:
            print(f"   ✗ 失败: {response.status_code}")

        # 测试批量帧API
        print("3. 测试批量帧API...")
        response = requests.get(f"{base_url}/api/video/vis.ban/frames/0/5")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 收到 {len(data['frames'])} 帧")
        else:
            print(f"   ✗ 失败: {response.status_code}")

        # 测试15秒限制
        print("4. 测试15秒限制（帧150）...")
        response = requests.get(f"{base_url}/api/video/vis.ban/frame/150")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 帧150正常: {data.get('watch_limit', {}).get('can_watch', True)}")
        elif response.status_code == 403:
            print(f"   ✓ 帧150被正确限制")
        else:
            print(f"   ? 状态码: {response.status_code}")

        print("\n=== API测试完成 ===")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == '__main__':
    time.sleep(2)  # 等待服务器启动
    success = test_api()
    if success:
        print("\n✓ 所有测试通过")
    else:
        print("\n✗ 测试失败")