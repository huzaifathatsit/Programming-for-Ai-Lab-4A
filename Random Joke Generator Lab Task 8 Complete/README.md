# Enhanced Random Joke API Backend

This is a Flask-based backend for a Random Joke Application. It is designed to be highly usable, acting as a robust API wrapper over [JokeAPI v2](https://sv443.net/jokeapi/v2/). 

Instead of multiple fixed endpoints, it offers a single, powerful endpoint that uses query parameters to fetch exactly the jokes you want.

## Endpoints

### 1. `GET /`
API Welcome page, feature list, and examples.

### 2. `GET /api/joke/categories`
Returns a list of all supported joke categories (e.g., Programming, Pun, Misc).

### 3. `GET /api/joke`
The core endpoint. It is highly customizable using the following query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | String | `Any` | Category of the joke (`Programming`, `Misc`, `Dark`, `Pun`, `Spooky`, `Christmas`, or `Any`). |
| `type` | String | (Both) | Type of joke: `single` (one-liner) or `twopart` (setup and delivery). |
| `contains` | String | None | Search for a specific word or phrase in the joke. |
| `amount` | Integer | `1` | Number of jokes to retrieve (between 1 and 10). |
| `safe` | Boolean | `true` | If `true`, filters out NSFW, religious, political, racist, sexist, and explicit jokes. |

#### Examples:
- **Get a random safe joke:** `/api/joke`
- **Get 3 programming jokes:** `/api/joke?category=Programming&amount=3`
- **Search for a joke with the word 'dog':** `/api/joke?contains=dog`
- **Get a two-part pun:** `/api/joke?category=Pun&type=twopart`
- **Get a potentially NSFW joke (if you dare):** `/api/joke?safe=false&category=Dark`

## Setup Instructions

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. The server will start running at `http://127.0.0.1:5000/`.

## Note
CORS is enabled by default, so you can easily connect any frontend application to this backend without cross-origin issues. All responses are neatly standardized with a `success` boolean flag.
