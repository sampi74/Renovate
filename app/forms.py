# Define los formularios de la aplicación utilizando Flask-WTF.
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import TextAreaField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Optional, NumberRange

from app.enums import Talle
from app.models import Provincia, Localidad, Categoria, Subcategoria


class LoginForm(FlaskForm):
    nombre_usuario = StringField('Nombre de usuario', validators=[DataRequired()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')


class RegisterForm(FlaskForm):
    nombre = StringField('nombre', validators=[DataRequired()])
    apellido_usuario = StringField('apellido_usuario', validators=[DataRequired()])
    nombre_usuario = StringField('Nombre de usuario', validators=[DataRequired()])
    contrasena_usuario = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6, max=35)])
    repetir_contrasena = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('contrasena_usuario', message='Las contraseñas deben coincidir')])
    email_usuario = StringField('email_usuario', validators=[DataRequired()])
    fecha_nacimiento_usuario = DateField('fecha_nacimiento_usuario', validators=[DataRequired()])
    foto_usuario = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    calle_direccion = StringField('Calle', validators=[DataRequired()])
    numero_direccion = StringField('Número', validators=[DataRequired()])
    submit = SubmitField('Registrarse')


class ProvinciaForm(FlaskForm):
    nombre_provincia = StringField('Nombre de la Provincia', validators=[DataRequired()])
    submit = SubmitField('Guardar')


class LocalidadForm(FlaskForm):
    nombre_localidad = StringField('Nombre de la Localidad', validators=[DataRequired()])
    submit = SubmitField('Agregar Localidad')


class UpdateUserForm(FlaskForm):
    email = StringField('Email', validators=[Optional()])
    password = PasswordField('New Password', validators=[
        Optional(),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password', validators=[Optional()])
    foto_usuario = FileField('Profile Picture', validators=[Optional()])
    # Campos de dirección
    calle = StringField('Calle', validators=[DataRequired()])
    numero = StringField('Número', validators=[DataRequired()])
    provincia = SelectField('Provincia', coerce=int, validators=[DataRequired()])
    localidad = SelectField('Localidad', coerce=int, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.provincia.choices = [(prov.cod_provincia, prov.nombre_provincia) for prov in Provincia.query.all()]
        self.localidad.choices = [(loc.cod_localidad, loc.nombre_localidad) for loc in Localidad.query.all()]


class CategoriaForm(FlaskForm):
    nombre_categoria = StringField('Nombre de la Categoría', validators=[DataRequired()])
    submit = SubmitField('Crear Categoría')


class ModificarSubcategoriaForm(FlaskForm):
    nombre_subcategoria = StringField('Nombre de la Subcategoría', validators=[DataRequired(), Length(min=1, max=100)])
    categorias = SelectField('Categorías', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Agregar Subcategoría')

    def __init__(self, *args, **kwargs):
        super(ModificarSubcategoriaForm, self).__init__(*args, **kwargs)
        self.categorias.choices = [(categoria.cod_categoria, categoria.nombre_categoria) for categoria in
                                   Categoria.query.all()]


class SubcategoriaForm(FlaskForm):
    nombre_subcategoria = StringField('Nombre de la Subcategoría', validators=[DataRequired(), Length(min=1, max=100)])
    categorias = SelectMultipleField('Categorías', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Agregar Subcategoría')

    def __init__(self, *args, **kwargs):
        super(SubcategoriaForm, self).__init__(*args, **kwargs)
        self.categorias.choices = [(categoria.cod_categoria, categoria.nombre_categoria) for categoria in Categoria.query.all()]


class PublicacionForm(FlaskForm):
    nombre_publicacion = StringField('Nombre de la Publicación', validators=[DataRequired(), Length(max=100)])
    descripcion_publicacion = TextAreaField('Descripción', validators=[Length(max=300)])
    precio_publicacion = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0)])
    talle_publicacion = SelectField('Talle', choices=[(choice.name, choice.value) for choice in Talle], validators=[DataRequired()])
    color_publicacion = StringField('Color', validators=[DataRequired(), Length(max=20)])
    foto_publicacion = FileField('Foto de la Publicación', validators=[DataRequired()])
    submit = SubmitField('Crear Publicación')
