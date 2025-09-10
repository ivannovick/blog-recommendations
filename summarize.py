import psycopg2
import os
import openai
from datetime import datetime

# --- CONFIG ---
DBNAME   = "demo"
USER     = "gpadmin"
HOST     = "localhost"
MODEL    = "gpt-4o-mini"  # fast + cheap for summarization
CLUSTER_SAMPLE_SIZE = 40

openai.api_key = "YOUR_OPENAI_API_KEY"
# Pull API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set!")

# --- CONNECT DB ---
conn = psycopg2.connect(f"dbname={DBNAME} user={USER} host={HOST}")
cur = conn.cursor()

# 1. Get cluster IDs
cur.execute("SELECT DISTINCT cluster_id FROM blog_posts WHERE cluster_id IS NOT NULL;")
cluster_ids = [r[0] for r in cur.fetchall()]

for cid in cluster_ids:
    print(f"Summarizing cluster {cid}...")

    # 2. Fetch 40 sample titles+descriptions
    cur.execute(f"""
        WITH ranked AS (
            SELECT title, description,
                   ROW_NUMBER() OVER (ORDER BY random()) AS rn
            FROM blog_posts
            WHERE cluster_id = %s
        )
        SELECT title, description FROM ranked WHERE rn <= %s;
    """, (cid, CLUSTER_SAMPLE_SIZE))
    rows = cur.fetchall()

    # Build text block
    articles_text = "\n".join([f"- {title}: {desc}" for title, desc in rows])

    # 3. Send to OpenAI for summarization
    prompt = f"""
    Here are ~40 article titles and descriptions from one cluster of blog posts.
    Summarize the overall theme of this cluster in 4–6 sentences.
    Articles:
    {articles_text}
    """

    response = openai.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    summary = response.choices[0].message.content.strip()

    # 4. Insert into summaries table
    cur.execute("""
        INSERT INTO blog_cluster_summaries (cluster_id, summary, generated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (cluster_id) DO UPDATE SET
            summary = EXCLUDED.summary,
            generated_at = EXCLUDED.generated_at;
    """, (cid, summary, datetime.now()))

    conn.commit()
    print(f"Cluster {cid} summary saved.")

cur.close()
conn.close()
