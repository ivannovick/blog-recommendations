/**
 * Blog Recommendation Engine - Frontend JavaScript
 * Modern, responsive UI for the Greenplum + AI demo
 */

class RecommendationApp {
    constructor() {
        this.clusters = [];
        this.ratings = {};
        this.currentStep = 1;
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Blog Recommendation Engine...');

        // Load system stats
        await this.loadStats();

        // Load clusters
        await this.loadClusters();

        // Setup event listeners
        this.setupEventListeners();
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();

            if (stats.error) {
                throw new Error(stats.error);
            }

            // Update stats display
            const statsContainer = document.getElementById('system-stats');
            statsContainer.innerHTML = `
                <div class="flex items-center">
                    <span class="font-medium">${stats.total_posts.toLocaleString()}</span>
                    <span class="ml-1">blog posts</span>
                </div>
                <div class="flex items-center">
                    <span class="font-medium">${stats.num_clusters}</span>
                    <span class="ml-1">AI clusters</span>
                </div>
                <div class="flex items-center">
                    <span class="font-medium">${stats.embedding_dimensions}D</span>
                    <span class="ml-1">embeddings</span>
                </div>
                <div class="flex items-center">
                    <span class="font-medium">${stats.embedding_model}</span>
                </div>
            `;

            console.log('📊 Stats loaded:', stats);
        } catch (error) {
            console.error('❌ Error loading stats:', error);
            this.showError('Failed to load system statistics');
        }
    }

    async loadClusters() {
        try {
            const response = await fetch('/api/clusters');
            this.clusters = await response.json();

            if (this.clusters.error) {
                throw new Error(this.clusters.error);
            }

            console.log(`📚 Loaded ${this.clusters.length} clusters`);
            this.renderClusters();

        } catch (error) {
            console.error('❌ Error loading clusters:', error);
            this.showError('Failed to load content clusters');
        }
    }

    renderClusters() {
        const container = document.getElementById('cluster-container');
        const loading = document.getElementById('loading-clusters');

        loading.classList.add('hidden');
        container.classList.remove('hidden');

        container.innerHTML = this.clusters.map(cluster => `
            <div class="cluster-card glass-card rounded-2xl p-6">
                <div class="mb-4">
                    <div class="flex items-center justify-between mb-3">
                        <span class="inline-flex items-center metallic-blue px-3 py-1 rounded-full text-sm font-medium text-white shadow-lg">
                            Cluster ${cluster.cluster_id}
                        </span>
                        <span class="text-sm text-metallic-secondary">${cluster.size} posts</span>
                    </div>
                    <h3 class="text-lg font-semibold text-metallic mb-3 leading-tight">
                        ${cluster.summary}
                    </h3>
                </div>

                <div class="mb-4">
                    <h4 class="text-sm font-medium text-metallic-secondary mb-2">Sample articles:</h4>
                    <div class="space-y-1">
                        ${cluster.sample_posts.slice(0, 3).map(post => `
                            <div class="text-sm text-metallic-secondary truncate" title="${post.title}">
                                • ${post.title}
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <label class="text-sm font-medium text-metallic">Interest Level:</label>
                        <span id="rating-display-${cluster.cluster_id}" class="text-lg font-bold text-metallic-accent">5</span>
                    </div>
                    <div class="relative">
                        <input
                            type="range"
                            id="rating-${cluster.cluster_id}"
                            min="1"
                            max="10"
                            value="5"
                            class="w-full cursor-pointer slider"
                            data-cluster-id="${cluster.cluster_id}"
                        >
                        <div class="flex justify-between text-xs text-metallic-secondary mt-1">
                            <span>Not interested</span>
                            <span>Very interested</span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Show generate button
        document.getElementById('generate-section').classList.remove('hidden');

        // Add slider event listeners
        this.setupSliders();
    }

    setupSliders() {
        const sliders = document.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            slider.addEventListener('input', (e) => {
                const clusterId = e.target.dataset.clusterId;
                const value = e.target.value;

                // Update display
                document.getElementById(`rating-display-${clusterId}`).textContent = value;

                // Store rating
                this.ratings[clusterId] = parseInt(value);

                console.log(`📊 Cluster ${clusterId} rated: ${value}`);
            });
        });

        // Initialize default ratings
        this.clusters.forEach(cluster => {
            this.ratings[cluster.cluster_id] = 5;
        });
    }

    setupEventListeners() {
        // Cluster count slider
        const clusterSlider = document.getElementById('cluster-count');
        const clusterDisplay = document.getElementById('cluster-count-display');

        clusterSlider.addEventListener('input', (e) => {
            clusterDisplay.textContent = e.target.value;
        });

        // Re-cluster button
        document.getElementById('recluster-btn').addEventListener('click', () => {
            this.reclusterData();
        });

        // Generate recommendations button
        document.getElementById('generate-btn').addEventListener('click', () => {
            this.generateRecommendations();
        });

        // Start over button
        document.getElementById('start-over-btn').addEventListener('click', () => {
            this.startOver();
        });

        // Export button
        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportResults();
        });
    }

    async reclusterData() {
        try {
            const numClusters = parseInt(document.getElementById('cluster-count').value);
            const reclusterBtn = document.getElementById('recluster-btn');

            console.log(`🔄 Re-clustering data with ${numClusters} clusters...`);

            // Disable button and show loading state
            reclusterBtn.disabled = true;
            reclusterBtn.innerHTML = '⏳ Clustering...';

            // Show processing message
            this.showProcessingMessage('Re-clustering data with new parameters...');

            // Call re-clustering API
            const response = await fetch('/api/recluster', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ num_clusters: numClusters })
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            console.log('✅ Re-clustering completed:', result);

            // Generate new summaries
            this.showProcessingMessage('Generating AI summaries for new clusters...');

            const summariesResponse = await fetch('/api/generate_summaries', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const summariesResult = await summariesResponse.json();

            if (summariesResult.error) {
                console.warn('⚠️ Summaries generation failed:', summariesResult.error);
            } else {
                console.log('✅ Summaries generated:', summariesResult);
            }

            // Reload clusters
            await this.loadClusters();

            // Reset to step 1
            this.showStep(1);

            // Re-enable button
            reclusterBtn.disabled = false;
            reclusterBtn.innerHTML = '🔄 Re-cluster Data';

            this.showSuccess(`Successfully re-clustered into ${numClusters} clusters!`);

        } catch (error) {
            console.error('❌ Error re-clustering:', error);
            this.showError('Failed to re-cluster data: ' + error.message);

            // Re-enable button
            const reclusterBtn = document.getElementById('recluster-btn');
            reclusterBtn.disabled = false;
            reclusterBtn.innerHTML = '🔄 Re-cluster Data';
        }
    }

    showProcessingMessage(message) {
        // Create or update processing modal
        let modal = document.getElementById('processing-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'processing-modal';
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="glass-panel rounded-2xl p-8 max-w-md mx-4 text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-metallic-accent mx-auto mb-4 shimmer"></div>
                <h3 class="text-xl font-bold text-metallic mb-2">Processing</h3>
                <p class="text-metallic-secondary">${message}</p>
            </div>
        `;

        modal.style.display = 'flex';
    }

    hideProcessingMessage() {
        const modal = document.getElementById('processing-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    showSuccess(message) {
        // Create success notification
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 glass-panel text-metallic px-6 py-4 rounded-xl shadow-lg z-50 border border-green-500';
        successDiv.innerHTML = `
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                <span>${message}</span>
                <button class="ml-4 text-metallic hover:text-metallic-accent" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        document.body.appendChild(successDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (successDiv.parentElement) {
                successDiv.remove();
            }
        }, 5000);

        // Hide processing modal
        this.hideProcessingMessage();
    }

    async generateRecommendations() {
        try {
            console.log('🤖 Generating recommendations with ratings:', this.ratings);

            // Show processing step
            this.showStep(2);

            // Simulate processing time for better UX
            setTimeout(async () => {
                const response = await fetch('/api/recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ ratings: this.ratings })
                });

                const results = await response.json();

                if (results.error) {
                    throw new Error(results.error);
                }

                console.log('✅ Recommendations generated:', results);
                this.renderRecommendations(results);
                this.showStep(3);

            }, 2000); // 2 second processing animation

        } catch (error) {
            console.error('❌ Error generating recommendations:', error);
            this.showError('Failed to generate recommendations');
            this.showStep(1);
        }
    }

    renderRecommendations(results) {
        // Render preference stats
        const statsContainer = document.getElementById('preference-stats');
        const stats = results.preference_stats;

        statsContainer.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="text-center">
                    <div class="text-3xl font-bold text-blue-600">${stats.average_rating.toFixed(1)}</div>
                    <div class="text-sm text-gray-600">Average Interest Rating</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-purple-600">${stats.total_clusters_rated}</div>
                    <div class="text-sm text-gray-600">Clusters Evaluated</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-green-600">${results.most_interesting.length}</div>
                    <div class="text-sm text-gray-600">Recommendations Found</div>
                </div>
            </div>
        `;

        // Render most interesting
        const mostContainer = document.getElementById('most-interesting-container');
        mostContainer.innerHTML = results.most_interesting.map((article, index) => `
            <div class="recommendation-card bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4">
                <div class="flex items-start justify-between mb-2">
                    <span class="inline-flex items-center bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                        #${index + 1}
                    </span>
                    <span class="text-xs text-gray-500">Cluster ${article.cluster_id}</span>
                </div>
                <h4 class="font-semibold text-gray-900 mb-2 leading-tight">${article.title}</h4>
                <p class="text-sm text-gray-600 leading-relaxed">${article.description || 'No description available'}</p>
            </div>
        `).join('');

        // Render least interesting
        const leastContainer = document.getElementById('least-interesting-container');
        leastContainer.innerHTML = results.least_interesting.map((article, index) => `
            <div class="recommendation-card bg-gradient-to-r from-red-50 to-rose-50 border border-red-200 rounded-xl p-4">
                <div class="flex items-start justify-between mb-2">
                    <span class="inline-flex items-center bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                        #${index + 1}
                    </span>
                    <span class="text-xs text-gray-500">Cluster ${article.cluster_id}</span>
                </div>
                <h4 class="font-semibold text-gray-900 mb-2 leading-tight">${article.title}</h4>
                <p class="text-sm text-gray-600 leading-relaxed">${article.description || 'No description available'}</p>
            </div>
        `).join('');

        // Store results for export
        this.lastResults = results;
    }

    showStep(stepNumber) {
        // Hide all steps
        document.getElementById('step1').classList.add('hidden');
        document.getElementById('step2').classList.add('hidden');
        document.getElementById('step3').classList.add('hidden');

        // Show target step
        document.getElementById(`step${stepNumber}`).classList.remove('hidden');
        this.currentStep = stepNumber;

        console.log(`📍 Showing step ${stepNumber}`);
    }

    startOver() {
        // Reset ratings
        this.ratings = {};

        // Reset sliders
        const sliders = document.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            slider.value = 5;
            const clusterId = slider.dataset.clusterId;
            document.getElementById(`rating-display-${clusterId}`).textContent = '5';
            this.ratings[clusterId] = 5;
        });

        // Show first step
        this.showStep(1);

        console.log('🔄 App reset');
    }

    async exportResults() {
        if (!this.lastResults) {
            this.showError('No results to export');
            return;
        }

        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.lastResults)
            });

            const exportData = await response.json();

            // Download as JSON file
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `blog-recommendations-${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);

            console.log('📁 Results exported');

        } catch (error) {
            console.error('❌ Error exporting results:', error);
            this.showError('Failed to export results');
        }
    }

    showError(message) {
        // Create error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg shadow-lg z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                <span>${message}</span>
                <button class="ml-4 text-red-900 hover:text-red-700" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        document.body.appendChild(errorDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RecommendationApp();
});
