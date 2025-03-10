import streamlit as st
import pandas as pd
import os
from database import init_db_with_csv, get_reviews, Review, Session

# Page configuration
st.set_page_config(
    page_title="Restaurant Review Dashboard",
    page_icon="🍽️",
    layout="wide"
)

# Load custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize database with CSV data
init_db_with_csv()

# Main title
st.markdown('<h1 class="restaurant-title">Restaurant Review Dashboard 🍽️</h1>', unsafe_allow_html=True)

# Create filter section
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    # Get unique restaurant names from database
    session = Session()
    restaurant_names = sorted(set(r[0] for r in session.query(Review.restaurant_name).distinct()))
    session.close()

    selected_restaurant = st.selectbox(
        'Select Restaurant',
        ['All'] + list(restaurant_names)
    )

with col2:
    # Get unique restaurant types from database
    session = Session()
    restaurant_types = sorted(set(r[0] for r in session.query(Review.type).distinct()))
    session.close()

    selected_type = st.selectbox(
        'Select Cuisine Type',
        ['All'] + list(restaurant_types)
    )

with col3:
    # Name & Review filter
    name_and_review_options = ['All', 'yes', 'no']
    selected_name_and_review = st.selectbox(
        'Filter by Name & Review',
        name_and_review_options
    )

with col4:
    # Confidence filter
    session = Session()
    confidence_levels = sorted(set(r[0] for r in session.query(Review.confidence).distinct()))
    session.close()

    selected_confidence = st.selectbox(
        'Select Confidence Level',
        ['All'] + list(confidence_levels)
    )

with col5:
    # Review Only filter
    review_only_options = ['All', 'yes', 'no']
    selected_review_only = st.selectbox(
        'Filter by Review Only',
        review_only_options
    )

st.markdown('</div>', unsafe_allow_html=True)

# Get filtered reviews from database
reviews = get_reviews(selected_restaurant, selected_type, selected_name_and_review, selected_confidence, selected_review_only)

# Convert reviews to dataframe for display
filtered_df = pd.DataFrame([{
    'restaurant_name': r.restaurant_name,
    'type': r.type,
    'date_created': r.date_created,
    'name': r.name,
    'review': r.review,
    'rating': r.rating,
    'name_and_review': r.name_and_review,
    'word_count': r.word_count,
    'name_only': r.name_only,
    'review_only': r.review_only,
    'confidence': r.confidence,
    'model': r.model
} for r in reviews])

# Display metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    st.metric("Total Reviews", len(filtered_df))
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    avg_rating = round(filtered_df['rating'].mean(), 2) if not filtered_df.empty else 0
    st.metric("Average Rating", f"⭐ {avg_rating}")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    # Calculate Is-a-Local rate: percentage of reviews that are from local reviewers
    if not filtered_df.empty:
        total_responses = len(filtered_df)
        condition = ((filtered_df['name_and_review'] == 'yes') & (filtered_df['confidence'] == 'high'))
        responded_reviews = len(filtered_df[condition])
        response_rate = round(100 * responded_reviews / total_responses, 1)
    else:
        response_rate = 0.0

    st.metric(
        "Is-a-Local Rate", 
        f"{response_rate}%",
        help="Percentage of reviews with 'Name and Review' = yes and 'Confidence' = high"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Display reviews
st.markdown("<h3>Reviews</h3>", unsafe_allow_html=True)

if not filtered_df.empty:
    # Format the dataframe for display
    display_df = filtered_df.copy()
    display_df['date_created'] = pd.to_datetime(display_df['date_created']).dt.strftime('%Y-%m-%d')
    display_df = display_df.sort_values('date_created', ascending=False)

    # Display the dataframe with improved text display
    st.dataframe(
        display_df[['restaurant_name', 'type', 'date_created', 'name', 'rating', 'review', 'word_count', 'name_only', 'review_only', 'name_and_review', 'confidence', 'model']],  # Reordered columns
        column_config={
            "restaurant_name": st.column_config.TextColumn(
                "Restaurant",
                width=150
            ),
            "type": st.column_config.TextColumn(
                "Cuisine Type",
                width=80
            ),
            "date_created": st.column_config.DateColumn(
                "Date",
                format="MMM DD, YYYY",
                width=80
            ),
            "name": st.column_config.TextColumn(
                "Reviewer",
                width=120
            ),
            "rating": st.column_config.NumberColumn(
                "Rating",
                help="Restaurant rating",
                format="%d",
                width=50
            ),
            "review": st.column_config.TextColumn(
                "Review",
                help="Customer review",
                max_chars=None,  # No character limit for full text display
                width=None  # Allow column to expand
            ),
            "word_count": st.column_config.NumberColumn(
                "Word Count",
                help="Word count of the review",
                format="%d",
                width=50
            ),
            "name_only": st.column_config.TextColumn(
                "Name Only",
                width=50
            ),
            "review_only": st.column_config.TextColumn(
                "Review Only",
                width=50
            ),
            "name_and_review": st.column_config.TextColumn(
                "Name & Review",
                width=50
            ),
            "confidence": st.column_config.TextColumn(
                "Confidence",
                width=50
            ),
            "model": st.column_config.TextColumn(
                "Model",
                width=80
            )
        },
        hide_index=True,
        use_container_width=True,
        height=600  # Set a fixed height for better scrolling
    )
else:
    st.info("No reviews found with the selected filters.")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666666;'>Restaurant Review Dashboard | Created with Streamlit</p>", 
    unsafe_allow_html=True
)