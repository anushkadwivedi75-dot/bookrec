# Book Recommendation System

A comprehensive book recommendation system built with Python, featuring both popularity-based and collaborative filtering recommendations. The system includes a modern Tkinter GUI with two tabs for exploring popular books and getting personalized recommendations.

## Features

- **Popularity-Based Recommendations**: Uses a weighted rating formula (similar to IMDB) to recommend the most popular books
- **Collaborative Filtering**: Recommends books based on user similarity using cosine similarity
- **Modern GUI**: Clean, professional Tkinter interface with two tabs:
  - **Popular Books Tab**: Displays top 50 popular books with covers, ratings, and weighted scores
  - **Search & Recommendations Tab**: Search for books with autocomplete and get 10 personalized recommendations with similarity scores
- **Image Caching**: Efficient caching system for book cover images
- **Async Loading**: Threading for non-blocking data loading and image fetching
- **Error Handling**: Graceful error handling throughout the application

## Dataset

The system uses the Kaggle Books Dataset:
- **271,360 books** with metadata (title, author, publisher, cover images)
- **278,858 users** with location information
- **1,149,780 ratings** (1-10 scale)

After filtering (removing zero ratings, inactive users, and unpopular books):
- **~679 books** in the collaborative filtering model
- **~810 active users** with sufficient ratings

## Installation

1. Clone or download this repository

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Download the Kaggle Books Dataset and place the following CSV files in the project directory:
   - `Books.csv`
   - `Ratings.csv`
   - `Users.csv` (optional)

## Usage

### Running the GUI Application

```bash
python app.py
```

The application will:
1. Load the dataset (this may take a minute)
2. Build the recommendation models
3. Display the GUI with two tabs

### Using the Popular Books Tab

1. Click on the "📊 Popular Books" tab
2. View the top 50 popular books sorted by weighted rating
3. Each book card shows:
   - Book cover image
   - Title and author
   - Average rating and number of ratings
   - Weighted score

### Using the Search & Recommendations Tab

1. Click on the "🔍 Search & Recommendations" tab
2. Type a book title in the search box (autocomplete will appear)
3. Select a book from autocomplete or click "Search"
4. View 10 recommended books with:
   - Book title and author
   - Similarity score (percentage)
   - Visual progress bar for similarity

### Testing with Example Books

Try searching for:
- "To Kill a Mockingbird"
- "1984"
- "The Catcher in the Rye"
- "The Great Gatsby"

## Technical Details

### Weighted Rating Formula

The popularity recommender uses a weighted rating formula:
```
Weighted Rating = (v/(v+m)) * R + (m/(v+m)) * C
```

Where:
- `v` = number of votes (ratings) for the book
- `m` = minimum votes required (90th percentile)
- `R` = average rating for the book
- `C` = mean rating across all books

This ensures that books with many ratings are ranked higher than books with few but high ratings.

### Collaborative Filtering

The collaborative filtering recommender:
1. Filters users with at least 200 ratings
2. Filters books with at least 50 ratings
3. Creates a pivot table (books × users)
4. Calculates cosine similarity between books
5. Returns the most similar books for a given book

### Data Processing

The system performs the following data cleaning:
- Removes zero ratings (implicit/explicit non-ratings)
- Drops the Age column from users (many missing values)
- Filters inactive users and unpopular books
- Handles missing values and duplicates

## Project Structure

```
bookrec-1/
├── code3.ipynb                 # Jupyter notebook with data analysis and bug fixes
├── recommendation_engine.py    # Backend recommendation engine
├── app.py                      # Tkinter GUI application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── Books.csv                   # Book metadata (required)
├── Ratings.csv                 # User ratings (required)
└── Users.csv                   # User information (optional)
```

## Classes

### PopularityRecommender
- `get_top_n(n=50)`: Get top N popular books
- `get_book_info(book_title)`: Get information about a specific book

### CollaborativeRecommender
- `recommend(book_title, n=10)`: Get recommendations for a book
- `search_books(query, limit=20)`: Search for books by title
- `get_available_books()`: Get list of all available books
- `get_book_info(book_title)`: Get information about a specific book

### RecommendationEngine
Main engine that combines both recommenders:
- `get_popular_books(n=50)`: Get popular books
- `get_recommendations(book_title, n=10)`: Get recommendations
- `search_books(query, limit=20)`: Search for books
- `get_book_info(book_title)`: Get book information

## Bug Fixes

The following bugs were fixed in `code3.ipynb`:

1. **ChainedAssignment warnings**: Replaced `book.iloc[index]['column']` with `book.loc[index, 'column']`
2. **Missing Age column drop**: Added code to drop the Age column from users
3. **Missing non-zero rating filter**: Added filter to remove zero ratings
4. **Weighted rating formula**: Implemented weighted rating instead of simple average
5. **Improved recommend() function**: Added error handling and better return values

## Performance

- Data loading: ~30-60 seconds (depending on system)
- Popular books display: Instant (cached)
- Recommendations: < 1 second
- Image loading: Asynchronous with caching (200 image cache)

## Limitations

- Requires sufficient memory for large datasets
- Image loading depends on external URLs (some may be broken)
- Collaborative filtering requires books to be in the filtered dataset
- GUI may be slow on older systems

## Future Improvements

- Add user-based collaborative filtering
- Implement matrix factorization (SVD, NMF)
- Add book genre filtering
- Export recommendations to CSV/PDF
- Add user authentication and personalization
- Implement real-time recommendations

## License

This project is provided as-is for educational purposes.

## Acknowledgments

- Kaggle Books Dataset: https://www.kaggle.com/datasets/arashnic/book-recommendation-dataset
- scikit-learn for cosine similarity implementation
- PIL/Pillow for image processing

## Contact

For questions or issues, please open an issue on the repository.

