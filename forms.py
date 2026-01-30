#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, StringField, PasswordField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime

class TodoListForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 64)])
    status = RadioField('是否完成', validators=[DataRequired()],  choices=[("1", '是'),("0",'否')])
    category = SelectField('分类', validators=[DataRequired()], 
                          choices=[('工作', '工作'), ('生活', '生活'), ('学习', '学习'), ('亲子', '亲子'), ('家庭', '家庭')])
    priority = SelectField('优先级', validators=[DataRequired()], 
                          choices=[('P0', 'P0-最高'), ('P1', 'P1-中等'), ('P2', 'P2-普通')])
    deadline = StringField('截止时间', render_kw={"placeholder": "点击选择日期和时间"})
    submit = SubmitField('提交')


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 24)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('登录')
