/* =========================================================
   FLEETFLOW MASTER JAVASCRIPT
   Interactive validation, modals, filtering & UI controls
   ========================================================= */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Modal open/close handlers
  document.querySelectorAll('[data-modal-target]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-modal-target');
      const modal = document.getElementById(targetId);
      if (modal) {
        modal.classList.add('show');
      }
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-backdrop');
      if (modal) {
        modal.classList.remove('show');
      }
    });
  });

  window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
      e.target.classList.remove('show');
    }
  });

  // 2. Client-side Search and Filter for data tables
  const searchInput = document.getElementById('tableSearchInput');
  const typeFilter = document.getElementById('typeFilter');
  const statusFilter = document.getElementById('statusFilter');
  const regionFilter = document.getElementById('regionFilter');

  function filterTable() {
    const table = document.querySelector('.data-table tbody');
    if (!table) return;

    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const selectedType = typeFilter ? typeFilter.value.toLowerCase() : '';
    const selectedStatus = statusFilter ? statusFilter.value.toLowerCase() : '';
    const selectedRegion = regionFilter ? regionFilter.value.toLowerCase() : '';

    Array.from(table.rows).forEach(row => {
      const text = row.textContent.toLowerCase();
      const rowType = (row.getAttribute('data-type') || '').toLowerCase();
      const rowStatus = (row.getAttribute('data-status') || '').toLowerCase();
      const rowRegion = (row.getAttribute('data-region') || '').toLowerCase();

      const matchesSearch = !searchTerm || text.includes(searchTerm);
      const matchesType = !selectedType || rowType === selectedType;
      const matchesStatus = !selectedStatus || rowStatus === selectedStatus;
      const matchesRegion = !selectedRegion || rowRegion === selectedRegion;

      if (matchesSearch && matchesType && matchesStatus && matchesRegion) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  }

  if (searchInput) searchInput.addEventListener('input', filterTable);
  if (typeFilter) typeFilter.addEventListener('change', filterTable);
  if (statusFilter) statusFilter.addEventListener('change', filterTable);
  if (regionFilter) regionFilter.addEventListener('change', filterTable);

  // 3. Real-time Cargo Payload vs Max Capacity Validator in Trip Modal
  const vehicleSelect = document.getElementById('tripVehicleSelect');
  const cargoWeightInput = document.getElementById('tripCargoWeight');
  const payloadWarning = document.getElementById('payloadWarning');
  const submitTripBtn = document.getElementById('submitTripBtn');
  const driverSelect = document.getElementById('tripDriverSelect');
  const driverWarning = document.getElementById('driverWarning');

  function validateTripForm() {
    if (!vehicleSelect || !cargoWeightInput) return;

    const selectedOpt = vehicleSelect.options[vehicleSelect.selectedIndex];
    const maxCapacity = parseFloat(selectedOpt ? selectedOpt.getAttribute('data-capacity') : 0) || 0;
    const vehicleType = selectedOpt ? selectedOpt.getAttribute('data-type') : '';
    const cargoWeight = parseFloat(cargoWeightInput.value) || 0;

    let hasCapacityError = false;
    let hasDriverError = false;

    if (maxCapacity > 0 && cargoWeight > 0) {
      if (cargoWeight > maxCapacity) {
        hasCapacityError = true;
        if (payloadWarning) {
          payloadWarning.textContent = `❌ Overweight Cargo! Weight (${cargoWeight} kg) exceeds vehicle max capacity (${maxCapacity} kg).`;
          payloadWarning.style.display = 'block';
        }
      } else {
        if (payloadWarning) {
          payloadWarning.textContent = `✅ Valid payload: ${cargoWeight} kg / ${maxCapacity} kg (${Math.round((cargoWeight / maxCapacity) * 100)}% load)`;
          payloadWarning.style.color = '#10b981';
          payloadWarning.style.display = 'block';
        }
      }
    } else if (payloadWarning) {
      payloadWarning.style.display = 'none';
    }

    // Check driver category compatibility if driver selected
    if (driverSelect && driverSelect.value && selectedOpt && vehicleType) {
      const driverOpt = driverSelect.options[driverSelect.selectedIndex];
      const driverCategory = driverOpt.getAttribute('data-category');
      const isExpired = driverOpt.getAttribute('data-expired') === 'true';

      if (isExpired) {
        hasDriverError = true;
        if (driverWarning) {
          driverWarning.textContent = `❌ Driver license is EXPIRED. Assignment blocked.`;
          driverWarning.style.display = 'block';
        }
      } else if (driverCategory !== 'All' && driverCategory !== vehicleType) {
        hasDriverError = true;
        if (driverWarning) {
          driverWarning.textContent = `⚠️ Category mismatch: Driver holds '${driverCategory}' license, but vehicle is '${vehicleType}'.`;
          driverWarning.style.display = 'block';
        }
      } else if (driverWarning) {
        driverWarning.style.display = 'none';
      }
    }

    if (submitTripBtn) {
      submitTripBtn.disabled = hasCapacityError || hasDriverError;
    }
  }

  if (vehicleSelect) vehicleSelect.addEventListener('change', validateTripForm);
  if (cargoWeightInput) cargoWeightInput.addEventListener('input', validateTripForm);
  if (driverSelect) driverSelect.addEventListener('change', validateTripForm);

  // 4. Auto-dismiss toasts after 5 seconds
  document.querySelectorAll('.toast').forEach(toast => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  });
});
