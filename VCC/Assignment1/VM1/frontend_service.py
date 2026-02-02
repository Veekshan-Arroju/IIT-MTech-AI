from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # Request data from the Backend VM via the Internal Network
        response = requests.get('http://192.168.1.2:5001/api/status')
        backend_data = response.json()
        return f"<h1>Microservice Cluster Active</h1><p>Fetched from Backend: {backend_data}</p>"
    except Exception as e:
        return f"<h1>Error</h1><p>Could not reach Backend: {str(e)}</p>"

if __name__ == '__main__':
    # Listen on all interfaces to allow access
    app.run(host='0.0.0.0', port=5000)
