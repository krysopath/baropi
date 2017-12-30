#!/usr/bin/env python3
# coding=utf-8
from flask import Flask, g, send_file, request, make_response
from json import dumps
from flask_restful import Api
from . import database as db
from . import sensors as sensors_module
from .readout import create_graph, get_last_samples
from .encoder import APIEncoder
import mimetypes
import io
from .config import cfg

mimetypes.add_type('image/svg+xml', '.svg')
app = Flask(__name__)
api = Api(app)

settings = app.config.get('RESTFUL_JSON', {})
settings.setdefault('indent', 2)
settings.setdefault('sort_keys', True)
app.config['RESTFUL_JSON'] = settings


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(
        dumps(
            data,
            cls=APIEncoder,
            indent=2
        ),
        code
    )
    resp.headers.extend(headers or {})
    return resp


@app.before_first_request
def add_resources():
    for sensor_def in cfg.sensors:
        sensor_class = getattr(sensors_module, sensor_def['module'])
        sensor = sensor_class(**sensor_def)

        for res in sensor.resources:
            # res_class, sensor, res_path = res
            link = "/%s/%s/%s" % (cfg.server.prefix, sensor_def['path'], res.such_args)

            print(
                " +++ mounting", res,
                "from", sensor_class,
                "with", sensor_def, "on", link)
            api.add_resource(
                res, link
            )


@app.before_request
def before_request():
    g.db = db.make_session()
    if cfg.redis.enabled:
        # print(" +++ baropi server app is using redis", cfg.redis.connection)
        pass


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.remove()


@app.route('/graph')
def view_graphs():
    delta = {
        key: int("".join(request.args[key]))
        for key in request.args
    }  # flask's requests.args values are a foken list of chars?! just nope.. TODO want beautiful code
    buf = io.BytesIO()
    plt, fig = create_graph(
        get_last_samples(delta)
    )
    fig.savefig(
        buf,
        pad_inches=0,
        bbox_inches='tight',
        dpi=100,
        format='svg'
    )
    buf.seek(0)
    plt.clf()
    plt.close()
    return send_file(
        buf, mimetype='image/svg+xml'
    )