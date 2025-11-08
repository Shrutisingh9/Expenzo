// Components JavaScript - Form handling and interactions

// Helper function for API calls
async function postJSON(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

async function putJSON(url, data) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

// Show message helper
function showMessage(message, type = 'success') {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message message-${type}`;
  messageDiv.textContent = message;
  messageDiv.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    background: ${type === 'success' ? '#10b981' : '#ef4444'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 3000;
    animation: slideIn 0.3s ease;
  `;
  document.body.appendChild(messageDiv);
  
  setTimeout(() => {
    messageDiv.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => messageDiv.remove(), 300);
  }, 3000);
}

// Form Toggle Function
function initFormToggles() {
  // Show/Hide Add Card Form
  const showAddCardBtn = document.getElementById('showAddCardForm');
  const showAddCardBtnEmpty = document.getElementById('showAddCardFormEmpty');
  const addCardFormContainer = document.getElementById('addCardFormContainer');
  const cancelAddCard = document.getElementById('cancelAddCard');
  
  if (showAddCardBtn && addCardFormContainer) {
    showAddCardBtn.addEventListener('click', () => {
      addCardFormContainer.style.display = 'block';
    });
  }
  
  if (showAddCardBtnEmpty && addCardFormContainer) {
    showAddCardBtnEmpty.addEventListener('click', () => {
      addCardFormContainer.style.display = 'block';
    });
  }
  
  if (cancelAddCard && addCardFormContainer) {
    cancelAddCard.addEventListener('click', () => {
      addCardFormContainer.style.display = 'none';
      const form = document.getElementById('addCardForm');
      if (form) form.reset();
    });
  }
  
  // Show/Hide Add Income Form
  const showAddIncomeBtn = document.getElementById('showAddIncomeForm');
  const addIncomeFormContainer = document.getElementById('addIncomeFormContainer');
  const cancelAddIncome = document.getElementById('cancelAddIncome');
  
  if (showAddIncomeBtn && addIncomeFormContainer) {
    showAddIncomeBtn.addEventListener('click', () => {
      addIncomeFormContainer.style.display = 'block';
      // Set today's date
      const dateInput = document.querySelector('#addIncomeForm input[name="date"]');
      if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
      }
    });
  }
  
  if (cancelAddIncome && addIncomeFormContainer) {
    cancelAddIncome.addEventListener('click', () => {
      addIncomeFormContainer.style.display = 'none';
      const form = document.getElementById('addIncomeForm');
      if (form) form.reset();
    });
  }
  
  // Show/Hide Add Expense Form
  const showAddExpenseBtn = document.getElementById('showAddExpenseForm');
  const addExpenseFormContainer = document.getElementById('addExpenseFormContainer');
  const cancelAddExpense = document.getElementById('cancelAddExpense');
  
  if (showAddExpenseBtn && addExpenseFormContainer) {
    showAddExpenseBtn.addEventListener('click', () => {
      addExpenseFormContainer.style.display = 'block';
      // Set today's date
      const dateInput = document.querySelector('#addExpenseForm input[name="date"]');
      if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
      }
    });
  }
  
  if (cancelAddExpense && addExpenseFormContainer) {
    cancelAddExpense.addEventListener('click', () => {
      addExpenseFormContainer.style.display = 'none';
      const form = document.getElementById('addExpenseForm');
      if (form) form.reset();
    });
  }
  
  // Show/Hide Add Subscription Form
  const showAddSubscriptionBtn = document.getElementById('showAddSubscriptionForm');
  const addSubscriptionFormContainer = document.getElementById('addSubscriptionFormContainer');
  const cancelAddSubscription = document.getElementById('cancelAddSubscription');
  
  if (showAddSubscriptionBtn && addSubscriptionFormContainer) {
    showAddSubscriptionBtn.addEventListener('click', () => {
      addSubscriptionFormContainer.style.display = 'block';
    });
  }
  
  if (cancelAddSubscription && addSubscriptionFormContainer) {
    cancelAddSubscription.addEventListener('click', () => {
      addSubscriptionFormContainer.style.display = 'none';
      const form = document.getElementById('addSubscriptionForm');
      if (form) form.reset();
    });
  }
}

document.addEventListener('DOMContentLoaded', function() {
  // ========== FORM TOGGLES ==========
  initFormToggles();
  
  // ========== CARDS ==========
  const addCardForm = document.getElementById('addCardForm');
  if (addCardForm) {
    addCardForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(addCardForm);
      const data = Object.fromEntries(formData.entries());
      
      // Format card number
      if (data.number) {
        data.number = data.number.replace(/\s/g, '');
      }
      
      try {
      const res = await postJSON('/api/cards', data);
        if (res.success) {
          showMessage('Card added successfully!', 'success');
          addCardForm.reset();
          const addCardFormContainer = document.getElementById('addCardFormContainer');
          if (addCardFormContainer) addCardFormContainer.style.display = 'none';
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(res.error || 'Error adding card', 'error');
        }
      } catch (error) {
        showMessage('Error adding card. Please try again.', 'error');
      }
    });
  }

  // Delete card
  document.querySelectorAll('.btn-delete-card').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      if (!confirm('Are you sure you want to delete this card?')) return;
      
      const id = btn.dataset.id;
      try {
      const res = await fetch(`/api/cards/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          showMessage('Card deleted successfully!', 'success');
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(data.error || 'Error deleting card', 'error');
        }
      } catch (error) {
        showMessage('Error deleting card. Please try again.', 'error');
      }
    });
  });

  // ========== INCOME ==========
  const addIncomeForm = document.getElementById('addIncomeForm');
  if (addIncomeForm) {
    addIncomeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(addIncomeForm);
      const data = Object.fromEntries(formData.entries());
      
      try {
      const res = await postJSON('/api/income', data);
        if (res.success) {
          showMessage('Income added successfully!', 'success');
          addIncomeForm.reset();
          const addIncomeFormContainer = document.getElementById('addIncomeFormContainer');
          if (addIncomeFormContainer) addIncomeFormContainer.style.display = 'none';
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(res.error || 'Error adding income', 'error');
        }
      } catch (error) {
        showMessage('Error adding income. Please try again.', 'error');
      }
    });
  }

  // Delete income
  document.querySelectorAll('.delete-income').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      if (!confirm('Are you sure you want to delete this income record?')) return;
      
      const id = btn.dataset.id;
      try {
        const res = await fetch(`/api/income/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          showMessage('Income deleted successfully!', 'success');
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(data.error || 'Error deleting income', 'error');
        }
      } catch (error) {
        showMessage('Error deleting income. Please try again.', 'error');
      }
    });
  });

  // Income search
  const incomeSearch = document.getElementById('incomeSearch');
  if (incomeSearch) {
    incomeSearch.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const rows = document.querySelectorAll('#incomeTableBody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
      });
    });
  }

  // ========== EXPENSE ==========
  const addExpenseForm = document.getElementById('addExpenseForm');
  if (addExpenseForm) {
    addExpenseForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(addExpenseForm);
      const data = Object.fromEntries(formData.entries());
      
      try {
      const res = await postJSON('/api/expense', data);
        if (res.success) {
          showMessage('Expense added successfully!', 'success');
          addExpenseForm.reset();
          const addExpenseFormContainer = document.getElementById('addExpenseFormContainer');
          if (addExpenseFormContainer) addExpenseFormContainer.style.display = 'none';
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(res.error || 'Error adding expense', 'error');
        }
      } catch (error) {
        showMessage('Error adding expense. Please try again.', 'error');
      }
    });
  }

  // Delete expense
  document.querySelectorAll('.delete-expense').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      if (!confirm('Are you sure you want to delete this expense record?')) return;
      
      const id = btn.dataset.id;
      try {
        const res = await fetch(`/api/expense/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          showMessage('Expense deleted successfully!', 'success');
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(data.error || 'Error deleting expense', 'error');
        }
      } catch (error) {
        showMessage('Error deleting expense. Please try again.', 'error');
      }
    });
  });

  // Expense filters
  const categoryFilter = document.getElementById('categoryFilter');
  const expenseSearch = document.getElementById('expenseSearch');
  
  function filterExpenses() {
    const category = categoryFilter ? categoryFilter.value : '';
    const search = expenseSearch ? expenseSearch.value.toLowerCase() : '';
    const rows = document.querySelectorAll('#expenseTableBody tr');
    
    rows.forEach(row => {
      const rowCategory = row.dataset.category || '';
      const rowText = row.textContent.toLowerCase();
      
      const matchCategory = !category || rowCategory === category;
      const matchSearch = !search || rowText.includes(search);
      
      row.style.display = (matchCategory && matchSearch) ? '' : 'none';
    });
  }
  
  if (categoryFilter) categoryFilter.addEventListener('change', filterExpenses);
  if (expenseSearch) expenseSearch.addEventListener('input', filterExpenses);

  // ========== TRANSACTIONS ==========
  // Filter Panel Toggle
  const showFiltersBtn = document.getElementById('showFilters');
  const filterPanel = document.getElementById('filterPanel');
  
  if (showFiltersBtn && filterPanel) {
    showFiltersBtn.addEventListener('click', () => {
      const isHidden = filterPanel.style.display === 'none' || filterPanel.style.display === '';
      filterPanel.style.display = isHidden ? 'block' : 'none';
    });
  }
  
  // Transaction filters
  let currentTypeFilter = 'all';
  let currentSort = 'latest';
  let currentPeriod = 'all';
  
  const transactionFilters = document.querySelectorAll('.filter-btn[data-filter]');
  transactionFilters.forEach(btn => {
    btn.addEventListener('click', function() {
      transactionFilters.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      currentTypeFilter = this.dataset.filter;
      applyAllFilters();
    });
  });

  // Sort buttons (Latest/Oldest)
  const sortButtons = document.querySelectorAll('.sort-btn[data-sort]');
  sortButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      sortButtons.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      currentSort = this.dataset.sort;
      applyAllFilters();
    });
  });

  // Time period buttons (1 month, 6 months)
  const periodButtons = document.querySelectorAll('.period-btn[data-period]');
  periodButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      periodButtons.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      currentPeriod = this.dataset.period;
      applyAllFilters();
    });
  });

  // Apply all filters together
  function applyAllFilters() {
    const items = Array.from(document.querySelectorAll('.transaction-timeline-item'));
    if (items.length === 0) return;
    
    // Filter by type
    let filtered = items.filter(item => {
      if (currentTypeFilter === 'all') return true;
      return item.dataset.type === currentTypeFilter;
    });
    
    // Filter by time period
    if (currentPeriod !== 'all') {
      const periodDate = new Date();
      if (currentPeriod === '1month') {
        periodDate.setMonth(periodDate.getMonth() - 1);
      } else if (currentPeriod === '6months') {
        periodDate.setMonth(periodDate.getMonth() - 6);
      }
      
      filtered = filtered.filter(item => {
        const itemDate = item.dataset.date;
        if (!itemDate || itemDate === '') return false;
        
        // Parse date - handle YYYY-MM-DD format
        const dateParts = itemDate.split('-');
        if (dateParts.length === 3) {
          const txDate = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]));
          return txDate >= periodDate;
        }
        return false;
      });
    }
    
    // Sort by latest/oldest
    filtered.sort((a, b) => {
      const dateAStr = a.dataset.date || '';
      const dateBStr = b.dataset.date || '';
      
      if (!dateAStr || !dateBStr) return 0;
      
      const datePartsA = dateAStr.split('-');
      const datePartsB = dateBStr.split('-');
      
      if (datePartsA.length === 3 && datePartsB.length === 3) {
        const dateA = new Date(parseInt(datePartsA[0]), parseInt(datePartsA[1]) - 1, parseInt(datePartsA[2]));
        const dateB = new Date(parseInt(datePartsB[0]), parseInt(datePartsB[1]) - 1, parseInt(datePartsB[2]));
        return currentSort === 'latest' ? dateB - dateA : dateA - dateB;
      }
      return 0;
    });
    
    // Hide all items first
    items.forEach(item => item.style.display = 'none');
    
    // Show filtered and sorted items
    filtered.forEach(item => item.style.display = '');
    
    // Reorder in DOM
    const container = document.querySelector('.transactions-timeline');
    if (container && filtered.length > 0) {
      filtered.forEach(item => container.appendChild(item));
    }
    
    updateTransactionSummary();
  }
  
  // Initialize - show all transactions on page load
  setTimeout(() => {
    const items = document.querySelectorAll('.transaction-timeline-item');
    items.forEach(item => item.style.display = '');
    // Apply initial sort
    if (currentSort === 'latest') {
      const itemsArray = Array.from(items);
      itemsArray.sort((a, b) => {
        const dateAStr = a.dataset.date || '';
        const dateBStr = b.dataset.date || '';
        if (!dateAStr || !dateBStr) return 0;
        const datePartsA = dateAStr.split('-');
        const datePartsB = dateBStr.split('-');
        if (datePartsA.length === 3 && datePartsB.length === 3) {
          const dateA = new Date(parseInt(datePartsA[0]), parseInt(datePartsA[1]) - 1, parseInt(datePartsA[2]));
          const dateB = new Date(parseInt(datePartsB[0]), parseInt(datePartsB[1]) - 1, parseInt(datePartsB[2]));
          return dateB - dateA;
        }
        return 0;
      });
      const container = document.querySelector('.transactions-timeline');
      if (container) {
        itemsArray.forEach(item => container.appendChild(item));
      }
    }
  }, 100);

  // Transaction search
  const transactionSearch = document.getElementById('transactionSearch');
  if (transactionSearch) {
    transactionSearch.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      if (searchTerm === '') {
        // If search is cleared, reapply all filters
        applyAllFilters();
        return;
      }
      
      const items = document.querySelectorAll('.transaction-timeline-item');
      items.forEach(item => {
        const text = item.textContent.toLowerCase();
        // Only filter if item is already visible from other filters
        if (item.style.display !== 'none') {
          item.style.display = text.includes(searchTerm) ? '' : 'none';
        }
      });
      updateTransactionSummary();
    });
  }

  // Date range filter
  const startDate = document.getElementById('startDate');
  const endDate = document.getElementById('endDate');
  const applyFilters = document.getElementById('applyFilters');
  
  if (applyFilters) {
    applyFilters.addEventListener('click', function() {
      const start = startDate ? startDate.value : '';
      const end = endDate ? endDate.value : '';
      const items = document.querySelectorAll('.transaction-timeline-item');
      
      items.forEach(item => {
        const itemDate = item.dataset.date || '';
        const show = (!start || itemDate >= start) && (!end || itemDate <= end);
        if (show && item.style.display !== 'none') {
          // Keep visible if it passes date range filter
        } else {
          item.style.display = show ? '' : 'none';
        }
      });
      
      updateTransactionSummary();
    });
  }

  // Clear filters
  const clearFilters = document.getElementById('clearFilters');
  if (clearFilters) {
    clearFilters.addEventListener('click', function() {
      // Reset type filter
      const allTypeBtn = document.querySelector('.filter-btn[data-filter="all"]');
      if (allTypeBtn) {
        transactionFilters.forEach(b => b.classList.remove('active'));
        allTypeBtn.classList.add('active');
        currentTypeFilter = 'all';
      }
      
      // Reset sort
      const latestSortBtn = document.querySelector('.sort-btn[data-sort="latest"]');
      if (latestSortBtn) {
        sortButtons.forEach(b => b.classList.remove('active'));
        latestSortBtn.classList.add('active');
        currentSort = 'latest';
      }
      
      // Reset period
      const allPeriodBtn = document.querySelector('.period-btn[data-period="all"]');
      if (allPeriodBtn) {
        periodButtons.forEach(b => b.classList.remove('active'));
        allPeriodBtn.classList.add('active');
        currentPeriod = 'all';
      }
      
      // Clear date inputs
      if (startDate) startDate.value = '';
      if (endDate) endDate.value = '';
      if (transactionSearch) transactionSearch.value = '';
      
      // Show all items
      const items = document.querySelectorAll('.transaction-timeline-item');
      items.forEach(item => item.style.display = '');
      
      // Re-sort by latest
      applyAllFilters();
    });
  }

  // Update transaction summary
  function updateTransactionSummary() {
    if (typeof window.transactionsData === 'undefined') return;
    
    const visibleItems = Array.from(document.querySelectorAll('.transaction-timeline-item'))
      .filter(item => item.style.display !== 'none');
    
    let totalIncome = 0;
    let totalExpense = 0;
    
    visibleItems.forEach(item => {
      const type = item.dataset.type;
      const amountText = item.querySelector('.transaction-amount')?.textContent || '';
      const amount = parseFloat(amountText.replace(/[^0-9.]/g, '')) || 0;
      
      if (type === 'income') {
        totalIncome += amount;
      } else if (type === 'expense') {
        totalExpense += amount;
      }
    });
    
    const totalIncomeEl = document.getElementById('totalIncome');
    const totalExpenseEl = document.getElementById('totalExpense');
    const netBalanceEl = document.getElementById('netBalance');
    
    if (totalIncomeEl) totalIncomeEl.textContent = `₹${totalIncome.toFixed(2)}`;
    if (totalExpenseEl) totalExpenseEl.textContent = `₹${totalExpense.toFixed(2)}`;
    if (netBalanceEl) {
      const balance = totalIncome - totalExpense;
      netBalanceEl.textContent = `₹${balance.toFixed(2)}`;
      netBalanceEl.className = `summary-value ${balance >= 0 ? 'positive' : 'negative'}`;
    }
  }

  // Delete transaction
  document.querySelectorAll('.delete-transaction').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      if (!confirm('Are you sure you want to delete this transaction?')) return;
      
      const id = btn.dataset.id;
      try {
        const res = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          showMessage('Transaction deleted successfully!', 'success');
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(data.error || 'Error deleting transaction', 'error');
        }
      } catch (error) {
        showMessage('Error deleting transaction. Please try again.', 'error');
      }
    });
  });

  // ========== LIMITS ==========
  const setLimitForm = document.getElementById('setLimitForm');
  if (setLimitForm) {
    setLimitForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(setLimitForm);
      const data = Object.fromEntries(formData.entries());
      
      try {
      const res = await fetch('/api/limits', {
        method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
        const result = await res.json();
        if (result.success) {
          showMessage('Limit set successfully!', 'success');
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(result.error || 'Error setting limit', 'error');
        }
      } catch (error) {
        showMessage('Error setting limit. Please try again.', 'error');
      }
    });
  }

  // Delete limit
  const deleteLimit = document.getElementById('deleteLimit');
  if (deleteLimit) {
    deleteLimit.addEventListener('click', async (e) => {
      if (!confirm('Are you sure you want to delete your expense limit?')) return;
      
      try {
        const res = await fetch('/api/limits', { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          showMessage('Limit deleted successfully!', 'success');
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(data.error || 'Error deleting limit', 'error');
        }
      } catch (error) {
        showMessage('Error deleting limit. Please try again.', 'error');
      }
    });
  }

  // Update limit progress
  if (typeof window.limitData !== 'undefined' && window.limitData) {
    updateLimitProgress();
  }

  function updateLimitProgress() {
    // Fetch current spending and update progress bar
    fetch('/api/expense')
      .then(res => res.json())
      .then(data => {
        if (data.expenses && window.limitData) {
          const totalSpent = data.expenses.reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
          const limit = parseFloat(window.limitData.limit || 0);
          const percentage = limit > 0 ? Math.min((totalSpent / limit) * 100, 100) : 0;
          
          const progressBar = document.getElementById('limitProgress');
          const spentAmount = document.getElementById('spentAmount');
          const limitWarning = document.getElementById('limitWarning');
          
          if (progressBar) progressBar.style.width = `${percentage}%`;
          if (spentAmount) spentAmount.textContent = `₹${totalSpent.toFixed(2)}`;
          
          if (limitWarning && percentage >= 80) {
            limitWarning.style.display = 'flex';
          }
        }
      })
      .catch(err => console.error('Error updating limit progress:', err));
  }

  // ========== SUBSCRIPTIONS ==========
  const addSubscriptionForm = document.getElementById('addSubscriptionForm');
  if (addSubscriptionForm) {
    addSubscriptionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(addSubscriptionForm);
      const data = Object.fromEntries(formData.entries());
      
      try {
      const res = await postJSON('/api/subscriptions', data);
        if (res.success) {
          showMessage('Subscription added successfully!', 'success');
          document.getElementById('addSubscriptionFormContainer').style.display = 'none';
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(res.error || 'Error adding subscription', 'error');
        }
      } catch (error) {
        showMessage('Error adding subscription. Please try again.', 'error');
      }
    });
  }

  // Edit subscription
  document.querySelectorAll('.edit-subscription').forEach(btn => {
    btn.addEventListener('click', function() {
      const id = this.dataset.id;
      if (typeof window.subscriptionsData === 'undefined') return;
      
      const sub = window.subscriptionsData.find(s => s._id === id);
      if (!sub) return;
      
      const modal = document.getElementById('editSubscriptionModal');
      if (modal) {
        document.getElementById('editSubscriptionId').value = id;
        document.getElementById('editName').value = sub.name || '';
        document.getElementById('editAmount').value = sub.amount || '';
        document.getElementById('editCycle').value = sub.cycle || 'monthly';
        document.getElementById('editNextDate').value = sub.next_payment_date || '';
        document.getElementById('editEndDate').value = sub.end_date || '';
        document.getElementById('editNotes').value = sub.notes || '';
        modal.style.display = 'flex';
      }
    });
  });

  // Close edit modal
  const closeEditModal = document.getElementById('closeEditModal');
  const cancelEditSubscription = document.getElementById('cancelEditSubscription');
  if (closeEditModal) {
    closeEditModal.addEventListener('click', () => {
      document.getElementById('editSubscriptionModal').style.display = 'none';
    });
  }
  if (cancelEditSubscription) {
    cancelEditSubscription.addEventListener('click', () => {
      document.getElementById('editSubscriptionModal').style.display = 'none';
    });
  }

  // Update subscription
  const editSubscriptionForm = document.getElementById('editSubscriptionForm');
  if (editSubscriptionForm) {
    editSubscriptionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(editSubscriptionForm);
      const id = formData.get('subscription_id');
      const data = Object.fromEntries(formData.entries());
      delete data.subscription_id;
      
      try {
        const res = await putJSON(`/api/subscriptions/${id}`, data);
        if (res.success) {
          showMessage('Subscription updated successfully!', 'success');
          document.getElementById('editSubscriptionModal').style.display = 'none';
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(res.error || 'Error updating subscription', 'error');
        }
      } catch (error) {
        showMessage('Error updating subscription. Please try again.', 'error');
      }
    });
  }

  // Delete subscription
  document.querySelectorAll('.delete-subscription').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      if (!confirm('Are you sure you want to delete this subscription?')) return;
      
      const id = btn.dataset.id;
      try {
      const res = await fetch(`/api/subscriptions/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          showMessage('Subscription deleted successfully!', 'success');
          setTimeout(() => location.reload(), 1000);
        } else {
          showMessage(data.error || 'Error deleting subscription', 'error');
        }
      } catch (error) {
        showMessage('Error deleting subscription. Please try again.', 'error');
      }
    });
  });

  // Calculate days remaining for subscriptions
  if (typeof window.subscriptionsData !== 'undefined') {
    window.subscriptionsData.forEach(sub => {
      if (sub.next_payment_date) {
        const daysLeftEl = document.getElementById(`daysLeft-${sub._id}`);
        if (daysLeftEl) {
          const today = new Date();
          const nextDate = new Date(sub.next_payment_date);
          const diffTime = nextDate - today;
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
          
          if (diffDays < 0) {
            daysLeftEl.textContent = 'Overdue';
            daysLeftEl.style.color = '#ef4444';
          } else if (diffDays === 0) {
            daysLeftEl.textContent = 'Due today';
            daysLeftEl.style.color = '#ef4444';
          } else if (diffDays <= 2) {
            daysLeftEl.textContent = `${diffDays} day${diffDays > 1 ? 's' : ''} left`;
            daysLeftEl.style.color = '#f59e0b';
          } else {
            daysLeftEl.textContent = `${diffDays} days left`;
            daysLeftEl.style.color = '#64748b';
          }
        }
      }
    });
  }

  // Load upcoming reminders
  loadUpcomingReminders();
  
  async function loadUpcomingReminders() {
    try {
      const res = await fetch('/api/subscriptions/upcoming?days=7');
      const data = await res.json();
      
      if (data.success && data.upcoming && data.upcoming.length > 0) {
        const remindersList = document.getElementById('upcomingReminders');
        if (remindersList) {
          remindersList.innerHTML = data.upcoming.map(sub => `
            <div class="subscription-item">
              <div class="subscription-name">${sub.name}</div>
              <div class="subscription-amount">₹${parseFloat(sub.amount || 0).toFixed(2)}</div>
              <div class="subscription-date">Due: ${sub.next_payment_date} (${sub.days_left || 0} days)</div>
            </div>
          `).join('');
        }
      }
    } catch (error) {
      console.error('Error loading reminders:', error);
    }
  }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);
