from flask import Blueprint, jsonify, request, current_app
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.queries import (
    get_database_stats, get_all_users, get_all_machines,
    get_user_usage, get_machine_usage, get_time_usage, get_size_distribution,
    get_time_stats_for_user, get_top_users_recent_logs
)

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/stats', methods=['GET'])
def stats():
    """Get overall database statistics"""
    db_path = current_app.config['DB_PATH']
    stats = get_database_stats(db_path)
    return jsonify(stats)

@api.route('/users', methods=['GET'])
def users():
    """Get all users"""
    db_path = current_app.config['DB_PATH']
    users_list = get_all_users(db_path)
    return jsonify(users_list)

@api.route('/machines', methods=['GET'])
def machines():
    """Get all machines"""
    db_path = current_app.config['DB_PATH']
    machines_list = get_all_machines(db_path)
    return jsonify(machines_list)

@api.route('/usage/user/<username>', methods=['GET'])
def user_usage(username):
    """Get usage statistics for a specific user"""
    db_path = current_app.config['DB_PATH']
    user_data = get_user_usage(db_path, username=username)
    
    if not user_data:
        return jsonify({'error': f'User {username} not found'}), 404
    
    return jsonify(user_data)

@api.route('/usage/machine/<machine_name>', methods=['GET'])
def machine_usage(machine_name):
    """Get usage statistics for a specific machine"""
    db_path = current_app.config['DB_PATH']
    machine_data = get_machine_usage(db_path, machine_name=machine_name)
    
    if not machine_data:
        return jsonify({'error': f'Machine {machine_name} not found'}), 404
    
    return jsonify(machine_data)

@api.route('/usage/time', methods=['GET'])
def time_usage():
    """Get time-based usage statistics"""
    db_path = current_app.config['DB_PATH']
    time_data = get_time_usage(db_path)
    return jsonify(time_data)

@api.route('/usage/size', methods=['GET'])
def size_usage():
    """Get size distribution statistics"""
    db_path = current_app.config['DB_PATH']
    size_data = get_size_distribution(db_path)
    return jsonify(size_data)

@api.route('/usage/user/<username>/time', methods=['GET'])
def user_time_stats(username):
    """Get time-based usage statistics for a specific user"""
    db_path = current_app.config['DB_PATH']
    time_data = get_time_stats_for_user(db_path, username)
    return jsonify(time_data)

@api.route('/top-users/recent', methods=['GET'])
def top_users_recent():
    """Get top users by IO operations for recent logs"""
    db_path = current_app.config['DB_PATH']
    log_count = request.args.get('logs', default=5, type=int)
    user_count = request.args.get('users', default=10, type=int)
    users_data = get_top_users_recent_logs(db_path, log_count, user_count)
    return jsonify(users_data)
