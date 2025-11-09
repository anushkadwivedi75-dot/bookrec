"""
Book Recommendation Engine
Provides PopularityRecommender and CollaborativeRecommender classes
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os


class PopularityRecommender:
    """
    Recommends books based on popularity using weighted rating formula.
    """
    
    def __init__(self, books_df, ratings_df, min_ratings=250):
        """
        Initialize the popularity recommender.
        
        Args:
            books_df: DataFrame with book information (ISBN, Book-Title, Book-Author, Image-URL-M, etc.)
            ratings_df: DataFrame with ratings (User-ID, ISBN, Book-Rating)
            min_ratings: Minimum number of ratings required for a book to be considered
        """
        self.books_df = books_df
        self.ratings_df = ratings_df
        self.min_ratings = min_ratings
        self.popular_books = None
        self._build_model()
    
    def _build_model(self):
        """Build the popularity model using weighted rating formula."""
        # Merge books and ratings
        book_rat = self.ratings_df.merge(self.books_df, on='ISBN')
        
        # Calculate number of ratings per book
        num_rating_df = book_rat.groupby('Book-Title').count()['Book-Rating'].reset_index()
        num_rating_df.rename(columns={'Book-Rating': 'num_rating'}, inplace=True)
        
        # Calculate average rating per book
        avg_rating_df = book_rat.groupby('Book-Title')['Book-Rating'].mean().reset_index()
        avg_rating_df.rename(columns={'Book-Rating': 'avg_rating'}, inplace=True)
        
        # Merge to get both metrics
        rating_df = num_rating_df.merge(avg_rating_df, on='Book-Title')
        
        # Check if we have any data
        if rating_df.empty:
            self.popular_books = pd.DataFrame(columns=['Book-Title', 'Book-Author', 'Image-URL-M', 'num_rating', 'avg_rating', 'weighted_rating'])
            return
        
        # Calculate weighted rating: (v/(v+m)) * R + (m/(v+m)) * C
        # v = number of votes, m = minimum votes required, R = average rating, C = mean rating
        m = rating_df['num_rating'].quantile(0.90)  # 90th percentile
        C = rating_df['avg_rating'].mean()  # Mean rating across all books
        
        # Handle edge cases where m or C might be NaN
        if pd.isna(m) or pd.isna(C):
            # If we can't calculate weighted rating, just use average rating
            rating_df['weighted_rating'] = rating_df['avg_rating']
        else:
            rating_df['weighted_rating'] = (
                (rating_df['num_rating'] / (rating_df['num_rating'] + m)) * rating_df['avg_rating'] +
                (m / (rating_df['num_rating'] + m)) * C
            )
        
        # Filter by minimum ratings and sort by weighted rating
        rating_df = rating_df[rating_df['num_rating'] >= self.min_ratings]
        rating_df = rating_df.sort_values('weighted_rating', ascending=False)
        
        # Merge with book information
        self.popular_books = rating_df.merge(
            self.books_df, 
            on='Book-Title'
        ).drop_duplicates('Book-Title')[
            ['Book-Title', 'Book-Author', 'Image-URL-M', 'num_rating', 'avg_rating', 'weighted_rating']
        ]
    
    def get_top_n(self, n=50):
        """
        Get top N popular books.
        
        Args:
            n: Number of books to return
            
        Returns:
            DataFrame with top N popular books
        """
        if self.popular_books is None:
            self._build_model()
        return self.popular_books.head(n).copy()
    
    def get_book_info(self, book_title):
        """
        Get information about a specific book.
        
        Args:
            book_title: Title of the book
            
        Returns:
            Dictionary with book information or None if not found
        """
        if self.popular_books is None:
            self._build_model()
        
        # First try to find in popular books
        book_info = self.popular_books[self.popular_books['Book-Title'] == book_title]
        if not book_info.empty:
            return book_info.iloc[0].to_dict()
        
        # If not found in popular books, search in full books dataframe
        book_info = self.books_df[self.books_df['Book-Title'] == book_title]
        if book_info.empty:
            return None
        
        return book_info.iloc[0].to_dict()


class CollaborativeRecommender:
    """
    Recommends books based on collaborative filtering using cosine similarity.
    """
    
    def __init__(self, books_df, ratings_df, min_user_ratings=200, min_book_ratings=50):
        """
        Initialize the collaborative filtering recommender.
        
        Args:
            books_df: DataFrame with book information
            ratings_df: DataFrame with ratings (User-ID, ISBN, Book-Rating)
            min_user_ratings: Minimum number of ratings a user must have
            min_book_ratings: Minimum number of ratings a book must have
        """
        self.books_df = books_df
        self.ratings_df = ratings_df
        self.min_user_ratings = min_user_ratings
        self.min_book_ratings = min_book_ratings
        self.pivot_table = None
        self.similarity_matrix = None
        self._build_model()
    
    def _build_model(self):
        """Build the collaborative filtering model."""
        # Merge books and ratings
        book_rat = self.ratings_df.merge(self.books_df, on='ISBN')
        
        if book_rat.empty:
            # Create empty pivot table if no data
            self.pivot_table = pd.DataFrame()
            self.similarity_matrix = np.array([])
            return
        
        # Filter users with at least min_user_ratings ratings
        user_rating_counts = book_rat.groupby('User-ID').count()['Book-Rating']
        active_users = user_rating_counts[user_rating_counts > self.min_user_ratings].index
        
        if len(active_users) == 0:
            # No active users, create empty pivot table
            self.pivot_table = pd.DataFrame()
            self.similarity_matrix = np.array([])
            return
        
        filtered_ratings = book_rat[book_rat['User-ID'].isin(active_users)]
        
        # Filter books with at least min_book_ratings ratings
        book_rating_counts = filtered_ratings.groupby('Book-Title').count()['Book-Rating']
        popular_books = book_rating_counts[book_rating_counts > self.min_book_ratings].index
        
        if len(popular_books) == 0:
            # No popular books, create empty pivot table
            self.pivot_table = pd.DataFrame()
            self.similarity_matrix = np.array([])
            return
        
        final_ratings = filtered_ratings[filtered_ratings['Book-Title'].isin(popular_books)]
        
        # Create pivot table: books as rows, users as columns
        self.pivot_table = final_ratings.pivot_table(
            index='Book-Title',
            columns='User-ID',
            values='Book-Rating',
            fill_value=0
        )
        
        # Calculate cosine similarity between books
        if self.pivot_table.empty or len(self.pivot_table) < 2:
            # Need at least 2 books for similarity
            self.similarity_matrix = np.array([])
        else:
            self.similarity_matrix = cosine_similarity(self.pivot_table)
    
    def recommend(self, book_title, n=10):
        """
        Get book recommendations based on a given book.
        
        Args:
            book_title: Title of the book to get recommendations for
            n: Number of recommendations to return
            
        Returns:
            List of dictionaries with recommended books and similarity scores
        """
        if self.pivot_table is None or self.similarity_matrix is None:
            self._build_model()
        
        try:
            # Check if pivot table is empty
            if self.pivot_table.empty or len(self.similarity_matrix) == 0:
                return []
            
            # Check if book exists
            if book_title not in self.pivot_table.index:
                return []
            
            # Get index of the book
            book_index = np.where(self.pivot_table.index == book_title)[0][0]
            
            # Check if similarity matrix is valid
            if book_index >= len(self.similarity_matrix):
                return []
            
            # Get similarity scores for this book
            similarity_scores = list(enumerate(self.similarity_matrix[book_index]))
            
            # Sort by similarity (excluding the book itself)
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)[1:n+1]
            
            # Build recommendations list
            recommendations = []
            for idx, similarity in similarity_scores:
                if idx < len(self.pivot_table.index):
                    book_name = self.pivot_table.index[idx]
                    recommendations.append({
                        'book': book_name,
                        'similarity': float(similarity)
                    })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in recommend function: {str(e)}")
            return []
    
    def get_available_books(self):
        """
        Get list of all available books in the model.
        
        Returns:
            List of book titles
        """
        if self.pivot_table is None:
            self._build_model()
        
        # Check if pivot table is empty
        if self.pivot_table.empty:
            return []
        
        return list(self.pivot_table.index)
    
    def search_books(self, query, limit=20):
        """
        Search for books by title (case-insensitive partial match).
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching book titles
        """
        if self.pivot_table is None:
            self._build_model()
        
        # Check if pivot table is empty
        if self.pivot_table.empty:
            return []
        
        query_lower = query.lower()
        matching_books = [
            book for book in self.pivot_table.index 
            if query_lower in book.lower()
        ]
        return matching_books[:limit]
    
    def get_book_info(self, book_title):
        """
        Get information about a specific book from the books dataframe.
        
        Args:
            book_title: Title of the book
            
        Returns:
            Dictionary with book information or None if not found
        """
        book_info = self.books_df[self.books_df['Book-Title'] == book_title]
        if book_info.empty:
            return None
        
        # Get first match and convert to dict
        book_dict = book_info.iloc[0].to_dict()
        return book_dict


class RecommendationEngine:
    """
    Main recommendation engine that combines both recommenders.
    """
    
    def __init__(self, books_csv, ratings_csv, users_csv=None):
        """
        Initialize the recommendation engine.
        
        Args:
            books_csv: Path to Books.csv
            ratings_csv: Path to Ratings.csv
            users_csv: Path to Users.csv (optional)
        """
        # Load data
        print("Loading books data...")
        self.books_df = pd.read_csv(books_csv)
        
        print("Loading ratings data...")
        self.ratings_df = pd.read_csv(ratings_csv)
        
        # Filter out zero ratings
        self.ratings_df = self.ratings_df[self.ratings_df['Book-Rating'] > 0]
        print(f"Ratings after filtering zeros: {len(self.ratings_df)}")
        
        # Initialize recommenders
        print("Building popularity recommender...")
        self.popularity_recommender = PopularityRecommender(self.books_df, self.ratings_df)
        
        print("Building collaborative filtering recommender...")
        self.collaborative_recommender = CollaborativeRecommender(self.books_df, self.ratings_df)
        
        print("Recommendation engine initialized successfully!")
    
    def get_popular_books(self, n=50):
        """Get top N popular books."""
        return self.popularity_recommender.get_top_n(n)
    
    def get_recommendations(self, book_title, n=10):
        """Get recommendations for a book."""
        return self.collaborative_recommender.recommend(book_title, n)
    
    def search_books(self, query, limit=20):
        """Search for books."""
        return self.collaborative_recommender.search_books(query, limit)
    
    def get_book_info(self, book_title):
        """Get book information."""
        return self.collaborative_recommender.get_book_info(book_title)

