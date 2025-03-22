    // setup.js

    document.addEventListener('DOMContentLoaded', function() {
        // DOM elements
        const interfacesContainer = document.getElementById('interfaces-container');
        const nextBtn = document.getElementById('next-btn');
        const backBtn = document.getElementById('back-btn');
        const steps = [
            document.getElementById('step1'),
            document.getElementById('step2'),
            document.getElementById('step3'),
            document.getElementById('step4')
        ];
        const stepContainers = [
            document.getElementById('step1-container'),
            document.getElementById('step2-container'),
            document.getElementById('step3-container'),
            document.getElementById('step4-container')
        ];
        
        // WAN configuration elements
        const wanDhcp = document.getElementById('wan-dhcp');
        const wanStatic = document.getElementById('wan-static');
        const wanStaticConfig = document.getElementById('wan-static-config');
        
        // LAN configuration elements
        const lanDhcpServer = document.getElementById('lan-dhcp-server');
        const dhcpServerConfig = document.getElementById('dhcp-server-config');
        
        // Global state
        let currentStep = 1;
        let interfaces = [];
        let selectedWanInterface = null;
        let selectedLanInterfaces = [];
        
        // Initialize event listeners
        initEventListeners();
        
        // Fetch interfaces from API
        fetchInterfaces();
        
        function initEventListeners() {
            nextBtn.addEventListener('click', goToNextStep);
            backBtn.addEventListener('click', goToPrevStep);
            
            // Radio button events for WAN config
            wanDhcp.addEventListener('change', toggleWanConfig);
            wanStatic.addEventListener('change', toggleWanConfig);
            
            // Checkbox event for LAN DHCP server
            lanDhcpServer.addEventListener('change', toggleLanConfig);
        }
        
        function fetchInterfaces() {
            // Show loading
            interfacesContainer.innerHTML = '<div class="loading">Loading interfaces...</div>';
            
            fetch('/interfaces')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    interfaces = data;
                    // First load - initialize selections from database config
                    interfaces.forEach(iface => {
                        if (iface.is_wan) {
                            selectedWanInterface = iface.name;
                        } else {
                            selectedLanInterfaces.push(iface.name);
                        }
                    });
                    renderInterfaceCards();
                })
                .catch(error => {
                    console.error('Error fetching interfaces:', error);
                    interfacesContainer.innerHTML = '<div class="error">Error loading interfaces. Please refresh the page.</div>';
                });
        }
        
        function renderInterfaceCards() {
            interfacesContainer.innerHTML = '';
            
            // Render each interface card
            interfaces.forEach(iface => {
                const isWan = selectedWanInterface === iface.name;
                const isLan = selectedLanInterfaces.includes(iface.name);
                
                const card = document.createElement('div');
                card.className = 'interface-card';
                card.dataset.name = iface.name; // Store name in dataset for easy lookup
                
                if (isWan) {
                    card.classList.add('selected-wan');
                } else if (isLan) {
                    card.classList.add('selected-lan');
                }
                
                // Label for WAN/LAN
                const labelDiv = document.createElement('div');
                labelDiv.className = 'interface-label';
                if (isWan) {
                    labelDiv.classList.add('wan');
                    labelDiv.textContent = 'WAN';
                } else if (isLan) {
                    labelDiv.classList.add('lan');
                    labelDiv.textContent = 'LAN';
                } else {
                    labelDiv.classList.add('hidden');
                }
                card.appendChild(labelDiv);
                
                // Status indicator class
                const statusClass = iface.status === 'UP' ? 'status-up' : 'status-down';
                
                // Create interface details
                card.innerHTML += `
                    <div class="interface-header">
                        <div class="interface-name">
                            <div class="interface-icon"><i class="fas fa-network-wired"></i></div>
                            ${iface.name}
                        </div>
                    </div>
                    <div class="interface-details">
                        <div class="detail-row">
                            <div class="detail-label">Status:</div>
                            <div class="detail-value"><span class="status-indicator ${statusClass}"></span> ${iface.status}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">MAC:</div>
                            <div class="detail-value">${iface.mac || 'N/A'}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">IPs:</div>
                            <div class="detail-value">${iface.ips && iface.ips.length > 0 ? iface.ips.join(', ') : 'None'}</div>
                        </div>
                    </div>
                    <div class="interface-actions">
                        <button class="btn ${isWan ? 'btn-primary' : ''}" onclick="setWAN('${iface.name}')">Set as WAN</button>
                        <button class="btn ${isLan ? 'btn-success' : ''}" onclick="setLAN('${iface.name}')">Set as LAN</button>
                    </div>
                `;
                
                interfacesContainer.appendChild(card);
            });
        }
        
        // Define global functions for the buttons
        window.setWAN = function(name) {
            console.log('Setting WAN interface to:', name);
            selectedWanInterface = name;
            // Remove from LAN if it was there
            selectedLanInterfaces = selectedLanInterfaces.filter(n => n !== name);
            renderInterfaceCards();
        };
        
        window.setLAN = function(name) {
            console.log('Setting LAN interface:', name);
            // Cannot be WAN and LAN at the same time
            if (selectedWanInterface === name) {
                selectedWanInterface = null;
            }
            
            // Toggle LAN selection
            if (selectedLanInterfaces.includes(name)) {
                selectedLanInterfaces = selectedLanInterfaces.filter(n => n !== name);
            } else {
                selectedLanInterfaces.push(name);
            }
            
            renderInterfaceCards();
        };
        
        function toggleWanConfig() {
            if (wanStatic.checked) {
                wanStaticConfig.classList.remove('hidden');
            } else {
                wanStaticConfig.classList.add('hidden');
            }
        }
        
        function toggleLanConfig() {
            if (lanDhcpServer.checked) {
                dhcpServerConfig.classList.remove('hidden');
            } else {
                dhcpServerConfig.classList.add('hidden');
            }
        }
        
        function goToNextStep() {
            if (currentStep === 1) {
                // Validate WAN/LAN selection
                if (!selectedWanInterface) {
                    alert('Please select a WAN interface for internet connection.');
                    return;
                }
                
                if (selectedLanInterfaces.length === 0) {
                    alert('Please select at least one LAN interface for your local network.');
                    return;
                }
                
                // Save the interface assignments
                saveInterfaceAssignments()
                    .then(() => {
                        // Move to next step
                        currentStep++;
                        updateStepDisplay();
                    })
                    .catch(error => {
                        alert('Error saving interface assignments: ' + error.message);
                    });
            } else if (currentStep === 2) {
                // Save WAN configuration
                saveWanConfiguration()
                    .then(() => {
                        currentStep++;
                        updateStepDisplay();
                    })
                    .catch(error => {
                        alert('Error saving WAN configuration: ' + error.message);
                    });
            } else if (currentStep === 3) {
                // Save LAN configuration
                saveLanConfiguration()
                    .then(() => {
                        // Update review page
                        updateReviewPage();
                        currentStep++;
                        updateStepDisplay();
                    })
                    .catch(error => {
                        alert('Error saving LAN configuration: ' + error.message);
                    });
            } else if (currentStep === 4) {
                // Apply system configuration
                applySystemConfiguration()
                    .then(response => {
                        alert('Configuration applied successfully!');
                        window.location.href = '/dashboard';
                    })
                    .catch(error => {
                        alert('Error applying configuration: ' + error.message);
                    });
            }
        }
        
        function goToPrevStep() {
            if (currentStep > 1) {
                currentStep--;
                updateStepDisplay();
            }
        }
        
        function updateStepDisplay() {
            // Update step indicators
            for (let i = 0; i < steps.length; i++) {
                if (i + 1 < currentStep) {
                    steps[i].classList.remove('active');
                    steps[i].classList.add('completed');
                } else if (i + 1 === currentStep) {
                    steps[i].classList.add('active');
                    steps[i].classList.remove('completed');
                } else {
                    steps[i].classList.remove('active');
                    steps[i].classList.remove('completed');
                }
            }
            
            // Show/hide step containers
            for (let i = 0; i < stepContainers.length; i++) {
                if (i + 1 === currentStep) {
                    stepContainers[i].classList.remove('hidden');
                } else {
                    stepContainers[i].classList.add('hidden');
                }
            }
            
            // Show/hide back button
            if (currentStep > 1) {
                backBtn.classList.remove('hidden');
            } else {
                backBtn.classList.add('hidden');
            }
            
            // Update next button text
            if (currentStep === 4) {
                nextBtn.innerHTML = 'Apply Configuration <i class="fas fa-check"></i>';
            } else {
                nextBtn.innerHTML = 'Next <i class="fas fa-arrow-right"></i>';
            }
        }
        
        async function saveInterfaceAssignments() {
            const promises = [];
            
            // Update all interfaces with their WAN/LAN status
            interfaces.forEach(iface => {
                const isWan = iface.name === selectedWanInterface;
                const isCurrentlyWan = iface.is_wan;
                
                // Only update if the status changed
                if (isWan !== isCurrentlyWan) {
                    promises.push(
                        fetch(`/interfaces/${iface.name}`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                is_wan: isWan,
                                label: isWan ? 'WAN' : 'LAN'
                            })
                        }).then(response => {
                            if (!response.ok) {
                                throw new Error('Failed to update interface ' + iface.name);
                            }
                            // Update the local interface data
                            iface.is_wan = isWan;
                            return response.json();
                        })
                    );
                }
            });
            
            // Wait for all requests to complete
            return Promise.all(promises);
        }
        
        async function saveWanConfiguration() {
            if (!selectedWanInterface) {
                return Promise.reject(new Error('No WAN interface selected'));
            }
            
            const data = {
                dhcp_enabled: wanDhcp.checked
            };
            
            if (wanStatic.checked) {
                const ip = document.getElementById('wan-ip').value;
                const netmask = document.getElementById('wan-netmask').value;
                const gateway = document.getElementById('wan-gateway').value;
                const dns = document.getElementById('wan-dns').value;
                
                if (!ip || !netmask || !gateway) {
                    return Promise.reject(new Error('Please fill in all static IP fields'));
                }
                
                data.static_ip = ip;
                data.static_netmask = netmask;
                data.static_gateway = gateway;
                data.dns_servers = dns;
            }
            
            return fetch(`/interfaces/${selectedWanInterface}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update WAN configuration');
                }
                return response.json();
            });
        }
        
        async function saveLanConfiguration() {
            if (selectedLanInterfaces.length === 0) {
                return Promise.reject(new Error('No LAN interfaces selected'));
            }
            
            const lanIp = document.getElementById('lan-ip').value;
            const lanNetmask = document.getElementById('lan-netmask').value;
            
            if (!lanIp || !lanNetmask) {
                return Promise.reject(new Error('Please fill in all LAN IP fields'));
            }
            
            const data = {
                static_ip: lanIp,
                static_netmask: lanNetmask,
                dhcp_enabled: lanDhcpServer.checked
            };
            
            const promises = selectedLanInterfaces.map(name => 
                fetch(`/interfaces/${name}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                }).then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to update LAN configuration for ' + name);
                    }
                    return response.json();
                })
            );
            
            return Promise.all(promises);
        }
        
        function updateReviewPage() {
            const wanReview = document.getElementById('wan-review');
            const lanReview = document.getElementById('lan-review');
            
            // Update WAN review
            if (wanDhcp.checked) {
                wanReview.innerHTML = `
                    <p><strong>Interface:</strong> ${selectedWanInterface}</p>
                    <p><strong>Configuration:</strong> DHCP (automatic)</p>
                `;
            } else {
                wanReview.innerHTML = `
                    <p><strong>Interface:</strong> ${selectedWanInterface}</p>
                    <p><strong>Configuration:</strong> Static IP</p>
                    <p><strong>IP Address:</strong> ${document.getElementById('wan-ip').value}</p>
                    <p><strong>Subnet Mask:</strong> ${document.getElementById('wan-netmask').value}</p>
                    <p><strong>Gateway:</strong> ${document.getElementById('wan-gateway').value}</p>
                    <p><strong>DNS Servers:</strong> ${document.getElementById('wan-dns').value}</p>
                `;
            }
            
            // Update LAN review
            lanReview.innerHTML = `
                <p><strong>Interfaces:</strong> ${selectedLanInterfaces.join(', ')}</p>
                <p><strong>IP Address:</strong> ${document.getElementById('lan-ip').value}</p>
                <p><strong>Subnet Mask:</strong> ${document.getElementById('lan-netmask').value}</p>
                <p><strong>DHCP Server:</strong> ${lanDhcpServer.checked ? 'Enabled' : 'Disabled'}</p>
            `;
            
            if (lanDhcpServer.checked) {
                lanReview.innerHTML += `
                    <p><strong>DHCP Range:</strong> ${document.getElementById('dhcp-start').value} - ${document.getElementById('dhcp-end').value}</p>
                    <p><strong>Lease Time:</strong> ${document.getElementById('dhcp-lease').value} hours</p>
                `;
            }
        }
        
        async function applySystemConfiguration() {
            return fetch('/apply-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Failed to apply configuration');
                }
                return response.json();
            });
        }
    });