"""
Web version of Book Recommendation System using Flask
Run with: python app_web.py
Access at: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
from recommendation_engine import RecommendationEngine
import os
import numpy as np

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Initialize engine (load once at startup)
engine = None

def initialize_engine():
    """Initialize the recommendation engine."""
    global engine
    try:
        print("Initializing recommendation engine...")
        
        # Check if required files exist
        required_files = ["Books.csv", "Ratings.csv"]
        for file in required_files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"Required file not found: {file}")
        
        # Initialize engine with additional validation
        engine = RecommendationEngine("Books.csv", "Ratings.csv")
        
        # Validate engine initialization
        if not hasattr(engine, 'books_df') or engine.books_df.empty:
            raise ValueError("Books data failed to load properly")
        if not hasattr(engine, 'ratings_df') or engine.ratings_df.empty:
            raise ValueError("Ratings data failed to load properly")
        
        print("Engine initialized successfully!")
        return True
    except FileNotFoundError as e:
        print(f"File error: {e}")
        engine = None
        return False
    except ValueError as e:
        print(f"Data validation error: {e}")
        engine = None
        return False
    except Exception as e:
        print(f"Error initializing engine: {str(e)}")
        engine = None
        return False

# Initialize on startup
initialize_engine()

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/popular', methods=['GET'])
def get_popular_books():
    """Get popular books."""
    if engine is None:
        return jsonify({
            'success': False,
            'error': 'Recommendation engine is not initialized. Please try again later.'
        }), 503
    
    try:
        # Get and validate limit parameter
        n = request.args.get('n', 50, type=int)
        if n <= 0:
            return jsonify({
                'success': False,
                'error': 'Number of books (n) must be positive'
            }), 400
        if n > 100:
            return jsonify({
                'success': False,
                'error': 'Maximum number of books (n) is 100'
            }), 400
        
        books = engine.get_popular_books(n)
        
        if books is None or books.empty:
            return jsonify({
                'success': False,
                'error': 'No popular books found'
            }), 404
        
        # Convert to dictionary and handle NaN values
        books_dict = books.replace({np.nan: None}).to_dict('records')
        
        return jsonify({
            'success': True,
            'books': books_dict,
            'count': len(books_dict)
        })
    except Exception as e:
        print(f"Error in get_popular_books: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error occurred while fetching popular books'
        }), 500

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """Get recommendations for a book."""
    if engine is None:
        return jsonify({
            'success': False,
            'error': 'Recommendation engine is not initialized. Please try again later.'
        }), 503
    
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        book_title = data.get('book_title')
        if not book_title or not isinstance(book_title, str):
            return jsonify({
                'success': False,
                'error': 'Valid book_title is required'
            }), 400
        
        book_title = book_title.strip()
        if not book_title:
            return jsonify({
                'success': False,
                'error': 'book_title cannot be empty'
            }), 400
        
        # Validate number of recommendations
        n = data.get('n', 10)
        try:
            n = int(n)
            if n <= 0:
                raise ValueError("n must be positive")
            if n > 50:
                raise ValueError("n cannot exceed 50")
        except (TypeError, ValueError) as e:
            return jsonify({
                'success': False,
                'error': f'Invalid value for n: {str(e)}'
            }), 400
        
        # Get book info first to validate book exists
        book_info = engine.get_book_info(book_title)
        if book_info is None:
            return jsonify({
                'success': False,
                'error': f'Book not found: {book_title}'
            }), 404
        
        # Get recommendations
        recommendations = engine.get_recommendations(book_title, n)
        if not recommendations:
            return jsonify({
                'success': False,
                'error': 'No recommendations found. The book may not have enough ratings.'
            }), 404
        
        return jsonify({
            'success': True,
            'book_info': book_info,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error occurred while getting recommendations'
        }), 500

@app.route('/api/search', methods=['GET'])
def search_books():
    """Search for books."""
    if engine is None:
        return jsonify({
            'success': False,
            'error': 'Recommendation engine is not initialized. Please try again later.'
        }), 503
    
    try:
        # Get and validate query parameter
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Get and validate limit parameter
        try:
            limit = request.args.get('limit', 20, type=int)
            if limit <= 0:
                raise ValueError("limit must be positive")
            if limit > 100:
                raise ValueError("limit cannot exceed 100")
        except (TypeError, ValueError) as e:
            return jsonify({
                'success': False,
                'error': f'Invalid limit parameter: {str(e)}'
            }), 400
        
        # Search for books
        books = engine.search_books(query, limit)
        
        # Return appropriate response based on results
        if not books:
            return jsonify({
                'success': True,
                'books': [],
                'count': 0,
                'message': f'No books found matching: {query}'
            })
        
        return jsonify({
            'success': True,
            'books': books,
            'count': len(books)
        })
    except Exception as e:
        print(f"Error in search_books: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error occurred while searching books'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy' if engine is not None else 'unhealthy',
        'engine_initialized': engine is not None
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)

