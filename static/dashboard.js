// static/dashboard.js
document.addEventListener('DOMContentLoaded', async () => {
  // fetch summary for visualization
  const res = await fetch('/api/visualization/summary');
  if (!res.ok) return;
  const data = await res.json();
  // render simple pie or doughnut for income vs expense
  if (document.getElementById('incomeExpenseChart')) {
    const ctx = document.getElementById('incomeExpenseChart').getContext('2d');
    const income = data.by_type.income || 0;
    const expense = data.by_type.expense || 0;
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Income', 'Expense'],
        datasets: [{
          data: [income, expense],
          backgroundColor: ['#06b6d4', '#f87171']
        }]
      }
    });
  }
  // category chart
  if (document.getElementById('categoryChart')) {
    const ctx2 = document.getElementById('categoryChart').getContext('2d');
    const labels = Object.keys(data.by_category);
    const values = Object.values(data.by_category);
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Spending by category', data: values }]
      }
    });
  }
});
document.addEventListener("DOMContentLoaded", async () => {
  const chartCanvas = document.getElementById("expenseChart");

  if (!chartCanvas) return;

  const ctx = chartCanvas.getContext("2d");

  // 🔹 Later you can replace this with an API call:
  // const res = await fetch('/api/summary');
  // const chartData = await res.json();
  const chartData = {
    income: 3500,
    expense: 1800
  };

  const total = chartData.income + chartData.expense;
  const incomePercent = ((chartData.income / total) * 100).toFixed(1);
  const expensePercent = ((chartData.expense / total) * 100).toFixed(1);

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: [
        `Income (${incomePercent}%)`,
        `Expense (${expensePercent}%)`
      ],
      datasets: [
        {
          data: [chartData.income, chartData.expense],
          backgroundColor: ["#4FC3F7", "#80CBC4"],
          hoverBackgroundColor: ["#29B6F6", "#26A69A"],
          borderWidth: 2,
          borderColor: "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      cutout: "65%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#333",
            font: {
              size: 14,
              family: "Poppins, sans-serif",
            },
          },
        },
        tooltip: {
          backgroundColor: "rgba(255,255,255,0.95)",
          titleColor: "#00796B",
          bodyColor: "#333",
          borderColor: "#80CBC4",
          borderWidth: 1,
          callbacks: {
            label: (context) =>
              `${context.label}: ₹${context.parsed.toLocaleString()}`,
          },
        },
      },
      animation: {
        animateScale: true,
      },
    },
  });
});
