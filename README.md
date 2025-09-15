# Blog Recommendation Engine with Greenplum + AI

![Blog Recommendation Engine](screenshots/ui-screenshot-1.png)

A sophisticated **content recommendation system** powered by [VMware Tanzu Greenplum](https://tanzu.vmware.com/greenplum), [pgvector](https://github.com/pgvector/pgvector), and AI-generated embeddings. This project demonstrates how to build a complete AI-driven recommendation pipeline with a stunning modern web interface featuring real-time clustering and metallic design.

## 🌟 Features

### 🎨 **Modern Metallic Web Interface**
- **Glass morphism design** with metallic gradients and effects
- **Interactive cluster rating system** with custom metallic sliders
- **Real-time re-clustering** with adjustable parameters (5-25 clusters)
- **Responsive design** that works beautifully on all devices
- **Dark theme** with gold accents and shimmer animations

### 🧠 **AI-Powered Recommendation Engine**
- **Embedding generation** using configurable AI models (OpenAI or local)
- **KMeans clustering** with PL/Python and scikit-learn
- **Vector similarity search** using pgvector for recommendations
- **AI-generated cluster summaries** for better user understanding
- **Personalized preference modeling** based on cluster ratings

### ⚙️ **Advanced Capabilities**
- **Dynamic re-clustering** - Change cluster count and regenerate groupings
- **Configurable embedding dimensions** (supports 768D, 1536D, etc.)
- **Local or cloud AI models** via OpenAI-compatible APIs
- **Export functionality** for recommendations and analytics
- **Comprehensive pre-flight checks** for data integrity

## 🚀 Quick Start

### Prerequisites
- **Greenplum Database 7.x** with pgvector extension
- **Python 3.8+** with virtual environment support
- **AI Model Access** (OpenAI API or local model server)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd blog-recommendations
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment** (edit `.env`):
   ```bash
   # Database Configuration
   GP_HOST=localhost
   GP_PORT=15432
   GP_USER=gpadmin
   DB_NAME=demo

   # AI Model Configuration
   USE_LOCAL_MODELS=true
   LOCAL_API_BASE=http://127.0.0.1:1234/v1
   EMBEDDING_MODEL=text-embedding-nomic-embed-text-v2
   EMBEDDING_DIMENSIONS=768

   # Web Interface
   WEB_PORT=8081
   ```

3. **Run the complete demo**:
   ```bash
   ./run_demo.sh
   ```

## 📊 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw CSV Data │ -> │  Greenplum + AI  │ -> │  Web Interface  │
│   (Blog Posts)  │    │   Processing     │    │   (Metallic UI) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Recommendation  │
                    │     Engine       │
                    └──────────────────┘
```

### Data Flow
1. **Load** → Blog posts imported into Greenplum
2. **Embed** → AI generates vector embeddings for each post
3. **Cluster** → KMeans groups similar content (configurable clusters)
4. **Summarize** → AI creates thematic summaries for each cluster
5. **Recommend** → Vector similarity finds personalized content

## 🎯 Demo Workflow

![Recommendation Workflow](screenshots/ui-screenshot-2.png)

### Step 1: Cluster Analysis
- View AI-generated cluster summaries with sample articles
- Adjust cluster count (5-25) using the metallic slider
- Click "Re-cluster Data" to dynamically reorganize content

### Step 2: Preference Rating
- Rate each cluster from 1-10 using metallic sliders
- Build your personalized preference vector in real-time
- Visual feedback with gold accent colors

### Step 3: AI Recommendations
- Get top 25 most interesting articles for you
- See 25 least relevant articles (for comparison)
- Export results with metadata and system information

## 🛠 Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | Greenplum 7.x | Scalable data warehouse |
| **Vector Search** | pgvector | Similarity search & storage |
| **Clustering** | PL/Python + scikit-learn | KMeans clustering |
| **AI Models** | OpenAI API / Local LLMs | Embeddings & summaries |
| **Backend** | Flask + Python | REST API server |
| **Frontend** | HTML/CSS/JS + Tailwind | Metallic web interface |
| **Config** | Environment variables | Flexible configuration |

## 📁 Project Structure

```
blog-recommendations/
├── 🌐 web_app.py              # Flask web server with REST API
├── ⚙️ config.py               # Configuration management
├── 🔧 run_demo.sh             # One-click demo launcher
├── 📊 genvec.py               # Embedding generation
├── 🎯 cluster.sql             # KMeans clustering query
├── 📝 summarize.py            # AI cluster summaries
├── 🗄️ load_data.sh            # Data pipeline setup
├── 🔧 create_kmeans_function.sql  # PL/Python KMeans UDF
├── 📋 generate_schema.py      # Dynamic schema generation
├── 🌐 templates/
│   └── index.html             # Metallic UI template
├── 📱 static/
│   └── js/app.js              # Frontend JavaScript
├── 📜 scripts/                # Utility scripts
└── 📸 screenshots/            # Demo screenshots
```

## ⚡ Advanced Usage

### Re-clustering Data
```javascript
// Via Web UI - adjust slider and click "Re-cluster Data"
// Or via API:
curl -X POST http://localhost:8081/api/recluster \
  -H "Content-Type: application/json" \
  -d '{"num_clusters": 20}'
```

### Custom Embedding Models
```bash
# In .env file:
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSIONS=3072
```

### Batch Processing
```bash
# Complete pipeline:
bash load_data.sh              # Load CSV data
python genvec.py               # Generate embeddings
psql -f create_kmeans_function.sql demo  # Create KMeans function
psql -f cluster.sql demo       # Run clustering
python summarize.py            # Generate summaries
python web_app.py              # Start web interface
```

## 🔧 Configuration Options

### Database Settings
- `GP_HOST`, `GP_PORT`, `GP_USER` - Database connection parameters
- `DB_NAME` - Target database name

### AI Model Settings
- `USE_LOCAL_MODELS` - Toggle between local and cloud AI models
- `EMBEDDING_MODEL` - Model for generating embeddings
- `EMBEDDING_DIMENSIONS` - Vector dimensions (768, 1536, 3072, etc.)
- `CHAT_MODEL` - Model for generating cluster summaries

### Web Interface
- `WEB_PORT` - Flask server port (default: 8081)
- `CLUSTER_SAMPLE_SIZE` - Articles per cluster for summaries

## 🎨 UI Customization

The metallic theme uses CSS custom properties for easy customization:

```css
/* Metallic color scheme */
.metallic-bg { /* Silver gradients */ }
.metallic-blue { /* Blue metallic accents */ }
.metallic-gold { /* Gold highlights */ }
.glass-panel { /* Glassmorphism effects */ }
```

## 📈 Performance & Scaling

- **Vector Search**: pgvector provides fast similarity search at scale
- **Clustering**: PL/Python enables in-database ML processing
- **Caching**: Configuration display caching for faster startups
- **Responsive**: UI adapts from mobile to large displays

## 💡 Example Use Cases

- **Media & Publishing**: Personalized article feeds and content discovery
- **E-commerce**: Product recommendations based on user behavior
- **Education**: Adaptive learning content recommendations
- **Research**: Academic paper recommendation systems
- **Corporate**: Knowledge base content suggestion

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Test** with your Greenplum setup
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Submit** a pull request

## 📝 License

This project demonstrates advanced Greenplum + AI capabilities for educational and commercial use.

## 🔗 Links

- [Greenplum Documentation](https://docs.vmware.com/en/VMware-Tanzu-Greenplum/index.html)
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Built with ❤️ using Greenplum, pgvector, and modern web technologies**

*Showcasing the power of in-database AI and vector search for next-generation recommendation systems*
