from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import traceback
import json
# Helper scripts
from dataPrep import clean_and_build_dataset

app = Flask(__name__)
CORS(app)

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import traceback
import json

from flask import Flask, request
from flask_cors import CORS
import traceback
import json

app = Flask(__name__)
CORS(app)

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

        print("STEP 1: About to call clean_and_build_dataset")
        
        # Try calling it
        result = clean_and_build_dataset(file_stream=file)
        
        print("STEP 2: Returned from clean_and_build_dataset")
        print(f"STEP 3: Result = {result}")
        
        # Return immediately without processing
        print("STEP 4: About to return")
        return '{"test":"works"}', 200
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return '{"error":"error"}', 500


if __name__ == '__main__':
    app.run(debug=True)