# Define los modelos de datos utilizando SQLAlchemy u otro ORM.
from app import db
from datetime import datetime


class RolUsuario(db.Model):
    cod_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(14), index=True, unique=True)
    fecha_baja_RU = db.Column(db.Date, default=None)
    usuarios = db.relationship('Usuario', backref='rol_usuario', lazy='dynamic')

    def dar_de_baja(self):
        self.fecha_baja_RU = datetime.utcnow().date()


class Usuario(db.Model):
    cod_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(14), index=True, unique=True)
    contrasena_usuario = db.Column(db.String(20))
    email_usuario = db.Column(db.String(100), index=True, unique=True)
    fecha_nacimiento_usuario = db.Column(db.Date)
    cod_rol = db.Column(db.Integer, db.ForeignKey('rol_usuario.cod_rol'))


class Direccion(db.Model):
    cod_direccion = db.Column(db.Integer, primary_key=True)
    calle_direccion = db.Column(db.String(100), index=True)
    numero_direccion = db.Column(db.Integer)
    cod_localidad = db.Column(db.Integer, db.ForeignKey('localidad.cod_localidad'))


class Localidad(db.Model):
    cod_localidad = db.Column(db.Integer, primary_key=True)
    nombre_localidad = db.Column(db.String(100), index=True)
    fecha_baja_localidad = db.Column(db.Date, default=None)
    direcciones = db.relationship('Direccion', backref='localidad', lazy='dynamic')
    cod_provincia = db.Column(db.Integer, db.ForeignKey('provincia.cod_provincia'))

    def dar_de_baja(self):
        self.fecha_baja_localidad = datetime.utcnow().date()


class Provincia(db.Model):
    cod_provincia = db.Column(db.Integer, primary_key=True)
    nombre_provincia = db.Column(db.String(100), index=True, unique=True)
    fecha_baja_provincia = db.Column(db.Date, default=None)
    localidades = db.relationship('Localidad', backref='provincia', lazy='dynamic')

    def dar_de_baja(self):
        self.fecha_baja_provincia = datetime.utcnow().date()


