document.addEventListener("DOMContentLoaded", () => {
  const ctx = document.getElementById("expenseChart").getContext("2d");

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Income", "Expense"],
      datasets: [{
        data: [3000, 1200], // Replace with dynamic values later
        backgroundColor: [
          "#4FC3F7", // light sky blue
          "#80CBC4"  // light teal
        ],
        hoverBackgroundColor: [
          "#29B6F6", // slightly darker blue on hover
          "#26A69A"  // slightly darker teal on hover
        ],
        borderWidth: 2,
        borderColor: "#ffffff"
      }]
    },
    options: {
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#333",
            font: {
              size: 14,
              family: "Poppins, sans-serif"
            }
          }
        },
        tooltip: {
          backgroundColor: "rgba(255,255,255,0.9)",
          titleColor: "#00796B",
          bodyColor: "#333",
          borderColor: "#80CBC4",
          borderWidth: 1
        }
      },
      cutout: "65%", // makes it look cleaner
      animation: {
        animateScale: true
      }
    }
  });
});
