/* ════════════════════════════════════════════════════════════════════════════
   Milk Platform – Client-side JavaScript
   ════════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Role toggle on registration page ──────────────────────────────────────
    const roleSelect = document.getElementById('roleSelect');
    const farmerFields = document.getElementById('farmerFields');

    if (roleSelect && farmerFields) {
        function toggleFarmerFields() {
            if (roleSelect.value === 'farmer') {
                farmerFields.style.display = 'block';
                farmerFields.querySelectorAll('input').forEach(function (input) {
                    if (input.dataset.required === 'true') {
                        input.setAttribute('required', 'required');
                    }
                });
            } else {
                farmerFields.style.display = 'none';
                farmerFields.querySelectorAll('input').forEach(function (input) {
                    input.removeAttribute('required');
                });
            }
        }
        roleSelect.addEventListener('change', toggleFarmerFields);
        toggleFarmerFields();
    }

    // ── Geolocation detection ─────────────────────────────────────────────────
    const detectBtn = document.getElementById('detectLocationBtn');
    const latInput = document.getElementById('user_latitude');
    const lngInput = document.getElementById('user_longitude');
    const locInput = document.getElementById('user_location');
    const locStatus = document.getElementById('locationStatus');

    if (detectBtn && latInput && lngInput) {
        detectBtn.addEventListener('click', function () {
            if (!navigator.geolocation) {
                showLocationStatus('Geolocation is not supported by your browser.', 'danger');
                return;
            }

            detectBtn.disabled = true;
            detectBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Detecting...';
            showLocationStatus('Requesting location access...', 'info');

            navigator.geolocation.getCurrentPosition(
                function (position) {
                    var lat = position.coords.latitude;
                    var lng = position.coords.longitude;
                    latInput.value = lat.toFixed(6);
                    lngInput.value = lng.toFixed(6);

                    // Try reverse geocoding with Nominatim (free, no API key)
                    fetch('https://nominatim.openstreetmap.org/reverse?format=json&lat=' + lat + '&lon=' + lng + '&zoom=14')
                        .then(function (resp) { return resp.json(); })
                        .then(function (data) {
                            if (data && data.address) {
                                var parts = [];
                                if (data.address.village || data.address.town || data.address.city) {
                                    parts.push(data.address.village || data.address.town || data.address.city);
                                }
                                if (data.address.county || data.address.state_district) {
                                    parts.push(data.address.county || data.address.state_district);
                                }
                                if (data.address.state) {
                                    parts.push(data.address.state);
                                }
                                var areaName = parts.join(', ') || data.display_name.split(',').slice(0, 3).join(',');
                                if (locInput && !locInput.value) {
                                    locInput.value = areaName;
                                }
                                showLocationStatus('Location detected: ' + areaName, 'success');
                            } else {
                                showLocationStatus('Coordinates captured. Please enter your area name manually.', 'success');
                            }
                        })
                        .catch(function () {
                            showLocationStatus('Coordinates captured (' + lat.toFixed(4) + ', ' + lng.toFixed(4) + '). Enter area name manually.', 'success');
                        });

                    detectBtn.disabled = false;
                    detectBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;vertical-align:-2px;margin-right:4px;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> Location Detected';
                },
                function (error) {
                    var msg = 'Unable to detect location. ';
                    switch (error.code) {
                        case error.PERMISSION_DENIED:
                            msg += 'Permission denied. Please allow location access or enter coordinates manually.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            msg += 'Position unavailable. Please enter coordinates manually.';
                            break;
                        case error.TIMEOUT:
                            msg += 'Request timed out. Please try again or enter coordinates manually.';
                            break;
                    }
                    showLocationStatus(msg, 'danger');
                    detectBtn.disabled = false;
                    detectBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;vertical-align:-2px;margin-right:4px;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> Detect My Location';
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
            );
        });
    }

    function showLocationStatus(message, type) {
        if (locStatus) {
            locStatus.style.display = 'block';
            locStatus.className = 'form-text mt-2 text-' + (type === 'danger' ? 'danger' : type === 'success' ? 'success' : 'muted');
            locStatus.textContent = message;
        }
    }

    // ── Auto-dismiss flash messages ───────────────────────────────────────────
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // ── Quantity validation on order form ─────────────────────────────────────
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', function (e) {
            var qtyInput = document.getElementById('quantity');
            var qty = parseFloat(qtyInput.value);
            if (isNaN(qty) || qty <= 0) {
                e.preventDefault();
                showToast('Please enter a valid quantity greater than 0.', 'danger');
                qtyInput.focus();
                return false;
            }
        });
    }

    // ── Listing selection on order page ───────────────────────────────────────
    const listingCards = document.querySelectorAll('.listing-select-card');
    const listingInput = document.getElementById('listing_id');

    listingCards.forEach(function (card) {
        card.addEventListener('click', function () {
            listingCards.forEach(function (c) {
                c.classList.remove('border-success', 'selected');
            });
            this.classList.add('border-success', 'selected');
            if (listingInput) {
                listingInput.value = this.dataset.listingId;
            }
            var remaining = this.dataset.remaining;
            var availDisplay = document.getElementById('availableDisplay');
            if (availDisplay) {
                availDisplay.textContent = remaining + ' litres available';
            }
        });
    });

    // ── Product buy form validation ───────────────────────────────────────────
    const buyForms = document.querySelectorAll('.buy-product-form');
    buyForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var qtyInput = form.querySelector('input[name="quantity"]');
            var maxQty = parseFloat(qtyInput.max);
            var qty = parseFloat(qtyInput.value);
            if (isNaN(qty) || qty <= 0) {
                e.preventDefault();
                showToast('Please enter a valid quantity.', 'danger');
                return false;
            }
            if (qty > maxQty) {
                e.preventDefault();
                showToast('Quantity exceeds available stock (' + maxQty + ').', 'danger');
                return false;
            }
        });
    });

    // ── Confirm delete ────────────────────────────────────────────────────────
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            if (!confirm('Are you sure you want to remove this item?')) {
                e.preventDefault();
            }
        });
    });

    // ── Simple toast helper ───────────────────────────────────────────────────
    function showToast(message, type) {
        var container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;';
            document.body.appendChild(container);
        }
        var toast = document.createElement('div');
        toast.className = 'alert alert-' + (type || 'info') + ' alert-dismissible fade show';
        toast.setAttribute('role', 'alert');
        toast.style.cssText = 'min-width:280px;margin-bottom:0.5rem;box-shadow:0 4px 16px rgba(0,0,0,0.1);';
        toast.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
        container.appendChild(toast);
        setTimeout(function () {
            if (toast.parentNode) {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(toast);
                bsAlert.close();
            }
        }, 4000);
    }

    // ── Smooth number counter animation on stat cards ─────────────────────────
    const statNumbers = document.querySelectorAll('.stat-number[data-count]');
    statNumbers.forEach(function (el) {
        var target = parseFloat(el.dataset.count);
        var duration = 800;
        var start = performance.now();
        var isFloat = target % 1 !== 0;

        function update(now) {
            var elapsed = now - start;
            var progress = Math.min(elapsed / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = target * eased;
            el.textContent = isFloat ? current.toFixed(1) : Math.round(current);
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        requestAnimationFrame(update);
    });
});
