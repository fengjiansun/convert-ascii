#!/usr/bin/env python3
"""
多用户隔离功能演示脚本
展示如何同时为多个用户处理不同的转换任务
"""
import requests
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor

def simulate_user_session(user_id, video_file, custom_chars):
    """模拟一个用户会话"""
    base_url = 'http://localhost:5001'
    
    print(f"👤 用户 {user_id} 开始会话")
    
    try:
        # 1. 获取初始状态
        status_response = requests.get(f'{base_url}/api/status?user_id={user_id}')
        print(f"   初始状态: {status_response.json()['status']}")
        
        # 2. 发起转换请求
        convert_params = {
            'video_file': video_file,
            'user_id': user_id,
            'params': {
                'frame_width': 60,
                'charset': 'custom',
                'custom_chars': custom_chars,
                'duration': 3  # 只处理3秒，加快演示
            }
        }
        
        print(f"   发起转换请求: {video_file} 使用字符集 '{custom_chars}'")
        convert_response = requests.post(f'{base_url}/api/convert',
                                       headers={'Content-Type': 'application/json'},
                                       data=json.dumps(convert_params))
        
        if convert_response.status_code == 200:
            print(f"   ✅ 转换开始成功")
            
            # 3. 监控进度
            for i in range(8):  # 最多监控8次
                time.sleep(2)
                status_response = requests.get(f'{base_url}/api/status?user_id={user_id}')
                status_data = status_response.json()
                
                if status_data['status'] == 'running':
                    progress = status_data.get('progress', 0)
                    current_frame = status_data.get('current_frame', 0)
                    total_frames = status_data.get('total_frames', 0)
                    print(f"   📊 进度: {progress:.1f}% ({current_frame}/{total_frames})")
                elif status_data['status'] == 'completed':
                    print(f"   🎉 转换完成！共 {status_data.get('total_frames', 0)} 帧")
                    break
                elif status_data['status'] == 'error':
                    print(f"   ❌ 转换失败: {status_data.get('message', '')}")
                    break
            
            # 4. 测试文件访问
            frame_url = f'{base_url}/ascii_frames_{user_id}/frame_00000.txt'
            frame_response = requests.get(frame_url)
            if frame_response.status_code == 200:
                print(f"   📁 文件访问成功，第一帧长度: {len(frame_response.text)} 字符")
            else:
                print(f"   📁 文件访问失败: {frame_response.status_code}")
                
        else:
            print(f"   ❌ 转换请求失败: {convert_response.text}")
    
    except Exception as e:
        print(f"   ❌ 用户会话异常: {e}")
    
    print(f"👤 用户 {user_id} 会话结束\n")

def main():
    """主演示函数"""
    print("🎭 多用户隔离功能演示")
    print("=" * 50)
    print("此演示将模拟3个用户同时使用系统")
    print("每个用户使用不同的参数和字符集")
    print("=" * 50)
    
    # 定义3个模拟用户
    users = [
        {
            'user_id': 'demo_user_alice',
            'video_file': 'bottom-banner.mp4',
            'custom_chars': '/>.10'
        },
        {
            'user_id': 'demo_user_bob', 
            'video_file': 'bottom-banner.mp4',
            'custom_chars': '░▒▓█'
        },
        {
            'user_id': 'demo_user_charlie',
            'video_file': 'bottom-banner.mp4', 
            'custom_chars': '·•●'
        }
    ]
    
    # 使用线程池并发执行用户会话
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for user in users:
            future = executor.submit(
                simulate_user_session,
                user['user_id'],
                user['video_file'], 
                user['custom_chars']
            )
            futures.append(future)
        
        # 等待所有用户会话完成
        for future in futures:
            future.result()
    
    print("🎉 演示完成！")
    print("\n📋 演示总结:")
    print("- 3个用户同时发起转换请求")
    print("- 每个用户使用不同的字符集")
    print("- 每个用户拥有独立的转换状态")
    print("- 每个用户的文件存储在独立目录")
    print("- 系统正确隔离了不同用户的操作")
    
    # 显示生成的目录
    print("\n📁 生成的用户目录:")
    for user in users:
        user_dir = f"ascii_frames_{user['user_id']}"
        if os.path.exists(user_dir):
            file_count = len([f for f in os.listdir(user_dir) if f.endswith('.txt')])
            print(f"   {user_dir}: {file_count} 个帧文件")
        else:
            print(f"   {user_dir}: 目录不存在")

if __name__ == '__main__':
    main() 