import psycopg2
from config import *
#from pgvector.psycopg2 import register_vector

# --- OpenAI CLIENT ---
client = get_openai_client()

# --- DB CONNECT ---
conn = psycopg2.connect(get_connection_string())
#register_vector(conn)

# --- FETCH BLOG POSTS WITHOUT EMBEDDINGS ---
cur = conn.cursor()
cur.execute("SELECT id, title, description FROM blog_posts WHERE embedding IS NULL limit 7000;")
rows = cur.fetchall()

print(f"Found {len(rows)} blog posts without embeddings")

# --- GENERATE + UPDATE ---
for row_id, title, desc in rows:
    text = f"{title}. {desc}"  # combine title + description
    print(f"Generate for {text} with model {EMBEDDING_MODEL}")
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    vec = response.data[0].embedding

    cur.execute(
        "UPDATE blog_posts SET embedding = %s WHERE id = %s;",
        (vec, row_id)
    )

conn.commit()
cur.close()
conn.close()
print("✅ Embeddings populated.")
