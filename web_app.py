#!/usr/bin/env python3
"""
Modern Flask web application for the Blog Recommendation Engine.
Provides a sleek UI for the Greenplum + AI recommendation demo.
"""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from pgvector import Vector
import json
from config import *

app = Flask(__name__)
CORS(app)

def get_db_connection():
    """Get database connection with pgvector support"""
    conn = psycopg2.connect(get_connection_string())
    register_vector(conn)
    return conn

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get basic stats
        cur.execute("""
            SELECT
                COUNT(*) as total_posts,
                COUNT(embedding) as posts_with_embeddings,
                COUNT(DISTINCT cluster_id) as num_clusters,
                COUNT(DISTINCT category) as num_categories
            FROM blog_posts
            WHERE embedding IS NOT NULL
        """)
        stats = cur.fetchone()

        # Get embedding dimensions from config
        dimensions = (EMBEDDING_DIMENSIONS,)

        result = {
            'total_posts': stats[0],
            'posts_with_embeddings': stats[1],
            'num_clusters': stats[2],
            'num_categories': stats[3],
            'embedding_dimensions': dimensions[0] if dimensions else 0,
            'embedding_model': EMBEDDING_MODEL
        }

        cur.close()
        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """Get all cluster summaries with sample posts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get cluster summaries
        cur.execute("""
            SELECT cluster_id, summary
            FROM blog_cluster_summaries
            ORDER BY cluster_id
        """)
        clusters = cur.fetchall()

        result = []
        for cluster_id, summary in clusters:
            # Get sample posts for this cluster
            cur.execute("""
                SELECT title, description
                FROM blog_posts
                WHERE cluster_id = %s AND embedding IS NOT NULL
                LIMIT 5
            """, (cluster_id,))
            sample_posts = cur.fetchall()

            # Get cluster size
            cur.execute("""
                SELECT COUNT(*)
                FROM blog_posts
                WHERE cluster_id = %s
            """, (cluster_id,))
            cluster_size = cur.fetchone()[0]

            result.append({
                'cluster_id': cluster_id,
                'summary': summary,
                'sample_posts': [{'title': title, 'description': desc} for title, desc in sample_posts],
                'size': cluster_size
            })

        cur.close()
        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Generate recommendations based on cluster ratings"""
    try:
        ratings_data = request.get_json()
        if not ratings_data or 'ratings' not in ratings_data:
            return jsonify({'error': 'No ratings provided'}), 400

        ratings = ratings_data['ratings']

        conn = get_db_connection()
        cur = conn.cursor()

        # Get cluster centroids and compute preference vector
        cur.execute("""
            SELECT c.cluster_id, s.summary, AVG(b.embedding)::vector
            FROM blog_cluster_summaries s
            JOIN blog_posts b ON b.cluster_id = s.cluster_id
            JOIN (SELECT DISTINCT cluster_id FROM blog_cluster_summaries) c ON c.cluster_id = s.cluster_id
            WHERE b.embedding IS NOT NULL
            GROUP BY c.cluster_id, s.summary
            ORDER BY c.cluster_id
        """)
        clusters = cur.fetchall()

        # Build preference vector
        embeddings = []
        weights = []
        cluster_info = []

        for cluster_id, summary, embedding in clusters:
            if str(cluster_id) in ratings:
                rating = float(ratings[str(cluster_id)])
                embeddings.append(np.array(embedding, dtype=float))
                weights.append(rating)
                cluster_info.append({
                    'cluster_id': cluster_id,
                    'summary': summary,
                    'rating': rating
                })

        if not embeddings:
            return jsonify({'error': 'No valid ratings provided'}), 400

        # Compute weighted preference vector
        embeddings = np.array(embeddings)
        weights = np.array(weights, dtype=float)
        preference_vec = np.average(embeddings, axis=0, weights=weights)

        # Convert to pgvector format
        pref_vec = Vector(preference_vec.tolist())

        # Get most similar articles
        cur.execute("""
            SELECT id, title, description, cluster_id
            FROM blog_posts
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s ASC
            LIMIT 25
        """, (pref_vec,))
        most_interesting = cur.fetchall()

        # Get least similar articles
        cur.execute("""
            SELECT id, title, description, cluster_id
            FROM blog_posts
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s DESC
            LIMIT 25
        """, (pref_vec,))
        least_interesting = cur.fetchall()

        # Calculate preference stats
        avg_rating = np.mean(weights)
        total_clusters_rated = len(weights)

        result = {
            'preference_stats': {
                'average_rating': float(avg_rating),
                'total_clusters_rated': total_clusters_rated,
                'cluster_breakdown': cluster_info
            },
            'most_interesting': [
                {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'cluster_id': row[3]
                }
                for row in most_interesting
            ],
            'least_interesting': [
                {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'cluster_id': row[3]
                }
                for row in least_interesting
            ]
        }

        cur.close()
        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recluster', methods=['POST'])
def recluster_data():
    """Re-cluster the blog posts with a different number of clusters"""
    try:
        data = request.get_json()
        if not data or 'num_clusters' not in data:
            return jsonify({'error': 'num_clusters parameter required'}), 400

        num_clusters = int(data['num_clusters'])
        if num_clusters < 2 or num_clusters > 50:
            return jsonify({'error': 'num_clusters must be between 2 and 50'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Clear existing cluster assignments
        cur.execute("UPDATE blog_posts SET cluster_id = NULL")

        # Delete existing cluster summaries
        cur.execute("DELETE FROM blog_cluster_summaries")

        # Run kmeans clustering with new number of clusters
        cur.execute("""
            WITH data AS (
                SELECT id,
                       string_to_array(trim(both '[]' from embedding::text), ',')::float8[] AS vec
                FROM blog_posts
                WHERE embedding IS NOT NULL
            ),
            agg AS (
                SELECT array_agg(vec) AS all_vecs, array_agg(id) AS all_ids
                FROM data
            ),
            clusters AS (
                SELECT t.cluster_id, t.rn
                FROM (
                    SELECT unnest(kmeans_assign(all_vecs, %s, 100)) AS cluster_id,
                           generate_subscripts(all_ids, 1) AS rn
                    FROM agg
                ) t
            ),
            mapping AS (
                SELECT all_ids[rn] AS id, cluster_id
                FROM clusters, agg
            )
            UPDATE blog_posts p
            SET cluster_id = m.cluster_id
            FROM mapping m
            WHERE p.id = m.id
        """, (num_clusters,))

        conn.commit()

        # Get cluster distribution
        cur.execute("""
            SELECT cluster_id, COUNT(*) as size
            FROM blog_posts
            WHERE cluster_id IS NOT NULL
            GROUP BY cluster_id
            ORDER BY cluster_id
        """)
        cluster_sizes = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'num_clusters': num_clusters,
            'cluster_sizes': [{'cluster_id': row[0], 'size': row[1]} for row in cluster_sizes],
            'message': f'Successfully re-clustered data into {num_clusters} clusters'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_summaries', methods=['POST'])
def generate_summaries():
    """Generate summaries for the current clusters"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all cluster IDs
        cur.execute("SELECT DISTINCT cluster_id FROM blog_posts WHERE cluster_id IS NOT NULL ORDER BY cluster_id")
        cluster_ids = [row[0] for row in cur.fetchall()]

        summaries_generated = 0

        for cluster_id in cluster_ids:
            # Get sample posts for this cluster
            cur.execute("""
                SELECT title, description
                FROM blog_posts
                WHERE cluster_id = %s AND embedding IS NOT NULL
                LIMIT %s
            """, (cluster_id, CLUSTER_SAMPLE_SIZE))

            posts = cur.fetchall()
            if not posts:
                continue

            # Create prompt for summarization
            posts_text = "\n".join([f"- {title}: {desc}" for title, desc in posts if title])

            prompt = f"""Analyze these blog post titles and descriptions from cluster {cluster_id}:

{posts_text}

Please provide a 2-3 sentence summary that captures the main themes, topics, and focus areas of this cluster of blog posts. Be specific about the subject matter and technical domains covered."""

            try:
                # Generate summary using the configured client
                client = get_openai_client()
                response = client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )

                summary = response.choices[0].message.content.strip()

                # Insert summary into database
                cur.execute("""
                    INSERT INTO blog_cluster_summaries (cluster_id, summary)
                    VALUES (%s, %s)
                    ON CONFLICT (cluster_id) DO UPDATE SET summary = EXCLUDED.summary
                """, (cluster_id, summary))

                summaries_generated += 1

            except Exception as e:
                print(f"Error generating summary for cluster {cluster_id}: {e}")
                continue

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'summaries_generated': summaries_generated,
            'total_clusters': len(cluster_ids),
            'message': f'Generated {summaries_generated} cluster summaries'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_recommendations():
    """Export recommendations as JSON"""
    try:
        data = request.get_json()

        # Add metadata
        export_data = {
            'export_metadata': {
                'timestamp': '2024-01-01T00:00:00Z',  # You might want to use real timestamp
                'model': EMBEDDING_MODEL,
                'dimensions': EMBEDDING_DIMENSIONS,
                'system': 'Greenplum + pgvector + OpenAI'
            },
            'recommendations': data
        }

        return jsonify(export_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Blog Recommendation Engine - Web UI")
    print("=" * 60)
    print(f"📊 Model: {EMBEDDING_MODEL}")
    print(f"📐 Dimensions: {EMBEDDING_DIMENSIONS}")
    print(f"🗄️  Database: {DB_NAME} @ {GP_HOST}:{GP_PORT}")
    print("=" * 60)
    print("🌐 Starting Flask server...")
    print(f"💡 Open http://localhost:{WEB_PORT} in your browser")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=WEB_PORT)