#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
数据库迁移脚本：添加分类、优先级和截止时间字段
"""
import sqlite3
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'todolist.db')

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查是否已经添加了新字段
    cursor.execute("PRAGMA table_info(todolist)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # 添加分类字段
    if 'category' not in columns:
        cursor.execute("ALTER TABLE todolist ADD COLUMN category VARCHAR(32) DEFAULT '工作'")
        print("已添加分类字段")
    
    # 添加优先级字段
    if 'priority' not in columns:
        cursor.execute("ALTER TABLE todolist ADD COLUMN priority VARCHAR(8) DEFAULT 'P2'")
        print("已添加优先级字段")
    
    # 添加截止时间字段
    if 'deadline' not in columns:
        cursor.execute("ALTER TABLE todolist ADD COLUMN deadline INTEGER")
        print("已添加截止时间字段")
    
    # 提交更改
    conn.commit()
    print("数据库迁移完成")
    
except Exception as e:
    print(f"数据库迁移失败: {e}")
    conn.rollback()

finally:
    conn.close()