#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, StringField, PasswordField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Length, Optional

class TodoListForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 64)])
    status = RadioField('是否完成', validators=[DataRequired()],  choices=[("1", '是'),("0",'否')])
    category = SelectField('分类', validators=[DataRequired()], choices=[
        ('work', '工作'),
        ('life', '生活'),
        ('study', '学习'),
        ('parenting', '亲子'),
        ('family', '家庭')
    ], default='work')
    priority = SelectField('优先级', validators=[DataRequired()], choices=[
        ('P0', 'P0 - 紧急'),
        ('P1', 'P1 - 重要'),
        ('P2', 'P2 - 普通')
    ], default='P2')
    deadline = StringField('截止时间 (格式: 2026-01-30 18:00)', validators=[Optional()])
    submit = SubmitField('提交')


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 24)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('登录')
