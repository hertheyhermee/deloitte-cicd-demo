from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "deloitte-demo"}), 200

@app.route("/")
def index():
    return jsonify({"message": "CI/CD pipeline is live"}), 200

@app.route("/version")
def version():
    return jsonify({"version": "1.0.0"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)