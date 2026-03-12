from app import app
import re

app.config['TESTING'] = True
client = app.test_client()

# 登录admin
client.post('/login', data={'username': 'admin', 'password': 'admin'})

# 获取主页
response = client.get('/')
html = response.data.decode('utf-8')

# 检查关键元素
print('=== 检查主页内容 ===')
print('包含"admin 的待办事项":', 'admin 的待办事项' in html)
print('包含"完成项目报告":', '完成项目报告' in html)
print('包含"当前用户":', '当前用户' in html)
print('包含"切换账号":', '切换账号' in html)

# 登录第二个用户
client.post('/login', data={'username': 'user1', 'password': '123456'})
response = client.get('/')
html = response.data.decode('utf-8')
print('\n=== 登录user1后 ===')
print('包含"user1 的待办事项":', 'user1 的待办事项' in html)
print('包含"整理工作文档":', '整理工作文档' in html)

# 检查下拉菜单
response = client.get('/')
html = response.data.decode('utf-8')
print('\n=== 检查下拉菜单 ===')
print('包含"已登录账号":', '已登录账号' in html)
print('包含"(2/3)":', '(2/3)' in html)
print('包含"添加登录账号":', '添加登录账号' in html)

# 检查上下文处理器注入
print('\n=== 检查切换链接 ===')
switch_links = re.findall(r'/switch/\d+', html)
print('切换链接:', switch_links)
logout_links = re.findall(r'/logout/\d+', html)
print('登出链接:', logout_links)

# 检查base.html中的g对象使用
print('\n=== 检查g对象渲染 ===')
print('检查g.current_user:', 'g.current_user' in html)
print('检查g.logged_in_users:', 'g.logged_in_users' in html)

# 打印一些调试信息
print('\n=== 打印部分HTML ===')
idx = html.find('当前用户')
if idx > 0:
    print('当前用户附近:', html[idx:idx+100])

idx = html.find('切换账号')
if idx > 0:
    print('切换账号附近:', html[idx:idx+200])
    
# 检查实际渲染的logged_in_users长度
with client.session_transaction() as sess:
    print('\n=== Session信息 ===')
    print('logged_in_users:', sess.get('logged_in_users'))
    print('active_user_id:', sess.get('active_user_id'))

# 测试用户切换
print('\n=== 测试切换用户 ===')
response = client.get('/switch/1', follow_redirects=True)
html = response.data.decode('utf-8')
print('切换到admin后状态:', response.status_code)
print('是否显示admin的待办:', '完成项目报告' in html)

# 测试登出功能
print('\n=== 测试登出功能 ===')
response = client.get('/logout/2', follow_redirects=True)
html = response.data.decode('utf-8')
print('登出user1后状态:', response.status_code)
with client.session_transaction() as sess:
    print('当前logged_in_users:', sess.get('logged_in_users'))
