#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, StringField, PasswordField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional

class TodoListForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 64)])
    status = RadioField('是否完成', validators=[DataRequired()],  choices=[("1", '是'),("0",'否')])
    priority = SelectField('优先级', validators=[DataRequired()], choices=[('P0', 'P0 - 紧急'), ('P1', 'P1 - 重要'), ('P2', 'P2 - 普通')], default='P2')
    due_date = StringField('完成日期', validators=[Optional()])
    submit = SubmitField('提交')


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 24)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 24)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 24)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('注册')
