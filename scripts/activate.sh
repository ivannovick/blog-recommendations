# Convenience script to activate virtual environment
# Usage: source activate.sh

source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "💡 Run 'deactivate' to exit the virtual environment"
echo ""
echo "Available scripts:"
echo "  python genvec.py           - Generate embeddings for blog posts"
echo "  python summarize.py        - Generate cluster summaries"
echo "  python summariesprint.py   - Print all cluster summaries"
echo "  python rec-based-summaries.py - Recommendation based summaries"
echo "  ./load_data.sh            - Load data into Greenplum"