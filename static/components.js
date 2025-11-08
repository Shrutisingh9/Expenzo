// static/components.js

async function postJSON(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

// Cards - add
document.addEventListener('DOMContentLoaded', () => {
  const addCardForm = document.getElementById('addCardForm');
  if (addCardForm) {
    addCardForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(addCardForm);
      const data = Object.fromEntries(fd.entries());
      const res = await postJSON('/api/cards', data);
      if (res.success) location.reload();
      else alert('Error adding card');
    });
  }

  // delete card buttons
  document.querySelectorAll('.btn-delete-card').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const id = btn.dataset.id;
      const res = await fetch(`/api/cards/${id}`, { method: 'DELETE' });
      const j = await res.json();
      if (j.success) location.reload();
    });
  });

  // Income form
  const incomeForm = document.getElementById('addIncomeForm');
  if (incomeForm) {
    incomeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(incomeForm).entries());
      const res = await postJSON('/api/income', data);
      if (res.success) location.reload();
      else alert('Error adding income');
    });
  }

  // Expense form
  const expenseForm = document.getElementById('addExpenseForm');
  if (expenseForm) {
    expenseForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(expenseForm).entries());
      const res = await postJSON('/api/expense', data);
      if (res.success) location.reload();
      else alert('Error adding expense');
    });
  }

  // Limits form
  const limitForm = document.getElementById('setLimitForm');
  if (limitForm) {
    limitForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(limitForm).entries());
      const res = await fetch('/api/limits', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(data)
      });
      const j = await res.json();
      if (j.success) location.reload();
    });
  }

  // Subscriptions form
  const subForm = document.getElementById('addSubscriptionForm');
  if (subForm) {
    subForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(subForm).entries());
      const res = await postJSON('/api/subscriptions', data);
      if (res.success) location.reload();
    });
  }

  // delete subscription
  document.querySelectorAll('.del-sub').forEach(b => {
    b.addEventListener('click', async () => {
      const id = b.dataset.id;
      const res = await fetch(`/api/subscriptions/${id}`, { method: 'DELETE' });
      const j = await res.json();
      if (j.success) location.reload();
    });
  });
});
