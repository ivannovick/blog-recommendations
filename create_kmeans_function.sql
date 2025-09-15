-- Create the kmeans_assign PL/Python function for clustering
-- This function takes an array of vectors and performs KMeans clustering using scikit-learn

DROP FUNCTION IF EXISTS kmeans_assign(float8[][], integer, integer);

CREATE OR REPLACE FUNCTION kmeans_assign(
    vectors float8[][],      -- Array of vectors (each vector is a float8[])
    k integer,              -- Number of clusters
    max_iter integer        -- Maximum iterations for KMeans
)
RETURNS integer[]           -- Returns array of cluster assignments
AS $$
    import numpy as np
    from sklearn.cluster import KMeans

    # Convert the PostgreSQL array to numpy array
    # vectors is a list of lists at this point
    X = np.array(vectors)

    # Create and fit KMeans model
    kmeans = KMeans(
        n_clusters=k,
        max_iter=max_iter,
        random_state=42,  # For reproducibility
        n_init=10         # Number of times KMeans runs with different centroid seeds
    )

    # Fit the model and get cluster assignments
    cluster_labels = kmeans.fit_predict(X)

    # Convert numpy array to Python list for PostgreSQL
    return cluster_labels.tolist()

$$ LANGUAGE plpython3u;

-- Grant execute permission to current user
GRANT EXECUTE ON FUNCTION kmeans_assign(float8[][], integer, integer) TO PUBLIC;

-- Optional: Test the function with a simple example
-- SELECT kmeans_assign(ARRAY[
--     ARRAY[1.0, 2.0]::float8[],
--     ARRAY[1.1, 2.1]::float8[],
--     ARRAY[5.0, 6.0]::float8[],
--     ARRAY[5.1, 6.1]::float8[]
-- ]::float8[][], 2, 100);