#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired, Length
from wtforms import SelectField
from wtforms import DateTimeField

class TodoListForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 64)])
    status = RadioField('是否完成', validators=[DataRequired()],  choices=[("1", '是'),("0",'否')])
    category = SelectField('分类', choices=[
        ('工作', '工作'),
        ('生活', '生活'),
        ('学习', '学习'),
        ('亲子', '亲子'),
        ('家庭', '家庭')
    ], default='工作')
    priority = SelectField('优先级', choices=[
        ("0", 'P0 - 最高优先级'),
        ("1", 'P1 - 中等优先级'),
        ("2", 'P2 - 最低优先级')
    ], default="1")
    due_time = DateTimeLocalField('截止时间', format='%Y-%m-%dT%H:%M', validators=[], default=None)
    submit = SubmitField('提交')


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 24)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('登录')
