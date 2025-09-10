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
[gpadmin@hp34 ~]$ cat cluster.sql
-- KMeans clustering on blog_posts embeddings (k=16)

-- 1. KMeans UDF (already created once — no need to recreate unless changing code)

-- 2. Run clustering on embeddings and update table
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
        SELECT unnest(kmeans_assign(all_vecs, 16, 100)) AS cluster_id,
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
WHERE p.id = m.id;
