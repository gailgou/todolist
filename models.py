#!/usr/bin/python
#-*- coding: UTF-8 -*-
import time
import subprocess
import platform
from datetime import datetime

from ext import db
from flask_login import UserMixin


class TodoList(db.Model):
    __tablename__ = 'todolist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    create_time = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(32), nullable=False, default='工作')
    priority = db.Column(db.String(8), nullable=False, default='P1')
    deadline = db.Column(db.Integer, nullable=True)
    alarm_set = db.Column(db.Integer, nullable=False, default=0)

    CATEGORIES = ['工作', '生活', '学习', '亲子', '家庭']
    PRIORITIES = ['P0', 'P1', 'P2']

    def __init__(self, user_id, title, status, category='工作', priority='P1', deadline=None):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.create_time = time.time()
        self.category = category if category in self.CATEGORIES else '工作'
        self.priority = priority if priority in self.PRIORITIES else 'P1'
        self.deadline = deadline
        self.alarm_set = 0

    def get_priority_value(self):
        """获取优先级数值，用于排序"""
        priority_map = {'P0': 0, 'P1': 1, 'P2': 2}
        return priority_map.get(self.priority, 1)

    def get_overdue_time(self):
        """获取逾期时间，按年/月/天/时展示"""
        if not self.deadline or self.status == 1:
            return None
        
        now = time.time()
        if self.deadline >= now:
            return None
        
        diff = now - self.deadline
        
        # 计算各时间单位
        years = int(diff // (365 * 24 * 3600))
        if years >= 1:
            return f"{years}年"
        
        months = int(diff // (30 * 24 * 3600))
        if months >= 1:
            return f"{months}月"
        
        days = int(diff // (24 * 3600))
        if days >= 1:
            return f"{days}天"
        
        hours = int(diff // 3600)
        if hours >= 1:
            return f"{hours}小时"
        
        minutes = int(diff // 60)
        if minutes >= 1:
            return f"{minutes}分钟"
        
        return "刚刚"

    def is_overdue(self):
        """检查是否已逾期"""
        if not self.deadline or self.status == 1:
            return False
        return time.time() > self.deadline

    def format_deadline(self):
        """格式化截止时间显示"""
        if not self.deadline:
            return '无'
        dt = datetime.fromtimestamp(self.deadline)
        return dt.strftime('%Y-%m-%d %H:%M')

    def set_alarm(self):
        """为此任务设置系统提醒"""
        if not self.deadline:
            return False, '该任务没有设置截止时间'
        
        system = platform.system()
        
        try:
            dt = datetime.fromtimestamp(self.deadline)
            
            if system == 'Darwin':
                success, msg = self._set_mac_alarm(self.title, dt)
            elif system == 'Windows':
                success, msg = self._set_windows_alarm(self.title, dt)
            else:
                return False, f'不支持的操作系统: {system}'
            
            if success:
                self.alarm_set = 1
            return success, msg
        except Exception as e:
            return False, f'设置失败: {str(e)}'
    
    @staticmethod
    def _set_mac_alarm(title, dt):
        """Mac OS设置提醒"""
        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        script = f'''
        tell application "Reminders"
            make new reminder with properties {{name:"{title}", due date:date "{time_str}"}}
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return True, '已成功添加到Mac提醒事项'
        else:
            return False, f'设置失败: {result.stderr}'
    
    @staticmethod
    def _set_windows_alarm(title, dt):
        """Windows设置提醒 - 使用schtasks创建计划任务"""
        import tempfile
        import os
        
        time_str = dt.strftime('%Y-%m-%d %H:%M')
        task_name = f"TodoReminder_{int(time.time())}_{os.getpid()}"
        
        # 创建VBS脚本显示提醒
        vbs_content = f'''Set objShell = CreateObject("WScript.Shell")
objShell.Popup "待办事项提醒：{title}", 0, "待办提醒 - {time_str}", 64
Set objShell = Nothing'''
        
        # 创建临时目录存放脚本
        temp_dir = os.path.join(tempfile.gettempdir(), 'todo_reminders')
        os.makedirs(temp_dir, exist_ok=True)
        
        vbs_path = os.path.join(temp_dir, f"{task_name}.vbs")
        with open(vbs_path, 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        
        try:
            # 使用schtasks创建计划任务
            cmd = [
                'schtasks', '/create', 
                '/tn', task_name,
                '/tr', f'wscript.exe "{vbs_path}"',
                '/sc', 'once',
                '/st', dt.strftime('%H:%M'),
                '/sd', dt.strftime('%m/%d/%Y'),
                '/f'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, f'提醒已设置成功！将在 {time_str} 弹出提醒窗口'
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                # 尝试立即运行测试
                test_result = subprocess.run(['wscript.exe', vbs_path], 
                                           capture_output=True, text=True, timeout=10)
                if test_result.returncode == 0:
                    return True, f'提醒脚本测试成功！将在 {time_str} 提醒（任务计划创建失败，但脚本可用）'
                return False, f'提醒设置失败: {error_msg}'
        except Exception as e:
            return False, f'提醒设置失败: {str(e)}'


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False)
    password = db.Column(db.String(24), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password
