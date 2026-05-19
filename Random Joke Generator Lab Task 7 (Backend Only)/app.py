from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
# Enable CORS for all routes so frontends can easily call this API
CORS(app)  

# Switching to JokeAPI which is extremely feature-rich, reliable, and usable
JOKE_API_BASE_URL = "https://v2.jokeapi.dev/joke"

@app.route('/api/joke', methods=['GET'])
def get_custom_joke():
    """
    Fetches a customized joke based on query parameters.
    Query Parameters:
    - category: Any (default), Programming, Misc, Dark, Pun, Spooky, Christmas
    - type: single, twopart (default is both)
    - contains: A search string to find in the joke
    - amount: Number of jokes to fetch (1-10)
    - safe: true/false (if true, adds strict blacklist flags to avoid NSFW content)
    """
    category = request.args.get('category', 'Any')
    joke_type = request.args.get('type')
    contains = request.args.get('contains')
    amount = request.args.get('amount', 1)
    safe = request.args.get('safe', 'true').lower() == 'true'

    params = {}
    
    if joke_type in ['single', 'twopart']:
        params['type'] = joke_type
        
    if contains:
        params['contains'] = contains
        
    if safe:
        # Prevent offensive jokes by default for safety
        params['blacklistFlags'] = 'nsfw,religious,political,racist,sexist,explicit'
        
    # amount > 1 will return an array of jokes
    try:
        amount = int(amount)
        if 1 <= amount <= 10:
            params['amount'] = amount
    except ValueError:
        pass

    try:
        url = f"{JOKE_API_BASE_URL}/{category}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        joke_data = response.json()
        
        # Check if JokeAPI returned an error (e.g., search string not found)
        if joke_data.get('error'):
            return jsonify({
                'success': False,
                'error': joke_data.get('message', 'JokeAPI returned an error'),
                'details': joke_data.get('additionalInfo', '')
            }), 404 if 'not found' in joke_data.get('message', '').lower() else 400

        # Standardize response structure
        return jsonify({
            'success': True,
            'data': joke_data
        }), 200

    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'error': 'Failed to communicate with the external Joke API',
            'details': str(e)
        }), 502

@app.route('/api/joke/categories', methods=['GET'])
def get_categories():
    """Returns available joke categories."""
    return jsonify({
        'success': True,
        'categories': ['Any', 'Misc', 'Programming', 'Dark', 'Pun', 'Spooky', 'Christmas']
    }), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Welcome to the Enhanced Random Joke API Backend!',
        'features': 'Supports safe mode, categories, search strings, and joke types.',
        'endpoints': {
            'GET /api/joke': 'Get customizable jokes. Query params: category, type, contains, amount, safe',
            'GET /api/joke/categories': 'Get list of supported categories'
        },
        'examples': [
            '/api/joke',
            '/api/joke?category=Programming',
            '/api/joke?safe=true&amount=2',
            '/api/joke?type=twopart&contains=dog'
        ]
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
