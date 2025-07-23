from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from models import get_user_by_username, create_user
from config import Config
import hashlib
import psycopg2
import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


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
        
        print("stock-entry-Headers:", dict(request.headers))
        print("Received JSON:", request.get_json())
        
        data = request.get_json()
        conn = psycopg2.connect(Config.DB_URL)
        cursor = conn.cursor()
        for entry in data.get('entries', []):
            print(f"Saving entry: {entry}")
            cursor.execute("""
                INSERT INTO stockitem (username, item, description, unit, qty, rate, value)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                get_jwt_identity(),
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


@app.route('/stock-report', methods=['GET'])  # ✅ Now outside of save_stock_entry
@jwt_required()
def get_stock_entries():
    try:

        print("stock-report-Headers:", dict(request.headers))

        conn = psycopg2.connect(Config.DB_URL)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT item, description, unit, qty, rate, value, created_at
            FROM stockitem
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

@app.route('/export-csv', methods=['GET'])
def export_csv():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401

    # Replace with actual token validation logic
    # username = validate_token(token)
    username = 'testuser'  # placeholder

    cur = conn.cursor()
    cur.execute("SELECT item, description, unit, qty, rate, value FROM stock WHERE username = %s", (username,))
    rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Item', 'Description', 'Unit', 'Qty', 'Rate', 'Value'])
    for row in rows:
        writer.writerow(row)

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=stock_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/export-pdf', methods=['GET'])
def export_pdf():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401

    username = 'testuser'  # replace with real logic

    cur = conn.cursor()
    cur.execute("SELECT item, description, unit, qty, rate, value FROM stock WHERE username = %s", (username,))
    rows = cur.fetchall()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    p.drawString(100, y, 'Stock Report')
    y -= 25
    p.drawString(50, y, 'Item | Description | Unit | Qty | Rate | Value')
    y -= 20

    for row in rows:
        line = ' | '.join(str(col) for col in row)
        p.drawString(50, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            y = 750

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='stock_report.pdf', mimetype='application/pdf')
