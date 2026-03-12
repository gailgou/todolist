#!/usr/bin/python
#-*- coding: UTF-8 -*-
import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

from app import app, db
from models import User, TodoList

client = app.test_client()

# 先清除session
with client.session_transaction() as sess:
    sess.clear()

# 先登录3个用户
print("Login admin...")
response = client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
print(f"  Status: {response.status_code}")

print("Login user1...")
response = client.post('/login', data={'username': 'user1', 'password': '123456'}, follow_redirects=True)
print(f"  Status: {response.status_code}")

print("Login user2...")
response = client.post('/login', data={'username': 'user2', 'password': '123456'}, follow_redirects=True)
print(f"  Status: {response.status_code}")

with client.session_transaction() as sess:
    print(f"Logged in users: {sess.get('logged_in_users')}")
    print(f"Count: {len(sess.get('logged_in_users', []))}")

# 尝试登录第4个用户
print("\nTrying to login user3 (4th user)...")
response = client.post('/login', data={'username': 'user3', 'password': '123456'}, follow_redirects=True)
print(f"  Status: {response.status_code}")

with client.session_transaction() as sess:
    print(f"After trying 4th login, logged in users: {sess.get('logged_in_users')}")
    print(f"Count: {len(sess.get('logged_in_users', []))}")

print("\nResponse content (checking for limit message):")
content = response.data.decode('utf-8')
if '最多只能登录' in content:
    print("✓ Found limit message")
else:
    print("✗ Limit message NOT found in response")
    # Print flash messages area
    if 'alert' in content:
        idx = content.find('alert')
        print("Alert area:", content[idx:idx+500])
