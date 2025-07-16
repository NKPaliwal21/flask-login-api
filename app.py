from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from models import get_user_by_username, create_user
from config import Config
import hashlib

app = Flask(__name__)
app.config.from_object(Config)

# ✅ Simplified, reliable CORS config
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers="*", expose_headers="*")

# Initialize JWT Manager
jwt = JWTManager(app)

# Utility function to hash passwords
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
      return '', 204  # CORS preflight
      
    data = request.get_json()
    if get_user_by_username(data['username']):
        return jsonify({'error': 'User already exists'}), 400
    create_user(data['username'], hash_pw(data['password']))
    return jsonify({'message': 'Registered successfully'})

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    
    if request.method == 'OPTIONS':
        return '', 204  # CORS preflight
    
    data = request.get_json()
    user = get_user_by_username(data['username'])
    if user and hash_pw(data['password']) == user[2]:
        token = create_access_token(identity=user[1])
        return jsonify({'message': 'Login successful', 'token': token})
    return jsonify({'error': 'Invalid credentials'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
