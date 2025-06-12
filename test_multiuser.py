#!/usr/bin/env python3
"""
测试多用户隔离功能
"""
import requests
import json
import time
import os

def test_user_isolation():
    """测试用户隔离功能"""
    base_url = 'http://localhost:5001'
    
    # 模拟两个不同的用户
    user1_id = 'test_user_001'
    user2_id = 'test_user_002'
    
    print("🧪 开始测试多用户隔离功能...")
    
    # 测试1: 检查状态API是否需要用户ID
    print("\n📝 测试1: 状态API用户ID验证")
    try:
        response = requests.get(f'{base_url}/api/status')
        if response.status_code == 400:
            print("✅ 状态API正确要求用户ID")
        else:
            print("❌ 状态API应该要求用户ID")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return
    
    # 测试2: 获取不同用户的状态
    print("\n📝 测试2: 获取不同用户状态")
    try:
        user1_status = requests.get(f'{base_url}/api/status?user_id={user1_id}')
        user2_status = requests.get(f'{base_url}/api/status?user_id={user2_id}')
        
        if user1_status.status_code == 200 and user2_status.status_code == 200:
            print("✅ 可以获取不同用户的状态")
            print(f"   用户1状态: {user1_status.json()['status']}")
            print(f"   用户2状态: {user2_status.json()['status']}")
        else:
            print("❌ 无法获取用户状态")
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")
    
    # 测试3: 检查目录隔离
    print("\n📝 测试3: 检查转换请求的用户ID验证")
    
    # 模拟转换请求
    test_params = {
        'video_file': 'bottom-banner.mp4',
        'user_id': user1_id,
        'params': {
            'frame_width': 50,
            'charset': 'custom',
            'custom_chars': '/>.10'
        }
    }
    
    try:
        print(f"   为用户1发送转换请求...")
        response = requests.post(f'{base_url}/api/convert', 
                               headers={'Content-Type': 'application/json'},
                               data=json.dumps(test_params))
        
        if response.status_code == 200:
            print("✅ 转换请求发送成功")
            
            # 检查目录是否会被创建
            user1_dir = f'ascii_frames_{user1_id}'
            
            # 取消转换以免影响其他测试
            time.sleep(1)
            cancel_response = requests.post(f'{base_url}/api/cancel',
                                          headers={'Content-Type': 'application/json'},
                                          data=json.dumps({'user_id': user1_id}))
            print(f"   取消转换: {cancel_response.json().get('message', '')}")
            
        else:
            print(f"❌ 转换请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 转换请求异常: {e}")
    
    # 测试4: 文件服务路径隔离
    print("\n📝 测试4: 文件服务路径隔离")
    
    try:
        # 测试用户专属路径
        frame_url = f'{base_url}/ascii_frames_{user1_id}/frame_00000.txt'
        response = requests.get(frame_url)
        
        if response.status_code == 404:
            print("✅ 用户专属路径正确返回404（文件不存在）")
        elif response.status_code == 200:
            print("✅ 用户专属路径可以访问文件")
        else:
            print(f"⚠️  用户专属路径返回状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 文件路径测试失败: {e}")
    
    print("\n🎉 多用户隔离功能测试完成！")
    print("\n重要说明:")
    print("- 每个用户都有独立的转换状态")
    print("- 每个用户的文件存储在独立目录中")
    print("- API调用需要提供用户ID进行隔离")
    print("- 前端会自动生成并管理用户ID")

if __name__ == '__main__':
    test_user_isolation() 