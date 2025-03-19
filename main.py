import streamlit as st
import pandas as pd
import os
from database import init_db_with_csv, get_reviews, get_rating_summary, Review, Session

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

# Initialize session state for filters if not exists
if 'reset_filters' not in st.session_state:
    st.session_state.reset_filters = False

# Main title
st.markdown('<h1 class="restaurant-title">Restaurant Review Dashboard 🍽️</h1>', unsafe_allow_html=True)

# Add reset button
if st.button('Reset Filters', key='reset_btn', help='Reset all filters to default'):
    # Force all multiselects to reset to 'All' on next rerun
    for key in list(st.session_state.keys()):
        if key.startswith('Select'):
            st.session_state[key] = ['All']
    st.rerun()

# Create filter section
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

def get_unique_values(column):
    session = Session()
    values = sorted(set(r[0] for r in session.query(column).distinct()))
    session.close()
    values.insert(0, 'All')
    return values

with col1:
    restaurant_names = get_unique_values(Review.restaurant_name)
    selected_restaurant = st.multiselect('Select Restaurant', restaurant_names, default=st.session_state.get('Select Restaurant', ['All']))

with col2:
    restaurant_types = get_unique_values(Review.cuisine)
    selected_type = st.multiselect('Select Cuisine Type', restaurant_types, default=st.session_state.get('Select Cuisine Type', ['All']))

with col3:
    # Name Only filter
    name_only_options = ['All', 'yes', 'no']
    selected_name_only = st.multiselect(
        'Filter by Name Only',
        name_only_options,
        default=st.session_state.get('Filter by Name Only', ['All'])
    )

with col4:
    # Review Only filter
    review_only_options = ['All', 'yes', 'no']
    selected_review_only = st.multiselect(
        'Filter by Review Only',
        review_only_options,
        default=st.session_state.get('Filter by Review Only', ['All'])
    )

with col5:
    # Name & Review filter
    name_and_review_options = ['All', 'yes', 'no']
    selected_name_and_review = st.multiselect(
        'Filter by Name & Review',
        name_and_review_options,
        default=st.session_state.get('Filter by Name & Review', ['All'])
    )

with col6:
    # Is Local filter
    is_local_options = ['All', 'yes', 'no']
    selected_is_local = st.multiselect(
        'Is Local',
        is_local_options,
        default=st.session_state.get('Is Local', ['All'])
    )

with col7:
    confidence_levels = get_unique_values(Review.confidence)
    selected_confidence = st.multiselect('Select Confidence Level', confidence_levels, default=st.session_state.get('Select Confidence Level', ['All']))

st.markdown('</div>', unsafe_allow_html=True)

# Get filtered reviews from database
reviews = get_reviews(
    selected_restaurant, 
    selected_type, 
    selected_name_and_review, 
    selected_confidence, 
    selected_review_only, 
    selected_name_only,
    selected_is_local
)

# Convert reviews to dataframe for display
filtered_df = pd.DataFrame([{
    'restaurant_name': r.restaurant_name,
    'cuisine': r.cuisine,
    'date_created': r.date_created,
    'name': r.name,
    'review': r.review,
    'rating': r.rating,
    'name_and_review': r.name_and_review,
    'word_count': r.word_count,
    'name_only': r.name_only,
    'review_only': r.review_only,
    'confidence': r.confidence,
    'model': r.model,
    'is_local': r.is_local
} for r in reviews])

# Create metric section
col1, col2  = st.columns([1,2])

# Calculate metrics
num_restaurants = filtered_df['restaurant_name'].nunique()
total_reviews = len(filtered_df)
avg_rating = round(filtered_df['rating'].mean(), 2) if not filtered_df.empty else 0
condition = ((filtered_df['review_only'] == 'yes') & (filtered_df['name_only'] == 'yes') & (filtered_df['confidence'] == 'high'))
local_rating = round(filtered_df[condition]['rating'].mean(), 2) if not filtered_df.empty else 0
if not filtered_df.empty:
    total_responses = len(filtered_df)
    responded_reviews = len(filtered_df[condition])
    response_rate = round(100 * responded_reviews / total_responses, 1)
else:
    response_rate = 0.0

# Create a dataframe for the metrics
metrics_df = pd.DataFrame({
    "Metric": ["Number of Restaurants", "Total Reviews", "Average Rating", "Local Rating", "Is-a-Local Rate"],
    "Value": [f"{num_restaurants}", f"{total_reviews}", f"{avg_rating} ⭐ ", f"{local_rating} ⭐ ", f"{response_rate}%"]
})
with col1:
    # Display the metrics dataframe
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    st.markdown('<h3>Overall Metrics</h3>', unsafe_allow_html=True)
    st.dataframe(
        metrics_df,
        column_config={
            "Metric": st.column_config.TextColumn(
                "Metric",
                width=150
            ),
            "Value": st.column_config.TextColumn(
                "Value",
                width=100
            )
        },
        hide_index=True,
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    st.markdown('<h3>Metric Summary By Restaurant</h3>', unsafe_allow_html=True)
    
    # Get rating summary
    rating_summary = get_rating_summary(
        selected_restaurant, 
        selected_type, 
        selected_name_and_review, 
        selected_confidence, 
        selected_review_only, 
        selected_name_only,
        selected_is_local)
    
    # Convert to dataframe with all columns
    summary_df = pd.DataFrame(rating_summary, columns=[
        'Restaurant', 'Review Count', 'Average Rating', 
        'Average Local Rating', 'Local Rate'
    ])
    
    # Round numeric columns
    summary_df['Average Rating'] = summary_df['Average Rating'].round(2)
    summary_df['Average Local Rating'] = summary_df['Average Local Rating'].round(2)
    summary_df['Local Rate'] = summary_df['Local Rate'].round(1)
    
    # Sort by average rating in descending order
    summary_df = summary_df.sort_values('Average Rating', ascending=False)
    
    # Display the summary table
    st.dataframe(
        summary_df,
        column_config={
            "Restaurant": st.column_config.TextColumn(
                "Restaurant",
                width=150
            ),
            "Review Count": st.column_config.NumberColumn(
                "Reviews",
                format="%d",
                width=70
            ),
            "Average Rating": st.column_config.NumberColumn(
                "Avg Rating",
                format="%.2f ⭐",
                width=100
            ),
            "Average Local Rating": st.column_config.NumberColumn(
                "Local Rating",
                format="%.2f ⭐",
                width=100
            ),
            "Local Rate": st.column_config.NumberColumn(
                "Local %",
                format="%.1f%%",
                width=80
            )
        },
        hide_index=True,
        use_container_width=True
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
        display_df[['restaurant_name', 'cuisine', 'date_created', 'name', 'rating', 'review', 'word_count', 'name_only', 'review_only', 'name_and_review', 'confidence', 'model', 'is_local']],  # Added is_local
        column_config={
            "restaurant_name": st.column_config.TextColumn(
                "Restaurant",
                width=150
            ),
            "cuisine": st.column_config.TextColumn(
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
            ),
            "is_local": st.column_config.TextColumn(
                "Is Local",
                width=50
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