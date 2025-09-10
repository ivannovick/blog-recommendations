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
