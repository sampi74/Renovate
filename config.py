# Archivo de configuración para la aplicación
# (configuración de desarrollo, producción, etc.).
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'C:/Seminario/Renovate_2/fotos_perfil'
    FOTOS_PUBLICACION = 'C:/Seminario/Renovate_2/fotos_publicacion'


