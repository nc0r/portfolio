function showMessage(message, type = 'info') {
    let container = document.getElementById('messageContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'messageContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    container.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

function refreshStats() { window.location.reload(); }

function exportData() {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "ID,Name,Phone,Service,Date,Time,User ID,Created At\n";
    const table = document.querySelector('table');
    if (table) {
        table.querySelectorAll('tbody tr').forEach(row => {
            const cells = row.querySelectorAll('td');
            csvContent += Array.from(cells).map(cell => cell.textContent.trim()).join(',') + "\n";
        });
    }
    const link = document.createElement("a");
    link.setAttribute("href", encodeURI(csvContent));
    link.setAttribute("download", `barberflow_bookings_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showMessage('Data exported successfully', 'success');
}
