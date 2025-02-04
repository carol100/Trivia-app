import os
from unicodedata import category
from urllib import response
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories', methods=['GET'])
    def get_all_categories():
        categories = Category.query.all()
        result = {}
        for category in categories:
            result[category.id] = category.type

        return jsonify({
            'success': True,
            'total_categories': len(categories),
            'categories': result
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by('category').all()
        questions_list = paginate_questions(request, selection)
        categories = Category.query.all()
        result = {}
        for category in categories:
            result[category.id] = category.type

        if len(questions_list) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": questions_list,
                "total_questions": len(Question.query.all()),
                "categories": result,
                "current_category": category.type
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            selection = Question.query.order_by(Question.id).all()
            questions_list = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': questions_list,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        request_data = request.get_json()

        try:
            new_question = request_data.get("question", None)
            new_category = request_data.get("category", None)
            new_answer = request_data.get("answer", None)
            new_difficulty = request_data.get("difficulty", None)

            question = Question(question=new_question, category=new_category,
                                answer=new_answer, difficulty=new_difficulty)

            question.insert()

            selection = Question.query.order_by(Question.id).all()
            questions_list = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': questions_list,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/questions/search', methods=['POST'])
    def search_question():
        data = request.get_json()

        search_term = data.get("searchTerm", None)

        # Return 422 status code if search_term is empty
        if search_term == "":
            abort(422)

        try:
            # get all questions with the search_term substring
            search_results = Question.query.filter(
                Question.question.ilike("%{}%".format(search_term))).all()

            # Return 404 status code where search results is empty
            if len(search_results) == 0:
                abort(404)

            current_category_id = search_results[0].category
            current_category = Category.query.filter(
                Category.id == current_category_id).first()

            # else, paginate search results
            results = paginate_questions(request, search_results)

            # return jsonify object for successful response

            return jsonify({
                "success": True,
                "questions": results,
                "total_questions": len(search_results),
                "current_category": current_category.type
            }), 200

        except:
            abort(404)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def get_category_questions(category_id):
        selection = Question.query.filter(
            Question.category == category_id).all()
        questions_list = paginate_questions(request, selection)

        current_category = Category.query.filter(
            Category.id == category_id).first()

        if len(questions_list) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": questions_list,
                "total_questions": len(selection),
                "current_category": current_category.type
            }
        )

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def play_quizzes():
        try:
            request_data = request.get_json()
            previous_questions = request_data.get("previous_questions", None)
            category = request_data.get("quiz_category", None)

            # if not previous_questions:
            #     previous_questions = []

            # if category is provided
            if category['id']:
                question = Question.query.filter(
                    Question.category == category['id']).filter(~Question.id.in_(previous_questions)).order_by(func.random()).first()

            else:

                question = Question.query.filter(~Question.id.in_(
                    previous_questions)).order_by(func.random()).first()

            if question:
                previous_questions.append(question.id)

                return jsonify(
                    {
                        "success": True,
                        "question": question.format(),
                        "previous_questions": previous_questions
                    }
                )

            else:
                return jsonify(
                    {
                        "success": True,
                        "question": None,
                        "previous_questions": previous_questions
                    }
                )

        except:
            abort(404)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not Found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    return app
