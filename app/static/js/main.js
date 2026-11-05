document.addEventListener('DOMContentLoaded', function () {
  // 1. Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 2. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function (e) {
      e.preventDefault();
      document.body.classList.toggle('sb-sidenav-toggled');
      const sidebarWrapper = document.getElementById('sidebar-wrapper');
      if (sidebarWrapper) {
        sidebarWrapper.classList.toggle('d-none');
      }
    });
  }

  // 3. Dynamic Soft Delete Confirmation Modal
  const deleteModal = document.getElementById('softDeleteModal');
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const deleteUrl = button.getAttribute('data-delete-url');
      const recordName = button.getAttribute('data-record-name') || 'this record';
      
      const form = deleteModal.querySelector('#softDeleteForm');
      const namePlaceholder = deleteModal.querySelector('#deleteRecordName');
      
      if (form) form.action = deleteUrl;
      if (namePlaceholder) namePlaceholder.textContent = recordName;
    });
  }

  // 4. Chart.js Dashboard Charts (if elements present on page)
  initDashboardCharts();
});

function initDashboardCharts() {
  // Chart 1: Appointments by Status (Doughnut)
  const apptCanvas = document.getElementById('appointmentStatusChart');
  if (apptCanvas && window.Chart && window.hmsChartData) {
    const statusData = window.hmsChartData.apptStatus || {};
    const labels = Object.keys(statusData);
    const dataValues = Object.values(statusData);

    new Chart(apptCanvas, {
      type: 'doughnut',
      data: {
        labels: labels.length ? labels : ['Scheduled', 'Confirmed', 'Completed', 'Cancelled'],
        datasets: [{
          data: dataValues.length ? dataValues : [3, 2, 4, 1],
          backgroundColor: [
            '#f59e0b', // Scheduled (Amber)
            '#0ea5e9', // Confirmed (Sky)
            '#10b981', // Completed (Emerald)
            '#ef4444'  // Cancelled (Red)
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } }
          }
        },
        cutout: '70%'
      }
    });
  }

  // Chart 2: Department Doctor Distribution (Bar / Polar)
  const deptCanvas = document.getElementById('deptDistributionChart');
  if (deptCanvas && window.Chart && window.hmsChartData) {
    const deptData = window.hmsChartData.deptDistribution || [];
    const labels = deptData.map(d => d[0]);
    const values = deptData.map(d => d[1]);

    new Chart(deptCanvas, {
      type: 'bar',
      data: {
        labels: labels.length ? labels : ['Cardiology', 'Neurology', 'Pediatrics'],
        datasets: [{
          label: 'Doctors',
          data: values.length ? values : [2, 1, 1],
          backgroundColor: '#0284c7',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1 }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  // Chart 3: Blood Group Distribution (Pie)
  const bgCanvas = document.getElementById('bloodGroupChart');
  if (bgCanvas && window.Chart && window.hmsChartData) {
    const bgData = window.hmsChartData.bloodGroups || [];
    const labels = bgData.map(b => b[0]);
    const values = bgData.map(b => b[1]);

    new Chart(bgCanvas, {
      type: 'pie',
      data: {
        labels: labels.length ? labels : ['O+', 'B+', 'A+', 'AB+'],
        datasets: [{
          data: values.length ? values : [2, 1, 1, 1],
          backgroundColor: [
            '#0d9488',
            '#3b82f6',
            '#6366f1',
            '#ec4899',
            '#8b5cf6',
            '#14b8a6'
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10 } }
        }
      }
    });
  }
}
