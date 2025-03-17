import os
from flask import Flask, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Retrieve all dogs and calculate statistics for the admin dashboard."""
    try:
        response = supabase.table("dogs").select("*").execute()
        dogs = response.data
        
        if not dogs:
            stats = {
                "total_dogs": 0,
                "unique_breeds": 0,
                "breed_distribution": {},
                "total_inventory_value": 0,
                "average_price": 0
            }
        else:
            breeds = {}
            total_value = 0
            
            for dog in dogs:
                breed = dog.get('breed')
                if breed in breeds:
                    breeds[breed] += 1
                else:
                    breeds[breed] = 1
                
                total_value += dog.get('price', 0)
            
            stats = {
                "total_dogs": len(dogs),
                "unique_breeds": len(breeds),
                "breed_distribution": breeds,
                "total_inventory_value": total_value,
                "average_price": total_value / len(dogs) if dogs else 0
            }
        
        return jsonify({"dogs": dogs, "statistics": stats}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dogs', methods=['GET'])
def get_dogs():
    """Retrieve a paginated list of dogs with optional filters."""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = 20
        offset = (page - 1) * page_size

        breeds = request.args.getlist("breed")
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)

        query = supabase.table("dogs").select("*")

        if breeds:
            query = query.in_("breed", breeds)
        if min_price is not None:
            query = query.gte("price", min_price)
        if max_price is not None:
            query = query.lte("price", max_price)

        response = query.order("id").range(offset, offset + page_size - 1).execute()
        dogs = response.data

        return jsonify({"page": page, "dogs": dogs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def add_dogs(name, image, breed, price):
    """Add a new dog to the database."""
    try:
        response = supabase.table("dogs").insert({
            "name": name,
            "image": image,
            "breed": breed,
            "price": price
        }).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error adding dog: {str(e)}")
    
@app.route("/admin/login", methods=["POST"])
def admin_login():
    """Handle admin login with hardcoded credentials."""
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username == "admin" and password == "password":
        return jsonify({
            "access_token": "dummy_admin_token",
            "message": "Login successful"
        }), 200

    return jsonify({"error": "Invalid credentials"}), 403

@app.route('/admin', methods=['POST', 'DELETE', 'PUT'])
def admin_dogs():
    """Open admin endpoints without authentication"""
    try:
        if request.method == 'DELETE':
            dog_id = request.json.get('id') if request.is_json else request.args.get('id')
            if not dog_id:
                return jsonify({"error": "Missing dog id"}), 400

            response = supabase.table("dogs").delete().eq("id", dog_id).execute()
            return jsonify({"message": "Dog deleted", "data": response.data}), 200

        elif request.method == 'POST':
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.json
            name = data.get('name')
            image = data.get('image')
            breed = data.get('breed')
            price = data.get('price')

            if not all([name, image, breed, price]):
                return jsonify({"error": "Missing required fields"}), 400

            result = add_dogs(name, image, breed, price)
            return jsonify({"message": "Dog added successfully", "data": result}), 200

        elif request.method == 'PUT':
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            dog_id = request.json.get('id')
            if not dog_id:
                return jsonify({"error": "Missing dog id"}), 400

            update_data = {k: v for k, v in request.json.items() if k in ['name', 'image', 'breed', 'price']}
            if not update_data:
                return jsonify({"error": "No valid fields to update"}), 400

            response = supabase.table("dogs").update(update_data).eq("id", dog_id).execute()
            return jsonify({"message": "Dog updated", "data": response.data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
