/**
 * Map Data API Service
 * 
 * This module provides functions to fetch GIS data from the API instead of local files.
 */

class MapDataService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || 'http://localhost:8000'; // Default API base URL
        this.endpoints = {
            substations: '/api/gis/substations',
            demandGroups: '/api/gis/demand-groups',
            circuits: '/api/gis/circuits'
        };
    }

    /**
     * Convert API GeoJSON response to the format expected by the application
     * 
     * @param {Object} geoJson - GeoJSON response from the API
     * @returns {Object} - Formatted data for the application
     */
    _convertSubstationsGeoJsonToAppFormat(geoJson) {
        const substations = [];

        // Process each feature (substation)
        if (geoJson && geoJson.features) {
            geoJson.features.forEach(feature => {
                const properties = feature.properties || {};
                const coordinates = feature.geometry.coordinates;
                
                // Create a substation object in the application's expected format
                substations.push({
                    name: properties.id || properties.name,
                    display_name: properties.name || properties.display_name || properties.id,
                    coordinates: {
                        lat: coordinates[1], // GeoJSON uses [longitude, latitude]
                        lng: coordinates[0]
                    },
                    metadata: {
                        voltage_level: properties.voltage_level || properties.voltage || "33/11kV",
                        region: properties.region || properties.area || "Default",
                        capacity_mw: properties.capacity || properties.capacity_mw || 30.0,
                        transformer_count: properties.transformer_count || 1,
                        demand_group: properties.demand_group || properties.group_id
                    },
                    icon: {
                        color: properties.voltage_level?.includes("132") ? "#0DA9FF" : "#00A443",
                        size: properties.voltage_level?.includes("132") ? "large" : "medium"
                    }
                });
            });
        }

        return substations;
    }
    
    /**
     * Convert API GeoJSON demand groups to the format expected by the application
     * 
     * @param {Object} geoJson - GeoJSON response from the API
     * @returns {Object} - Formatted data for the application
     */
    _convertDemandGroupsGeoJsonToAppFormat(geoJson) {
        const demandGroups = [];
        
        // Process each feature (demand group)
        if (geoJson && geoJson.features) {
            geoJson.features.forEach(feature => {
                const properties = feature.properties || {};
                const coordinates = feature.geometry.coordinates;
                
                // Skip if no polygon data
                if (!coordinates || !coordinates[0]) return;
                
                // Extract points from the first polygon ring
                const points = coordinates[0].map(coord => ({
                    lat: coord[1], // GeoJSON uses [longitude, latitude]
                    lng: coord[0]
                }));
                
                // Create a demand group in the application's expected format
                demandGroups.push({
                    id: properties.id || properties.group_id,
                    name: properties.name || properties.display_name || `Group ${properties.id}`,
                    polygon: {
                        color: properties.color || "#00A443",
                        fillColor: properties.fillColor || "#00A44333",
                        weight: properties.weight || 2,
                        points: points
                    },
                    metadata: {
                        firm_capacity_mw: properties.firm_capacity || properties.capacity || 45.0,
                        total_energy_mwh: properties.total_energy || properties.energy || 980.0,
                        energy_above_capacity_mwh: properties.energy_above_capacity || 18.0,
                        substation_count: properties.substation_count || 1,
                        substations: properties.substations || [],
                        peak_demand_time: properties.peak_time || "2025-01-15T18:30:00Z"
                    }
                });
            });
        }
        
        return demandGroups;
    }

    /**
     * Fetch substation data from the API
     * 
     * @param {Object} filters - Optional filters for the API request
     * @returns {Promise<Array>} - Formatted substation data
     */
    async fetchSubstations(filters = {}) {
        try {
            // Build query string from filters
            const queryParams = new URLSearchParams();
            if (filters.area) queryParams.append('area', filters.area);
            if (filters.type) queryParams.append('type', filters.type);
            
            const queryString = queryParams.toString();
            const url = `${this.baseUrl}${this.endpoints.substations}${queryString ? '?' + queryString : ''}`;
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            return this._convertSubstationsGeoJsonToAppFormat(data);
        } catch (error) {
            console.error('Error fetching substations:', error);
            throw error;
        }
    }
    
    /**
     * Fetch demand groups data from the API
     * 
     * @param {Array} groupIds - Optional array of group IDs to filter
     * @returns {Promise<Array>} - Formatted demand group data
     */
    async fetchDemandGroups(groupIds = null) {
        try {
            // Build query string for group IDs filter
            const queryParams = new URLSearchParams();
            if (groupIds && groupIds.length > 0) {
                groupIds.forEach(id => queryParams.append('group_ids', id));
            }
            
            const queryString = queryParams.toString();
            const url = `${this.baseUrl}${this.endpoints.demandGroups}${queryString ? '?' + queryString : ''}`;
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            return this._convertDemandGroupsGeoJsonToAppFormat(data);
        } catch (error) {
            console.error('Error fetching demand groups:', error);
            throw error;
        }
    }
    
    /**
     * Fetch both substations and demand groups and return combined data 
     * 
     * @param {Object} filters - Filters for the API
     * @returns {Promise<Object>} - Combined map data
     */
    async fetchMapData(filters = {}) {
        try {
            const [substations, demandGroups] = await Promise.all([
                this.fetchSubstations(filters),
                this.fetchDemandGroups(filters.groupIds)
            ]);
            
            // Return in the format the application expects
            return {
                substations,
                demand_groups: demandGroups,
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
                    center: {
                        lat: substations.length > 0 ? 
                            substations.reduce((sum, s) => sum + s.coordinates.lat, 0) / substations.length : 
                            55.0500,
                        lng: substations.length > 0 ? 
                            substations.reduce((sum, s) => sum + s.coordinates.lng, 0) / substations.length : 
                            -1.4500
                    },
                    zoom: 10,
                    max_zoom: 18,
                    min_zoom: 6
                }
            };
        } catch (error) {
            console.error('Error fetching map data:', error);
            throw error;
        }
    }
}

// Export the service
export default MapDataService;