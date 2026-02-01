// Enhanced response formatter
class ResponseFormatter {
    
    static formatResponse(text) {
        // Convert plain text to beautifully formatted HTML
        
        // Step 1: Handle line breaks
        text = text.replace(/\n/g, '<br>');
        
        // Step 2: Format currency (₹1,234.56)
        text = text.replace(/₹(\d+(?:,\d{3})*(?:\.\d{2})?)/g, 
            '<span class="currency">₹$1</span>');
        
        // Step 3: Format percentages (45.2%)
        text = text.replace(/(\d+(?:\.\d+)?%)/g, 
            '<span class="percentage">$1</span>');
        
        // Step 4: Format numbers (50 transactions)
        text = text.replace(/\b(\d+)\s+(transaction|document|item|day|month|year)s?\b/gi, 
            '<span class="number">$1</span> $2s');
        
        // Step 5: Bold important words
        const importantWords = ['total', 'average', 'highest', 'lowest', 'top', 'most', 'increased', 'decreased'];
        importantWords.forEach(word => {
            const regex = new RegExp(`\\b(${word})\\b`, 'gi');
            text = text.replace(regex, '<strong>$1</strong>');
        });
        
        // Step 6: Format lists (numbered or bulleted)
        text = text.replace(/(\d+)\.\s+([^\n<]+)/g, 
            '<div class="list-item"><span class="list-number">$1.</span> $2</div>');
        
        text = text.replace(/[•·]\s+([^\n<]+)/g, 
            '<div class="list-item"><span class="list-bullet">•</span> $1</div>');
        
        // Step 7: Highlight categories
        const categories = ['Food & Dining', 'Transportation', 'Shopping', 'Entertainment', 
                          'Utilities', 'Healthcare', 'Education', 'Travel', 'Insurance'];
        categories.forEach(cat => {
            const regex = new RegExp(`\\b(${cat})\\b`, 'g');
            text = text.replace(regex, '<span class="category-tag">$1</span>');
        });
        
        // Step 8: Format comparison indicators
        text = text.replace(/\b(higher|lower|more|less|increased|decreased)\s+than\b/gi, 
            '<span class="comparison">$1 than</span>');
        
        // Step 9: Emoji enhancement
        text = text.replace(/\b(success|great|excellent)\b/gi, '✅ $1');
        text = text.replace(/\b(warning|caution|alert)\b/gi, '⚠️ $1');
        text = text.replace(/\b(error|failed|problem)\b/gi, '❌ $1');
        
        return text;
    }
    
    static formatSuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) return '';
        
        let html = '<div class="suggestions-box">';
        html += '<p class="suggestions-title">💡 You might want to ask:</p>';
        html += '<div class="suggestions-list">';
        
        suggestions.forEach(suggestion => {
            html += `
                <button class="suggestion-chip" onclick="sendQuickQuery('${suggestion}')">
                    ${suggestion}
                </button>
            `;
        });
        
        html += '</div></div>';
        return html;
    }
    
    static formatDataTable(data) {
        if (!data || typeof data !== 'object') return '';
        
        // Skip certain keys
        const skipKeys = ['suggestions', 'top_items', 'months', 'payment_methods', 'vendors'];
        const entries = Object.entries(data).filter(([key]) => !skipKeys.includes(key));
        
        if (entries.length === 0) return '';
        
        let html = '<div class="data-table-wrapper">';
        html += '<table class="response-data-table">';
        
        entries.forEach(([key, value]) => {
            const label = this.formatLabel(key);
            const formattedValue = this.formatValue(key, value);
            
            html += `
                <tr>
                    <td class="data-label">${label}</td>
                    <td class="data-value">${formattedValue}</td>
                </tr>
            `;
        });
        
        html += '</table></div>';
        return html;
    }
    
    static formatLabel(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }
    
    static formatValue(key, value) {
        if (value === null || value === undefined) return 'N/A';
        
        // Format based on key type
        if (key.includes('amount') || key.includes('total') || key === 'average') {
            return `<span class="currency">₹${parseFloat(value).toLocaleString('en-IN', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}</span>`;
        }
        
        if (key.includes('percentage') || key.includes('change')) {
            const num = parseFloat(value);
            const color = num >= 0 ? '#10B981' : '#EF4444';
            const icon = num >= 0 ? '↑' : '↓';
            return `<span style="color: ${color}; font-weight: 600;">${icon} ${Math.abs(num).toFixed(1)}%</span>`;
        }
        
        if (key.includes('count')) {
            return `<span class="number">${value}</span>`;
        }
        
        if (key === 'period') {
            return `<span class="period">${value}</span>`;
        }
        
        if (key === 'category') {
            return `<span class="category-tag">${value}</span>`;
        }
        
        return value;
    }
    
    static createSummaryCard(title, items) {
        let html = '<div class="summary-card">';
        html += `<h4 class="summary-title">${title}</h4>`;
        html += '<div class="summary-items">';
        
        items.forEach((item, index) => {
            html += `
                <div class="summary-item">
                    <span class="rank">#${index + 1}</span>
                    <span class="item-name">${item.name}</span>
                    <span class="item-value">₹${item.amount.toLocaleString('en-IN')}</span>
                </div>
            `;
        });
        
        html += '</div></div>';
        return html;
    }
}