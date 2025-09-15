import psycopg2
from config import *

# --- CONNECT DB ---
conn = psycopg2.connect(get_connection_string())
cur = conn.cursor()

# 1. Get all cluster summaries ordered by cluster_id
cur.execute("""
    SELECT cluster_id, summary
    FROM blog_cluster_summaries
    ORDER BY cluster_id;
""")
clusters = cur.fetchall()

for cid, summary in clusters:
    print("=" * 80)
    print(f"Cluster {cid}")
    print("-" * 80)
    print(f"Summary:\n{summary}\n")

    # 2. Fetch 5 random samples from this cluster
    cur.execute("""
        SELECT title, description
        FROM blog_posts
        WHERE cluster_id = %s
        ORDER BY random()
        LIMIT 5;
    """, (cid,))
    samples = cur.fetchall()

    print("Sample Posts:")
    for title, desc in samples:
        print(f"- {title}: {desc}")
    print("\n")

cur.close()
conn.close()
