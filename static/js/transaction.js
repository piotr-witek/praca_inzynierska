let selectedRow = null;

function selectTransaction(transactionId) {
    if (selectedRow) {
        selectedRow.classList.remove('selected');
    }
    selectedRow = document.querySelector(`[data-transaction-id="${transactionId}"]`);
    selectedRow.classList.add('selected');

    fetchTransactionDetails(transactionId);
}

function fetchTransactionDetails(transactionId) {
    fetch(`/dashboard/transaction_details/${transactionId}/`)
        .then(response => response.json())
        .then(data => {
            const detailsContainer = document.getElementById('transaction_details');
            const detailsContent = document.getElementById('details-content');
            detailsContainer.style.display = 'block';
            detailsContent.innerHTML = `
                <p><strong>Numer transakcji:</strong> ${data.transaction_id}</p>
                <p><strong>Data:</strong> ${data.transaction_date}</p>
                <p><strong>Kwota:</strong> ${data.total_amount} PLN</p>
                <p><strong>Metoda płatności:</strong> ${data.payment_method}</p>
                <p><strong>Numer zamówienia:</strong> ${data.order_id}</p>
                <p><strong>Numer stolika:</strong> ${data.table_id}</p>
                <p><strong>Status:</strong> ${data.is_completed ? "Zakończona" : "Niezakończona"}</p>
                <h3>Produkty</h3>
                <ul>
                    ${data.items.map(item => `
                        <li>${item.product_name} (${item.quantity} ${item.product_unit}) - 
                            ${item.total_price} PLN</li>
                    `).join('')}
                </ul>
            `;
        })
        .catch(error => console.error('Błąd pobierania szczegółów transakcji:', error));
}

function itemDetail(itemId) {
    // Zmiana lokalizacji na stronę szczegółów produktu
    window.location.href = `/dashboard/transaction_item_details/${itemId}/`;
}


function closeDetails() {
    document.getElementById('transaction_details').style.display = 'none';
}
