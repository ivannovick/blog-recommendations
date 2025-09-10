import openai
import psycopg2
#from pgvector.psycopg2 import register_vector

# --- CONFIG ---
DBNAME   = "demo"
USER     = "gpadmin"
HOST     = "localhost"   # or your WSL IP if connecting externally
MODEL    = "text-embedding-3-small"  # 384 dimensions

# --- DB CONNECT ---
conn = psycopg2.connect(f"dbname={DBNAME} user={USER} host={HOST}")
#register_vector(conn)

# --- FETCH BLOG POSTS WITHOUT EMBEDDINGS ---
cur = conn.cursor()
cur.execute("SELECT id, title, description FROM blog_posts WHERE embedding IS NULL limit 1000;")
rows = cur.fetchall()

print(f"Found {len(rows)} blog posts without embeddings")

# --- GENERATE + UPDATE ---
for row_id, title, desc in rows:
    text = f"{title}. {desc}"  # combine title + description
    print(f"Generate for {text} with model {MODEL}")
    response = openai.embeddings.create(model=MODEL, input=text)
    vec = response.data[0].embedding

    cur.execute(
        "UPDATE blog_posts SET embedding = %s WHERE id = %s;",
        (vec, row_id)
    )

conn.commit()
cur.close()
conn.close()
print("✅ Embeddings populated.")
