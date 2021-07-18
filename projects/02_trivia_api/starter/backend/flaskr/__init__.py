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
  page=request.args.get('page',1,type=int)
  start=  (page-1) * QUESTIONS_PER_PAGE
  end=start+QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions
  


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={"/": {"origins": "*"}})


  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTION')
    return response
  '''

  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories',methods=['GET'])
  def retrieve_categories():
    selection=Category.query.order_by(Category.id).all()
    #dictionary of categories
    categories={}
    for category in selection:
      categories[category.id]=category.type

    if(len(selection)==0):
      abort(404)
    return jsonify({
      'success':True,
      'categories':categories
    })


  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions',methods=['GET'])
  def retrieve_questions():
    selection=Question.query.order_by(Question.id).all()
    current_questions=paginate_questions(request,selection)

    categories=Category.query.order_by(Category.id).all()
    #dictionary of categories
    categoriesFormat={}
    for category in categories:
      categoriesFormat[category.id]=category.type
    
    if(len(current_questions)==0):
      abort(404)
    return jsonify({
      'success':True,
      'questions':current_questions,
      'total_questions':len(selection),
      'categories':categoriesFormat,
    })
  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()
      if (question  is None):
        abort(400)

      question.delete()

      return jsonify({
        'success': True,
        'deleted': question_id,
        'total_questions':len(Question.query.all())
      })
    except:
      abort(422)
  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.


  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    new_question=body.get('question',None)
    new_answer=body.get('answer',None)
    new_category=body.get('category',None)
    new_difficulty=body.get('difficulty',None)
    
    if(len(new_question)==0 or len(new_answer)==0):
      abort(422)
      
    try:
      question=Question(
        question=new_question,
        answer=new_answer,
       difficulty=new_difficulty,
       category=new_category
        )
      question.insert()
      selection=Question.query.order_by(Question.id).all()
      current_questions=paginate_questions(request,selection)
      return jsonify({
        'success':True,
        'created':question.id,
        'questions':current_questions,
        'total_questions':len(selection)
      })
    except:
      abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/search', methods=['POST'])
  def search_question():
    body = request.get_json()
    try:
      term=body.get('searchTerm',None)
      Qresult=Question.query.filter(Question.question.ilike(f'%{term}%')).all()
      Qpag=paginate_questions(request,Qresult)
      return jsonify({
        'success':True,
        'questions':Qpag,
        'total_questions':len(Qresult)
      })
    except:
      abort(404)
  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def question_by_category(category_id):
      category=Category.query.get(category_id)
      if (category  is None):
        abort(400)

      selection=Question.query.filter(Question.category == category_id).all()

      current_questions=paginate_questions(request,selection)
      return jsonify({
        'success':True,
        'questions':current_questions,
        'current_category':category_id,
        'total_questions':len(selection)
      })



  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes',methods=['POST'])
  def play_quiz():
    body = request.get_json()
    try:
      category=body.get('quiz_category',None)
      previous_questions=body.get('previous_questions',None)
     
      if category is None or previous_questions is None :
        abort(400)
       #question if all or specific category
      if category['id'] == 0:
        questions = Question.query.order_by(Question.id).all()
      else:
        questions = Question.query.filter_by(category=category['id']).all()
      
      nextQ=random.choice(questions).format()

      #not in previous questions 
      old=True
      while old:
       if  nextQ['id'] in previous_questions:
        nextQ=random.choice(questions).format()
       else:
        old=False
    
      return jsonify({
      'success':True,
      'question':nextQ
      })
    except:
      abort(404)     

 
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
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

    