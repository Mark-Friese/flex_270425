/**
 * Flexibility Analysis System - Frontend Application
 * 
 * This script handles the interaction between the web UI and the Python backend
 * through the PyWebView JS API.
 */

document.addEventListener('DOMContentLoaded', function() {
    // UI Element References
    const loadConfigBtn = document.getElementById('loadConfigBtn');
    const outputDirBtn = document.getElementById('outputDirBtn');
    const viewLogsBtn = document.getElementById('viewLogsBtn');
    const configStatus = document.getElementById('configStatus');
    const substationSelect = document.getElementById('substationSelect');
    const generateCompetitionsCheck = document.getElementById('generateCompetitionsCheck');
    const targetYearInput = document.getElementById('targetYearInput');
    const analysisForm = document.getElementById('analysisForm');
    const runAnalysisBtn = document.getElementById('runAnalysisBtn');
    const statusArea = document.getElementById('statusArea');
    const progressBar = document.getElementById('progressBar');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const resultsArea = document.getElementById('resultsArea');
    const summaryTable = document.getElementById('summaryTable').querySelector('tbody');
    const plotsContainer = document.getElementById('plotsContainer');
    const competitionsContainer = document.getElementById('competitionsContainer');
    const mapContainer = document.getElementById('mapContainer');
    const logsContent = document.getElementById('logsContent');
    const previousResultsList = document.getElementById('previousResultsList');
    
    // Map instance
    let map = null;
    
    // Current results state
    let currentSubstation = null;
    let currentResults = null;
    
    // Event Listeners
    loadConfigBtn.addEventListener('click', handleLoadConfig);
    outputDirBtn.addEventListener('click', handleSetOutputDir);
    viewLogsBtn.addEventListener('click', handleViewLogs);
    analysisForm.addEventListener('submit', handleRunAnalysis);
    substationSelect.addEventListener('change', handleSubstationChange);
    
    // Tab change listeners for map initialization
    document.getElementById('map-tab').addEventListener('shown.bs.tab', function() {
        initMap();
    });
    
    // Check for config data on load
    initializeApp();
    
    /**
     * Initialize the application
     */
    async function initializeApp() {
        try {
            // Try to load default config
            const result = await window.pywebview.api.load_config();
            
            if (result.status === 'success') {
                updateConfigStatus(true);
                populateSubstations(await window.pywebview.api.get_substations());
                loadPreviousResults();
            } else {
                updateConfigStatus(false);
            }
        } catch (error) {
            console.error('Error initializing app:', error);
            updateConfigStatus(false);
        }
    }
    
    /**
     * Handle loading configuration file
     */
    async function handleLoadConfig() {
        try {
            // Open file dialog
            const fileResult = await window.pywebview.api.select_config_file();
            
            if (fileResult.status === 'cancelled') {
                return;
            }
            
            if (fileResult.status === 'success') {
                setStatus('Loading configuration...', 'info');
                showProgress();
                
                // Load the selected config
                const result = await window.pywebview.api.load_config(fileResult.path);
                
                hideProgress();
                
                if (result.status === 'success') {
                    setStatus('Configuration loaded successfully.', 'success');
                    updateConfigStatus(true);
                    
                    // Load substations
                    populateSubstations(await window.pywebview.api.get_substations());
                    
                    // Load previous results
                    loadPreviousResults();
                } else {
                    setStatus(`Error loading config: ${result.message}`, 'danger');
                    updateConfigStatus(false);
                }
            } else {
                setStatus(`Error selecting config file: ${fileResult.message}`, 'danger');
            }
        } catch (error) {
            hideProgress();
            setStatus(`Error: ${error}`, 'danger');
            console.error('Error loading config:', error);
        }
    }
    
    /**
     * Handle setting output directory
     */
    async function handleSetOutputDir() {
        try {
            const result = await window.pywebview.api.select_output_directory();
            
            if (result.status === 'cancelled') {
                return;
            }
            
            if (result.status === 'success') {
                setStatus(`Output directory set to: ${result.path}`, 'info');
                
                // Reload previous results
                loadPreviousResults();
            } else {
                setStatus(`Error setting output directory: ${result.message}`, 'danger');
            }
        } catch (error) {
            setStatus(`Error: ${error}`, 'danger');
            console.error('Error setting output directory:', error);
        }
    }
    
    /**
     * Handle viewing application logs
     */
    async function handleViewLogs() {
        try {
            // Not implemented in backend API yet - would load logs from file
            logsContent.textContent = "Log viewing not implemented yet";
            
            // Show modal
            const logsModal = new bootstrap.Modal(document.getElementById('logsModal'));
            logsModal.show();
        } catch (error) {
            setStatus(`Error viewing logs: ${error}`, 'danger');
            console.error('Error viewing logs:', error);
        }
    }
    
    /**
     * Handle running analysis
     */
    async function handleRunAnalysis(event) {
        event.preventDefault();
        
        const selectedSubstation = substationSelect.value;
        if (!selectedSubstation) {
            setStatus('Please select a substation first.', 'warning');
            return;
        }
        
        try {
            setStatus(`Running analysis for ${selectedSubstation}...`, 'info');
            showProgress();
            
            // Gather parameters
            const params = {
                generate_competitions: generateCompetitionsCheck.checked,
                target_year: targetYearInput.value || null
            };
            
            // Run analysis
            const result = await window.pywebview.api.run_analysis(selectedSubstation, params);
            
            if (result.status === 'success') {
                setStatus(`Analysis completed successfully for ${selectedSubstation}.`, 'success');
                currentSubstation = selectedSubstation;
                
                // Get full results
                await loadResults(selectedSubstation);
                
                // Refresh previous results list
                loadPreviousResults();
            } else {
                setStatus(`Error in analysis: ${result.message}`, 'danger');
                console.error('Analysis error details:', result.details);
            }
        } catch (error) {
            setStatus(`Error: ${error}`, 'danger');
            console.error('Error running analysis:', error);
        } finally {
            hideProgress();
        }
    }
    
    /**
     * Handle substation selection change
     */
    async function handleSubstationChange() {
        const selectedSubstation = substationSelect.value;
        if (!selectedSubstation) return;
        
        currentSubstation = selectedSubstation;
        
        try {
            // Check for existing results
            await loadResults(selectedSubstation);
        } catch (error) {
            console.error('Error checking for results:', error);
            hideResults();
        }
    }
    
    /**
     * Load results for a substation
     */
    async function loadResults(substationName) {
        try {
            const results = await window.pywebview.api.get_results(substationName);
            
            if (results.status === 'success') {
                setStatus(`Loaded results for ${substationName}.`, 'info');
                displayResults(results);
                currentResults = results;
                
                // Update previous results list to show current selection
                const previousItems = document.querySelectorAll('.previous-result-item');
                previousItems.forEach(item => {
                    if (item.dataset.substation === substationName) {
                        item.classList.add('active');
                    } else {
                        item.classList.remove('active');
                    }
                });
                
                return true;
            } else {
                hideResults();
                return false;
            }
        } catch (error) {
            console.error('Error loading results:', error);
            hideResults();
            return false;
        }
    }
    
    /**
     * Load and display list of previous results
     */
    async function loadPreviousResults() {
        try {
            const results = await window.pywebview.api.get_all_results();
            
            if (results.status === 'success' && results.summary && results.summary.length > 0) {
                const list = document.createElement('div');
                list.className = 'list-group';
                
                results.summary.forEach(result => {
                    const substation = result.substation;
                    const item = document.createElement('div');
                    item.className = 'list-group-item list-group-item-action previous-result-item';
                    if (currentSubstation === substation) {
                        item.classList.add('active');
                    }
                    item.dataset.substation = substation;
                    
                    const nameEl = document.createElement('div');
                    nameEl.className = 'fw-bold';
                    nameEl.textContent = substation;
                    
                    const detailsEl = document.createElement('div');
                    detailsEl.className = 'small text-muted';
                    detailsEl.textContent = `Firm Capacity: ${result.C_peak_MW?.toFixed(2) || 'N/A'} MW`;
                    
                    item.appendChild(nameEl);
                    item.appendChild(detailsEl);
                    
                    item.addEventListener('click', () => {
                        substationSelect.value = substation;
                        loadResults(substation);
                    });
                    
                    list.appendChild(item);
                });
                
                previousResultsList.innerHTML = '';
                previousResultsList.appendChild(list);
            } else {
                previousResultsList.innerHTML = '<p class="text-center text-muted">No results available</p>';
            }
        } catch (error) {
            console.error('Error loading previous results:', error);
            previousResultsList.innerHTML = '<p class="text-center text-danger">Error loading results</p>';
        }
    }
    
    /**
     * Update configuration status display
     */
    function updateConfigStatus(loaded) {
        if (loaded) {
            configStatus.innerHTML = '<span class="badge bg-success">Config Loaded</span>';
            runAnalysisBtn.disabled = false;
            substationSelect.disabled = false;
        } else {
            configStatus.innerHTML = '<span class="badge bg-warning">Config Not Loaded</span>';
            runAnalysisBtn.disabled = true;
            substationSelect.disabled = true;
        }
    }
    
    /**
     * Populate substations dropdown
     */
    function populateSubstations(result) {
        if (result.status !== 'success') {
            console.error('Error loading substations:', result.message);
            return;
        }
        
        // Clear existing options except the default one
        while (substationSelect.options.length > 1) {
            substationSelect.remove(1);
        }
        
        const substations = result.substations;
        
        // Add substation options
        if (substations && substations.length > 0) {
            substations.forEach(substation => {
                const option = document.createElement('option');
                option.value = substation;
                option.textContent = substation;
                substationSelect.appendChild(option);
            });
            
            substationSelect.disabled = false;
        } else {
            // No substations found
            const option = document.createElement('option');
            option.disabled = true;
            option.textContent = 'No substations found in config';
            substationSelect.appendChild(option);
        }
    }
    
    /**
     * Display results in the UI
     */
    function displayResults(results) {
        // Show results area and hide no results message
        resultsArea.classList.remove('d-none');
        noResultsMessage.classList.add('d-none');
        
        // Set summary title
        document.getElementById('summaryTitle').textContent = `Results for ${results.results.substation}`;
        
        // Update metrics
        document.getElementById('metricCPlain').textContent = formatNumber(results.results.C_plain_MW);
        document.getElementById('metricCPeak').textContent = formatNumber(results.results.C_peak_MW);
        document.getElementById('metricMeanDemand').textContent = formatNumber(results.results.mean_demand_MW);
        document.getElementById('metricMaxDemand').textContent = formatNumber(results.results.max_demand_MW);
        document.getElementById('metricTotalEnergy').textContent = formatNumber(results.results.total_energy_MWh);
        document.getElementById('metricEnergyAbove').textContent = formatNumber(results.results.energy_above_capacity_MWh);
        document.getElementById('metricTarget').textContent = formatNumber(results.results.target_mwh);
        
        // Update competitions count
        const competitionsCount = results.competitions ? results.competitions.length : 0;
        document.getElementById('metricCompetitions').textContent = competitionsCount;
        
        // Display summary table
        summaryTable.innerHTML = '';
        
        for (const [key, value] of Object.entries(results.results)) {
            const row = document.createElement('tr');
            const keyCell = document.createElement('td');
            const valueCell = document.createElement('td');
            
            keyCell.textContent = formatKey(key);
            valueCell.textContent = formatValue(value);
            
            row.appendChild(keyCell);
            row.appendChild(valueCell);
            summaryTable.appendChild(row);
        }
        
        // Display plots
        displayPlots(results.plots);
        
        // Display competitions
        displayCompetitions(results.competitions);
        
        // Update map if initialized
        if (map) {
            updateMap(results);
        }
    }
    
    /**
     * Display plots in the plots tab
     */
    function displayPlots(plots) {
        plotsContainer.innerHTML = '';
        
        if (plots && plots.length > 0) {
            const plotsRow = document.createElement('div');
            plotsRow.className = 'row mt-3';
            
            plots.forEach(plot => {
                const col = document.createElement('div');
                col.className = 'col-md-6 mb-4';
                
                const plotCard = document.createElement('div');
                plotCard.className = 'card h-100';
                
                const cardHeader = document.createElement('div');
                cardHeader.className = 'card-header';
                cardHeader.textContent = formatKey(plot.name);
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body text-center';
                
                const plotContainer = document.createElement('div');
                plotContainer.className = 'plot-image-container';
                
                const img = document.createElement('img');
                img.src = plot.path;
                img.className = 'img-fluid';
                img.alt = plot.name;
                img.title = formatKey(plot.name);
                
                // Add click to view full size
                img.addEventListener('click', () => {
                    window.open(plot.path, '_blank');
                });
                
                plotContainer.appendChild(img);
                cardBody.appendChild(plotContainer);
                
                plotCard.appendChild(cardHeader);
                plotCard.appendChild(cardBody);
                col.appendChild(plotCard);
                plotsRow.appendChild(col);
            });
            
            plotsContainer.appendChild(plotsRow);
        } else {
            plotsContainer.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>No plots available
                </div>
            `;
        }
    }
    
    /**
     * Display competitions in the competitions tab
     */
    function displayCompetitions(competitions) {
        competitionsContainer.innerHTML = '';
        
        if (competitions && competitions.length > 0) {
            // Create accordion for competitions
            const accordion = document.createElement('div');
            accordion.className = 'accordion mt-3';
            accordion.id = 'competitionsAccordion';
            
            competitions.forEach((competition, index) => {
                const accordionItem = document.createElement('div');
                accordionItem.className = 'accordion-item';
                
                const headerId = `competition-heading-${index}`;
                const collapseId = `competition-collapse-${index}`;
                
                // Header
                const header = document.createElement('h2');
                header.className = 'accordion-header';
                header.id = headerId;
                
                const button = document.createElement('button');
                button.className = 'accordion-button collapsed';
                button.type = 'button';
                button.setAttribute('data-bs-toggle', 'collapse');
                button.setAttribute('data-bs-target', `#${collapseId}`);
                button.setAttribute('aria-expanded', 'false');
                button.setAttribute('aria-controls', collapseId);
                
                const headerContent = document.createElement('div');
                headerContent.className = 'competition-header w-100';
                
                const titleSpan = document.createElement('span');
                titleSpan.textContent = `${competition.name} (${competition.reference})`;
                
                const badgesSpan = document.createElement('span');
                badgesSpan.className = 'competition-badges';
                
                // Add badges for periods and windows
                const periodCount = competition.service_periods ? competition.service_periods.length : 0;
                const periodBadge = document.createElement('span');
                periodBadge.className = 'badge bg-primary me-2';
                periodBadge.textContent = `${periodCount} Periods`;
                
                let windowCount = 0;
                if (competition.service_periods) {
                    competition.service_periods.forEach(period => {
                        if (period.service_windows) {
                            windowCount += period.service_windows.length;
                        }
                    });
                }
                
                const windowBadge = document.createElement('span');
                windowBadge.className = 'badge bg-secondary';
                windowBadge.textContent = `${windowCount} Windows`;
                
                badgesSpan.appendChild(periodBadge);
                badgesSpan.appendChild(windowBadge);
                
                headerContent.appendChild(titleSpan);
                headerContent.appendChild(badgesSpan);
                button.appendChild(headerContent);
                header.appendChild(button);
                
                // Body
                const collapseDiv = document.createElement('div');
                collapseDiv.id = collapseId;
                collapseDiv.className = 'accordion-collapse collapse';
                collapseDiv.setAttribute('aria-labelledby', headerId);
                collapseDiv.setAttribute('data-bs-parent', '#competitionsAccordion');
                
                const accordionBody = document.createElement('div');
                accordionBody.className = 'accordion-body';
                
                // Competition details
                const detailsCard = document.createElement('div');
                detailsCard.className = 'card bg-light mb-3';
                
                const detailsBody = document.createElement('div');
                detailsBody.className = 'card-body';
                
                // Competition basic info
                const basicInfo = document.createElement('div');
                basicInfo.className = 'row mb-3';
                
                const infoItems = [
                    { label: 'Reference', value: competition.reference },
                    { label: 'Need Type', value: competition.need_type },
                    { label: 'Type', value: competition.type },
                    { label: 'Need Direction', value: competition.need_direction },
                    { label: 'Power Type', value: competition.power_type }
                ];
                
                infoItems.forEach(item => {
                    const col = document.createElement('div');
                    col.className = 'col-md-4 col-sm-6 mb-2';
                    
                    const infoGroup = document.createElement('div');
                    infoGroup.className = 'small';
                    
                    const label = document.createElement('div');
                    label.className = 'text-muted';
                    label.textContent = item.label;
                    
                    const value = document.createElement('div');
                    value.className = 'fw-bold';
                    value.textContent = item.value;
                    
                    infoGroup.appendChild(label);
                    infoGroup.appendChild(value);
                    col.appendChild(infoGroup);
                    basicInfo.appendChild(col);
                });
                
                detailsBody.appendChild(basicInfo);
                
                // Dates
                const datesSection = document.createElement('div');
                datesSection.className = 'mb-3';
                
                const datesTitle = document.createElement('h5');
                datesTitle.className = 'card-title';
                datesTitle.textContent = 'Competition Dates';
                
                const datesRow = document.createElement('div');
                datesRow.className = 'row';
                
                const dateItems = [
                    { label: 'Qualification Open', value: formatDateTime(competition.qualification_open) },
                    { label: 'Qualification Closed', value: formatDateTime(competition.qualification_closed) },
                    { label: 'Bidding Open', value: formatDateTime(competition.open) },
                    { label: 'Bidding Closed', value: formatDateTime(competition.closed) }
                ];
                
                dateItems.forEach(item => {
                    const col = document.createElement('div');
                    col.className = 'col-md-3 col-sm-6 mb-2';
                    
                    const dateGroup = document.createElement('div');
                    dateGroup.className = 'small';
                    
                    const label = document.createElement('div');
                    label.className = 'text-muted';
                    label.textContent = item.label;
                    
                    const value = document.createElement('div');
                    value.className = 'fw-bold';
                    value.textContent = item.value;
                    
                    dateGroup.appendChild(label);
                    dateGroup.appendChild(value);
                    col.appendChild(dateGroup);
                    datesRow.appendChild(col);
                });
                
                datesSection.appendChild(datesTitle);
                datesSection.appendChild(datesRow);
                detailsBody.appendChild(datesSection);
                
                // Service Periods
                if (competition.service_periods && competition.service_periods.length > 0) {
                    const periodsSection = document.createElement('div');
                    
                    const periodsTitle = document.createElement('h5');
                    periodsTitle.className = 'card-title mt-4';
                    periodsTitle.textContent = 'Service Periods';
                    
                    const periodsAccordion = document.createElement('div');
                    periodsAccordion.className = 'accordion';
                    periodsAccordion.id = `periods-accordion-${index}`;
                    
                    competition.service_periods.forEach((period, periodIndex) => {
                        const periodItem = document.createElement('div');
                        periodItem.className = 'accordion-item';
                        
                        const periodHeaderId = `period-heading-${index}-${periodIndex}`;
                        const periodCollapseId = `period-collapse-${index}-${periodIndex}`;
                        
                        // Period header
                        const periodHeader = document.createElement('h2');
                        periodHeader.className = 'accordion-header';
                        periodHeader.id = periodHeaderId;
                        
                        const periodButton = document.createElement('button');
                        periodButton.className = 'accordion-button collapsed';
                        periodButton.type = 'button';
                        periodButton.setAttribute('data-bs-toggle', 'collapse');
                        periodButton.setAttribute('data-bs-target', `#${periodCollapseId}`);
                        periodButton.setAttribute('aria-expanded', 'false');
                        periodButton.setAttribute('aria-controls', periodCollapseId);
                        
                        const periodTitle = document.createElement('div');
                        periodTitle.className = 'd-flex justify-content-between w-100';
                        
                        const periodName = document.createElement('span');
                        periodName.textContent = period.name;
                        
                        const periodDates = document.createElement('span');
                        periodDates.className = 'text-muted small ms-3';
                        periodDates.textContent = `${formatDate(period.start)} - ${formatDate(period.end)}`;
                        
                        const periodWindowCount = document.createElement('span');
                        periodWindowCount.className = 'badge bg-info ms-auto';
                        periodWindowCount.textContent = `${period.service_windows?.length || 0} Windows`;
                        
                        periodTitle.appendChild(periodName);
                        periodTitle.appendChild(periodDates);
                        periodTitle.appendChild(periodWindowCount);
                        
                        periodButton.appendChild(periodTitle);
                        periodHeader.appendChild(periodButton);
                        
                        // Period body
                        const periodCollapseDiv = document.createElement('div');
                        periodCollapseDiv.id = periodCollapseId;
                        periodCollapseDiv.className = 'accordion-collapse collapse';
                        periodCollapseDiv.setAttribute('aria-labelledby', periodHeaderId);
                        periodCollapseDiv.setAttribute('data-bs-parent', `#periods-accordion-${index}`);
                        
                        const periodBody = document.createElement('div');
                        periodBody.className = 'accordion-body';
                        
                        // Windows table
                        if (period.service_windows && period.service_windows.length > 0) {
                            const windowsTable = document.createElement('div');
                            windowsTable.className = 'table-responsive';
                            
                            const table = document.createElement('table');
                            table.className = 'table table-sm table-striped table-hover';
                            
                            const thead = document.createElement('thead');
                            const headerRow = document.createElement('tr');
                            
                            ['Window', 'Time', 'Days', 'Capacity (MW)'].forEach(headerText => {
                                const th = document.createElement('th');
                                th.textContent = headerText;
                                headerRow.appendChild(th);
                            });
                            
                            thead.appendChild(headerRow);
                            table.appendChild(thead);
                            
                            const tbody = document.createElement('tbody');
                            
                            period.service_windows.forEach(window => {
                                const row = document.createElement('tr');
                                
                                const nameCell = document.createElement('td');
                                nameCell.textContent = window.name;
                                
                                const timeCell = document.createElement('td');
                                timeCell.textContent = `${window.start} - ${window.end}`;
                                
                                const daysCell = document.createElement('td');
                                daysCell.textContent = window.service_days.join(', ');
                                
                                const capacityCell = document.createElement('td');
                                capacityCell.textContent = window.capacity_required;
                                
                                row.appendChild(nameCell);
                                row.appendChild(timeCell);
                                row.appendChild(daysCell);
                                row.appendChild(capacityCell);
                                
                                tbody.appendChild(row);
                            });
                            
                            table.appendChild(tbody);
                            windowsTable.appendChild(table);
                            periodBody.appendChild(windowsTable);
                        } else {
                            periodBody.innerHTML = '<div class="alert alert-info">No service windows for this period</div>';
                        }
                        
                        periodCollapseDiv.appendChild(periodBody);
                        
                        periodItem.appendChild(periodHeader);
                        periodItem.appendChild(periodCollapseDiv);
                        periodsAccordion.appendChild(periodItem);
                    });
                    
                    periodsSection.appendChild(periodsTitle);
                    periodsSection.appendChild(periodsAccordion);
                    detailsBody.appendChild(periodsSection);
                }
                
                // Add JSON view toggle button
                const jsonToggle = document.createElement('button');
                jsonToggle.className = 'btn btn-sm btn-outline-secondary mt-3';
                jsonToggle.innerHTML = '<i class="fas fa-code me-1"></i>View JSON Data';
                
                const jsonView = document.createElement('pre');
                jsonView.className = 'json-viewer mt-3 d-none';
                jsonView.textContent = JSON.stringify(competition, null, 2);
                
                jsonToggle.addEventListener('click', () => {
                    if (jsonView.classList.contains('d-none')) {
                        jsonView.classList.remove('d-none');
                        jsonToggle.innerHTML = '<i class="fas fa-code-branch me-1"></i>Hide JSON Data';
                    } else {
                        jsonView.classList.add('d-none');
                        jsonToggle.innerHTML = '<i class="fas fa-code me-1"></i>View JSON Data';
                    }
                });
                
                detailsBody.appendChild(jsonToggle);
                detailsBody.appendChild(jsonView);
                
                detailsCard.appendChild(detailsBody);
                accordionBody.appendChild(detailsCard);
                
                collapseDiv.appendChild(accordionBody);
                
                accordionItem.appendChild(header);
                accordionItem.appendChild(collapseDiv);
                accordion.appendChild(accordionItem);
            });
            
            competitionsContainer.appendChild(accordion);
        } else {
            competitionsContainer.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>No competitions available
                </div>
            `;
        }
    }
    
    /**
     * Initialize or update the map
     */
    function initMap() {
        if (map) {
            // Map already initialized, just update
            if (currentResults) {
                updateMap(currentResults);
            }
            return;
        }
        
        // Clear container
        mapContainer.innerHTML = '';
        
        // Initialize map
        map = L.map(mapContainer).setView([55.378, -3.436], 6); // Center on UK
        
        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Update with current results if available
        if (currentResults) {
            updateMap(currentResults);
        } else {
            // Add placeholder content if no results
            mapContainer.innerHTML = `
                <div class="alert alert-info position-absolute" style="z-index: 1000; top: 10px; left: 10px; right: 10px;">
                    <i class="fas fa-info-circle me-2"></i>No data to display on map. Please run an analysis first.
                </div>
                <div id="map-placeholder" style="height: 100%; width: 100%;"></div>
            `;
            
            // Initialize placeholder map
            const placeholderMap = L.map('map-placeholder').setView([55.378, -3.436], 6);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(placeholderMap);
        }
        
        // Force a resize to ensure the map renders correctly
        setTimeout(() => {
            if (map) {
                map.invalidateSize();
            }
        }, 100);
    }
    
    /**
     * Update map with results data
     */
    function updateMap(results) {
        if (!map) return;
        
        // Clear existing markers and layers
        map.eachLayer(layer => {
            if (layer instanceof L.Marker || layer instanceof L.Circle) {
                map.removeLayer(layer);
            }
        });
        
        const substation = results.results.substation;
        
        // In a real implementation, you'd use actual coordinates from your data
        // This is just a placeholder using random coordinates near the UK
        const lat = 55.378 + (Math.random() - 0.5) * 2;
        const lng = -3.436 + (Math.random() - 0.5) * 2;
        
        // Add marker
        const marker = L.marker([lat, lng]).addTo(map);
        
        // Create popup content
        let popupContent = `
            <div class="map-popup">
                <h5>${substation}</h5>
                <div><strong>Firm Capacity:</strong> ${formatNumber(results.results.C_peak_MW)} MW</div>
                <div><strong>Max Demand:</strong> ${formatNumber(results.results.max_demand_MW)} MW</div>
                <div><strong>Energy Above Capacity:</strong> ${formatNumber(results.results.energy_above_capacity_MWh)} MWh</div>
            </div>
        `;
        
        if (results.competitions && results.competitions.length > 0) {
            popupContent += `<div class="mt-2"><strong>Competitions:</strong> ${results.competitions.length}</div>`;
        }
        
        marker.bindPopup(popupContent);
        
        // Add circle to represent capacity
        const circle = L.circle([lat, lng], {
            color: 'red',
            fillColor: '#f03',
            fillOpacity: 0.2,
            radius: results.results.C_peak_MW * 500 // Scale for visualization
        }).addTo(map);
        
        // Center map on marker
        map.setView([lat, lng], 10);
    }
    
    /**
     * Hide the results display
     */
    function hideResults() {
        resultsArea.classList.add('d-none');
        noResultsMessage.classList.remove('d-none');
    }
    
    /**
     * Set status message
     */
    function setStatus(message, type = 'info') {
        statusArea.className = `alert alert-${type} mb-0`;
        statusArea.innerHTML = message;
    }
    
    /**
     * Show progress bar
     */
    function showProgress() {
        progressBar.classList.remove('d-none');
    }
    
    /**
     * Hide progress bar
     */
    function hideProgress() {
        progressBar.classList.add('d-none');
    }
    
    /**
     * Format a field key for display
     */
    function formatKey(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase())
            .replace('Mw', 'MW')
            .replace('Mwh', 'MWh');
    }
    
    /**
     * Format a value for display
     */
    function formatValue(value) {
        if (typeof value === 'number') {
            return formatNumber(value);
        }
        return value;
    }
    
    /**
     * Format a number with appropriate precision
     */
    function formatNumber(value) {
        if (typeof value !== 'number') return value;
        
        // If it's a whole number or nearly whole, format as integer
        if (Math.abs(value - Math.round(value)) < 0.00001) {
            return Math.round(value).toLocaleString();
        }
        
        // Otherwise format with 2 decimal places
        return parseFloat(value).toFixed(2).toLocaleString();
    }
    
    /**
     * Format a date string
     */
    function formatDate(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString();
        } catch (error) {
            return dateString;
        }
    }
    
    /**
     * Format a date-time string
     */
    function formatDateTime(dateTimeString) {
        if (!dateTimeString) return '';
        
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleString();
        } catch (error) {
            return dateTimeString;
        }
    }
});
