from app import app
from flask import g, request
from flask_login import current_user

app.config['TESTING'] = True

# 在应用启动前添加调试
import sys
original_before = app.before_request_funcs.get(None, [])[:]

@app.before_request
def debug_g():
    print(f'[debug {request.path}] g.current_user={g.current_user.username if g.current_user else None}', file=sys.stderr)
    print(f'[debug {request.path}] current_user={current_user.username if current_user.is_authenticated else None}', file=sys.stderr)

client = app.test_client()

# 测试切换
print('=== Login admin ===')
client.post('/login', data={'username': 'admin', 'password': 'admin'})

print('\n=== Login user1 ===')
client.post('/login', data={'username': 'user1', 'password': '123456'})

print('\n=== Before switch ===')
with client.session_transaction() as sess:
    print(f'active_user_id: {sess.get("active_user_id")}')
    print(f'_user_id: {sess.get("_user_id")}')

print('\n=== Switching to admin ===')
response = client.get('/switch/1')
print(f'Switch status: {response.status_code}')

print('\n=== After switch ===')
with client.session_transaction() as sess:
    print(f'active_user_id: {sess.get("active_user_id")}')
    print(f'_user_id: {sess.get("_user_id")}')

# 检查页面
response = client.get('/')
html = response.data.decode('utf-8')
print(f'\nPage shows current user: {"当前用户: <strong>admin" in html}')
print(f'Page has admin\'s todos: {"完成项目报告" in html}')

# 检查问题 - 在switch_user中，login_user后g对象没有更新
print('\n=== 检查关键问题 ===')
# 修改switch_user函数，添加调试
from flask_login import login_user
from models import User

# 测试在一个请求中调用login_user后g是否更新
with client:
    client.post('/login', data={'username': 'user1', 'password': '123456'})
    
    # 模拟在switch_user中的情况
    with app.test_request_context('/switch_test'):
        # 设置session
        with client.session_transaction() as sess:
            from flask import session as flask_session
            flask_session['logged_in_users'] = sess.get('logged_in_users')
            flask_session['active_user_id'] = sess.get('active_user_id')
            flask_session['_user_id'] = sess.get('_user_id')
        
        # 先执行before_request
        app.preprocess_request()
        print(f'Before login_user in same request:')
        print(f'  g.current_user: {g.current_user.username}')
        print(f'  current_user: {current_user.username}')
        
        # 调用login_user (模拟switch_user中的操作)
        admin = User.query.get(1)
        login_user(admin)
        print(f'\nAfter login_user in same request:')
        print(f'  g.current_user: {g.current_user.username}')  # 这里可能还是旧值！
        print(f'  current_user: {current_user.username}')
        
        # 手动更新g
        g.current_user = admin
        print(f'\nAfter manual update g:')
        print(f'  g.current_user: {g.current_user.username}')
        print(f'  current_user: {current_user.username}')
