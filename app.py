import os
from functools import wraps
import simplejson as json
import traceback

from flask import Flask, Response, render_template, make_response, url_for, redirect
from flask import jsonify
from flask import request

from model import media
from peewee import DoesNotExist
from peewee import fn as dbfn

STATIC_DIR = '/static'
TEMPLATE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')

app = Flask(__name__, static_url_path=STATIC_DIR, template_folder=TEMPLATE_DIR)
app.debug = True


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


# Open database connection before requests and close them afterwards
@app.before_request
def before_request():
    media.DATABASE.connect()


@app.after_request
def after_request(response):
    media.DATABASE.close()
    return response


@app.route('/')
def root():
    try:
        image = media.Image.select().where(media.Image.quality.is_null()).order_by(dbfn.Random()).get()
    except DoesNotExist:
        print("No data available")
        return render_template("/empty.html")

    return render_template("/index.html", data=image)


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


@app.route('/images/<id>', methods=['GET'])
def rate(id=None):
    response_var = request.args.get('quality', '0')  # when in doubt choose 0 for quality
    print("Response %s for image with id %s" % (response_var, id))

    try:
        id = int(id)
        response_var = int(response_var)
    except ValueError:
        print("Could not convert id or response to integer")
        return redirect(url_for('root'))

    try:
        image = media.Image.get_by_id(id)
        image.quality = response_var
        image.save()
    except DoesNotExist:
        print("Image with that id could not be found.")
        return redirect(url_for('root'))

    return redirect(url_for('root'))


if __name__ == '__main__':
    app.run()
