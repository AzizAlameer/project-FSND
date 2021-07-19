import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from sqlalchemy.orm import query
from sqlalchemy.sql.expression import false

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={"/": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization')
        response.headers.add(
            'Access-Control-Allow-Headers',
            'GET, POST, PATCH, DELETE, OPTION')
        return response

    @app.route('/categories', methods=['GET'])
    def retrieve_categories():
        selection = Category.query.order_by(Category.id).all()
        # dictionary of categories
        categories = {}
        for category in selection:
            categories[category.id] = category.type

        if(len(selection) == 0):
            abort(404)
        return jsonify({
            'success': True,
            'categories': categories
        })

    @app.route('/questions', methods=['GET'])
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        categories = Category.query.order_by(Category.id).all()
        # dictionary of categories
        categoriesFormat = {}
        for category in categories:
            categoriesFormat[category.id] = category.type

        if(len(current_questions) == 0):
            abort(404)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': categoriesFormat,
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if (question is None):
                abort(400)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id,
                'total_questions': len(Question.query.all())
            })
        except BaseException:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        if(len(new_question) == 0 or len(new_answer) == 0):
            abort(422)

        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                difficulty=new_difficulty,
                category=new_category
            )
            question.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(selection)
            })
        except BaseException:
            abort(422)

    @app.route('/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        try:
            term = body.get('searchTerm', None)
            Qresult = Question.query.filter(
                Question.question.ilike(f'%{term}%')).all()
            Qpag = paginate_questions(request, Qresult)
            return jsonify({
                'success': True,
                'questions': Qpag,
                'total_questions': len(Qresult)
            })
        except BaseException:
            abort(404)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def question_by_category(category_id):
        category = Category.query.get(category_id)
        if (category is None):
            abort(400)

        selection = Question.query.filter(
            Question.category == category_id).all()

        current_questions = paginate_questions(request, selection)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'current_category': category_id,
            'total_questions': len(selection)
        })

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()
        try:
            category = body.get('quiz_category', None)
            previous_questions = body.get('previous_questions', None)

            if category is None or previous_questions is None:
                abort(400)
            # question if all or specific category
            if category['id'] == 0:
                questions = Question.query.order_by(Question.id).all()
            else:
                questions = Question.query.filter_by(
                    category=category['id']).all()

            numQ = len(questions)
            nextQ = random.choice(questions).format()

            # not in previous questions
            old = True
            while old:
                if nextQ['id'] in previous_questions:
                    nextQ = random.choice(questions).format()
                else:
                    old = False
                if (len(previous_questions) == numQ):
                    return jsonify({
                        'success': True,
                        'message': "done"
                    }), 200

            return jsonify({
                'success': True,
                'question': nextQ
            })
        except BaseException:
            abort(404)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

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

    return app
