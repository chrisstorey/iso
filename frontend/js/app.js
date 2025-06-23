// This is the app.js file for frontend JavaScript logic.
document.addEventListener('DOMContentLoaded', function () {
    const serviceList = document.getElementById('service-list');
    const API_BASE_URL = 'http://localhost:8000'; // Assuming backend runs on port 8000

    // Initialize Leaflet Map (basic setup, will be enhanced later)
    const map = L.map('mapid').setView([51.505, -0.09], 13); // Default view
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Fetch and display services
    async function fetchServices() {
        try {
            const response = await fetch(`${API_BASE_URL}/services/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const services = await response.json();
            renderServices(services);
        } catch (error) {
            console.error("Could not fetch services:", error);
            serviceList.innerHTML = '<p class="text-danger">Failed to load services.</p>';
        }
    }

    // Render services to the page
    function renderServices(services) {
        clearMapMarkers(); // Clear existing markers first
        serviceList.innerHTML = ''; // Clear existing service list content

        if (!services || services.length === 0) {
            serviceList.innerHTML = '<p>No services found.</p>';
            return;
        }

        services.forEach(service => {
            const card = `
                <div class="card mb-3">
                    <div class="card-body">
                        <h5 class="card-title">${service.name}</h5>
                        <p class="card-text">${service.description || 'No description available.'}</p>
                        <!-- Add more service details here as needed -->
                    </div>
                </div>
            `;
            const cardDiv = document.createElement('div');
            cardDiv.innerHTML = card;

            // Add Edit button
            const editButton = document.createElement('button');
            editButton.className = 'btn btn-sm btn-outline-primary ml-2 edit-service-btn';
            editButton.textContent = 'Edit';
            editButton.dataset.serviceId = service.id;
            // Store all service data on the button for easy modal population
            editButton.dataset.serviceData = JSON.stringify(service);

            const deleteButton = document.createElement('button');
            deleteButton.className = 'btn btn-sm btn-outline-danger ml-2 delete-service-btn';
            deleteButton.textContent = 'Delete';
            deleteButton.dataset.serviceId = service.id;
            deleteButton.dataset.serviceName = service.name; // For confirmation dialog

            const buttonGroup = document.createElement('div');
            buttonGroup.className = 'mt-2'; // Add some margin for the button group
            buttonGroup.appendChild(editButton);
            buttonGroup.appendChild(deleteButton);

            cardDiv.querySelector('.card-body').appendChild(buttonGroup);
            serviceList.appendChild(cardDiv.firstChild); // Append the card (div.card.mb-3)

            // Add marker to map if location data is available
            if (service.location && service.location.type === "Point" && service.location.coordinates) {
                const [lon, lat] = service.location.coordinates;
                if (typeof lat === 'number' && typeof lon === 'number') {
                    const marker = L.marker([lat, lon]) // Leaflet uses [lat, lon]
                        .addTo(markerLayerGroup) // Add to layer group for easy clearing
                        .bindPopup(`<b>${service.name}</b><br>${service.description || ''}`);
                }
            }
        });
        addEditButtonListeners(); // Add listeners after buttons are in DOM
        addDeleteButtonListeners(); // Add listeners for delete buttons
    }

    // Helper function to clear all markers from the map
    const markerLayerGroup = L.layerGroup().addTo(map);
    function clearMapMarkers() {
        markerLayerGroup.clearLayers();
    }

    // Fetch and display services (now with filters)
    async function fetchServices(filters = {}) {
        try {
            const queryParams = new URLSearchParams();
            if (filters.category) queryParams.append('category', filters.category);
            if (filters.fees) queryParams.append('fees', filters.fees);
            // Add location filters to queryParams when implemented

            const response = await fetch(`${API_BASE_URL}/services/?${queryParams.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const services = await response.json();
            renderServices(services);
        } catch (error) {
            console.error("Could not fetch services:", error);
            serviceList.innerHTML = '<p class="text-danger">Failed to load services.</p>';
        }
    }

    // Initial fetch of services (no filters)
    fetchServices();

    // Handle filter form submission
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const category = document.getElementById('filter-category').value;
            const fees = document.getElementById('filter-fees').value;
            fetchServices({ category, fees });
        });
    }

    function addDeleteButtonListeners() {
        const deleteButtons = document.querySelectorAll('.delete-service-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const serviceId = this.dataset.serviceId;
                const serviceName = this.dataset.serviceName;
                if (confirm(`Are you sure you want to delete the service: "${serviceName}" (ID: ${serviceId})?`)) {
                    try {
                        const response = await fetch(`${API_BASE_URL}/services/${serviceId}`, {
                            method: 'DELETE',
                        });
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Failed to delete service'}`);
                        }
                        // const deletedService = await response.json(); // Or handle 204 No Content
                        alert(`Service "${serviceName}" deleted successfully.`);
                        fetchServices(); // Refresh the list of services
                    } catch (error) {
                        console.error('Failed to delete service:', error);
                        alert(`Error deleting service: ${error.message}`);
                    }
                }
            });
        });
    }

    // Handle clear filters button
    const clearFiltersButton = document.getElementById('clear-filters');
    if (clearFiltersButton) {
        clearFiltersButton.addEventListener('click', function() {
            document.getElementById('filter-category').value = '';
            document.getElementById('filter-fees').value = '';
            fetchServices(); // Fetch all services
        });
    }

    // Claimant form submission
    const addClaimantForm = document.getElementById('add-claimant-form');
    const claimantList = document.getElementById('claimant-list');

    async function fetchClaimants() {
        try {
            const response = await fetch(`${API_BASE_URL}/claimants/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const claimants = await response.json();
            renderClaimants(claimants);
        } catch (error) {
            console.error("Could not fetch claimants:", error);
            if(claimantList) claimantList.innerHTML = '<p class="text-danger">Failed to load claimants.</p>';
        }
    }

    function renderClaimants(claimants) {
        if (!claimantList) return;
        claimantList.innerHTML = ''; // Clear existing content
        if (!claimants || claimants.length === 0) {
            claimantList.innerHTML = '<p>No claimants found.</p>';
            return;
        }
        const ul = document.createElement('ul');
        ul.className = 'list-group';
        claimants.forEach(claimant => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            let content = `ID: ${claimant.id}, Name: ${claimant.name}, Home: (${claimant.home_latitude}, ${claimant.home_longitude})`;
            if (claimant.travel_extent_geojson) {
                content += ` (Travel extent defined)`;
            } else {
                content += ` (No travel extent defined)`;
            }
            li.textContent = content; // Set base content

            const editBtn = document.createElement('button');
            editBtn.className = 'btn btn-sm btn-outline-primary ml-2 claimant-edit-btn';
            editBtn.textContent = 'Edit';
            editBtn.dataset.claimantId = claimant.id;
            editBtn.dataset.claimantData = JSON.stringify(claimant);
            li.appendChild(editBtn);

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-sm btn-outline-danger ml-1 claimant-delete-btn';
            deleteBtn.textContent = 'Delete';
            deleteBtn.dataset.claimantId = claimant.id;
            deleteBtn.dataset.claimantName = claimant.name;
            li.appendChild(deleteBtn);

            ul.appendChild(li);
        });
        claimantList.appendChild(ul);
        addClaimantEditButtonListeners(); // Add listeners for new buttons
        addClaimantDeleteButtonListeners(); // Add listeners for new buttons
    }


    if (addClaimantForm) {
        addClaimantForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const name = document.getElementById('claimant-name').value;
            const lat = parseFloat(document.getElementById('claimant-lat').value);
            const lon = parseFloat(document.getElementById('claimant-lon').value);

            if (!name || isNaN(lat) || isNaN(lon)) {
                alert('Please fill in all fields correctly.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/claimants/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name: name, home_latitude: lat, home_longitude: lon }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
                }
                // const newClaimant = await response.json();
                // console.log('Claimant added:', newClaimant);
                addClaimantForm.reset(); // Clear the form
                fetchClaimants(); // Refresh the claimant list
                alert('Claimant added successfully!');
            } catch (error) {
                console.error('Failed to add claimant:', error);
                alert(`Error adding claimant: ${error.message}`);
            }
        });
    }

    // Initial fetch of claimants to populate dropdown and list
    fetchClaimants();

    // Handle Add Service form submission
    const addServiceForm = document.getElementById('add-service-form');
    if (addServiceForm) {
        addServiceForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const serviceData = {
                name: document.getElementById('service-name').value,
                description: document.getElementById('service-description').value || null,
                category: document.getElementById('service-category').value || null,
                url: document.getElementById('service-url').value || null,
                email: document.getElementById('service-email').value || null,
                fees: document.getElementById('service-fees').value || null,
                latitude: parseFloat(document.getElementById('service-latitude').value) || null,
                longitude: parseFloat(document.getElementById('service-longitude').value) || null,
            };

            // Remove null latitude/longitude if they weren't provided or are NaN
            if (serviceData.latitude === null || isNaN(serviceData.latitude)) delete serviceData.latitude;
            if (serviceData.longitude === null || isNaN(serviceData.longitude)) delete serviceData.longitude;


            if (!serviceData.name) {
                alert('Service Name is required.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/services/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(serviceData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
                }
                // const newService = await response.json();
                addServiceForm.reset();
                fetchServices(); // Refresh service list
                alert('Service added successfully!');
            } catch (error) {
                console.error('Failed to add service:', error);
                alert(`Error adding service: ${error.message}`);
            }
        });
    }

    // --- US6: Claimant Travel Area and Services Within ---
    const claimantSelect = document.getElementById('claimant-select');
    let travelAreaLayer = null; // To keep track of the travel area polygon on map

    // --- US8: Edit Service --- (This section remains as is)
    const editServiceModal = $('#editServiceModal');
    const editServiceForm = document.getElementById('edit-service-form');

    function populateEditServiceForm(service) {
        // ... (existing code for populating service edit form) ...
        document.getElementById('edit-service-id').value = service.id;
        document.getElementById('edit-service-name').value = service.name || '';
        document.getElementById('edit-service-description').value = service.description || '';
        document.getElementById('edit-service-category').value = service.category || '';
        document.getElementById('edit-service-url').value = service.url || '';
        document.getElementById('edit-service-email').value = service.email || '';
        document.getElementById('edit-service-fees').value = service.fees || '';
        if (service.location && service.location.type === "Point" && service.location.coordinates) {
            document.getElementById('edit-service-longitude').value = service.location.coordinates[0];
            document.getElementById('edit-service-latitude').value = service.location.coordinates[1];
        } else {
            document.getElementById('edit-service-latitude').value = '';
            document.getElementById('edit-service-longitude').value = '';
        }
    }

    function addEditButtonListeners() { // This is for services
        const editButtons = document.querySelectorAll('.edit-service-btn');
        editButtons.forEach(button => {
            button.addEventListener('click', function() {
                const serviceData = JSON.parse(this.dataset.serviceData);
                populateEditServiceForm(serviceData);
                editServiceModal.modal('show');
            });
        });
    }

    function addDeleteButtonListeners() { // This is for services
        const deleteButtons = document.querySelectorAll('.delete-service-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const serviceId = this.dataset.serviceId;
                const serviceName = this.dataset.serviceName;
                if (confirm(`Are you sure you want to delete the service: "${serviceName}" (ID: ${serviceId})?`)) {
                    try {
                        const response = await fetch(`${API_BASE_URL}/services/${serviceId}`, {
                            method: 'DELETE',
                        });
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Failed to delete service'}`);
                        }
                        alert(`Service "${serviceName}" deleted successfully.`);
                        fetchServices();
                    } catch (error) {
                        console.error('Failed to delete service:', error);
                        alert(`Error deleting service: ${error.message}`);
                    }
                }
            });
        });
    }

    if (editServiceForm) { // This is for services
        // ... (existing event listener for editServiceForm) ...
        editServiceForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const serviceId = document.getElementById('edit-service-id').value;
            const serviceData = {
                name: document.getElementById('edit-service-name').value,
                description: document.getElementById('edit-service-description').value || null,
                category: document.getElementById('edit-service-category').value || null,
                url: document.getElementById('edit-service-url').value || null,
                email: document.getElementById('edit-service-email').value || null,
                fees: document.getElementById('edit-service-fees').value || null,
                latitude: document.getElementById('edit-service-latitude').value ? parseFloat(document.getElementById('edit-service-latitude').value) : null,
                longitude: document.getElementById('edit-service-longitude').value ? parseFloat(document.getElementById('edit-service-longitude').value) : null,
            };

            if (isNaN(serviceData.latitude)) serviceData.latitude = null;
            if (isNaN(serviceData.longitude)) serviceData.longitude = null;

            const payload = {};
            for (const key in serviceData) {
                if (serviceData[key] !== null && serviceData[key] !== undefined) {
                    payload[key] = serviceData[key];
                }
            }
            const latVal = parseFloat(document.getElementById('edit-service-latitude').value);
            const lonVal = parseFloat(document.getElementById('edit-service-longitude').value);

            if (!isNaN(latVal) && !isNaN(lonVal)) {
                payload.latitude = latVal;
                payload.longitude = lonVal;
            } else if (document.getElementById('edit-service-latitude').value === '' && document.getElementById('edit-service-longitude').value === '') {
                payload.latitude = null;
                payload.longitude = null;
            }


            try {
                const response = await fetch(`${API_BASE_URL}/services/${serviceId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
                }
                editServiceModal.modal('hide');
                fetchServices();
                alert('Service updated successfully!');
            } catch (error) {
                console.error('Failed to update service:', error);
                alert(`Error updating service: ${error.message}`);
            }
        });
    }

    // --- US10: Manage Claimants ---
    const editClaimantModal = $('#editClaimantModal');
    const editClaimantForm = document.getElementById('edit-claimant-form');

    function populateEditClaimantForm(claimant) {
        document.getElementById('edit-claimant-id').value = claimant.id;
        document.getElementById('edit-claimant-name').value = claimant.name || '';
        document.getElementById('edit-claimant-lat').value = claimant.home_latitude || '';
        document.getElementById('edit-claimant-lon').value = claimant.home_longitude || '';
    }

    function addClaimantEditButtonListeners() {
        const editButtons = document.querySelectorAll('.claimant-edit-btn');
        editButtons.forEach(button => {
            button.addEventListener('click', function() {
                const claimantData = JSON.parse(this.dataset.claimantData);
                populateEditClaimantForm(claimantData);
                editClaimantModal.modal('show');
            });
        });
    }

    function addClaimantDeleteButtonListeners() {
        const deleteButtons = document.querySelectorAll('.claimant-delete-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const claimantId = this.dataset.claimantId;
                const claimantName = this.dataset.claimantName;
                if (confirm(`Are you sure you want to delete claimant: "${claimantName}" (ID: ${claimantId})?`)) {
                    try {
                        const response = await fetch(`${API_BASE_URL}/claimants/${claimantId}`, {
                            method: 'DELETE',
                        });
                        if (!response.ok) {
                            const errorData = await response.json();
                            throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Failed to delete claimant'}`);
                        }
                        alert(`Claimant "${claimantName}" deleted successfully.`);
                        fetchClaimants(); // Refresh claimant list and dropdown
                    } catch (error) {
                        console.error('Failed to delete claimant:', error);
                        alert(`Error deleting claimant: ${error.message}`);
                    }
                }
            });
        });
    }

    if (editClaimantForm) {
        editClaimantForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const claimantId = document.getElementById('edit-claimant-id').value;
            const payload = {
                name: document.getElementById('edit-claimant-name').value,
                home_latitude: parseFloat(document.getElementById('edit-claimant-lat').value),
                home_longitude: parseFloat(document.getElementById('edit-claimant-lon').value),
            };

            if (!payload.name || isNaN(payload.home_latitude) || isNaN(payload.home_longitude)) {
                alert('Please fill in all fields correctly for the claimant.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/claimants/${claimantId}`, {
                    method: 'PATCH', // Or PUT if full replacement is intended
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
                }
                editClaimantModal.modal('hide');
                fetchClaimants(); // Refresh claimant list and dropdown
                alert('Claimant updated successfully!');
            } catch (error) {
                console.error('Failed to update claimant:', error);
                alert(`Error updating claimant: ${error.message}`);
            }
        });
    }

    async function populateClaimantDropdown(claimants) {
        document.getElementById('edit-service-id').value = service.id;
        document.getElementById('edit-service-name').value = service.name || '';
        document.getElementById('edit-service-description').value = service.description || '';
        document.getElementById('edit-service-category').value = service.category || '';
        document.getElementById('edit-service-url').value = service.url || '';
        document.getElementById('edit-service-email').value = service.email || '';
        document.getElementById('edit-service-fees').value = service.fees || '';
        if (service.location && service.location.type === "Point" && service.location.coordinates) {
            document.getElementById('edit-service-longitude').value = service.location.coordinates[0];
            document.getElementById('edit-service-latitude').value = service.location.coordinates[1];
        } else {
            document.getElementById('edit-service-latitude').value = '';
            document.getElementById('edit-service-longitude').value = '';
        }
    }

    function addEditButtonListeners() {
        const editButtons = document.querySelectorAll('.edit-service-btn');
        editButtons.forEach(button => {
            button.addEventListener('click', function() {
                const serviceData = JSON.parse(this.dataset.serviceData);
                populateEditServiceForm(serviceData);
                editServiceModal.modal('show');
            });
        });
    }

    if (editServiceForm) {
        editServiceForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const serviceId = document.getElementById('edit-service-id').value;
            const serviceData = {
                name: document.getElementById('edit-service-name').value,
                description: document.getElementById('edit-service-description').value || null,
                category: document.getElementById('edit-service-category').value || null,
                url: document.getElementById('edit-service-url').value || null,
                email: document.getElementById('edit-service-email').value || null,
                fees: document.getElementById('edit-service-fees').value || null,
                // Parse lat/lon, send null if empty or invalid to allow clearing them
                latitude: document.getElementById('edit-service-latitude').value ? parseFloat(document.getElementById('edit-service-latitude').value) : null,
                longitude: document.getElementById('edit-service-longitude').value ? parseFloat(document.getElementById('edit-service-longitude').value) : null,
            };

            // Pydantic expects either both lat/lon or neither for a valid Point.
            // If one is filled and the other isn't, it's ambiguous.
            // We'll send them if both are valid numbers, otherwise we might need to exclude them or send both as null
            // to explicitly clear location. For PATCH, we only send fields that changed.
            // The backend CRUD for update handles {lat, lon} or {lat:null, lon:null} to clear.
            // If only one is null and other is not, it's tricky. Best to ensure both are sent if either is touched.
            // For simplicity, if one is NaN after parse, make both null to signal clearing or no-change if they were already null.
            if (isNaN(serviceData.latitude)) serviceData.latitude = null;
            if (isNaN(serviceData.longitude)) serviceData.longitude = null;

            // If user clears one field, they likely mean to clear location or it's an invalid state.
            // To clear location, both lat & lon should be null.
            // If one is provided and the other is not (or invalid), we might choose to not send lat/lon at all,
            // relying on PATCH to only update provided fields.
            // However, our ServiceUpdate schema has both as optional.
            // Let's construct the payload carefully for PATCH.
            const payload = {};
            for (const key in serviceData) {
                if (serviceData[key] !== null && serviceData[key] !== undefined) { // Check for undefined too
                    // Specifically for lat/lon, if one is provided, the other must also be (or be null to clear)
                    if ((key === 'latitude' && serviceData['longitude'] === null) || (key === 'longitude' && serviceData['latitude'] === null)) {
                        // If one is set and the other is explicitly cleared to null, this is ambiguous for a Point.
                        // Let's assume if one is present, the other should be too.
                        // If user clears one, they should clear both to remove location.
                        // For now, if this state is reached, we might not send location update.
                        // This part needs careful UX and backend validation alignment.
                        // A simpler PATCH: only include lat/lon if BOTH are valid numbers.
                    }
                    payload[key] = serviceData[key];
                }
            }
             // Refined logic for lat/lon in PATCH:
            const latVal = parseFloat(document.getElementById('edit-service-latitude').value);
            const lonVal = parseFloat(document.getElementById('edit-service-longitude').value);

            if (!isNaN(latVal) && !isNaN(lonVal)) {
                payload.latitude = latVal;
                payload.longitude = lonVal;
            } else if (document.getElementById('edit-service-latitude').value === '' && document.getElementById('edit-service-longitude').value === '') {
                // If both are explicitly empty, signal to backend to nullify location.
                // Backend's update_service handles this by setting location to None if lat/lon are null.
                payload.latitude = null;
                payload.longitude = null;
            } // If one is filled and other is empty/invalid, we don't send lat/lon to avoid partial update.


            try {
                const response = await fetch(`${API_BASE_URL}/services/${serviceId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
                }
                editServiceModal.modal('hide');
                fetchServices(); // Refresh service list & markers
                alert('Service updated successfully!');
            } catch (error) {
                console.error('Failed to update service:', error);
                alert(`Error updating service: ${error.message}`);
            }
        });
    }


    async function populateClaimantDropdown(claimants) {
        if (!claimantSelect) return;
        claimantSelect.innerHTML = '<option value="">-- Select a Claimant --</option>'; // Clear existing options
        claimants.forEach(claimant => {
            const option = document.createElement('option');
            option.value = claimant.id;
            option.textContent = `${claimant.name} (ID: ${claimant.id})`;
            // Store full claimant object if needed, or just enough data
            option.dataset.claimantData = JSON.stringify(claimant);
            claimantSelect.appendChild(option);
        });
    }

    if (claimantSelect) {
        claimantSelect.addEventListener('change', async function() {
            const claimantId = this.value;
            clearMapMarkers(); // Clear service markers
            if (travelAreaLayer) {
                map.removeLayer(travelAreaLayer); // Clear previous travel area
                travelAreaLayer = null;
            }

            if (!claimantId) {
                fetchServices(); // No claimant selected, show all services (or based on filters)
                return;
            }

            // Fetch claimant details to get travel_extent_geojson
            // This assumes the claimant data in the dropdown option is sufficient
            // or we make another fetch for /claimants/{claimant_id} if needed.
            // For simplicity, using the data stored if available.
            const selectedOption = this.options[this.selectedIndex];
            let claimant;
            if (selectedOption.dataset.claimantData) {
                claimant = JSON.parse(selectedOption.dataset.claimantData);
            } else {
                // Fallback: fetch if not in dataset (should not happen if populated correctly)
                // const claimantResp = await fetch(`${API_BASE_URL}/claimants/${claimantId}`);
                // if (!claimantResp.ok) { /* handle error */ return; }
                // claimant = await claimantResp.json();
                console.error("Claimant data not found in dropdown option for ID:", claimantId);
                return;
            }

            if (claimant && claimant.travel_extent_geojson) {
                travelAreaLayer = L.geoJSON(claimant.travel_extent_geojson, {
                    style: function (feature) {
                        return {color: "#ff7800", weight: 2, opacity: 0.65, fillOpacity: 0.1};
                    }
                }).addTo(map);
                map.fitBounds(travelAreaLayer.getBounds()); // Zoom to the travel area
            }

            // Fetch services within this claimant's area
            try {
                const response = await fetch(`${API_BASE_URL}/services/within/claimant/${claimantId}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.detail || 'Unknown error'}`);
                }
                const servicesWithinArea = await response.json();
                renderServices(servicesWithinArea); // Render only these services
            } catch (error) {
                console.error("Could not fetch services within claimant's area:", error);
                serviceList.innerHTML = `<p class="text-danger">Failed to load services for claimant: ${error.message}</p>`;
            }
        });
    }

    // Modify fetchClaimants to also populate the dropdown
    async function fetchClaimants() { // Original fetchClaimants is modified
        try {
            const response = await fetch(`${API_BASE_URL}/claimants/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const claimants = await response.json();
            renderClaimants(claimants);
            populateClaimantDropdown(claimants); // Populate dropdown
        } catch (error) {
            console.error("Could not fetch claimants:", error);
            if(claimantList) claimantList.innerHTML = '<p class="text-danger">Failed to load claimants.</p>';
        }
    }


    console.log("Frontend app.js loaded and initialized.");
});
