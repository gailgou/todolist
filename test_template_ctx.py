from app import app
from flask import g, template_rendered
from contextlib import contextmanager

app.config['TESTING'] = True
client = app.test_client()

@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

# 测试切换用户后的模板上下文
print('=== 测试模板上下文 ===')
with captured_templates(app) as templates:
    client.post('/login', data={'username': 'admin', 'password': 'admin'})
    client.post('/login', data={'username': 'user1', 'password': '123456'})
    
    print('\n--- Before switch ---')
    with client.session_transaction() as sess:
        print(f'active_user_id: {sess.get("active_user_id")}')
    
    print('\n--- Switching and following redirect ---')
    response = client.get('/switch/1', follow_redirects=True)
    
    print(f'\nNumber of templates rendered: {len(templates)}')
    for i, (template, context) in enumerate(templates):
        print(f'\nTemplate {i}: {template.name}')
        if 'active_user' in context:
            print(f'  active_user: {context["active_user"].username if context["active_user"] else None}')
        g_ctx = context.get('g')
        if g_ctx:
            print(f'  g.current_user: {g_ctx.current_user.username if hasattr(g_ctx, "current_user") and g_ctx.current_user else None}')
            print(f'  g.logged_in_users: {g_ctx.logged_in_users if hasattr(g_ctx, "logged_in_users") else None}')

# 检查base.html中g的使用问题
print('\n=== 检查g对象问题 ===')
with captured_templates(app) as templates:
    client.post('/login', data={'username': 'admin', 'password': 'admin'})
    response = client.get('/')
    
    template, context = templates[-1]
    g_ctx = context.get('g')
    
    print(f'g in context: {g_ctx is not None}')
    if g_ctx:
        print(f'g.current_user: {hasattr(g_ctx, "current_user")}')
        print(f'g.logged_in_users: {hasattr(g_ctx, "logged_in_users")}')
    
    # 检查context_processor注入的变量
    print(f'\ncontext_processor variables:')
    print(f'  active_user in context: {"active_user" in context}')
    print(f'  logged_in_users in context: {"logged_in_users" in context}')
