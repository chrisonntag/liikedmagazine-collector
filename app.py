import os
from functools import wraps
import traceback

from flask import Flask, Response, render_template, send_from_directory, url_for, redirect
from flask import jsonify
from flask import request
from flask_basicauth import BasicAuth

from settings import settings

from model.model import User, MediaObject, DATABASE
from peewee import DoesNotExist
from peewee import fn as dbfn

STATIC_DIR = '/static'
TEMPLATE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
IMAGE_FOLDER = 'data'

app = Flask(__name__, static_url_path=STATIC_DIR, template_folder=TEMPLATE_DIR)
app.debug = True
app.config['BASIC_AUTH_USERNAME'] = settings.auth_username
app.config['BASIC_AUTH_PASSWORD'] = settings.auth_password
app.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(app)


def print_exceptions(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print('')
            print('------')
            print('API: exception')
            print(e)
            print(traceback.format_exc())
            print(request.url)
            print(request.data)
            print('------')
            raise
    return wrapped


def root_dir():
    return os.path.abspath(os.path.dirname(__file__)) + TEMPLATE_DIR


def get_file(filename):
    try:
        src = os.path.join(root_dir(), filename)
        return open(src).read()
    except IOError as exc:
        return str(exc)


def get_error(msg):
    return jsonify({'result': 'ERROR', 'message': msg})


@app.route('/')
def root():
    try:
        image = MediaObject.select()\
            .where(MediaObject.quality.is_null(), MediaObject.downloaded == True)\
            .order_by(dbfn.Random())\
            .get()
    except DoesNotExist:
        print("No data available")
        return render_template("/empty.html")

    data = {
        "image": image,
        "url": "media/%s.%s.jpg" % (image.user.user_id, image.media_id)
    }

    return render_template("/index.html", data=data)


# Serving static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_resource(path):
    mimetypes = {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "application/javascript",
    }
    complete_path = os.path.join(root_dir(), path)
    ext = os.path.splitext(path)[1]
    mimetype = mimetypes.get(ext, "text/html")
    content = get_file(complete_path)
    return Response(content, mimetype=mimetype)


@app.route('/media/<path:filename>')
def send_file(filename):
    return send_from_directory(settings.data_path, filename)


@app.route('/users/<user_id>/<media_id>', methods=['GET'])
def rate(user_id=None, media_id=None):
    response_var = request.args.get('quality', '0')  # when in doubt choose 0 for quality
    print("Response %s for image with id %s" % (response_var, media_id))

    try:
        media_id = int(media_id)
        user_id = int(user_id)
        response_var = int(response_var)
    except ValueError:
        print("Could not convert id or response to integer")
        return redirect(url_for('root'))

    try:
        image = MediaObject.get(user=user_id, media_id=media_id)
        image.quality = response_var
        image.save()
    except DoesNotExist:
        print("MediaObject with that id could not be found.")
        return redirect(url_for('root'))

    return redirect(url_for('root'))


if __name__ == '__main__':
    app.run()
