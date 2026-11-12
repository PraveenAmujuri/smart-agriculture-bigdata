/**
 * Charts Manager
 * Renders the Donezo-styled grouped bar chart for cluster distribution.
 */

const ChartsManager = (function () {
  let chart = null;

  function init() {
    const canvas = document.getElementById("clusterDistributionChart");
    if (!canvas) return;

    if (chart) chart.destroy();

    const totalObs = 124320;
    const labels = [
      "Cluster 0",
      "Cluster 1",
      "Cluster 2",
      "Cluster 3",
      "Cluster 4"
    ];

    chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "K-Means",
            data: [19934, 35765, 17191, 25734, 25696],
            backgroundColor: "#155d36", // Forest green
            borderRadius: 8,
            maxBarThickness: 38
          },
          {
            label: "Fuzzy K-Means",
            data: [16966, 40889, 30306, 22101, 14058],
            backgroundColor: "#52b788", // Soft mint/sage green
            borderRadius: 8,
            maxBarThickness: 38
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              boxWidth: 12,
              font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: "600" },
              color: "#374151"
            }
          },
          tooltip: {
            backgroundColor: "#111827",
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: function (ctx) {
                const val = ctx.raw;
                const pct = ((val / totalObs) * 100).toFixed(2);
                return ` ${ctx.dataset.label}: ${val.toLocaleString()} records (${pct}%)`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 12, weight: "600" }, color: "#4b5563" }
          },
          y: {
            beginAtZero: true,
            grid: { color: "#f3f4f6" },
            ticks: {
              font: { size: 11 },
              color: "#9ca3af",
              callback: (v) => (v / 1000) + "k"
            }
          }
        }
      }
    });
  }

  return { init };
})();
