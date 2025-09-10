import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from pgvector import Vector   # correct import

# --- DB CONFIG ---
DBNAME = "demo"
USER   = "gpadmin"
HOST   = "localhost"

# --- DB CONNECT ---
conn = psycopg2.connect(f"dbname={DBNAME} user={USER} host={HOST}")
register_vector(conn)
cur = conn.cursor()

# Step 1: Fetch cluster summaries and representative vectors
cur.execute("""
    SELECT c.cluster_id, s.summary, AVG(b.embedding)::vector
    FROM blog_cluster_summaries s
    JOIN blog_posts b ON b.cluster_id = s.cluster_id
    JOIN (SELECT DISTINCT cluster_id FROM blog_cluster_summaries) c ON c.cluster_id = s.cluster_id
    WHERE b.embedding IS NOT NULL
    GROUP BY c.cluster_id, s.summary
    ORDER BY c.cluster_id;
""")
clusters = cur.fetchall()

ratings = []
embeddings = []

# Step 2: Ask user to rate each cluster summary
print("\nRate each cluster summary from 1 (irrelevant) to 10 (very interesting):\n")
for cluster_id, summary, emb in clusters:
    print(f"\nCluster {cluster_id}:\n{summary}\n")

    # Print 5 sample titles from this cluster
    cur.execute("""
        SELECT title
        FROM blog_posts
        WHERE cluster_id = %s
          AND embedding IS NOT NULL
        LIMIT 5;
    """, (cluster_id,))
    samples = cur.fetchall()
    print("Sample titles:")
    for s in samples:
        print(f"  - {s[0]}")

    rating = int(input("\nYour rating for this cluster (1-10): "))
    ratings.append(rating)
    embeddings.append(np.array(emb, dtype=float))

# Step 3: Compute preference vector
ratings = np.array(ratings, dtype=float)
embeddings = np.array(embeddings)
preference_vec = np.average(embeddings, axis=0, weights=ratings)

print("\n✅ Preference vector built from your cluster ratings.")

# Wrap as pgvector.Vector
pref_vec = Vector(preference_vec.tolist())

# Step 4a: Query 25 most similar articles
cur.execute("""
    SELECT id, title, description, cluster_id
    FROM blog_posts
    WHERE embedding IS NOT NULL
    ORDER BY embedding <-> %s ASC
    LIMIT 25;
""", (pref_vec,))

print("\n🎯 Top 25 Most Interesting Articles for You (based on cluster ratings):")
for row in cur.fetchall():
    print(f"- {row[1]} (Cluster {row[3]})")

# Step 4b: Query 25 least similar articles
cur.execute("""
    SELECT id, title, description, cluster_id
    FROM blog_posts
    WHERE embedding IS NOT NULL
    ORDER BY embedding <-> %s DESC
    LIMIT 25;
""", (pref_vec,))

print("\n😴 25 Least Interesting Articles for You (based on cluster ratings):")
for row in cur.fetchall():
    print(f"- {row[1]} (Cluster {row[3]})")

cur.close()
conn.close()
