import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# db_drop_and_create_all()

# ROUTES


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()

    if len(drinks) == 0:
        abort(404)

    drinks_format = [drink.short() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': drinks_format
    }), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_details(f):
    drinks = Drink.query.all()
    if len(drinks) == 0:
        abort(404)

    drinks_format = [drink.long() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': drinks_format
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(f):
    req = request.get_json()

    drink_recipe = req.get('recipe', None)

    try:
        if not isinstance(drink_recipe, list):
            drink_recipe = [req.get('recipe', None)]
        drink = Drink(title=req['title'], recipe=json.dumps(drink_recipe))
        drink.insert()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except BaseException:
        abort(422)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(f, id):
    req = request.get_json()
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)

    try:
        if 'title' in req:
            drink.title = req['title']

        if 'recipe' in req:
            drink.recipe = json.dumps(req['recipe'])

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except BaseException:
        abort(422)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(f, id):
    drink = Drink.query.get(id)
    if drink is None:
        abort(404)

    try:
        drink.delete()

        return jsonify({
            'success': True,
            "delete": drink.id
        }), 200
    except BaseException:
        abort(422)


# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(405)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "method not allowed"
    }), 405


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
