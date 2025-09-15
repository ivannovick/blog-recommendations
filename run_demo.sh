#!/bin/bash

echo "🚀 Blog Recommendation Engine Demo"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
fi

echo ""
echo "📋 Pre-flight checks:"

# Check if database is accessible
echo -n "🗄️  Database connection: "
if python3 -c "import sys; sys.stdout = open('/dev/null', 'w'); from config import *; import psycopg2; psycopg2.connect(get_connection_string()).close()" 2>/dev/null; then
    echo "✅ Connected"
else
    echo "❌ Failed"
    echo "   Please ensure Greenplum is running and configuration is correct."
    exit 1
fi

# Check if data is loaded
echo -n "📊 Blog posts loaded: "
POST_COUNT=$(python3 -c "import sys; sys.stdout = open('/dev/null', 'w'); from config import *; sys.stdout = sys.__stdout__; import psycopg2; conn=psycopg2.connect(get_connection_string()); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM blog_posts'); print(cur.fetchone()[0]); conn.close()" 2>/dev/null)
if [ "$POST_COUNT" -gt 0 ]; then
    echo "✅ $POST_COUNT posts"
else
    echo "❌ No data found"
    echo "   Please run: bash load_data.sh"
    exit 1
fi

# Check if embeddings exist
echo -n "🔢 Embeddings generated: "
EMB_COUNT=$(python3 -c "import sys; sys.stdout = open('/dev/null', 'w'); from config import *; sys.stdout = sys.__stdout__; import psycopg2; conn=psycopg2.connect(get_connection_string()); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM blog_posts WHERE embedding IS NOT NULL'); print(cur.fetchone()[0]); conn.close()" 2>/dev/null)
if [ "$EMB_COUNT" -gt 0 ]; then
    echo "✅ $EMB_COUNT embeddings"
else
    echo "❌ No embeddings found"
    echo "   Please run: python3 genvec.py"
    exit 1
fi

# Check if clustering is done
echo -n "🎯 Clustering completed: "
CLUSTER_COUNT=$(python3 -c "import sys; sys.stdout = open('/dev/null', 'w'); from config import *; sys.stdout = sys.__stdout__; import psycopg2; conn=psycopg2.connect(get_connection_string()); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM blog_posts WHERE cluster_id IS NOT NULL'); print(cur.fetchone()[0]); conn.close()" 2>/dev/null)
if [ "$CLUSTER_COUNT" -gt 0 ]; then
    echo "✅ $CLUSTER_COUNT posts clustered"
else
    echo "❌ No clustering found"
    echo "   Please run: psql -f create_kmeans_function.sql demo && psql -f cluster.sql demo"
    exit 1
fi

# Check if summaries exist
echo -n "📝 Cluster summaries: "
SUMMARY_COUNT=$(python3 -c "import sys; sys.stdout = open('/dev/null', 'w'); from config import *; sys.stdout = sys.__stdout__; import psycopg2; conn=psycopg2.connect(get_connection_string()); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM blog_cluster_summaries'); print(cur.fetchone()[0]); conn.close()" 2>/dev/null)
if [ "$SUMMARY_COUNT" -gt 0 ]; then
    echo "✅ $SUMMARY_COUNT summaries"
else
    echo "❌ No summaries found"
    echo "   Please run: python3 summarize.py"
    exit 1
fi

echo ""
echo "🌐 Starting web application..."

# Get the configured port
WEB_PORT=$(python3 -c "import sys; sys.stdout = open('/dev/null', 'w'); from config import *; sys.stdout = sys.__stdout__; print(WEB_PORT)" 2>/dev/null)

echo "💡 Open http://localhost:${WEB_PORT} in your browser"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the web app
python3 web_app.py