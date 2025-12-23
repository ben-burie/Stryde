from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Helper scripts
from dataPrep import clean_and_build_dataset
from getPredictions import get_times, seconds_to_time

app = Flask(__name__)
CORS(app)

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('user-interface', 'home.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('user-interface', filename)

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
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)