from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import pandas as pd
from datetime import datetime
import streamlit as st
from sqlalchemy.sql import func, case  # Added missing imports

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
    cuisine = Column(String(50), nullable=False)
    date_created = Column(DateTime, nullable=False)
    name = Column(String(100), nullable=True)
    review = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    word_count = Column(Float, nullable=False, default=0)  # Added default value
    name_only = Column(String(3), nullable=False, default='no')  # Added default value
    review_only = Column(String(3), nullable=False, default='no')  # Added default value
    name_and_review = Column(String(3), nullable=False, default='no')  # Added default value
    confidence = Column(String(10), nullable=False, default='low')  # Added default value
    model = Column(String(50), nullable=False, default='unknown')  # Added default value
    is_local = Column(String(3), nullable=False, default='no')  # Added default value

# Create tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

@st.cache_resource
def init_db_with_csv():
    """Initialize database with data from CSV file"""
    try:
        session = Session()

        # Drop existing data
        session.query(Review).delete()
        session.commit()

        # Read new CSV file
        df = pd.read_csv('attached_assets/batch_aggregated_analysis.csv')

        # Convert dataframe to list of Review objects
        reviews = []
        for _, row in df.iterrows():
            try:
                # Handle potential missing columns with defaults
                review = Review(
                    restaurant_name=row['Restaurant Name'],
                    cuisine=row['Cuisine'],
                    date_created=pd.to_datetime(row['Review Date']),
                    name=row['Reviewer Name'],
                    review=row['Review'],
                    rating=float(row.get('Rating', 0)) if 'Rating' in row else None,
                    word_count=float(row.get('Word Count', 0)) if 'Word Count' in row else None,
                    name_only=row.get('Name Only', None),
                    review_only=row.get('Review Only', None),
                    name_and_review=row.get('Name & Review', None),
                    confidence=row.get('Confidence', None),
                    model=row.get('Model', 'unknown'),
                    is_local=row.get('Is Local', None)
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

@st.cache_data
def get_reviews(restaurant=None, cuisine=None, name_and_review=None, confidence=None, review_only=None, name_only=None, is_local=None):
    """Get reviews with optional filters"""
    session = Session()
    query = session.query(Review)
    if restaurant and 'All' not in restaurant:
        query = query.filter(Review.restaurant_name.in_(restaurant))
    if cuisine and 'All' not in cuisine:
        query = query.filter(Review.cuisine.in_(cuisine))
    if name_and_review and 'All' not in name_and_review:
        query = query.filter(Review.name_and_review.in_(name_and_review))
    if confidence and 'All' not in confidence:
        query = query.filter(Review.confidence.in_(confidence))
    if review_only and 'All' not in review_only:
        query = query.filter(Review.review_only.in_(review_only))
    if name_only and 'All' not in name_only:
        query = query.filter(Review.name_only.in_(name_only))
    if is_local and 'All' not in is_local:
        query = query.filter(Review.is_local.in_(is_local))
    reviews = query.all()
    session.close()
    return reviews

@st.cache_data
def get_rating_summary(restaurant=None, cuisine=None, name_and_review=None, confidence=None, review_only=None, name_only=None, is_local=None):
    """Get rating summary per restaurant with optional filters"""
    session = Session()
    query = session.query(
        Review.restaurant_name,
        func.count(Review.id).label('review_count'),
        func.avg(Review.rating).label('average_rating'),
        (func.sum(case(
            (Review.is_local == 'yes', Review.rating),
        )) / func.sum(case(
            (Review.is_local == 'yes', 1),
        ))).label('average_local_rating'),
        (func.sum(func.coalesce(case(
            (Review.is_local == 'yes', 1),
        ), 0)) / func.count(Review.id) * 100).label('local_rate')
    ).group_by(Review.restaurant_name)

    # Apply filters
    if restaurant and 'All' not in restaurant:
        query = query.filter(Review.restaurant_name.in_(restaurant))
    if cuisine and 'All' not in cuisine:
        query = query.filter(Review.cuisine.in_(cuisine))
    if name_and_review and 'All' not in name_and_review:
        query = query.filter(Review.name_and_review.in_(name_and_review))
    if confidence and 'All' not in confidence:
        query = query.filter(Review.confidence.in_(confidence))
    if review_only and 'All' not in review_only:
        query = query.filter(Review.review_only.in_(review_only))
    if name_only and 'All' not in name_only:
        query = query.filter(Review.name_only.in_(name_only))
    if is_local and 'All' not in is_local:
        query = query.filter(Review.is_local.in_(is_local))

    rating_summary = query.all()
    session.close()
    return rating_summary
