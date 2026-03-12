from app import app, switch_user
from flask import g, session, redirect, url_for, request
from flask_login import current_user, login_user

app.config['TESTING'] = True
client = app.test_client()

# 保存原来的switch_user函数
original_switch = app.view_functions['switch_user']

# 包装switch_user来添加调试
@app.route('/switch_debug/<int:user_id>')
def switch_debug(user_id):
    print(f'  [switch_debug] before login_user')
    print(f'    g.current_user: {g.current_user.username if g.current_user else None}')
    print(f'    current_user: {current_user.username if current_user.is_authenticated else None}')
    print(f'    session.active_user_id: {session.get("active_user_id")}')
    
    # 执行切换逻辑
    from models import User
    logged_in = session.get('logged_in_users', [])
    for user in logged_in:
        if user['id'] == user_id:
            session['active_user_id'] = user_id
            user_obj = User.query.get(user_id)
            login_user(user_obj)
            
            print(f'  [switch_debug] after login_user')
            print(f'    g.current_user: {g.current_user.username if g.current_user else None}')
            print(f'    current_user: {current_user.username if current_user.is_authenticated else None}')
            print(f'    session.active_user_id: {session.get("active_user_id")}')
            
            # 手动更新g对象？
            # g.current_user = user_obj
            
            return redirect(url_for('show_todo_list'))
    return redirect(url_for('show_todo_list'))

print('=== 测试switch_user中的g对象 ===')
with client:
    # 登录两个用户
    client.post('/login', data={'username': 'admin', 'password': 'admin'})
    client.post('/login', data={'username': 'user1', 'password': '123456'})
    
    print('Before switch request:')
    with client.session_transaction() as sess:
        print(f'  active_user_id: {sess.get("active_user_id")}')
        print(f'  _user_id: {sess.get("_user_id")}')
    
    # 添加before_request调试
    @app.before_request
    def debug_before():
        print(f'[before_request] path={request.path}: g={g.current_user.username if g.current_user else None}, current_user={current_user.username if current_user.is_authenticated else None}')
    
    print('\n--- Making switch request ---')
    response = client.get('/switch_debug/1', follow_redirects=False)
    print(f'Switch response: {response.status_code}')
    
    print('\n--- After switch, before redirect follows ---')
    with client.session_transaction() as sess:
        print(f'  active_user_id: {sess.get("active_user_id")}')
        print(f'  _user_id: {sess.get("_user_id")}')
    
    print('\n--- Following redirect ---')
    response = client.get('/')
    html = response.data.decode('utf-8')
    idx = html.find('当前用户')
    print(f'Final page: {html[idx:idx+80]}')
