from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import pandas as pd
from datetime import datetime

# Get the database URL from environment variable or use a default SQLite database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///reviews.db')

# Create the engine
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    restaurant_name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    date_created = Column(DateTime, nullable=False)
    name = Column(String(100), nullable=True)
    review = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    word_count = Column(Float, nullable=False)  # New column
    name_only = Column(String(3), nullable=False)  # New column
    review_only = Column(String(3), nullable=False)  # New column
    name_and_review = Column(String(3), nullable=False)  # New column
    confidence = Column(String(10), nullable=False)  # New column
    model = Column(String(50), nullable=False)  # New column

# Create tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

def init_db_with_csv():
    """Initialize database with data from CSV file"""
    try:
        session = Session()

        # Drop existing data
        session.query(Review).delete()
        session.commit()

        # Read new CSV file
        df = pd.read_csv('attached_assets/orinoco_aggregated_analysis.csv')

        # Convert dataframe to list of Review objects
        reviews = []
        for _, row in df.iterrows():
            try:
                # Handle potential missing columns with defaults
                review = Review(
                    restaurant_name=row['Restaurant Name'],
                    type=row['Cuisine'],
                    date_created=pd.to_datetime(row['Review Date']),
                    name=row['Reviewer Name'],
                    review=row['Review'],
                    rating=float(row.get('Rating', 0)) if 'Rating' in row else None,
                    word_count=float(row.get('Word Count', 0)) if 'Word Count' in row else None,
                    name_only=row.get('Name Only', None),
                    review_only=row.get('Review Only', None),
                    name_and_review=row.get('Name & Review', None),
                    confidence=row.get('Confidence', None),
                    model=row.get('Model', 'unknown')
                )
                reviews.append(review)
            except Exception as e:
                print(f"Error processing row: {row}\nError: {str(e)}")
                continue

        # Add all reviews to database
        if reviews:
            session.add_all(reviews)
            session.commit()
            print(f"Successfully imported {len(reviews)} reviews")
        else:
            print("No reviews were imported")

    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def get_reviews(selected_restaurant, selected_type, selected_response, selected_confidence, selected_review_only, selected_name_only, selected_model):
    """Get reviews with optional filters"""
    session = Session()
    query = session.query(Review)
    if selected_restaurant != 'All':
        query = query.filter(Review.restaurant_name == selected_restaurant)
    if selected_type != 'All':
        query = query.filter(Review.type == selected_type)
    if selected_response != 'All':
        query = query.filter(Review.name_and_review == selected_response)
    if selected_confidence != 'All':
        query = query.filter(Review.confidence == selected_confidence)
    if selected_review_only != 'All':
        query = query.filter(Review.review_only == selected_review_only)
    if selected_name_only != 'All':
        query = query.filter(Review.name_only == selected_name_only)
    if selected_model != 'All':
        query = query.filter(Review.model == selected_model)
    reviews = query.all()
    session.close()
    return reviews