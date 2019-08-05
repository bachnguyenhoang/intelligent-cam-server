from flask import Blueprint

bp = Blueprint('setting',__name__)

from app.setting import setting
