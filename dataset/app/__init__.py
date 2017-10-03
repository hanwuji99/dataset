# -*- coding: utf-8 -*-

from flask import Flask
from peewee import MySQLDatabase
from redis import StrictRedis

from .config import Config


db = MySQLDatabase(None)
redis_client = StrictRedis(**Config.REDIS)


def create_app():
    """
    创建flask应用对象
    :return:
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    db.init(**app.config['MYSQL'])

    from .models import models
    db.create_tables(models, safe=True)

    from .hooks import before_app_request, after_app_request
    app.before_request(before_app_request)
    app.teardown_request(after_app_request)

    from .blueprints.api import bp_api
    app.register_blueprint(bp_api, url_prefix='/api')

    return app
