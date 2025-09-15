#!/bin/bash

echo "📥 Downloading Medium Blog Posts Dataset..."
echo "=========================================="

# Check if file already exists
if [ -f "medium_post_titles.csv" ]; then
    echo "✅ Dataset already exists: medium_post_titles.csv"
    echo "   File size: $(ls -lh medium_post_titles.csv | awk '{print $5}')"
    echo "   Records: $(wc -l < medium_post_titles.csv)"
    exit 0
fi

# Download the dataset
echo "🌐 Downloading from Kaggle storage..."
curl -o medium_data.csv.zip "https://storage.googleapis.com/kaggle-data-sets/748442/1294572/compressed/medium_data.csv.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20250915%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20250915T195945Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=2641e2acbb04a08f983895bca92680cf78ecc5a4cb273a5b78d249e3b8a780e7da9481fd482a56947908916fdaa3f66dca87644ebc4f3d20a93d16ba18ecd865a60db000af100e0c328a7f028dc30700c23a9fccc34027d187402393331624ca3e45fc5b9d64cdf9dbe84f7774e0bdfcbbff28f1dd12ee662ff112d0fc082776d8b5b57cf5f69892887b03a71a742565f8d79c7149cedb9530e96a4c9bab8ec051d9505105b7c56da4ba145bcea0f9df48e80dae9f6c0e241fe741a119f9c01206974f8c36a5c123be324428df89be0f0024ea7d52e374409e15529a75ae4e70da7ee756a18b3eb8da6b18a9abb3b5515c8afffa81c753301a711947a4005107"

if [ $? -ne 0 ]; then
    echo "❌ Download failed. Please check your internet connection."
    exit 1
fi

echo "📦 Extracting dataset..."
unzip -q medium_data.csv.zip

if [ $? -ne 0 ]; then
    echo "❌ Extraction failed. The download may be corrupted."
    rm -f medium_data.csv.zip
    exit 1
fi

echo "📝 Renaming to expected filename..."
mv medium_data.csv medium_post_titles.csv

echo "🧹 Cleaning up..."
rm medium_data.csv.zip

echo ""
echo "✅ Dataset download complete!"
echo "   File: medium_post_titles.csv"
echo "   Size: $(ls -lh medium_post_titles.csv | awk '{print $5}')"
echo "   Records: $(wc -l < medium_post_titles.csv)"
echo ""
echo "🚀 You can now run: ./run_demo.sh"