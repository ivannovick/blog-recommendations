# Blog Recommendation Engine with Greenplum + AI

This project demonstrates how to build a **content recommendation engine** using [VMware Tanzu Greenplum](https://tanzu.vmware.com/greenplum), [pgvector](https://github.com/pgvector/pgvector), and AI-generated embeddings. The workflow shows how raw text data can be transformed into actionable recommendations through embeddings, clustering, and similarity search — all running at scale inside Greenplum.

## 🚀 Project Overview

We use the [Kaggle Medium Blog Posts dataset](https://www.kaggle.com) as input data. The pipeline:

1. **Data Loading**

   * Load blog post titles and descriptions into Greenplum.

2. **Vector Embeddings**

   * Use OpenAI Python SDK to generate 384-dimensional embeddings for each blog post.
   * Store embeddings in Greenplum with the `pgvector` extension.

3. **Clustering**

   * Run **KMeans clustering** inside Greenplum with PL/Python and `sklearn`.
   * Assign each blog post to one of `k` clusters.
   * Store cluster summaries (generated with ChatGPT) in a `blog_cluster_summaries` table.

4. **User Preference Modeling**

   * Instead of rating random articles, the user rates cluster summaries (1–10).
   * Each cluster has a **centroid vector** (average of all embeddings in the cluster).
   * The preference vector is computed as a weighted average of centroids, weighted by user ratings.

5. **Recommendations**

   * Articles most similar to the preference vector = "most interesting" content.
   * Articles farthest from the preference vector = "least interesting" content.
   * Search is done directly in SQL using `<->` distance operator provided by `pgvector`.

## 🛠️ Components

* **Greenplum Database 7.x** (data warehouse)
* **pgvector** (vector data type and similarity search)
* **PL/Python + scikit-learn** (clustering UDFs)
* **OpenAI API** (embeddings + cluster summarization)
* **Python scripts**

  * `genvec.py` → generate embeddings for blog posts
  * `cluster.sql` → run KMeans clustering in-database
  * `summarize.py` → create cluster summaries with GPT
  * `rec-based-summaries.py` → interactive recommender based on cluster ratings

## 📊 Math Behind Recommendations

* Each blog post = vector `v`.
* Each cluster centroid = mean of vectors in cluster.
* User assigns rating `r` to cluster.
* Weighted combination:

  $$
  \text{Preference Vector} = \frac{\sum_i r_i \cdot c_i}{\sum_i r_i}
  $$

  where `c_i` is the centroid of cluster *i*.
* Recommendation: articles ranked by similarity (cosine/Euclidean) between article vector and preference vector.

## 📋 Demo Flow

1. **Check dataset size**

   ```bash
   wc -l medium_post_titles.csv
   ```

2. **Inspect loaded data**

   ```sql
   SELECT * FROM blog_posts LIMIT 5;
   SELECT COUNT(*) FROM blog_posts;
   ```

3. **Generate embeddings**

   ```bash
   cat genvec.py
   ```

4. **Run clustering**

   ```bash
   psql -f cluster.sql demo
   ```

5. **Summarize clusters**

   ```bash
   python3 summarize.py
   ```

6. **Run recommender**

   ```bash
   python3 rec-based-summaries.py
   ```

7. **Search most / least interesting**

   ```sql
   ORDER BY embedding <-> preference_vector ASC LIMIT 25;
   ORDER BY embedding <-> preference_vector DESC LIMIT 25;
   ```

## 💡 Example Use Cases

* Media & Publishing: personalized article feeds
* Retail: personalized product recommendations
* Healthcare: tailored patient content delivery
* Education: adaptive learning content recommendations

## 📦 Installation Notes

* Requires Greenplum 7.x with `plpython3u` enabled
* Install Python packages inside PL/Python environment:

  * `numpy`, `scikit-learn`
* Install pgvector extension in Greenplum
* Set your `OPENAI_API_KEY` before running scripts

## 🔮 Outcomes

* End-to-end AI-driven content recommendation inside Greenplum
* Scalable clustering + summarization pipeline
* Simple interactive demo for showing the power of AI + SQL integration

---

👉 This README is demo-ready for GitHub. Do you want me to also add a **diagram image placeholder** (e.g., `docs/architecture.png`) so readers can visualize the flow Kaggle → Greenplum → Embeddings → Clustering → Summarization → Recommendation?
