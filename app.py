from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Helper scripts
from dataPrep import clean_and_build_dataset
from getPredictions import get_times, seconds_to_time
import loginHandler

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_login():
    return send_from_directory('user-interface', 'logon.html')

@app.route('/home.html')
def serve_home():
    return send_from_directory('user-interface', 'home.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('user-interface', filename)

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email and password required'}), 400

        print(f"Login attempt for user: {email}")

        result = loginHandler.login_user(email, password)
        
        if not result:
            return jsonify({'message': 'Invalid credentials'}), 401

        print(f"✓ Login successful for {email}")

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'token': result.session.access_token,
            'user': {
                'id': result.user.id,
                'email': result.user.email
            }
        }), 200

    except Exception as e:
        error_msg = str(e)
        print(f"Login failed: {error_msg}")
        print(f"Error type: {type(e).__name__}")
        return jsonify({'message': error_msg}), 401

@app.route('/api/verify-token', methods=['POST'])
def check_token():
    """Verify if token is valid"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'valid': False, 'message': 'No token provided'}), 401

        print(f"Verifying token...")

        user = loginHandler.verify_token(token)
        
        if not user:
            return jsonify({'valid': False, 'message': 'Invalid token'}), 401

        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'email': user.email
            }
        }), 200

    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return jsonify({'valid': False, 'message': str(e)}), 401
    
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/api/upload-data', methods=['POST'])
def upload_data():
    try:
        if 'file' not in request.files:
            return '{"error":"No file"}', 400
        
        file = request.files['file']
        if file.filename == '':
            return '{"error":"No file selected"}', 400
        
        if not file.filename.endswith('.csv'):
            return '{"error":"Not CSV"}', 400
        
        result = clean_and_build_dataset(file_stream=file)
        vdot = result[0]
        avg_hr = result[1]

        times = get_times(vdot)
        print(times)

        return {
            'vdot': vdot,
            'avg_hr': avg_hr,
            'fivek_time': seconds_to_time(times['5000']),
            'half_time': seconds_to_time(times['1/2 Marathon']),
            'full_time': seconds_to_time(times['Marathon']),
            'success': True
        }, 200
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return '{"error":"error"}', 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)