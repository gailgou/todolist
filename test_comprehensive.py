#!/usr/bin/python
#-*- coding: UTF-8 -*-
"""
综合测试：验证所有需求功能
1. 5个默认账户，每个至少3条预置待办
2. 切换账号功能，最多同时登录3个
3. 切换后显示对应账号的待办
"""
import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

from app import app, db, MAX_LOGIN_USERS
from models import User, TodoList

def test_default_users_and_todos():
    """测试1: 验证默认用户和待办事项"""
    print("=" * 60)
    print("测试1: 默认用户和预置待办事项")
    print("=" * 60)
    
    with app.app_context():
        users = User.query.all()
        print(f"用户总数: {len(users)} (预期: 5)")
        assert len(users) == 5, f"应该有5个默认用户，实际有{len(users)}个"
        
        expected_users = ['admin', 'user1', 'user2', 'user3', 'user4']
        for user in users:
            print(f"  用户: {user.username}")
            assert user.username in expected_users, f"意外的用户名: {user.username}"
            
            todos = TodoList.query.filter_by(user_id=user.id).all()
            print(f"    待办事项数: {len(todos)} (预期至少3个)")
            assert len(todos) >= 3, f"用户 {user.username} 应该至少有3条待办"
            
            for todo in todos:
                print(f"      - {todo.title}")
    
    print("✓ 默认用户和待办事项测试通过\n")

def test_multi_login_limit():
    """测试2: 最多同时登录3个账号"""
    print("=" * 60)
    print("测试2: 最多同时登录3个账号限制")
    print("=" * 60)
    
    client = app.test_client()
    
    # 清除session
    with client.session_transaction() as sess:
        sess.clear()
    
    # 登录前3个用户
    for i in range(3):
        username = f'user{i+1}'
        response = client.post('/login', data={
            'username': username,
            'password': '123456'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            logged_in = sess.get('logged_in_users', [])
            print(f"登录 {username} 后，已登录用户数: {len(logged_in)}")
    
    # 验证当前已登录3个用户
    with client.session_transaction() as sess:
        logged_in = sess.get('logged_in_users', [])
        assert len(logged_in) == 3, f"应该有3个已登录用户，实际有{len(logged_in)}个"
    
    # 尝试登录第4个用户
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    
    response_text = response.data.decode('utf-8')
    assert '最多只能登录' in response_text, "应该显示登录限制消息"
    print("✓ 第4个用户登录被阻止，显示限制消息")
    
    with client.session_transaction() as sess:
        logged_in = sess.get('logged_in_users', [])
        assert len(logged_in) == 3, f"应该仍然只有3个已登录用户，实际有{len(logged_in)}个"
    
    print("✓ 多用户登录限制测试通过\n")

def test_switch_user_and_todo_isolation():
    """测试3: 切换用户和待办事项隔离"""
    print("=" * 60)
    print("测试3: 用户切换和待办事项隔离")
    print("=" * 60)
    
    client = app.test_client()
    
    # 清除session
    with client.session_transaction() as sess:
        sess.clear()
    
    # 登录admin
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    
    # 检查admin的待办
    response = client.get('/')
    response_text = response.data.decode('utf-8')
    assert '完成项目报告' in response_text, "应该显示admin的待办"
    print("✓ 显示admin的待办事项")
    
    # 登录user1
    client.post('/login', data={'username': 'user1', 'password': '123456'}, follow_redirects=True)
    
    # 检查user1的待办
    response = client.get('/')
    response_text = response.data.decode('utf-8')
    assert '整理工作文档' in response_text, "应该显示user1的待办"
    print("✓ 登录user1后显示user1的待办事项")
    
    # 切换回admin
    with client.session_transaction() as sess:
        logged_in = sess.get('logged_in_users', [])
        admin_id = next(u['id'] for u in logged_in if u['username'] == 'admin')
    
    response = client.get(f'/switch/{admin_id}', follow_redirects=True)
    response_text = response.data.decode('utf-8')
    assert '完成项目报告' in response_text, "切换后应该显示admin的待办"
    print("✓ 切换回admin后显示admin的待办事项")
    
    print("✓ 用户切换和待办隔离测试通过\n")

def test_logout_function():
    """测试4: 登出功能"""
    print("=" * 60)
    print("测试4: 登出功能")
    print("=" * 60)
    
    client = app.test_client()
    
    # 清除session
    with client.session_transaction() as sess:
        sess.clear()
    
    # 登录3个用户
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    client.post('/login', data={'username': 'user1', 'password': '123456'}, follow_redirects=True)
    client.post('/login', data={'username': 'user2', 'password': '123456'}, follow_redirects=True)
    
    with client.session_transaction() as sess:
        logged_in = sess.get('logged_in_users', [])
        assert len(logged_in) == 3
        print(f"登录3个用户: {[u['username'] for u in logged_in]}")
    
    # 登出非活跃用户 (admin)
    with client.session_transaction() as sess:
        admin_id = next(u['id'] for u in sess['logged_in_users'] if u['username'] == 'admin')
    
    response = client.get(f'/logout/{admin_id}', follow_redirects=True)
    
    with client.session_transaction() as sess:
        logged_in = sess.get('logged_in_users', [])
        assert len(logged_in) == 2
        admin_logged = any(u['username'] == 'admin' for u in logged_in)
        assert not admin_logged, "admin应该已被登出"
    print("✓ 登出非活跃用户成功")
    
    # 登出活跃用户 (user2)
    with client.session_transaction() as sess:
        user2_id = next(u['id'] for u in sess['logged_in_users'] if u['username'] == 'user2')
    
    response = client.get(f'/logout/{user2_id}', follow_redirects=True)
    
    with client.session_transaction() as sess:
        logged_in = sess.get('logged_in_users', [])
        assert len(logged_in) == 1
        assert logged_in[0]['username'] == 'user1', "应该自动切换到user1"
    print("✓ 登出活跃用户后自动切换成功")
    
    print("✓ 登出功能测试通过\n")

def test_login_page_shows_logged_users():
    """测试5: 登录页面显示已登录用户"""
    print("=" * 60)
    print("测试5: 登录页面显示已登录用户")
    print("=" * 60)
    
    client = app.test_client()
    
    with client.session_transaction() as sess:
        sess.clear()
    
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    
    response = client.get('/login')
    response_text = response.data.decode('utf-8')
    assert '已登录账号' in response_text, "登录页面应该显示已登录账号"
    assert 'admin' in response_text, "登录页面应该显示admin"
    print("✓ 登录页面显示已登录用户")
    
    print("✓ 登录页面测试通过\n")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("待办事项应用综合测试")
    print("=" * 60 + "\n")
    
    try:
        test_default_users_and_todos()
        test_multi_login_limit()
        test_switch_user_and_todo_isolation()
        test_logout_function()
        test_login_page_shows_logged_users()
        
        print("=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
