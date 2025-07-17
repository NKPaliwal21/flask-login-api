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

@app.route('/stock-entry', methods=['POST'])
@jwt_required()
def save_stock_entry():
    try:
        data = request.get_json()

        conn = psycopg2.connect(Config.DB_URL)
        cursor = conn.cursor()

        for entry in data.get('entries', []):
            cursor.execute("""
                INSERT INTO stock (username, item, description, unit, qty, rate, value)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                get_jwt_identity(),  # current username
                entry['item'],
                entry['desc'],
                entry['unit'],
                entry['qty'],
                entry['rate'],
                entry['value']
            ))

        conn.commit()
        conn.close()
        return jsonify({"message": "Stock entries saved successfully"}), 200

    except Exception as e:
        print(f"Error saving stock: {e}")
        return jsonify({"error": "Failed to save stock entries"}), 500

    @app.route('/stock-report', methods=['GET'])
    @jwt_required()
    def get_stock_entries():
        try:
            conn = psycopg2.connect(Config.DB_URL)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT item, description, unit, qty, rate, value, created_at
                FROM stock
                WHERE username = %s
                ORDER BY created_at DESC
            """, (get_jwt_identity(),))

            rows = cursor.fetchall()
            conn.close()

            columns = ['item', 'description', 'unit', 'qty', 'rate', 'value', 'created_at']
            result = [dict(zip(columns, row)) for row in rows]

            return jsonify(result), 200

        except Exception as e:
            print(f"Error retrieving stock: {e}")
            return jsonify({"error": "Failed to retrieve stock report"}), 500
