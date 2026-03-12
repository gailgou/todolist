from app import app, db, User, load_current_user
from flask import g, session, request
from flask_login import current_user

app.config['TESTING'] = True
client = app.test_client()

with app.app_context():
    user1 = User.query.get(1)
    user2 = User.query.get(2)
    print('DB Users:', user1.username, user2.username)

print('\n=== 测试1: 登录和g对象 ===')
with client:
    # 先添加一个调试的before_request来查看g的值
    original_before = app.before_request_funcs.get(None, [])[:]
    
    @app.before_request
    def debug_g():
        print(f'  [debug] path: {request.path}')
        print(f'  [debug] g.current_user: {g.current_user.username if g.current_user else None}')
        print(f'  [debug] g.logged_in_users: {g.logged_in_users}')
        print(f'  [debug] current_user: {current_user.username if current_user.is_authenticated else None}')
        print(f'  [debug] session: {dict(session)}')
    
    response = client.post('/login', data={'username': 'admin', 'password': 'admin'})
    print(f'Login response: {response.status_code}')
    
    print('\n--- After login, before get / ---')
    with client.session_transaction() as sess:
        print(f'Session keys: {list(sess.keys())}')
        print(f'logged_in_users: {sess.get("logged_in_users")}')
        print(f'active_user_id: {sess.get("active_user_id")}')
    
    print('\n--- Getting / ---')
    response = client.get('/')
    print(f'Get / status: {response.status_code}')
    html = response.data.decode('utf-8')
    print(f'Has admin todo: {"admin 的待办事项" in html}')
    
    # 恢复原来的before_request
    if None in app.before_request_funcs:
        app.before_request_funcs[None] = original_before

print('\n=== 测试2: 检查模板渲染问题 ===')
with client:
    client.post('/login', data={'username': 'admin', 'password': 'admin'})
    client.post('/login', data={'username': 'user1', 'password': '123456'})
    
    response = client.get('/')
    html = response.data.decode('utf-8')
    
    # 检查g对象的渲染
    print(f'HTML has "当前用户: <strong>user1": {"当前用户: <strong>user1" in html}')
    print(f'HTML has "(2/3)": {"(2/3)" in html}')
    
    # 查找问题
    idx = html.find('已登录账号')
    if idx > 0:
        print(f'Context at 已登录账号: {html[idx:idx+50]}')
    
    with client.session_transaction() as sess:
        print(f'Session logged_in_users: {sess.get("logged_in_users")}')
        print(f'Session active_user_id: {sess.get("active_user_id")}')

print('\n=== 测试3: 检查g对象设置时机 ===')
with client:
    client.post('/login', data={'username': 'admin', 'password': 'admin'})
    
    # 手动调用load_current_user
    with client.session_transaction() as sess:
        print(f'Session before: {sess.get("logged_in_users")}')
    
    with app.test_request_context('/'):
        # 复制session
        with client.session_transaction() as sess:
            session['logged_in_users'] = sess.get('logged_in_users')
            session['active_user_id'] = sess.get('active_user_id')
            session['_user_id'] = sess.get('_user_id')
        
        load_current_user()
        print(f'After load_current_user:')
        print(f'  g.current_user: {g.current_user}')
        print(f'  g.logged_in_users: {g.logged_in_users}')
