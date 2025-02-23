 
function getStockData() {
    const ticker = document.getElementById('ticker').value;
    const period = document.getElementById('period').value;
    
    if (!ticker) {
        showError('Please enter a stock ticker');
        return;
    }
    
    
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('error-message').classList.add('hidden');
    document.getElementById('stock-info').classList.add('hidden');
    document.getElementById('chart-container').classList.add('hidden');
    
    
    const formData = new FormData();
    formData.append('ticker', ticker);
    formData.append('period', period);
    
     
    fetch('/get_stock', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loading').classList.add('hidden');
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        
        document.getElementById('current-price').textContent = 
            `$${data.stock_info.current_price.toFixed(2)}`;
        document.getElementById('period-high').textContent = 
            `$${data.stock_info.high.toFixed(2)}`;
        document.getElementById('period-low').textContent = 
            `$${data.stock_info.low.toFixed(2)}`;
        
        
        document.getElementById('stock-chart').src = 
            `data:image/png;base64,${data.plot_data}`;
        
        
        document.getElementById('stock-info').classList.remove('hidden');
        document.getElementById('chart-container').classList.remove('hidden');
    })
    .catch(error => {
        document.getElementById('loading').classList.add('hidden');
        showError('Failed to fetch stock data. Please try again.');
        console.error('Error:', error);
    });
}

function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
}

 
document.getElementById('ticker').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        getStockData();
    }
});