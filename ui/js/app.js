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
    let mapLayers = {};
    let layerControls = null;
    let substationCoordinates = null;
    
    // Current results state
    let currentSubstation = null;
    let currentResults = null;
    
    // Event Listeners
    loadConfigBtn.addEventListener('click', handleLoadConfig);
    outputDirBtn.addEventListener('click', handleSetOutputDir);
    viewLogsBtn.addEventListener('click', handleViewLogs);
    analysisForm.addEventListener('submit', handleRunAnalysis);
    substationSelect.addEventListener('change', handleSubstationChange);
    
    // Add event listeners for map data import/export if the elements exist
    document.getElementById('mapDataFile')?.addEventListener('change', () => {
        document.getElementById('importStatus').style.display = 'none';
    });
    
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
                
                // Try to load substation coordinates
                loadMapData();
            } else {
                updateConfigStatus(false);
            }
            
            // Add event listener for map tab to ensure map loads correctly
            document.querySelector('#resultsTabs button[data-bs-target="#map"]').addEventListener('shown.bs.tab', function() {
                if (map) {
                    map.invalidateSize();
                    
                    // If we have current results and coordinates were loaded after map initialization,
                    // update the map with real coordinates
                    if (currentResults && substationCoordinates) {
                        updateMap(currentResults);
                    }
                } else {
                    initMap();
                }
                
                // Update map data status
                updateMapDataStatus();
            });
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
     * Load substation coordinates and demand group data from the JSON file
     */
    async function loadMapData() {
        try {
            const response = await fetch('assets/substation_coordinates.json');
            if (!response.ok) {
                throw new Error(`Failed to load map data: ${response.status}`);
            }
            
            substationCoordinates = await response.json();
            console.log(`Loaded data for ${substationCoordinates.substations.length} substations and ${substationCoordinates.demand_groups?.length || 0} demand groups`);
            
            // Return the data in case it's needed directly
            return substationCoordinates;
        } catch (error) {
            console.error('Error loading map data:', error);
            setStatus(`Warning: Could not load substation and demand group data. Map will use approximate locations.`, 'warning');
            
            // Return null to indicate failure
            return null;
        }
    }

    /**
     * Get coordinates for a specific substation
     * 
     * @param {string} substationName - The name of the substation
     * @returns {Object|null} - Object with lat/lng and metadata or null if not found
     */
    function getSubstationData(substationName) {
        if (!substationCoordinates || !substationCoordinates.substations) {
            return null;
        }
        
        // Try to find a case-insensitive match
        const normalizedName = substationName.toLowerCase().trim();
        return substationCoordinates.substations.find(s => 
            s.name.toLowerCase() === normalizedName
        );
    }

    /**
     * Get demand group data for a given group ID
     * 
     * @param {string} groupId - The ID of the demand group
     * @returns {Object|null} - Demand group data or null if not found
     */
    function getDemandGroupData(groupId) {
        if (!substationCoordinates || !substationCoordinates.demand_groups) {
            return null;
        }
        
        return substationCoordinates.demand_groups.find(g => g.id === groupId);
    }

    /**
     * Get demand group data that contains a specific substation
     * 
     * @param {string} substationName - The name of the substation
     * @returns {Object|null} - Demand group data or null if not found
     */
    function getDemandGroupForSubstation(substationName) {
        if (!substationCoordinates || !substationCoordinates.demand_groups) {
            return null;
        }
        
        const normalizedName = substationName.toLowerCase().trim();
        
        return substationCoordinates.demand_groups.find(group => 
            group.metadata && 
            group.metadata.substations && 
            group.metadata.substations.some(sub => sub.toLowerCase() === normalizedName)
        );
    }
    
    /**
     * Initialize or update the map
     */
    function initMap() {
        if (map) {
            // Map already initialized, just update the data
            if (currentResults) {
                updateMap(currentResults);
            }
            return;
        }
        
        // Clear container
        mapContainer.innerHTML = '';
        
        // Initialize map - use defaults from config or fallback to UK center
        const mapDefaults = substationCoordinates?.map_defaults || {
            center: { lat: 55.378, lng: -3.436 },
            zoom: 6,
            max_zoom: 18,
            min_zoom: 5
        };
        
        map = L.map(mapContainer, {
            center: [mapDefaults.center.lat, mapDefaults.center.lng],
            zoom: mapDefaults.zoom,
            maxZoom: mapDefaults.max_zoom,
            minZoom: mapDefaults.min_zoom
        });
        
        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Add map controls
        L.control.scale().addTo(map);
        
        // Initialize layer groups
        mapLayers = {
            substations: L.layerGroup().addTo(map),
            demandGroups: L.layerGroup().addTo(map),
            highlightedSubstation: L.layerGroup().addTo(map),
            highlightedGroup: L.layerGroup().addTo(map)
        };
        
        // Add layer controls if we have layer definitions
        if (substationCoordinates && substationCoordinates.layers) {
            const overlayMaps = {};
            
            substationCoordinates.layers.forEach(layer => {
                if (layer.id === 'substations') {
                    overlayMaps['Substations'] = mapLayers.substations;
                } else if (layer.id === 'demand_groups') {
                    overlayMaps['Demand Groups'] = mapLayers.demandGroups;
                }
                
                // Set initial visibility
                if (!layer.visible) {
                    map.removeLayer(mapLayers[layer.id === 'substations' ? 'substations' : 'demandGroups']);
                }
            });
            
            layerControls = L.control.layers(null, overlayMaps).addTo(map);
        }
        
        // Add custom control for legend
        addMapLegend();
        
        // Load all substations and demand groups
        renderAllMapData();
        
        // Update with current results if available
        if (currentResults) {
            highlightSelectedSubstation(currentResults.results.substation);
        }
        
        // Force a resize to ensure the map renders correctly
        setTimeout(() => {
            if (map) {
                map.invalidateSize();
            }
        }, 100);
    }

    /**
     * Render all substations and demand groups on the map
     */
    function renderAllMapData() {
        if (!map || !substationCoordinates) return;
        
        // Clear existing layers
        mapLayers.substations.clearLayers();
        mapLayers.demandGroups.clearLayers();
        
        // Add demand group polygons first (so they're under substations)
        if (substationCoordinates.demand_groups) {
            substationCoordinates.demand_groups.forEach(group => {
                if (!group.polygon || !group.polygon.points || group.polygon.points.length < 3) return;
                
                const polygon = L.polygon(group.polygon.points, {
                    color: group.polygon.color || '#00A443',
                    fillColor: group.polygon.fillColor || '#00A44333',
                    fillOpacity: 0.2,
                    weight: group.polygon.weight || 2
                });
                
                // Create popup content for demand group
                let popupContent = `
                    <div class="map-popup">
                        <h5>${group.name}</h5>
                        <div><strong>Firm Capacity:</strong> ${formatNumber(group.metadata.firm_capacity_mw)} MW</div>
                        <div><strong>Energy Above Capacity:</strong> ${formatNumber(group.metadata.energy_above_capacity_mwh)} MWh</div>
                        <div><strong>Substations:</strong> ${group.metadata.substation_count}</div>
                    </div>
                `;
                
                // Add list of substations if available
                if (group.metadata.substations && group.metadata.substations.length > 0) {
                    popupContent += '<div class="mt-2"><strong>Included Substations:</strong><ul>';
                    
                    group.metadata.substations.forEach(subName => {
                        // Find the substation to get its display name
                        const sub = substationCoordinates.substations.find(s => s.name === subName);
                        const displayName = sub ? sub.display_name : subName;
                        
                        popupContent += `<li>${displayName}</li>`;
                    });
                    
                    popupContent += '</ul></div>';
                }
                
                polygon.bindPopup(popupContent);
                
                // Add mouseover/mouseout effects
                polygon.on('mouseover', function(e) {
                    this.setStyle({ 
                        fillOpacity: 0.4,
                        weight: 3
                    });
                });
                
                polygon.on('mouseout', function(e) {
                    this.setStyle({ 
                        fillOpacity: 0.2,
                        weight: group.polygon.weight || 2
                    });
                });
                
                // Add to demand groups layer
                mapLayers.demandGroups.addLayer(polygon);
            });
        }
        
        // Add substations
        if (substationCoordinates.substations) {
            substationCoordinates.substations.forEach(substation => {
                if (!substation.coordinates) return;
                
                // Determine marker icon
                const markerIcon = L.divIcon({
                    className: 'custom-div-icon',
                    html: `<div style="background-color: ${substation.icon?.color || '#00A443'}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
                    iconSize: [14, 14],
                    iconAnchor: [7, 7]
                });
                
                const marker = L.marker([substation.coordinates.lat, substation.coordinates.lng], {
                    icon: markerIcon,
                    title: substation.display_name
                });
                
                // Create popup content
                let popupContent = `
                    <div class="map-popup">
                        <h5>${substation.display_name}</h5>
                        <div><strong>Voltage Level:</strong> ${substation.metadata.voltage_level || 'N/A'}</div>
                        <div><strong>Capacity:</strong> ${formatNumber(substation.metadata.capacity_mw)} MW</div>
                        <div><strong>Region:</strong> ${substation.metadata.region || 'N/A'}</div>
                    </div>
                `;
                
                // Add demand group info if available
                if (substation.metadata.demand_group) {
                    const group = getDemandGroupData(substation.metadata.demand_group);
                    if (group) {
                        popupContent += `<div class="mt-2"><strong>Demand Group:</strong> ${group.name}</div>`;
                    }
                }
                
                marker.bindPopup(popupContent);
                
                // Add click handler to select this substation
                marker.on('click', function() {
                    // Check if this substation exists in the substationSelect dropdown
                    const option = Array.from(substationSelect.options).find(opt => 
                        opt.value.toLowerCase() === substation.name.toLowerCase()
                    );
                    
                    if (option) {
                        substationSelect.value = option.value;
                        handleSubstationChange();
                    }
                });
                
                // Add to substations layer
                mapLayers.substations.addLayer(marker);
            });
        }
    }

    /**
     * Highlight a specific substation and its demand group
     */
    function highlightSelectedSubstation(substationName) {
        if (!map) return;
        
        // Clear previous highlights
        mapLayers.highlightedSubstation.clearLayers();
        mapLayers.highlightedGroup.clearLayers();
        
        // Get substation data
        const substation = getSubstationData(substationName);
        if (!substation) return;
        
        // Add highlight circle for the substation
        const highlightCircle = L.circle([substation.coordinates.lat, substation.coordinates.lng], {
            color: '#FF9C1A',
            fillColor: '#FF9C1A',
            fillOpacity: 0.3,
            weight: 2,
            radius: 300 // Fixed size for visibility
        });
        
        mapLayers.highlightedSubstation.addLayer(highlightCircle);
        
        // Highlight associated demand group if it exists
        const demandGroup = getDemandGroupForSubstation(substationName);
        if (demandGroup && demandGroup.polygon && demandGroup.polygon.points) {
            const highlightPolygon = L.polygon(demandGroup.polygon.points, {
                color: '#FF9C1A',
                fillColor: '#FF9C1A33',
                fillOpacity: 0.3,
                weight: 3,
                dashArray: '5, 5' // Dashed line for highlight
            });
            
            mapLayers.highlightedGroup.addLayer(highlightPolygon);
        }
        
        // Pan to the substation
        map.setView([substation.coordinates.lat, substation.coordinates.lng], 12);
    }
    
    /**
     * Update map with results data for a specific substation
     */
    function updateMap(results) {
        if (!map) return;
        
        // First, render all map data if it hasn't been done yet
        if (mapLayers.substations.getLayers().length === 0) {
            renderAllMapData();
        }
        
        const substationName = results.results.substation;
        
        // Highlight the selected substation
        highlightSelectedSubstation(substationName);
        
        // Get substation data
        const substation = getSubstationData(substationName);
        if (!substation) return;
        
        // Create a results circle to show capacity
        mapLayers.highlightedSubstation.clearLayers();
        
        // Add results circle
        const resultsCircle = L.circle([substation.coordinates.lat, substation.coordinates.lng], {
            color: '#FF9C1A',
            fillColor: '#FF9C1A80',
            fillOpacity: 0.3,
            weight: 2,
            radius: results.results.C_peak_MW * 500 // Scale for visualization
        });
        
        // Create popup content
        let popupContent = `
            <div class="map-popup">
                <h5>${substation.display_name}</h5>
                <div><strong>Firm Capacity:</strong> ${formatNumber(results.results.C_peak_MW)} MW</div>
                <div><strong>Max Demand:</strong> ${formatNumber(results.results.max_demand_MW)} MW</div>
                <div><strong>Energy Above Capacity:</strong> ${formatNumber(results.results.energy_above_capacity_MWh)} MWh</div>
                <div><strong>Voltage Level:</strong> ${substation.metadata.voltage_level || 'N/A'}</div>
            </div>
        `;
        
        if (results.competitions && results.competitions.length > 0) {
            popupContent += `<div class="mt-2"><strong>Competitions:</strong> ${results.competitions.length}</div>`;
        }
        
        resultsCircle.bindPopup(popupContent);
        mapLayers.highlightedSubstation.addLayer(resultsCircle);
    }

    /**
     * Add a custom legend to the map
     */
    function addMapLegend() {
        if (!map) return;
        
        // Create a custom control for the legend
        const legend = L.control({position: 'bottomright'});
        
        legend.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'info legend');
            div.style.backgroundColor = 'white';
            div.style.padding = '10px';
            div.style.borderRadius = '4px';
            div.style.boxShadow = '0 1px 5px rgba(0,0,0,0.4)';
            
            div.innerHTML = `
                <h6 style="margin-top: 0; margin-bottom: 8px; color: #00402A;">Legend</h6>
                <div style="margin-bottom: 5px;">
                    <div style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #00A443; border: 2px solid white; vertical-align: middle;"></div>
                    <span style="margin-left: 5px; vertical-align: middle;">Primary Substation</span>
                </div>
                <div style="margin-bottom: 5px;">
                    <div style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #0DA9FF; border: 2px solid white; vertical-align: middle;"></div>
                    <span style="margin-left: 5px; vertical-align: middle;">Secondary Substation</span>
                </div>
                <div style="margin-bottom: 5px;">
                    <div style="display: inline-block; width: 16px; height: 6px; background-color: #00A443; vertical-align: middle;"></div>
                    <span style="margin-left: 5px; vertical-align: middle;">Demand Group</span>
                </div>
                <div>
                    <div style="display: inline-block; width: 16px; height: 6px; background-color: #FF9C1A; vertical-align: middle;"></div>
                    <span style="margin-left: 5px; vertical-align: middle;">Selected Item</span>
                </div>
            `;
            return div;
        };
        
        legend.addTo(map);
    }
    
    /**
     * Update map data status display
     */
    /**
     * Show the data import modal
     */
    function showDataImportModal() {
        const dataImportModal = new bootstrap.Modal(document.getElementById('dataImportModal'));
        dataImportModal.show();
        
        // Reset any previous status message
        const importStatus = document.getElementById('importStatus');
        if (importStatus) {
            importStatus.style.display = 'none';
        }
    }

    /**
     * Handle JSON file import for substation and demand group data
     */
    async function handleMapDataImport() {
        const fileInput = document.getElementById('mapDataFile');
        const importStatus = document.getElementById('importStatus');
        
        if (!fileInput || fileInput.files.length === 0) {
            importStatus.className = 'alert alert-warning';
            importStatus.textContent = 'Please select a file to import.';
            importStatus.style.display = 'block';
            return;
        }
        
        const file = fileInput.files[0];
        
        // Check file extension
        if (!file.name.toLowerCase().endsWith('.json')) {
            importStatus.className = 'alert alert-danger';
            importStatus.textContent = 'Only JSON files are supported.';
            importStatus.style.display = 'block';
            return;
        }
        
        try {
            // Read the file
            const fileContent = await readFileAsText(file);
            let mapData;
            
            try {
                // Parse JSON
                mapData = JSON.parse(fileContent);
            } catch (error) {
                importStatus.className = 'alert alert-danger';
                importStatus.textContent = 'Invalid JSON file: ' + error.message;
                importStatus.style.display = 'block';
                return;
            }
            
            // Basic validation
            if (!mapData.substations || !Array.isArray(mapData.substations)) {
                importStatus.className = 'alert alert-danger';
                importStatus.textContent = 'Invalid data format: Missing substations array.';
                importStatus.style.display = 'block';
                return;
            }
            
            // Validate data schema
            const validationResult = validateMapData(mapData);
            if (!validationResult.valid) {
                importStatus.className = 'alert alert-danger';
                importStatus.textContent = 'Invalid data: ' + validationResult.error;
                importStatus.style.display = 'block';
                return;
            }
            
            // Update the local data
            substationCoordinates = mapData;
            
            // Update the map
            if (map) {
                renderAllMapData();
                if (currentResults) {
                    updateMap(currentResults);
                }
            }
            
            importStatus.className = 'alert alert-success';
            importStatus.textContent = 'Map data imported successfully.';
            importStatus.style.display = 'block';
            
            // Close modal after a delay
            setTimeout(() => {
                try {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('dataImportModal'));
                    if (modal) modal.hide();
                } catch (e) {
                    console.error('Error closing modal:', e);
                }
            }, 1500);
            
            // Update the map data status
            updateMapDataStatus();
        } catch (error) {
            importStatus.className = 'alert alert-danger';
            importStatus.textContent = 'Error reading file: ' + error.message;
            importStatus.style.display = 'block';
        }
    }

    /**
     * Read a file as text
     * 
     * @param {File} file - The file to read
     * @returns {Promise<string>} - The file contents as text
     */
    function readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = event => resolve(event.target.result);
            reader.onerror = error => reject(error);
            reader.readAsText(file);
        });
    }

    /**
     * Validate map data structure
     * 
     * @param {Object} data - The map data to validate
     * @returns {Object} - Validation result {valid: boolean, error: string}
     */
    function validateMapData(data) {
        // Check if substations is an array
        if (!Array.isArray(data.substations)) {
            return { valid: false, error: 'Substations must be an array' };
        }
        
        // Check each substation
        for (const sub of data.substations) {
            if (!sub.name) {
                return { valid: false, error: 'Each substation must have a name' };
            }
            
            if (!sub.coordinates || typeof sub.coordinates.lat !== 'number' || typeof sub.coordinates.lng !== 'number') {
                return { valid: false, error: `Substation ${sub.name} has invalid coordinates` };
            }
        }
        
        // Check demand groups if present
        if (data.demand_groups) {
            if (!Array.isArray(data.demand_groups)) {
                return { valid: false, error: 'Demand groups must be an array' };
            }
            
            for (const group of data.demand_groups) {
                if (!group.id || !group.name) {
                    return { valid: false, error: 'Each demand group must have an id and name' };
                }
                
                if (!group.polygon || !Array.isArray(group.polygon.points) || group.polygon.points.length < 3) {
                    return { valid: false, error: `Demand group ${group.name} has invalid polygon data` };
                }
            }
        }
        
        return { valid: true };
    }

    /**
     * Export current map data to a JSON file
     */
    function exportMapData() {
        if (!substationCoordinates) {
            setStatus('No map data available to export.', 'warning');
            return;
        }
        
        try {
            // Create JSON content
            const jsonContent = JSON.stringify(substationCoordinates, null, 2);
            
            // Create blob
            const blob = new Blob([jsonContent], { type: 'application/json' });
            
            // Create download link
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'substation_coordinates.json';
            
            // Trigger download
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            document.body.removeChild(a);
            URL.revokeObjectURL(a.href);
            
            setStatus('Map data exported successfully.', 'success');
        } catch (error) {
            console.error('Error exporting map data:', error);
            setStatus('Error exporting map data: ' + error.message, 'danger');
        }
    }

    /**
     * Auto-generate map data based on current substations
     */
    function autoGenerateMapData() {
        if (!confirm("This will generate temporary coordinates for all substations in your configuration. Continue?")) {
            return;
        }
        
        const statusDiv = document.getElementById('mapDataStatus');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="alert alert-info">
                    <div class="d-flex align-items-center">
                        <div class="spinner-border spinner-border-sm me-2" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <div>Generating map data...</div>
                    </div>
                </div>
            `;
        }
        
        // Get all substations from the dropdown
        const substations = Array.from(substationSelect.options)
            .filter(opt => opt.value)
            .map(opt => ({
                name: opt.value,
                display_name: opt.textContent,
            }));
        
        // Create a basic map data structure
        const mapData = {
            substations: [],
            demand_groups: [],
            layers: [
                {
                    id: "substations",
                    name: "Substations",
                    type: "marker",
                    visible: true,
                    source: "substations"
                },
                {
                    id: "demand_groups",
                    name: "Demand Groups",
                    type: "polygon",
                    visible: true,
                    source: "demand_groups"
                }
            ],
            map_defaults: {
                center: { lat: 55.378, lng: -3.436 },
                zoom: 6,
                max_zoom: 18,
                min_zoom: 5
            }
        };
        
        // Generate coordinates for each substation
        const baseLatLng = { lat: 55.378, lng: -3.436 }; // Center of UK
        const groups = {};
        
        substations.forEach((substation, index) => {
            // Determine group - assign substations to groups of 3
            const groupIndex = Math.floor(index / 3);
            const groupId = `auto_group_${groupIndex}`;
            
            // Generate coordinates in a circle around the base point
            const angle = (index / substations.length) * 2 * Math.PI;
            const radius = 0.3 + (groupIndex * 0.15); // Different radius for each group
            
            const lat = baseLatLng.lat + (radius * Math.cos(angle));
            const lng = baseLatLng.lng + (radius * Math.sin(angle));
            
            // Create substation entry
            mapData.substations.push({
                name: substation.name,
                display_name: substation.display_name,
                coordinates: { lat, lng },
                metadata: {
                    voltage_level: "33/11kV",
                    region: `Region ${groupIndex + 1}`,
                    capacity_mw: 30 + (index % 5) * 5, // Random capacity between 30-50 MW
                    transformer_count: 1 + (index % 3),
                    demand_group: groupId
                },
                icon: {
                    color: index % 2 === 0 ? "#00A443" : "#0DA9FF", // Alternate colors
                    size: "medium"
                }
            });
            
            // Track substations in groups
            if (!groups[groupId]) {
                groups[groupId] = {
                    name: `Auto Group ${groupIndex + 1}`,
                    substations: [],
                    center: { lat: 0, lng: 0 }
                };
            }
            
            groups[groupId].substations.push(substation.name);
            groups[groupId].center.lat += lat;
            groups[groupId].center.lng += lng;
        });
        
        // Create demand groups
        Object.entries(groups).forEach(([groupId, group]) => {
            const subCount = group.substations.length;
            if (subCount === 0) return;
            
            // Calculate center
            const centerLat = group.center.lat / subCount;
            const centerLng = group.center.lng / subCount;
            
            // Create polygon points (hexagon)
            const polygonPoints = [];
            const polygonSize = 0.15 + (subCount * 0.02);
            
            for (let i = 0; i < 6; i++) {
                const angle = (i / 6) * 2 * Math.PI;
                polygonPoints.push({
                    lat: centerLat + polygonSize * Math.cos(angle),
                    lng: centerLng + polygonSize * Math.sin(angle)
                });
            }
            
            // Add closing point
            polygonPoints.push(polygonPoints[0]);
            
            // Add to demand groups
            mapData.demand_groups.push({
                id: groupId,
                name: group.name,
                polygon: {
                    color: "#00A443",
                    fillColor: "#00A44333",
                    weight: 2,
                    points: polygonPoints
                },
                metadata: {
                    firm_capacity_mw: 30 * subCount,
                    total_energy_mwh: 800 * subCount,
                    energy_above_capacity_mwh: 20 * subCount,
                    substation_count: subCount,
                    substations: group.substations,
                    peak_demand_time: "2025-01-15T18:30:00Z"
                }
            });
        });
        
        // Update the map data
        substationCoordinates = mapData;
        
        // Update the map if it exists
        if (map) {
            renderAllMapData();
            if (currentResults) {
                updateMap(currentResults);
            }
        }
        
        // Update status
        updateMapDataStatus();
        
        setStatus(`Auto-generated map data for ${mapData.substations.length} substations in ${mapData.demand_groups.length} groups.`, 'success');
    }
    
    function updateMapDataStatus() {
        const statusDiv = document.getElementById('mapDataStatus');
        if (!statusDiv) return;
        
        // Check if we have configuration
        if (!window.pywebview || !window.pywebview.api) {
            statusDiv.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    API not initialized. Please refresh the page.
                </div>
            `;
            return;
        }
        
        if (!substationCoordinates) {
            statusDiv.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No map data loaded. Click the Auto-Generate button to create temporary coordinates.
                </div>
            `;
            return;
        }
        
        // Check if we have substations in the configuration
        if (!substationSelect || substationSelect.options.length <= 1) {
            statusDiv.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No substations found in configuration.
                </div>
            `;
            return;
        }
        
        // Count matched and unmatched substations
        const configSubstations = Array.from(substationSelect.options)
            .filter(opt => opt.value)
            .map(opt => opt.value);
            
        const matchedSubstations = [];
        const unmatchedSubstations = [];
        
        configSubstations.forEach(subName => {
            const sub = getSubstationData(subName);
            if (sub) {
                matchedSubstations.push(subName);
            } else {
                unmatchedSubstations.push(subName);
            }
        });
        
        // Calculate match percentage
        const total = configSubstations.length;
        const matchPercent = total > 0 ? Math.round((matchedSubstations.length / total) * 100) : 0;
        
        let statusHtml = `
            <div class="mb-3">
                <div class="d-flex justify-content-between mb-1">
                    <div>Substation Match Rate:</div>
                    <div><strong>${matchPercent}%</strong> (${matchedSubstations.length}/${total})</div>
                </div>
                <div class="progress" style="height: 10px;">
                    <div class="progress-bar ${matchPercent >= 75 ? 'bg-success' : matchPercent >= 50 ? 'bg-warning' : 'bg-danger'}" 
                         role="progressbar" 
                         style="width: ${matchPercent}%;" 
                         aria-valuenow="${matchPercent}" 
                         aria-valuemin="0" 
                         aria-valuemax="100"></div>
                </div>
            </div>
        `;
        
        // Add matched substations
        if (matchedSubstations.length > 0) {
            statusHtml += `
                <div class="mb-3">
                    <h6>Matched Substations</h6>
                    <div class="table-responsive">
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    <th>Substation</th>
                                    <th>Coordinates</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            matchedSubstations.slice(0, 5).forEach(subName => {
                const sub = getSubstationData(subName);
                statusHtml += `
                    <tr>
                        <td>${sub.display_name || subName}</td>
                        <td>${sub.coordinates.lat.toFixed(4)}, ${sub.coordinates.lng.toFixed(4)}</td>
                    </tr>
                `;
            });
            
            if (matchedSubstations.length > 5) {
                statusHtml += `
                    <tr>
                        <td colspan="2" class="text-center">
                            <em>...and ${matchedSubstations.length - 5} more</em>
                        </td>
                    </tr>
                `;
            }
            
            statusHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
        
        // Add unmatched substations
        if (unmatchedSubstations.length > 0) {
            statusHtml += `
                <div>
                    <h6>Unmatched Substations</h6>
                    <div class="alert alert-warning">
                        <p class="mb-1">The following substations don't have coordinates:</p>
                        <div style="max-height: 100px; overflow-y: auto;">
                            ${unmatchedSubstations.join(', ')}
                        </div>
                        <p class="mt-2 mb-0">
                            Click <a href="#" onclick="autoGenerateMapData(); return false;">Auto-Generate</a> 
                            to create temporary coordinates for these substations.
                        </p>
                    </div>
                </div>
            `;
        } else if (total > 0) {
            statusHtml += `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    All substations have coordinates mapped!
                </div>
            `;
        } else {
            statusHtml += `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    No substations found in the current configuration.
                </div>
            `;
        }
        
        statusDiv.innerHTML = statusHtml;
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
