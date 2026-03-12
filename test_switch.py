from app import app, db
from flask import g
from flask_login import current_user

app.config['TESTING'] = True
client = app.test_client()

print('=== 测试用户切换时的同步问题 ===')
with client:
    # 添加调试
    debug_log = []
    
    @app.before_request
    def debug_before():
        debug_log.append(f'[before_request] g.current_user={g.current_user.username if g.current_user else None}, current_user={current_user.username if current_user.is_authenticated else None}')
    
    # 登录两个用户
    client.post('/login', data={'username': 'admin', 'password': 'admin'})
    print('After login admin:')
    with client.session_transaction() as sess:
        print(f'  logged_in_users: {sess.get("logged_in_users")}')
        print(f'  active_user_id: {sess.get("active_user_id")}')
        print(f'  _user_id: {sess.get("_user_id")}')
    
    client.post('/login', data={'username': 'user1', 'password': '123456'})
    print('\nAfter login user1:')
    with client.session_transaction() as sess:
        print(f'  logged_in_users: {sess.get("logged_in_users")}')
        print(f'  active_user_id: {sess.get("active_user_id")}')
        print(f'  _user_id: {sess.get("_user_id")}')
    
    debug_log.clear()
    print('\n=== Switching to admin ===')
    response = client.get('/switch/1', follow_redirects=True)
    print(f'Response status: {response.status_code}')
    
    print('\nDebug log:')
    for line in debug_log:
        print(f'  {line}')
    
    print('\nAfter switch:')
    with client.session_transaction() as sess:
        print(f'  logged_in_users: {sess.get("logged_in_users")}')
        print(f'  active_user_id: {sess.get("active_user_id")}')
        print(f'  _user_id: {sess.get("_user_id")}')
    
    # 检查下一个请求
    debug_log.clear()
    print('\n=== Next request (get /) ===')
    response = client.get('/')
    print('\nDebug log:')
    for line in debug_log:
        print(f'  {line}')
    
    html = response.data.decode('utf-8')
    print(f'\nHTML shows:')
    idx = html.find('当前用户')
    if idx > 0:
        print(f'  当前用户附近: {html[idx:idx+80]}')
