from flask import Flask
from flask_cors import CORS
from routes.layers import layers_bp
from routes.rasters import rasters_bp
from config import FRONTEND_URL

app = Flask(__name__)
CORS(app, origins=[FRONTEND_URL])

app.register_blueprint(layers_bp, url_prefix='/api/layers')

@app.route('/api/health')
def health():
    return {"status": "ok", "message": "Backend działa"}

if __name__ == '__main__':
    app.run(debug=True, port=5000) #TODO: debug=false after developing