# Define los formularios de la aplicación utilizando Flask-WTF.
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    nombre_usuario = StringField('Nombre de usuario', validators=[DataRequired()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')


class RegisterForm(FlaskForm):
    nombre = StringField('nombre', validators=[DataRequired()])
    apellido_usuario = StringField('apellido_usuario', validators=[DataRequired()])
    nombre_usuario = StringField('Nombre de usuario', validators=[DataRequired()])
    contrasena_usuario = StringField('Contraseña', validators=[DataRequired(), Length(min=6, max=35)])
    repetir_contrasena = StringField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('contrasena_usuario',message='Las contraseñas deben coincidir')])
    email_usuario = StringField('email_usuario', validators=[DataRequired()])
    fecha_nacimiento_usuario = DateField('fecha_nacimiento_usuario', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')
