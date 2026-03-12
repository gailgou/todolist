#!/usr/bin/python
#-*- coding: UTF-8 -*-
import os
import sys

# 首先设置正确的数据库路径
basedir = os.path.abspath(os.path.dirname(__file__))

import unittest
from app import app, db
from models import User, TodoList

def run_manual_check():
    """手动检查数据库"""
    print("=== 数据库检查 ===")
    
    with app.app_context():
        # 检查数据库
        print("\n1. 默认用户和待办事项:")
        users = User.query.all()
        print(f"用户总数: {len(users)}")
        for user in users:
            todos = TodoList.query.filter_by(user_id=user.id).all()
            print(f"  {user.username}: {len(todos)} 条待办")
            for todo in todos[:3]:
                print(f"    - {todo.title}")

def test_login_flow():
    """测试登录流程"""
    print("\n=== 测试登录流程 ===")
    
    client = app.test_client()
    
    # 测试1: 访问登录页面
    response = client.get('/login')
    print(f"登录页面状态: {response.status_code}")
    assert response.status_code == 200, "登录页面应该可访问"
    
    # 测试2: 登录admin
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    print(f"登录admin状态码: {response.status_code}")
    
    # 检查session
    with client.session_transaction() as sess:
        print(f"已登录用户: {sess.get('logged_in_users')}")
        print(f"活跃用户ID: {sess.get('active_user_id')}")
    
    # 测试3: 检查是否显示admin的待办
    response = client.get('/')
    print(f"主页状态码: {response.status_code}")
    response_text = response.data.decode('utf-8')
    if '完成项目报告' in response_text:
        print("✓ 显示admin的待办事项")
    else:
        print("✗ 未找到admin的待办事项")
    
    # 测试4: 登录第二个用户
    response = client.post('/login', data={
        'username': 'user1',
        'password': '123456'
    }, follow_redirects=True)
    
    with client.session_transaction() as sess:
        print(f"登录user1后 - 已登录用户: {sess.get('logged_in_users')}")
        print(f"活跃用户ID: {sess.get('active_user_id')}")
    
    # 测试5: 检查是否显示user1的待办
    response = client.get('/')
    response_text = response.data.decode('utf-8')
    if '整理工作文档' in response_text:
        print("✓ 显示user1的待办事项")
    else:
        print("✗ 未找到user1的待办事项")
    
    # 测试6: 切换回admin
    with client.session_transaction() as sess:
        users = sess.get('logged_in_users', [])
        admin_id = None
        for u in users:
            if u['username'] == 'admin':
                admin_id = u['id']
                break
    
    if admin_id:
        response = client.get(f'/switch/{admin_id}', follow_redirects=True)
        print(f"切换到admin状态码: {response.status_code}")
        
        with client.session_transaction() as sess:
            print(f"切换后活跃用户ID: {sess.get('active_user_id')}")
        
        response = client.get('/')
        response_text = response.data.decode('utf-8')
        if '完成项目报告' in response_text:
            print("✓ 切换后显示admin的待办事项")
        else:
            print("✗ 切换后未找到admin的待办事项")
    
    # 测试7: 登录第三个用户
    response = client.post('/login', data={
        'username': 'user2',
        'password': '123456'
    }, follow_redirects=True)
    
    with client.session_transaction() as sess:
        print(f"登录user2后 - 已登录用户数: {len(sess.get('logged_in_users', []))}")
        print(f"已登录用户: {sess.get('logged_in_users')}")
    
    # 测试8: 尝试登录第四个用户（应该失败）
    response = client.post('/login', data={
        'username': 'user3',
        'password': '123456'
    }, follow_redirects=True)
    
    response_text = response.data.decode('utf-8')
    if '最多只能登录' in response_text:
        print("✓ 正确限制最多3个登录用户")
    else:
        print("✗ 未正确限制登录用户数")
    
    # 测试9: 登出当前用户
    response = client.get('/logout', follow_redirects=True)
    print(f"登出状态码: {response.status_code}")
    
    with client.session_transaction() as sess:
        print(f"登出后 - 已登录用户: {sess.get('logged_in_users')}")
        print(f"活跃用户ID: {sess.get('active_user_id')}")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    run_manual_check()
    test_login_flow()
