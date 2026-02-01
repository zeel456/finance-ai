/**
 * Optimized Chart System for Finance AI Assistant
 * Save as: static/js/charts-optimized.js
 * 
 * Features:
 * - Lazy loading
 * - Canvas pooling
 * - Debounced rendering
 * - Memory management
 * - Performance monitoring
 */

class ChartManager {
    constructor() {
        this.charts = new Map();
        this.canvasPool = [];
        this.isChartJsLoaded = false;
        this.loadingPromise = null;
        this.renderQueue = [];
        this.isProcessingQueue = false;
        
        // Performance config
        this.config = {
            maxCharts: 10,
            poolSize: 3,
            debounceDelay: 100,
            animationDuration: 400,
            maxDataPoints: 50
        };
        
        // Performance metrics
        this.metrics = {
            chartsCreated: 0,
            chartsDestroyed: 0,
            averageRenderTime: 0,
            totalRenderTime: 0
        };
    }
    
    /**
     * Lazy load Chart.js library
     */
    async loadChartJs() {
        if (this.isChartJsLoaded) {
            return Promise.resolve();
        }
        
        if (this.loadingPromise) {
            return this.loadingPromise;
        }
        
        this.loadingPromise = new Promise((resolve, reject) => {
            // Check if already loaded
            if (typeof Chart !== 'undefined') {
                this.isChartJsLoaded = true;
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
            script.async = true;
            
            script.onload = () => {
                this.isChartJsLoaded = true;
                console.log('✅ Chart.js loaded');
                resolve();
            };
            
            script.onerror = () => {
                console.error('❌ Failed to load Chart.js');
                reject(new Error('Failed to load Chart.js'));
            };
            
            document.head.appendChild(script);
        });
        
        return this.loadingPromise;
    }
    
    /**
     * Get canvas from pool or create new
     */
    getCanvas(canvasId) {
        let canvas = document.getElementById(canvasId);
        
        if (!canvas) {
            // Try to get from pool
            if (this.canvasPool.length > 0) {
                canvas = this.canvasPool.pop();
                canvas.id = canvasId;
            } else {
                canvas = document.createElement('canvas');
                canvas.id = canvasId;
            }
        }
        
        return canvas;
    }
    
    /**
     * Return canvas to pool
     */
    returnCanvas(canvas) {
        if (this.canvasPool.length < this.config.poolSize) {
            canvas.id = '';
            canvas.width = 0;
            canvas.height = 0;
            this.canvasPool.push(canvas);
        }
    }
    
    /**
     * Optimize chart data
     */
    optimizeData(data, maxPoints = this.config.maxDataPoints) {
        if (!data || !Array.isArray(data)) return data;
        
        if (data.length <= maxPoints) return data;
        
        // Simple downsampling - take every nth point
        const step = Math.ceil(data.length / maxPoints);
        return data.filter((_, index) => index % step === 0);
    }
    
    /**
     * Get optimized chart options
     */
    getOptimizedOptions(baseOptions = {}) {
        return {
            ...baseOptions,
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: this.config.animationDuration,
                easing: 'easeOutQuart'
            },
            plugins: {
                ...baseOptions.plugins,
                legend: {
                    ...baseOptions.plugins?.legend,
                    labels: {
                        ...baseOptions.plugins?.legend?.labels,
                        usePointStyle: true,
                        boxWidth: 8,
                        padding: 8
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                intersect: false,
                axis: 'x'
            },
            // Performance optimizations
            parsing: false,
            normalized: true,
            spanGaps: true
        };
    }
    
    /**
     * Create or update chart with optimization
     */
    async createChart(canvasId, type, data, options = {}) {
        const startTime = performance.now();
        
        try {
            // Ensure Chart.js is loaded
            await this.loadChartJs();
            
            // Get canvas
            const canvas = this.getCanvas(canvasId);
            
            // Destroy existing chart
            if (this.charts.has(canvasId)) {
                this.destroyChart(canvasId);
            }
            
            // Optimize data
            const optimizedData = {
                ...data,
                datasets: data.datasets?.map(dataset => ({
                    ...dataset,
                    data: this.optimizeData(dataset.data)
                }))
            };
            
            // Create chart
            const chart = new Chart(canvas, {
                type: type,
                data: optimizedData,
                options: this.getOptimizedOptions(options)
            });
            
            // Store chart
            this.charts.set(canvasId, chart);
            this.metrics.chartsCreated++;
            
            // Track render time
            const renderTime = performance.now() - startTime;
            this.metrics.totalRenderTime += renderTime;
            this.metrics.averageRenderTime = 
                this.metrics.totalRenderTime / this.metrics.chartsCreated;
            
            console.log(`📊 Chart ${canvasId} rendered in ${renderTime.toFixed(2)}ms`);
            
            return chart;
            
        } catch (error) {
            console.error('Failed to create chart:', error);
            throw error;
        }
    }
    
    /**
     * Destroy chart and clean up
     */
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
            this.metrics.chartsDestroyed++;
            
            // Return canvas to pool
            const canvas = document.getElementById(canvasId);
            if (canvas) {
                this.returnCanvas(canvas);
            }
        }
    }
    
    /**
     * Update chart data efficiently
     */
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        
        if (!chart) {
            console.warn(`Chart ${canvasId} not found`);
            return;
        }
        
        // Update data
        chart.data = {
            ...chart.data,
            ...newData,
            datasets: newData.datasets?.map(dataset => ({
                ...dataset,
                data: this.optimizeData(dataset.data)
            }))
        };
        
        // Update with animation
        chart.update('none'); // Use 'none' for instant update, or 'active' for animation
    }
    
    /**
     * Debounced chart rendering
     */
    debounceRender(canvasId, type, data, options, delay = this.config.debounceDelay) {
        return new Promise((resolve) => {
            // Clear existing timeout
            if (this[`timeout_${canvasId}`]) {
                clearTimeout(this[`timeout_${canvasId}`]);
            }
            
            // Set new timeout
            this[`timeout_${canvasId}`] = setTimeout(async () => {
                const chart = await this.createChart(canvasId, type, data, options);
                resolve(chart);
            }, delay);
        });
    }
    
    /**
     * Queue-based rendering for multiple charts
     */
    async queueRender(canvasId, type, data, options) {
        return new Promise((resolve, reject) => {
            this.renderQueue.push({
                canvasId,
                type,
                data,
                options,
                resolve,
                reject
            });
            
            this.processQueue();
        });
    }
    
    /**
     * Process render queue
     */
    async processQueue() {
        if (this.isProcessingQueue || this.renderQueue.length === 0) {
            return;
        }
        
        this.isProcessingQueue = true;
        
        while (this.renderQueue.length > 0) {
            const task = this.renderQueue.shift();
            
            try {
                const chart = await this.createChart(
                    task.canvasId,
                    task.type,
                    task.data,
                    task.options
                );
                task.resolve(chart);
            } catch (error) {
                task.reject(error);
            }
            
            // Small delay between charts for smooth rendering
            await new Promise(resolve => setTimeout(resolve, 50));
        }
        
        this.isProcessingQueue = false;
    }
    
    /**
     * Destroy all charts
     */
    destroyAll() {
        this.charts.forEach((chart, canvasId) => {
            this.destroyChart(canvasId);
        });
        
        console.log('🗑️ All charts destroyed');
    }
    
    /**
     * Clean up old charts (keep only N most recent)
     */
    cleanup() {
        if (this.charts.size <= this.config.maxCharts) {
            return;
        }
        
        const chartIds = Array.from(this.charts.keys());
        const toRemove = chartIds.slice(0, chartIds.length - this.config.maxCharts);
        
        toRemove.forEach(id => this.destroyChart(id));
        
        console.log(`🧹 Cleaned up ${toRemove.length} old charts`);
    }
    
    /**
     * Get performance metrics
     */
    getMetrics() {
        return {
            ...this.metrics,
            activeCharts: this.charts.size,
            pooledCanvases: this.canvasPool.length,
            queueLength: this.renderQueue.length
        };
    }
    
    /**
     * Print performance report
     */
    printReport() {
        const metrics = this.getMetrics();
        
        console.log('📊 Chart Performance Report:');
        console.log(`   Active charts: ${metrics.activeCharts}`);
        console.log(`   Created: ${metrics.chartsCreated}`);
        console.log(`   Destroyed: ${metrics.chartsDestroyed}`);
        console.log(`   Avg render time: ${metrics.averageRenderTime.toFixed(2)}ms`);
        console.log(`   Canvas pool: ${metrics.pooledCanvases}`);
        console.log(`   Queue: ${metrics.queueLength}`);
    }
}

// Create global instance
const chartManager = new ChartManager();

// Expose to window for global access
window.chartManager = chartManager;

// Auto cleanup on page unload
window.addEventListener('beforeunload', () => {
    chartManager.destroyAll();
});

// Helper functions for backward compatibility
window.createOptimizedChart = (canvasId, type, data, options) => {
    return chartManager.createChart(canvasId, type, data, options);
};

window.updateOptimizedChart = (canvasId, newData) => {
    return chartManager.updateChart(canvasId, newData);
};

window.destroyOptimizedChart = (canvasId) => {
    return chartManager.destroyChart(canvasId);
};

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartManager;
}

console.log('✅ Optimized Chart System loaded');