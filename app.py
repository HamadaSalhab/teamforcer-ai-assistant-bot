from flask import Flask, request
from flask_restx import Api, Resource, fields
from datetime import datetime
from storage.sqlalchemy_database import get_db, ChatHistory
from sqlalchemy import func, case

app = Flask(__name__)
api = Api(app, version='1.0', title='Telegram Bot API',
    description='A simple API for Telegram Bot data')
ns = api.namespace('', description='Telegram Bot operations')

# Define models for Swagger documentation
request_model = api.model('Request', {
    'user_id': fields.Integer,
    'group_id': fields.Integer,
    'timestamp': fields.DateTime,
    'message_content': fields.String,
    'is_group': fields.Boolean,
    'file_name': fields.String,
    'file_type': fields.String
})

user_stats_model = api.model('UserStats', {
    'user_id': fields.Integer,
    'request_count': fields.Integer,
    'file_count': fields.Integer
})

@ns.route('/requests_by_date')
class RequestsByDate(Resource):
    @api.doc(params={'date': 'Date in YYYY-MM-DD format'})
    @api.marshal_list_with(request_model)
    def get(self):
        date_str = request.args.get('date')
        if not date_str:
            api.abort(400, "Date parameter is required")
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            api.abort(400, "Invalid date format. Use YYYY-MM-DD")
        
        db = next(get_db())
        try:
            requests = db.query(ChatHistory).filter(
                func.date(ChatHistory.timestamp) == date.date()
            ).all()
            return requests
        finally:
            db.close()

@ns.route('/user_stats_by_date')
class UserStatsByDate(Resource):
    @api.doc(params={'date': 'Date in YYYY-MM-DD format'})
    @api.marshal_list_with(user_stats_model)
    def get(self):
        date_str = request.args.get('date')
        if not date_str:
            api.abort(400, "Date parameter is required")
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            api.abort(400, "Invalid date format. Use YYYY-MM-DD")
        
        db = next(get_db())
        try:
            user_stats = db.query(
                ChatHistory.user_id,
                func.count(ChatHistory.id).label('request_count'),
                func.sum(case((ChatHistory.file_name.isnot(None), 1), else_=0)).label('file_count')
            ).filter(
                func.date(ChatHistory.timestamp) == date.date()
            ).group_by(ChatHistory.user_id).all()
            
            return [{'user_id': stat.user_id, 'request_count': stat.request_count, 'file_count': stat.file_count} for stat in user_stats]
        finally:
            db.close()

if __name__ == '__main__':
    app.run(debug=True)