from flask import Flask, request, jsonify

app = Flask(__name__)

# Temporary memory database (Testing ke liye)
db = {}

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "ZKP Gateway is Online!"}), 200

# ESP32 Phase 2 ki Public Key yahan bhejega
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or 'device_id' not in data or 'public_key' not in data:
        return jsonify({"error": "Missing data"}), 400
        
    device_id = data['device_id']
    public_key = data['public_key'] # ZKP Phase 2 Phi
    
    # Data save kar liya
    db[device_id] = {"phi": public_key}
    
    # Terminal/Logs mein print taake tumhe nazar aaye
    print(f"SUCCESS: Device {device_id} registered!")
    print(f"Public Key (Phi): {public_key}")
    
    return jsonify({"status": "success", "message": "Registered on Gateway!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)