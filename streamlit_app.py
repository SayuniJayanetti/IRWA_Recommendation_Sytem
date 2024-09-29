import streamlit as st
import requests

# Define sidebar for page navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Home", "Recommendation System"])

# Home Page - Display "Book Recommendation System" and Top 10 Books (Rating-Based)
if page == "Home":
    st.title("Book Store")

    # Display top 10 books based on rating-based filtering
    st.subheader("Top 10 Rated Books")

    try:
        # Call Flask API for top 10 rating-based recommendations
        response = requests.get("http://127.0.0.1:5000/rating_based?top_n=10")
        recommendations = response.json()

        if recommendations:
            for rec in recommendations:
                col1, col2 = st.columns([1, 2])

                # Display image in first column
                with col1:
                    image_url = rec.get('Image-URL-M', None)
                    if image_url:
                        st.image(image_url, width=100)
                    else:
                        st.write("(No image available)")

                # Display book details in the second column
                with col2:
                    title = rec.get('Book-Title', 'Title not available')
                    author = rec.get('Book-Author', 'Author not available')
                    rating = rec.get('Book-Rating', 'Rating not available')

                    st.write(f"**Title**: {title}")
                    st.write(f"**Author**: {author}")
                    st.write(f"**Rating**: {rating}")
                
                    # Add a "Buy" button
                    if st.button("Buy", key=title):  # Unique key for each button
                        st.write(f"You clicked on Buy for '{title}'")

                    st.write("---")
        else:
            st.write("No top-rated books available.")
    except Exception as e:
        st.write("Error fetching top-rated books:", e)

# Recommendation System Page - User selects filtering method
elif page == "Recommendation System":
    st.title("Book Store")

    # Dropdown to select filtering method
    filter_method = st.selectbox(
        "Select the Recommendation Method",
        ("Content-Based", "Collaborative Filtering", "Hybrid")
    )

    # Input fields based on the selected method
    if filter_method == "Content-Based":
        book_name = st.text_input("Enter a Book Title")
        top_n = st.slider("Number of recommendations", 1, 10, 5)  # Added top_n slider for content-based filtering
    else:
        user_id = st.text_input("Enter your User ID", value="67544")
        top_n = st.slider("Number of recommendations", 1, 10, 5)

    # Button to get recommendations
    if st.button('Get Recommendations'):
        try:
            if filter_method == "Content-Based":
                # Call Flask API for content-based recommendations
                response = requests.get(f"http://127.0.0.1:5000/content_based?book_name={book_name}&top_n={top_n}")
            elif filter_method == "Collaborative Filtering":
                # Call Flask API for collaborative filtering
                response = requests.get(f"http://127.0.0.1:5000/recommend?user_id={user_id}&top_n={top_n}")
            else:
                # Call Flask API for hybrid filtering
                response = requests.get(f"http://127.0.0.1:5000/hybrid?user_id={user_id}&top_n={top_n}")

            recommendations = response.json()

            if recommendations:
                st.subheader(f"{filter_method} Recommended Books:")
                for index, rec in enumerate(recommendations):
                    col1, col2 = st.columns([1, 2])
                    
                    # Display image in first column
                    with col1:
                        image_url = rec.get('Image-URL-M', None)
                          
                        if image_url:
                            st.image(image_url, width=100)
                        else:
                            st.write("(No image available)")
                    
                    # Display book details in second column
                    with col2:
                        title = rec.get('Book-Title', 'Title not available')
                        author = rec.get('Book-Author', 'Author not available')
                        st.write(f"**Title**: {title}")
                        st.write(f"**Author**: {author}")
                        st.button("Buy", key=f"buy_{index}_{title}")
                        st.write("---")

                         
            else:
                st.write("No recommendations available.")
        except Exception as e:
            st.write("Error retrieving recommendations:", e)

