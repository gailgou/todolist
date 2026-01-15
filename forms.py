#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, StringField, PasswordField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, EqualTo, Optional

class TodoListForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(1, 64)])
    status = RadioField('是否完成', validators=[DataRequired()],  choices=[("1", '是'),("0",'否')])
    deadline = DateTimeLocalField('截止时间', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    submit = SubmitField('提交')


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 24)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 24)])
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 24)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 24)])
    password_confirm = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password', message='密码必须一致')])
    submit = SubmitField('注册')
