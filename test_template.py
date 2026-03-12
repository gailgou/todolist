from app import app
from flask import g, session

app.config['TESTING'] = True
client = app.test_client()

# 测试场景：登录两个用户，然后检查模板渲染
with client:
    client.post('/login', data={'username': 'admin', 'password': 'admin'})
    client.post('/login', data={'username': 'user1', 'password': '123456'})
    
    # 检查session
    print('session.logged_in_users:', session.get('logged_in_users'))
    print('session.active_user_id:', session.get('active_user_id'))
    
    # 现在检查before_request何时被调用
    from flask import template_rendered
    
    recorded = []
    def record(sender, template, context, **extra):
        g_in_context = context.get('g')
        print(f'模板: {template.name}')
        print(f'  g in context: {g_in_context is not None}')
        if g_in_context:
            print(f'  g.current_user: {getattr(g_in_context, "current_user", None)}')
            print(f'  g.logged_in_users: {getattr(g_in_context, "logged_in_users", None)}')
        print(f'  context active_user: {context.get("active_user")}')
        print(f'  context logged_in_users: {context.get("logged_in_users")}')
    
    template_rendered.connect(record, app)
    try:
        response = client.get('/')
        html = response.data.decode('utf-8')
        print('\n--- 检查HTML ---')
        idx = html.find('当前用户')
        print('检查当前用户显示:', html[idx:idx+60] if idx > 0 else '未找到')
        
        # 检查下拉菜单
        idx = html.find('切换账号')
        print('切换账号位置:', html[idx:idx+200] if idx > 0 else '未找到')
        
        # 检查问题：条件判断
        print('\n--- 检查条件判断问题 ---')
        print('检查 g.logged_in_users 长度判断:')
        print('{% if g.logged_in_users|length > 0 %} 在base.html中')
        
        # 检查实际的g对象
        print('\n--- 检查g对象的实际值 ---')
        with client.session_transaction() as sess:
            print('session中:', sess.get('logged_in_users'))
            
    finally:
        template_rendered.disconnect(record, app)

# 检查base.html的问题
print('\n=== 检查base.html的一致性问题 ===')
with open('templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()
    # 检查使用g的地方
    print('使用g.logged_in_users的地方:')
    for i, line in enumerate(content.split('\n'), 1):
        if 'g.logged_in_users' in line:
            print(f'  行{i}: {line.strip()}')
    
    print('\n使用logged_in_users(无g)的地方:')
    for i, line in enumerate(content.split('\n'), 1):
        if 'logged_in_users' in line and 'g.logged_in_users' not in line:
            print(f'  行{i}: {line.strip()}')

# 关键问题：g对象可能在模板渲染时还未准备好！
print('\n=== 潜在问题分析 ===')
print('before_request在每次请求时设置g.current_user和g.logged_in_users')
print('context_processor也返回active_user和logged_in_users')
print('这可能导致不一致！')
