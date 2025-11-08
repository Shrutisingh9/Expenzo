// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
  // Dashboard Charts
  initDashboardCharts();
  
  // Transaction Filters
  initTransactionFilters();
  
  // Form Toggles
  initFormToggles();
});

// Initialize Dashboard Charts
function initDashboardCharts() {
  if (typeof window.dashboardData === 'undefined') return;
  
  const data = window.dashboardData;
  
  // Balance Chart
  const balanceCtx = document.getElementById('balanceChart');
  if (balanceCtx) {
    const balanceData = generateWeeklyData(data.balance);
    new Chart(balanceCtx, {
      type: 'line',
      data: {
        labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        datasets: [{
          label: 'Balance',
          data: balanceData,
          borderColor: '#00ACC1',
          backgroundColor: 'rgba(0, 172, 193, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: false }
        }
      }
    });
  }
  
  // Spending Chart (Doughnut)
  const spendingCtx = document.getElementById('spendingChart');
  if (spendingCtx && data.categorySpending) {
    const categories = Object.keys(data.categorySpending);
    const amounts = Object.values(data.categorySpending);
    const colors = generateColors(categories.length);
    
    new Chart(spendingCtx, {
      type: 'doughnut',
      data: {
        labels: categories,
        datasets: [{
          data: amounts,
          backgroundColor: colors,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        }
      }
    });
  }
  
  // Budget Chart
  const budgetCtx = document.getElementById('budgetChart');
  if (budgetCtx) {
    new Chart(budgetCtx, {
      type: 'bar',
      data: {
        labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        datasets: [
          {
            label: 'Income',
            data: generateWeeklyData(data.totalIncome / 7),
            backgroundColor: '#10b981'
          },
          {
            label: 'Spent',
            data: generateWeeklyData(data.totalExpense / 7),
            backgroundColor: '#ef4444'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true },
          y: { stacked: true, beginAtZero: true }
        }
      }
    });
  }
  
  // Overview Chart
  const overviewCtx = document.getElementById('overviewChart');
  if (overviewCtx && data.recentTransactions) {
    const dates = data.recentTransactions.slice(0, 7).map(t => {
      const date = t.date ? new Date(t.date) : new Date();
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    });
    const counts = Array(7).fill(0);
    data.recentTransactions.slice(0, 7).forEach((t, i) => {
      counts[i] = 1;
    });
    
    new Chart(overviewCtx, {
      type: 'line',
      data: {
        labels: dates.length > 0 ? dates : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        datasets: [{
          label: 'Transactions',
          data: counts,
          borderColor: '#00ACC1',
          backgroundColor: 'rgba(0, 172, 193, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } }
        }
      }
    });
  }
}

// Generate weekly data for charts
function generateWeeklyData(baseValue) {
  const days = 7;
  const data = [];
  for (let i = 0; i < days; i++) {
    const variation = (Math.random() - 0.5) * 0.3; // ±15% variation
    data.push(baseValue * (1 + variation));
  }
  return data;
}

// Generate colors for charts
function generateColors(count) {
  const colors = ['#4A90E2', '#7B68EE', '#FF6B9D', '#95A5A6', '#F39C12', '#E74C3C', '#3498DB'];
  return colors.slice(0, count);
}

// Transaction Filters
function initTransactionFilters() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const transactionItems = document.querySelectorAll('.transaction-item');
  
  filterBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      // Update active state
      filterBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      
      const filter = this.dataset.filter;
      
      // Filter transactions
      transactionItems.forEach(item => {
        if (filter === 'all' || item.dataset.type === filter) {
          item.style.display = 'flex';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });
}

// Form Toggles
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
    });
  }
  
  // Show/Hide Add Income Form
  const showAddIncomeBtn = document.getElementById('showAddIncomeForm');
  const addIncomeFormContainer = document.getElementById('addIncomeFormContainer');
  const cancelAddIncome = document.getElementById('cancelAddIncome');
  
  if (showAddIncomeBtn && addIncomeFormContainer) {
    showAddIncomeBtn.addEventListener('click', () => {
      addIncomeFormContainer.style.display = 'block';
    });
  }
  
  if (cancelAddIncome && addIncomeFormContainer) {
    cancelAddIncome.addEventListener('click', () => {
      addIncomeFormContainer.style.display = 'none';
    });
  }
  
  // Show/Hide Add Expense Form
  const showAddExpenseBtn = document.getElementById('showAddExpenseForm');
  const addExpenseFormContainer = document.getElementById('addExpenseFormContainer');
  const cancelAddExpense = document.getElementById('cancelAddExpense');
  
  if (showAddExpenseBtn && addExpenseFormContainer) {
    showAddExpenseBtn.addEventListener('click', () => {
      addExpenseFormContainer.style.display = 'block';
    });
  }
  
  if (cancelAddExpense && addExpenseFormContainer) {
    cancelAddExpense.addEventListener('click', () => {
      addExpenseFormContainer.style.display = 'none';
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
    });
  }
  
  // Filter Panel Toggle
  const showFiltersBtn = document.getElementById('showFilters');
  const filterPanel = document.getElementById('filterPanel');
  
  if (showFiltersBtn && filterPanel) {
    showFiltersBtn.addEventListener('click', () => {
      filterPanel.style.display = filterPanel.style.display === 'none' ? 'block' : 'none';
    });
  }
}


// Visualization Charts
if (typeof window.visualizationData !== 'undefined') {
  document.addEventListener('DOMContentLoaded', function() {
    const data = window.visualizationData;
    
    // Income vs Expense Chart
    const incomeExpenseCtx = document.getElementById('incomeExpenseChart');
    if (incomeExpenseCtx) {
      new Chart(incomeExpenseCtx, {
        type: 'doughnut',
        data: {
          labels: ['Income', 'Expense'],
          datasets: [{
            data: [data.totalIncome, data.totalExpense],
            backgroundColor: ['#10b981', '#ef4444'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom' }
          }
        }
      });
    }
    
    // Category Chart
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx && data.categoryExpenses) {
      const categories = Object.keys(data.categoryExpenses);
      const amounts = Object.values(data.categoryExpenses);
      
      new Chart(categoryCtx, {
        type: 'pie',
        data: {
          labels: categories,
          datasets: [{
            data: amounts,
            backgroundColor: generateColors(categories.length)
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom' }
          }
        }
      });
    }
    
    // Income Sources Chart
    const incomeSourcesCtx = document.getElementById('incomeSourcesChart');
    if (incomeSourcesCtx && data.incomeSources) {
      const sources = Object.keys(data.incomeSources);
      const amounts = Object.values(data.incomeSources);
      
      new Chart(incomeSourcesCtx, {
        type: 'bar',
        data: {
          labels: sources,
          datasets: [{
            label: 'Income',
            data: amounts,
            backgroundColor: '#10b981'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }
    
    // Monthly Trend Chart
    const monthlyTrendCtx = document.getElementById('monthlyTrendChart');
    if (monthlyTrendCtx && data.transactions) {
      const monthlyData = calculateMonthlyTrend(data.transactions);
      
      new Chart(monthlyTrendCtx, {
        type: 'line',
        data: {
          labels: monthlyData.labels,
          datasets: [
            {
              label: 'Income',
              data: monthlyData.income,
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              tension: 0.4,
              fill: true
            },
            {
              label: 'Expense',
              data: monthlyData.expense,
              borderColor: '#ef4444',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              tension: 0.4,
              fill: true
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    }
  });
}

// Calculate monthly trend from transactions
function calculateMonthlyTrend(transactions) {
  const monthly = {};
  
  if (!transactions || !Array.isArray(transactions)) {
    return { labels: [], income: [], expense: [] };
  }
  
  transactions.forEach(tx => {
    try {
      let date;
      if (tx.date) {
        date = new Date(tx.date);
      } else if (tx.created_at) {
        date = new Date(tx.created_at);
      } else {
        return; // Skip if no date
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return; // Skip invalid dates
      }
      
      const monthKey = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      
      if (!monthly[monthKey]) {
        monthly[monthKey] = { income: 0, expense: 0 };
      }
      
      if (tx.type === 'income') {
        monthly[monthKey].income += parseFloat(tx.amount || 0);
      } else if (tx.type === 'expense') {
        monthly[monthKey].expense += parseFloat(tx.amount || 0);
      }
    } catch (error) {
      console.error('Error processing transaction:', error, tx);
    }
  });
  
  const labels = Object.keys(monthly).sort((a, b) => {
    // Sort by date
    return new Date(a) - new Date(b);
  });
  const income = labels.map(m => monthly[m].income);
  const expense = labels.map(m => monthly[m].expense);
  
  return { labels, income, expense };
}
