from flask import Flask, jsonify, request
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

app = Flask(__name__)

# Load the dataset
df = pd.read_csv('cleaned_book_store_data.csv')  

# Split the dataset
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Batch processing for TF-IDF
batch_size = 10000
batches = np.array_split(df, len(df) // batch_size)
tfidf = TfidfVectorizer(stop_words='english')

for i, batch in enumerate(batches):
    combined_text = batch['Book-Title'] + ' ' + batch['Book-Author'] + ' ' + batch['Publisher']
    tfidf_matrix = tfidf.fit_transform(combined_text)
    batch['tfidf_matrix'] = list(tfidf_matrix)
    print(f'Processed batch {i+1}/{len(batches)}')

df_combined = pd.concat(batches)
indices = pd.Series(df_combined.index, index=df_combined['Book-Title']).drop_duplicates()

def recommend_books_by_author_batch(df, title, top_n=5):
    idx = indices[title]
    author = df.loc[idx, 'Book-Author']
    author_books = df[df['Book-Author'] == author]
    return author_books[['Book-Title', 'Book-Author', 'Image-URL-M']].head(top_n)

def collaborative_recommendation(df, user_id, top_n=5, batch_size=5000):
    user_ids = df['User-ID'].unique()
    num_batches = int(np.ceil(len(user_ids) / batch_size))
    user_id_batches = np.array_split(user_ids, num_batches)
    
    all_recommendations = []

    for batch_num, user_batch in enumerate(user_id_batches):
        print(f"Processing batch {batch_num + 1} of {num_batches}...")
        batch_train_df = df[df['User-ID'].isin(user_batch)]
        user_book_matrix = batch_train_df.pivot_table(index='User-ID', columns='ISBN', values='Book-Rating', aggfunc='mean').fillna(0)
        user_similarity = cosine_similarity(user_book_matrix)
        
        if user_id in user_book_matrix.index:
            target_user_index = user_book_matrix.index.get_loc(user_id)
            user_similarities = user_similarity[target_user_index]
            similar_user_indices = user_similarities.argsort()[::-1][1:]
            
            recommended_books = []
            for user_index in similar_user_indices:
                rated_by_similar_user = user_book_matrix.iloc[user_index]
                not_rated_by_target_user = (rated_by_similar_user != 0) & (user_book_matrix.iloc[target_user_index] == 0)
                recommended_books.extend(user_book_matrix.columns[not_rated_by_target_user][:top_n])
            
            all_recommendations.extend(list(set(recommended_books)))
    
    recommended_books_details = df[df['ISBN'].isin(all_recommendations)][['Book-Title', 'Book-Author', 'Image-URL-M']].drop_duplicates()
    
    return recommended_books_details.head(top_n).to_dict(orient='records')

@app.route('/recommend', methods=['GET'])
def recommend():
    user_id = int(request.args.get('user_id'))
    top_n = int(request.args.get('top_n', 5))
    
    recommendations = collaborative_recommendation(train_df, user_id, top_n)
    return jsonify(recommendations)

@app.route('/rating_based', methods=['GET'])
def rating_based():
    top_n = int(request.args.get('top_n', 10))
    average_ratings = train_df.groupby(['Book-Title', 'Book-Author', 'Image-URL-M'])['Book-Rating'].mean().reset_index()
    top_rated_books = average_ratings.sort_values(by='Book-Rating', ascending=False).head(top_n)
    top_rated_books['Book-Rating'] = top_rated_books['Book-Rating'].astype(int)
    response = top_rated_books[['Book-Title', 'Book-Author', 'Book-Rating', 'Image-URL-M']].to_dict(orient='records')
    return jsonify(response)

@app.route('/content_based', methods=['GET'])
def content_based():
    book_name = request.args.get('book_name')
    top_n = int(request.args.get('top_n', 5))
    content_based_rec = recommend_books_by_author_batch(df_combined, book_name, top_n=top_n)
    return jsonify(content_based_rec.to_dict(orient='records'))

@app.route('/hybrid', methods=['GET'])
def hybrid():
    user_id = int(request.args.get('user_id'))
    top_n = int(request.args.get('top_n', 5))
    
    # Combine collaborative and content-based recommendations here (for demonstration, returning collaborative)
    recommendations = collaborative_recommendation(train_df, user_id, top_n)
    return jsonify(recommendations)

if __name__ == '__main__':
    app.run(debug=True)


