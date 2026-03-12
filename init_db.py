#!/usr/bin/python
#-*- coding: UTF-8 -*-

from app import app, db, init_default_data

# 初始化数据库
def init_db():
    with app.app_context():
        # 创建所有表
        db.create_all()
        init_default_data()
        print("数据库初始化完成")

if __name__ == '__main__':
    init_db()
