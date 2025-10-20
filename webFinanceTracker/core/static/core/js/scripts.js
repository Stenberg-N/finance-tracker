export let selectedTransactions = new Set(JSON.parse(localStorage.getItem('selectedTransactions') || '[]'));

export function formatDateForDisplay(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    const options = { month: 'short', day: 'numeric', year: 'numeric' };
    let formatted = date.toLocaleDateString('en-US', options);

    const month = formatted.split(' ')[0];
    const monthsWithoutDot = ['May', 'Jun', 'Jul'];
    if (!monthsWithoutDot.includes(month)) {
        formatted = formatted.replace(month, month + '.');
    }

    return formatted;
}

export function showImportWindow() {
    const modal = document.getElementById('importModal');
    modal.style.display = 'block';
    modal.classList.add('active');
}

export function closeImportWindow() {
    const modal = document.getElementById('importModal');
    modal.classList.remove('active');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 200);
}

export function showSearchInfoModal() {
    const modal = document.getElementById('searchInfoModal');
    modal.style.display = 'block';
    modal.classList.add('active');
}

export function closeSearchInfoModal() {
    const modal = document.getElementById('searchInfoModal');
    modal.classList.remove('active');
    setTimeout(() => {
            modal.style.display = 'none';
    }, 200);
}

export function toggleExportOptions() {
    const options = document.getElementById('exportBtns');
    if (options.classList.contains('visible')) {
        options.classList.remove('visible');
        options.classList.remove('interactive');
        options.classList.add('hidden');
        setTimeout(() => {
            options.style.display = 'none';
        }, 150);
    } else {
        options.style.display = 'flex';
        options.classList.remove('hidden');
        options.classList.add('visible');
        setTimeout(() => {
            options.classList.add('interactive');
        }, 150)
    }
}

export function updateLocalStorage() {
    localStorage.setItem('selectedTransactions', JSON.stringify(Array.from(selectedTransactions)));
}

export function updateSelectionUI() {
    const count = selectedTransactions.size;
    const selectedCountSpan = document.getElementById('selectedCount');
    const bulkInfoText = document.getElementById('bulkInfoText');
    const bulkActions = document.querySelector('.bulk-actions');
    selectedCountSpan.textContent = count;
    bulkInfoText.textContent = count === 0
        ? 'No transactions selected'
        : `${count} transaction${count > 1 ? 's' : ''} selected`;
    if (bulkActions) {
        bulkActions.style.display = count > 0 ? 'block' : 'none';
    }
}

export function updateTableVisibility() {
    const tableBody = document.querySelector('#transactionsTable tbody');
    const tableContainer = document.getElementById('transactions-table');
    const tableHead = document.querySelector('#transactionsTable thead');
    const pagination = document.getElementById('pagination');
    const bottomPagination = document.getElementById('bottom-pagination');

    if (tableBody && tableBody.children.length === 0) {
        if (tableHead) tableHead.style.display = 'none';
        if (tableContainer) {
            tableContainer.innerHTML = `
                <p>No transactions yet. Add your first one above!</p>
                <img src="${window.staticImages?.wallet || 'static/core/images/wallet.svg'}" alt="Empty wallet" style="width: 100px; opacity: 0.5;">
            `;
            tableContainer.classList.add('empty-state');
            tableContainer.classList.remove('table-container');
        }
        if (pagination) pagination.style.display = 'none';
        if (bottomPagination) bottomPagination.style.display = 'none';
    } else if (tableBody && tableBody.children.length > 0) {
        if (pagination) pagination.style.display = 'flex';
        if (bottomPagination) bottomPagination.style.display = 'flex';
        tableContainer.classList.remove('empty-state');
        tableContainer.classList.add('table-container');
    }
}

export function updateTableAnalytics() {
    fetch(window.urls.analytics, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const analytics = document.querySelector('#table-analytics');
        if (analytics) {
            analytics.innerHTML = `
            <span>Transactions: ${data.transactions_count}</span>
            <span>Expenses: ${data.expense_count}</span>
            <span>Income: ${data.income_count}</span>
            `;
        }
    })
    .catch(error => {
        console.error('Error updating analytis:', error);
        showMessage('Error updating analytics', 'error');
    });
}

export function fetchFeedMessages() {
    fetch(window.urls.feedMessages, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const feedList = document.getElementById('feed-messages');
        if (feedList) {
            feedList.innerHTML = '';
            data.feed.forEach(message => {
                const li = document.createElement('li');
                li.innerHTML = message;
                feedList.appendChild(li);
            });
        }
    })
    .catch(error => {
        console.error('Error fetching feed messages:', error);
        showMessage('Failed to load spending insights', 'error');
    });
}

export function showMessage(message, type = 'success') {
    const msgDiv = document.createElement('div');
    msgDiv.textContent = message;
    msgDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 4px;
        color: white;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        z-index: 1000;
        transition: opacity 0.3s ease;
    `;
    document.body.appendChild(msgDiv);
    setTimeout(() => {
        msgDiv.style.opacity = '0';
        setTimeout(() => msgDiv.remove(), 300);
    }, 3000);
}

export function bindSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const rowCheckboxes = document.querySelectorAll('.row-checkbox');
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                const id = parseInt(checkbox.value);
                if (this.checked) {
                    selectedTransactions.add(id);
                } else {
                    selectedTransactions.delete(id);
                }
            });
            updateLocalStorage();
            updateSelectionUI();
        });
    }
}

export function bindRowCheckboxes() {
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    if (rowCheckboxes) {
        rowCheckboxes.forEach(checkbox => {
            const id = parseInt(checkbox.value);
            if (selectedTransactions.has(id)) {
                checkbox.checked = true;
            }
            checkbox.removeEventListener('change', checkbox._changeHandler);
            checkbox._changeHandler = function() {
                const id = parseInt(this.value);
                if (this.checked) {
                    selectedTransactions.add(id);
                } else {
                    selectedTransactions.delete(id);
                }
                updateLocalStorage();
                updateSelectionUI();
            };
            checkbox.addEventListener('change', checkbox._changeHandler);
        });
    }
}

export function bindDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-btn')
    if (deleteButtons) {
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const transactionId = this.dataset.id;
                const row = this.closest('tr');

                if (confirm('Are you sure you want to delete this transaction?')) {
                    fetch(`/delete/${transactionId}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            row.style.transition = 'all 0.3s ease';
                            row.style.opacity = '0';
                            row.style.transform = 'translateX(-50px)';
                            setTimeout(() => {
                                row.remove();
                                updateTableVisibility();
                            }, 300);

                            selectedTransactions.delete(parseInt(transactionId));
                            updateLocalStorage();
                            updateSelectionUI();
                            updateTableAnalytics();
                            fetchFeedMessages();
                            showMessage(data.message, 'success');
                        } else {
                            alert('Error deleting transaction: ' + (data.error || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Network error. Please try again.');
                    });
                }
            });
        });
    }
}

export function bindSelectAllBtn() {
    const selectAllBtn = document.getElementById('selectAllBtn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            const rowCheckboxes = document.querySelectorAll('.row-checkbox');
            rowCheckboxes.forEach(checkbox => {
                const id = parseInt(checkbox.value);
                checkbox.checked = true;
                selectedTransactions.add(id);
            });
            const selectAllCheckbox = document.getElementById('selectAllCheckbox');
            if (selectAllCheckbox) selectAllCheckbox.checked = true;
            updateLocalStorage();
            updateSelectionUI();
        });
    }
}

export function bindClearSelectionBtn() {
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', () => {
            const rowCheckboxes = document.querySelectorAll('.row-checkbox');
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            const selectAllCheckbox = document.getElementById('selectAllCheckbox');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
            selectedTransactions.clear();
            updateLocalStorage();
            updateSelectionUI();
        });
    }
}

export function bindBulkDeleteBtn() {
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', () => {
            const selectedIds = Array.from(selectedTransactions);
            if (selectedIds.length === 0) return;

            if (confirm(`Are you sure you want to delete ${selectedIds.length} transaction(s)?`)) {
                const formData = new URLSearchParams();
                selectedIds.forEach(id => formData.append('transaction_ids', id));

                fetch('/bulk-delete/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData.toString()
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        selectedIds.forEach(id => {
                            const row = document.querySelector(`tr[data-transaction-id="${id}"]`);
                            if (row) {
                                row.style.transition = 'all 0.3s ease';
                                row.style.opacity = '0';
                                row.style.transform = 'translateX(-50px)';
                                setTimeout(() => {
                                    row.remove();
                                    updateTableVisibility();
                                }, 300);
                            }
                        });
                        selectedTransactions.clear();
                        updateLocalStorage();
                        updateSelectionUI();
                        updateTableVisibility();
                        updateTableAnalytics();
                        fetchFeedMessages();
                        showMessage(data.message, 'success');
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Network error. Please try again.');
                });
            }
        });
    }
}

export function bindDeleteAllBtn() {
    const deleteAllBtn = document.getElementById('deleteAllBtn');
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete ALL transactions? This action cannot be undone.')) {
                const formData = new URLSearchParams();
                formData.append('delete_all', 'true');

                fetch('/bulk-delete/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: formData.toString()
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const tableBody = document.querySelector('#transactionsTable tbody');
                        if (tableBody) {
                            tableBody.innerHTML = '';
                        }
                        selectedTransactions.clear();
                        updateLocalStorage();
                        updateSelectionUI();
                        updateTableVisibility();
                        updateTableAnalytics();
                        fetchFeedMessages();
                        showMessage(data.message, 'success');
                    } else {
                        alert('Error: ' + (data.error || 'Failed to delete transactions'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Network error. Please try again.');
                });
            }
        });
    }
}