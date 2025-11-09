"""
Book Recommendation System GUI
Modern Tkinter interface with two tabs: Popular Books and Search & Recommendations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO
import time
import pandas as pd
from recommendation_engine import RecommendationEngine
import os


class ImageCache:
    """Cache for book cover images."""
    
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get(self, url):
        """Get image from cache."""
        if url in self.cache:
            self.access_times[url] = time.time()
            return self.cache[url]
        return None
    
    def set(self, url, image):
        """Store image in cache."""
        if len(self.cache) >= self.max_size and self.access_times:
            # Remove least recently used
            try:
                lru_url = min(self.access_times, key=self.access_times.get)
                del self.cache[lru_url]
                del self.access_times[lru_url]
            except (ValueError, KeyError):
                # If access_times is out of sync, remove a random item
                if self.cache:
                    random_url = next(iter(self.cache))
                    del self.cache[random_url]
                    if random_url in self.access_times:
                        del self.access_times[random_url]
        
        self.cache[url] = image
        self.access_times[url] = time.time()


class BookRecommendationApp:
    """Main application class."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Book Recommendation System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize recommendation engine
        self.engine = None
        self.loading = False
        
        # Image cache
        self.image_cache = ImageCache(max_size=200)
        
        # Default image (placeholder)
        self.default_image = self._create_placeholder_image()
        
        # Color scheme
        self.colors = {
            'bg': '#f0f0f0',
            'card_bg': '#ffffff',
            'primary': '#4a90e2',
            'secondary': '#7b68ee',
            'text': '#333333',
            'text_light': '#666666',
            'accent': '#50c878',
            'error': '#e74c3c'
        }
        
        # Setup UI
        self._setup_ui()
        
        # Load data in background
        self._load_data_async()
    
    def _create_placeholder_image(self):
        """Create a placeholder image for books without covers."""
        img = Image.new('RGB', (128, 192), color='#e0e0e0')
        return ImageTk.PhotoImage(img)
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Title
        title_font = tkfont.Font(family="Arial", size=24, weight="bold")
        title_label = tk.Label(
            self.root,
            text="📚 Book Recommendation System",
            font=title_font,
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=20)
        
        # Status bar
        self.status_var = tk.StringVar(value="Loading data...")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=self.colors['bg'],
            fg=self.colors['text_light'],
            font=tkfont.Font(family="Arial", size=10)
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # Notebook (tabs)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TNotebook.Tab', padding=[20, 10], font=tkfont.Font(family="Arial", size=11))
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tab 1: Popular Books
        self.popular_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.popular_frame, text="📊 Popular Books")
        self._setup_popular_tab()
        
        # Tab 2: Search & Recommendations
        self.search_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.search_frame, text="🔍 Search & Recommendations")
        self._setup_search_tab()
    
    def _setup_popular_tab(self):
        """Setup the popular books tab."""
        # Header
        header_frame = tk.Frame(self.popular_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        header_label = tk.Label(
            header_frame,
            text="Top 50 Popular Books",
            font=tkfont.Font(family="Arial", size=16, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        header_label.pack(side=tk.LEFT)
        
        # Refresh button
        refresh_btn = tk.Button(
            header_frame,
            text="🔄 Refresh",
            command=self._load_popular_books,
            bg=self.colors['primary'],
            fg='white',
            font=tkfont.Font(family="Arial", size=10),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        # Canvas with scrollbar
        canvas_frame = tk.Frame(self.popular_frame, bg=self.colors['bg'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.popular_canvas = tk.Canvas(
            canvas_frame,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.popular_canvas.yview)
        self.popular_scrollable_frame = tk.Frame(self.popular_canvas, bg=self.colors['bg'])
        
        def update_scroll_region(event=None):
            self.popular_canvas.configure(scrollregion=self.popular_canvas.bbox("all"))
        
        self.popular_scrollable_frame.bind("<Configure>", update_scroll_region)
        
        self.popular_canvas.create_window((0, 0), window=self.popular_scrollable_frame, anchor="nw")
        self.popular_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.popular_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Loading indicator
        self.popular_loading_label = tk.Label(
            self.popular_scrollable_frame,
            text="Loading popular books...",
            font=tkfont.Font(family="Arial", size=12),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        self.popular_loading_label.pack(pady=50)
    
    def _setup_search_tab(self):
        """Setup the search and recommendations tab."""
        # Search section
        search_frame = tk.Frame(self.search_frame, bg=self.colors['bg'])
        search_frame.pack(fill=tk.X, padx=20, pady=20)
        
        search_label = tk.Label(
            search_frame,
            text="Search for a book:",
            font=tkfont.Font(family="Arial", size=12, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        search_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Search entry with autocomplete
        self.search_entry_frame = tk.Frame(search_frame, bg=self.colors['bg'])
        self.search_entry_frame.pack(fill=tk.X)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        
        self.search_entry = tk.Entry(
            self.search_entry_frame,
            textvariable=self.search_var,
            font=tkfont.Font(family="Arial", size=11),
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        
        search_btn = tk.Button(
            self.search_entry_frame,
            text="🔍 Search",
            command=self._search_books,
            bg=self.colors['primary'],
            fg='white',
            font=tkfont.Font(family="Arial", size=10),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        search_btn.pack(side=tk.LEFT)
        
        # Autocomplete listbox container (to control visibility)
        self.autocomplete_container = tk.Frame(search_frame, bg=self.colors['bg'])
        # Don't pack initially
        
        self.autocomplete_listbox = tk.Listbox(
            self.autocomplete_container,
            height=5,
            font=tkfont.Font(family="Arial", size=10),
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.autocomplete_listbox.pack(fill=tk.X)
        self.autocomplete_listbox.bind('<<ListboxSelect>>', self._on_autocomplete_select)
        
        # Results section
        results_frame = tk.Frame(self.search_frame, bg=self.colors['bg'])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Canvas for recommendations
        canvas_frame = tk.Frame(results_frame, bg=self.colors['bg'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.search_canvas = tk.Canvas(
            canvas_frame,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.search_canvas.yview)
        self.search_scrollable_frame = tk.Frame(self.search_canvas, bg=self.colors['bg'])
        
        def update_scroll_region(event=None):
            self.search_canvas.configure(scrollregion=self.search_canvas.bbox("all"))
        
        self.search_scrollable_frame.bind("<Configure>", update_scroll_region)
        
        self.search_canvas.create_window((0, 0), window=self.search_scrollable_frame, anchor="nw")
        self.search_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.search_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial message
        self.search_message_label = tk.Label(
            self.search_scrollable_frame,
            text="Enter a book title to get recommendations",
            font=tkfont.Font(family="Arial", size=12),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        self.search_message_label.pack(pady=50)
    
    def _load_data_async(self):
        """Load data in a separate thread."""
        def load_data():
            try:
                self.status_var.set("Loading data...")
                self.engine = RecommendationEngine("Books.csv", "Ratings.csv")
                self.status_var.set("Data loaded successfully!")
                self.root.after(0, self._load_popular_books)
            except Exception as e:
                self.status_var.set(f"Error loading data: {str(e)}")
                messagebox.showerror("Error", f"Failed to load data: {str(e)}")
        
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()
    
    def _load_popular_books(self):
        """Load and display popular books."""
        if self.engine is None:
            return
        
        # Clear previous content
        for widget in self.popular_scrollable_frame.winfo_children():
            widget.destroy()
        
        self.popular_loading_label = tk.Label(
            self.popular_scrollable_frame,
            text="Loading popular books...",
            font=tkfont.Font(family="Arial", size=12),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        self.popular_loading_label.pack(pady=50)
        
        def load_books():
            try:
                popular_books = self.engine.get_popular_books(50)
                self.root.after(0, lambda: self._display_popular_books(popular_books))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load books: {str(e)}"))
        
        thread = threading.Thread(target=load_books, daemon=True)
        thread.start()
    
    def _display_popular_books(self, books_df):
        """Display popular books in a grid."""
        # Clear loading indicator
        for widget in self.popular_scrollable_frame.winfo_children():
            widget.destroy()
        
        if books_df.empty:
            no_books_label = tk.Label(
                self.popular_scrollable_frame,
                text="No popular books found",
                font=tkfont.Font(family="Arial", size=12),
                bg=self.colors['bg'],
                fg=self.colors['text_light']
            )
            no_books_label.pack(pady=50)
            return
        
        # Create grid
        row = 0
        col = 0
        max_cols = 4
        
        for idx, book_row in books_df.iterrows():
            self._create_book_card(
                self.popular_scrollable_frame,
                book_row,
                row,
                col,
                max_cols
            )
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.popular_canvas.update_idletasks()
        # Update scroll region after content is displayed
        self.popular_canvas.configure(scrollregion=self.popular_canvas.bbox("all"))
    
    def _create_book_card(self, parent, book_data, row, col, max_cols):
        """Create a book card widget."""
        card_frame = tk.Frame(
            parent,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            borderwidth=1
        )
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        # Configure grid weights
        parent.grid_columnconfigure(col, weight=1)
        
        # Image
        image_label = tk.Label(card_frame, image=self.default_image, bg=self.colors['card_bg'])
        image_label.pack(pady=10)
        
        # Load image asynchronously
        if 'Image-URL-M' in book_data and pd.notna(book_data['Image-URL-M']):
            self._load_image_async(image_label, book_data['Image-URL-M'])
        
        # Title
        title_text = book_data['Book-Title'][:50] + "..." if len(book_data['Book-Title']) > 50 else book_data['Book-Title']
        title_label = tk.Label(
            card_frame,
            text=title_text,
            font=tkfont.Font(family="Arial", size=10, weight="bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            wraplength=200,
            justify=tk.CENTER
        )
        title_label.pack(pady=5, padx=10)
        
        # Author
        author_text = f"by {book_data.get('Book-Author', 'Unknown')}"
        author_label = tk.Label(
            card_frame,
            text=author_text,
            font=tkfont.Font(family="Arial", size=9),
            bg=self.colors['card_bg'],
            fg=self.colors['text_light'],
            wraplength=200
        )
        author_label.pack(pady=2, padx=10)
        
        # Ratings
        avg_rating = book_data.get('avg_rating', 0)
        num_ratings = book_data.get('num_rating', 0)
        weighted_rating = book_data.get('weighted_rating', 0)
        
        rating_text = f"⭐ {avg_rating:.2f} ({int(num_ratings)} ratings)"
        rating_label = tk.Label(
            card_frame,
            text=rating_text,
            font=tkfont.Font(family="Arial", size=9),
            bg=self.colors['card_bg'],
            fg=self.colors['accent']
        )
        rating_label.pack(pady=2)
        
        # Weighted score
        score_text = f"Weighted Score: {weighted_rating:.3f}"
        score_label = tk.Label(
            card_frame,
            text=score_text,
            font=tkfont.Font(family="Arial", size=8),
            bg=self.colors['card_bg'],
            fg=self.colors['text_light']
        )
        score_label.pack(pady=2)
    
    def _load_image_async(self, label, url):
        """Load book cover image asynchronously."""
        def load_image():
            try:
                # Validate URL
                if not url or not isinstance(url, str) or not url.startswith('http'):
                    return
                
                # Check cache
                cached_img = self.image_cache.get(url)
                if cached_img:
                    self.root.after(0, lambda img=cached_img: label.config(image=img))
                    return
                
                # Download image
                response = requests.get(url, timeout=5, stream=True)
                if response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        return
                    
                    img = Image.open(BytesIO(response.content))
                    # Convert to RGB if necessary (handles RGBA, P, etc.)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img = img.resize((128, 192), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Cache image
                    self.image_cache.set(url, photo)
                    
                    # Update label (use default parameter to avoid closure issues)
                    self.root.after(0, lambda img=photo: label.config(image=img))
                    label.image = photo  # Keep a reference
            except (requests.RequestException, IOError, OSError, Exception):
                # Use default image on error (silently fail)
                pass
        
        thread = threading.Thread(target=load_image, daemon=True)
        thread.start()
    
    def _on_search_change(self, *args):
        """Handle search text changes for autocomplete."""
        query = self.search_var.get()
        
        if len(query) < 2:
            # Hide autocomplete container
            try:
                self.autocomplete_container.pack_info()
                self.autocomplete_container.pack_forget()
            except tk.TclError:
                pass
            return
        
        if self.engine is None:
            return
        
        def update_autocomplete():
            try:
                matches = self.engine.search_books(query, limit=10)
                self.root.after(0, lambda: self._update_autocomplete_list(matches))
            except Exception:
                pass
        
        thread = threading.Thread(target=update_autocomplete, daemon=True)
        thread.start()
    
    def _update_autocomplete_list(self, matches):
        """Update autocomplete listbox."""
        self.autocomplete_listbox.delete(0, tk.END)
        
        if matches:
            for match in matches:
                self.autocomplete_listbox.insert(tk.END, match)
            # Show container if not already visible
            try:
                self.autocomplete_container.pack_info()
            except tk.TclError:
                # Container is not packed, pack it now
                self.autocomplete_container.pack(fill=tk.X, pady=(5, 0))
        else:
            # Hide container
            try:
                self.autocomplete_container.pack_info()
                self.autocomplete_container.pack_forget()
            except tk.TclError:
                # Already not packed
                pass
    
    def _on_autocomplete_select(self, event):
        """Handle autocomplete selection."""
        selection = self.autocomplete_listbox.curselection()
        if selection:
            selected_text = self.autocomplete_listbox.get(selection[0])
            self.search_var.set(selected_text)
            # Hide autocomplete container
            try:
                self.autocomplete_container.pack_forget()
            except tk.TclError:
                pass
            self._search_books()
    
    def _search_books(self):
        """Search for books and show recommendations."""
        query = self.search_var.get().strip()
        
        if not query:
            messagebox.showwarning("Warning", "Please enter a book title")
            return
        
        if self.engine is None:
            messagebox.showwarning("Warning", "Data is still loading. Please wait.")
            return
        
        # Hide autocomplete
        try:
            self.autocomplete_container.pack_info()
            self.autocomplete_container.pack_forget()
        except tk.TclError:
            pass
        
        # Clear previous results
        for widget in self.search_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Show loading
        loading_label = tk.Label(
            self.search_scrollable_frame,
            text="Searching for recommendations...",
            font=tkfont.Font(family="Arial", size=12),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        loading_label.pack(pady=50)
        
        def get_recommendations():
            try:
                # Get recommendations first to check if book is in collaborative filtering model
                recommendations = self.engine.get_recommendations(query, n=10)
                
                # Get book info (searches full books_df, may find book even if not in CF model)
                book_info = self.engine.get_book_info(query)
                
                # If no recommendations, check if book exists in dataset
                if not recommendations:
                    if book_info is None:
                        self.root.after(0, lambda: self._show_search_error(
                            f"Book '{query}' not found in dataset.\n\n"
                            "Note: Only books with sufficient ratings (≥50) and users with "
                            "many ratings (≥200) are included in recommendations."
                        ))
                    else:
                        # Book exists in dataset but not in collaborative filtering model
                        self.root.after(0, lambda: self._show_search_error(
                            f"Book '{query}' found in dataset, but it doesn't have enough "
                            "ratings for recommendations.\n\n"
                            "To get recommendations, the book needs:\n"
                            "- At least 50 ratings from active users\n"
                            "- Users with at least 200 ratings each"
                        ))
                    return
                
                # If book_info is None but we have recommendations, try to get it from recommendations
                if book_info is None:
                    # Book might have a slightly different title in books_df
                    # Try to find it or use the first recommendation's info
                    rec_book_title = recommendations[0]['book'] if recommendations else query
                    book_info = self.engine.get_book_info(rec_book_title)
                    if book_info is None:
                        # Create a minimal book_info from the query
                        book_info = {'Book-Title': query, 'Book-Author': 'Unknown'}
                
                self.root.after(0, lambda: self._display_recommendations(book_info, recommendations))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to get recommendations: {str(e)}"))
        
        thread = threading.Thread(target=get_recommendations, daemon=True)
        thread.start()
    
    def _show_search_error(self, message):
        """Show error message in search results."""
        for widget in self.search_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Create a frame for the error message to allow wrapping
        error_frame = tk.Frame(self.search_scrollable_frame, bg=self.colors['bg'])
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=50)
        
        error_label = tk.Label(
            error_frame,
            text=message,
            font=tkfont.Font(family="Arial", size=11),
            bg=self.colors['bg'],
            fg=self.colors['error'],
            wraplength=600,
            justify=tk.LEFT
        )
        error_label.pack(anchor=tk.W)
    
    def _display_recommendations(self, book_info, recommendations):
        """Display search results and recommendations."""
        # Clear previous content
        for widget in self.search_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Display searched book
        searched_frame = tk.Frame(self.search_scrollable_frame, bg=self.colors['card_bg'], relief=tk.RAISED, borderwidth=2)
        searched_frame.pack(fill=tk.X, padx=20, pady=20)
        
        searched_title = tk.Label(
            searched_frame,
            text="Searched Book:",
            font=tkfont.Font(family="Arial", size=12, weight="bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        )
        searched_title.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        book_title_label = tk.Label(
            searched_frame,
            text=book_info.get('Book-Title', 'Unknown'),
            font=tkfont.Font(family="Arial", size=14, weight="bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['primary']
        )
        book_title_label.pack(anchor=tk.W, padx=20, pady=5)
        
        author_label = tk.Label(
            searched_frame,
            text=f"by {book_info.get('Book-Author', 'Unknown')}",
            font=tkfont.Font(family="Arial", size=11),
            bg=self.colors['card_bg'],
            fg=self.colors['text_light']
        )
        author_label.pack(anchor=tk.W, padx=20, pady=5)
        searched_frame.pack(pady=(0, 20))
        
        # Recommendations header
        rec_header = tk.Label(
            self.search_scrollable_frame,
            text="Recommended Books:",
            font=tkfont.Font(family="Arial", size=14, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        rec_header.pack(anchor=tk.W, padx=20, pady=(10, 10))
        
        # Display recommendations
        for rec in recommendations:
            self._create_recommendation_card(rec)
        
        self.search_canvas.update_idletasks()
        # Update scroll region after content is displayed
        self.search_canvas.configure(scrollregion=self.search_canvas.bbox("all"))
    
    def _create_recommendation_card(self, rec_data):
        """Create a recommendation card."""
        card_frame = tk.Frame(
            self.search_scrollable_frame,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            borderwidth=1
        )
        card_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Get book info
        book_title = rec_data['book']
        similarity = rec_data['similarity']
        
        # Try to get book info
        book_info = None
        if self.engine:
            book_info = self.engine.get_book_info(book_title)
        
        # Content frame
        content_frame = tk.Frame(card_frame, bg=self.colors['card_bg'])
        content_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Book title
        title_label = tk.Label(
            content_frame,
            text=book_title,
            font=tkfont.Font(family="Arial", size=12, weight="bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            anchor=tk.W
        )
        title_label.pack(anchor=tk.W, pady=5)
        
        # Author
        if book_info:
            author_text = f"by {book_info.get('Book-Author', 'Unknown')}"
            author_label = tk.Label(
                content_frame,
                text=author_text,
                font=tkfont.Font(family="Arial", size=10),
                bg=self.colors['card_bg'],
                fg=self.colors['text_light'],
                anchor=tk.W
            )
            author_label.pack(anchor=tk.W, pady=2)
        
        # Similarity score
        similarity_percent = similarity * 100
        similarity_label = tk.Label(
            content_frame,
            text=f"Similarity: {similarity_percent:.2f}%",
            font=tkfont.Font(family="Arial", size=10),
            bg=self.colors['card_bg'],
            fg=self.colors['accent'],
            anchor=tk.W
        )
        similarity_label.pack(anchor=tk.W, pady=5)
        
        # Progress bar for similarity
        progress_frame = tk.Frame(content_frame, bg=self.colors['card_bg'])
        progress_frame.pack(fill=tk.X, pady=5)
        
        progress_canvas = tk.Canvas(
            progress_frame,
            height=20,
            bg=self.colors['card_bg'],
            highlightthickness=0
        )
        progress_canvas.pack(fill=tk.X)
        
        # Draw progress bar
        width = 300
        fill_width = int(width * similarity)
        progress_canvas.create_rectangle(0, 0, width, 20, fill='#e0e0e0', outline='')
        progress_canvas.create_rectangle(0, 0, fill_width, 20, fill=self.colors['accent'], outline='')


def main():
    """Main function to run the application."""
    root = tk.Tk()
    app = BookRecommendationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

