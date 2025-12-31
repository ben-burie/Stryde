from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Helper scripts
from dataPrep import clean_and_build_dataset, check_for_data, write_current_fitness_metrics_to_db, write_training_plan_to_db, check_for_training_plan, load_training_plan
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

        print(f"Login successful for {email}")

        dataResult = check_for_data(result.user.id)

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

        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user = loginHandler.verify_token(token)
        userId = user.id
        print(f"User ID from token: {userId}")
        
        result = clean_and_build_dataset(file_stream=file, user=userId)
        vdot = result[0]
        avg_hr = result[1]

        times = get_times(vdot)

        write_current_fitness_metrics_to_db(vdot, avg_hr, times['5000'], times['1/2 Marathon'], times['Marathon'], userId)

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
    
@app.route('/api/get-user-data', methods=['GET'])
def get_user_data():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        print(token)

        if not token:
            return jsonify({'message': 'No token provided'}), 401

        user = loginHandler.verify_token(token)

        if not user:
            return jsonify({'message': 'Invalid token'}), 401

        dataResult = check_for_data(user.id)

        if dataResult is False:
            return jsonify({'message': 'No data found for user'}), 404

        vdot = dataResult['vdot']
        avg_hr = dataResult['avg_hr']
        fivek_time = seconds_to_time(dataResult['fivek_prediction'])
        half_time = seconds_to_time(dataResult['half_prediction'])
        full_time = seconds_to_time(dataResult['full_prediction'])

        if not dataResult:
            return jsonify({'message': 'No data found for user'}), 404

        return jsonify({
            'status': 'success',
            'vdot': vdot,
            'avg_hr': avg_hr,
            'fivek_time': fivek_time,
            'half_time': half_time,
            'full_time': full_time
        }), 200

    except Exception as e:
        print(f"Error retrieving user data: {str(e)}")
        return jsonify({'message': str(e)}), 500
    
@app.route('/api/training-plan', methods=['POST'])
def training_plan():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        print(f"DEBUG: Token received: {token[:20] if token else 'NO TOKEN'}...")
        
        if not token:
            print("DEBUG: No token provided")
            return jsonify({'message': 'No token provided'}), 401
        
        try:
            user = loginHandler.verify_token(token)
            print(f"DEBUG: User verified - ID: {user.id}")
        except Exception as token_error:
            print(f"DEBUG: Token verification failed: {str(token_error)}")
            return jsonify({'message': f'Token invalid: {str(token_error)}'}), 401
        
        userID = user.id

        plan_found = check_for_training_plan(userID)

        if plan_found:
            response = load_training_plan(userID)
        else:
            from coachChatbot import ask_gemini
            enhanced_prompt = f"""
                {"Create me a 30 day training plan."}

                IMPORTANT FORMATTING INSTRUCTIONS:
                - Use Markdown formatting (## for headers, ** for bold, * for bullet points)
                - Do NOT include coaching notes or disclaimers at the end
                - Keep the response focused on: fitness analysis, paces, and the weekly training schedule
                - Omit sections like "Important Coaching Notes" or any final advice/disclaimers
            """
            response = ask_gemini(enhanced_prompt, userID)
            write_training_plan_to_db(response, userID)
        
        return jsonify({
            'status': 'success',
            'response': response
        }), 200
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)