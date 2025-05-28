# EPA NonAttainment Areas Service Analysis Summary

## Overview
This document summarizes the comprehensive analysis of EPA services for nonattainment areas mapping and data access. The analysis was conducted to understand the structure, capabilities, and implementation requirements for the NonAttainmentINFO module.

## Primary Service Recommendation

**Service URL:** `https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer`

**Authority:** EPA Office of Air and Radiation (OAR)  
**Division:** Office of Air Quality Planning and Standards (OAQPS)  
**Coverage:** All criteria pollutants with current and historical data  
**Service Type:** ArcGIS MapServer  
**Max Record Count:** 2000 per query  

## Layer Structure (12 Layers Total)

| Layer ID | Pollutant | Standard | Status | Notes |
|----------|-----------|----------|---------|-------|
| 0 | Ozone 8-hr | 1997 standard | 🔴 REVOKED | Historical data only |
| 1 | Ozone 8-hr | 2008 standard | 🟢 ACTIVE | Current standard |
| 2 | Ozone 8-hr | 2015 Standard | 🟢 ACTIVE | Current standard |
| 3 | Lead | 2008 standard | 🟢 ACTIVE | Current standard |
| 4 | SO2 1-hr | 2010 standard | 🟢 ACTIVE | Current standard |
| 5 | PM2.5 24hr | 2006 standard | 🟢 ACTIVE | Current standard |
| 6 | PM2.5 Annual | 1997 standard | 🟢 ACTIVE | Current standard |
| 7 | PM2.5 Annual | 2012 standard | 🟢 ACTIVE | Current standard |
| 8 | PM10 | 1987 standard | 🟢 ACTIVE | Current standard |
| 9 | CO | 1971 Standard | 🟢 ACTIVE | Current standard |
| 10 | Ozone 1-hr | 1979 standard-revoked | 🔴 REVOKED | Historical data only |
| 11 | NO2 | 1971 Standard | 🟢 ACTIVE | Current standard |

## Field Categories and Key Attributes

### 🌫️ Pollutant Fields
- `pollutant_name` (String): Pollutant type (e.g., 'PM-2.5 (2012 Standard)')

### 📍 Location Fields
- `area_name` (String): Nonattainment area name
- `state_name` (String): State name
- `state_abbreviation` (String): State abbreviation
- `fips_state` (String): State FIPS code
- `composite_id_with_state` (String): Composite ID with state
- `state_suffix` (String): State suffix

### 📊 Status Fields
- `current_status` (String): Nonattainment, Maintenance, etc.
- `classification` (String): Marginal, Moderate, Serious, Severe, Extreme
- `meets_naaqs` (String): Yes/No - meets National Ambient Air Quality Standards
- `statutory_attainment_date` (Date): Statutory attainment date

### 📏 Measurements Fields
- `design_value` (Float): Current air quality measurement
- `dv_units` (String): Design value units (µg/m³, ppm, ppb)
- `original_design_value` (Float): Original design value
- `dv24` (Float): Design value 24hr

### 📅 Date Fields
- `designation_pub_date` (Date): Designation publication date
- `designation_effective_date` (Date): Designation effective date
- `classification_pub_date` (Date): Classification publication date
- `classification_effective_date` (Date): Classification effective date

### 👥 Population Fields
- `population_2010` (Integer): 2010 population
- `populationtotals_TOTPOP_CY` (Double): 2024 total population
- `populationtotalspl94_totpop20` (Double): 2020 total population

### 📋 Regulatory Fields
- `designation_citation` (String): Designation citation
- `designation_url` (String): Designation URL
- `classification_citation` (String): Classification citation
- `epa_region` (Integer): EPA region number (1-10)

### 🆔 Identifier Fields
- `OBJECTID` (OID): Object ID
- `composite_id` (String): Composite ID
- `composite_id2` (String): Secondary composite ID

### 🗺️ Geometry Fields
- `Shape` (Geometry): Polygon geometry
- `Shape_Length` (Double): Shape length
- `Shape_Area` (Double): Shape area

## Sample Data Patterns

### Pollutant Types Found
- 8-Hour Ozone (1997 Standard) - REVOKED
- 8-Hour Ozone (2008 Standard) - ACTIVE
- 8-Hour Ozone (2015 Standard) - ACTIVE
- Lead (2008 Standard) - ACTIVE
- Sulfur Dioxide (2010 Standard) - ACTIVE
- PM-2.5 (2006 Standard) - ACTIVE
- PM-2.5 (1997 Standard) - ACTIVE
- PM-2.5 (2012 Standard) - ACTIVE
- PM-10 (1987 Standard) - ACTIVE
- Carbon Monoxide (1971 Standard) - ACTIVE
- 1-Hour Ozone (1979 Standard) - REVOKED
- Nitrogen Dioxide (1971 Standard) - ACTIVE

### Status Types Found
- Nonattainment
- Maintenance
- Maintenance (NAAQS revoked)
- Nonattainment (NAAQS revoked)

### Classification Types Found
- Marginal
- Moderate
- Serious
- Severe
- Extreme
- Marginal (Rural Transport)
- Subpart 2/Moderate

### Units Found
- ppm (parts per million)
- ppb (parts per billion)
- µg/m³ (micrograms per cubic meter)
- est. exc. (estimated exceedances)

## Query Testing Results

### Geographic Coverage Testing
Tested queries across major metropolitan areas:

| Location | Ozone 2008 | Ozone 2015 | Lead | SO2 | PM2.5 24hr | PM2.5 Annual | PM10 | CO | NO2 |
|----------|------------|-------------|------|-----|------------|--------------|------|----|----|
| Los Angeles, CA | ✅ | ✅ | ✅ | ⭕ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Houston, TX | ✅ | ✅ | ⭕ | ⭕ | ⭕ | ❌ | ⭕ | ⭕ | ⭕ |
| Phoenix, AZ | ✅ | ✅ | ⭕ | ⭕ | ⭕ | ⭕ | ✅ | ❌ | ⭕ |
| New York, NY | ✅ | ✅ | ⭕ | ❌ | ✅ | ❌ | ✅ | ✅ | ⭕ |
| Chicago, IL | ❌ | ✅ | ❌ | ⭕ | ⭕ | ✅ | ⭕ | ⭕ | ⭕ |

**Legend:**
- ✅ = Features found (nonattainment/maintenance areas present)
- ⭕ = No features (area meets standards)
- ❌ = Query error (service issue)

## Service Capabilities

### ✅ Supported Operations
- Spatial intersection queries (point, polygon, buffer)
- Attribute filtering by pollutant, state, status
- Geometry return for mapping applications
- Statistical queries and aggregation
- Export capabilities (JSON, GeoJSON, KML)
- Count queries for performance optimization

### 📊 Query Parameters
- `geometry`: Spatial geometry for intersection
- `geometryType`: Point, polygon, etc.
- `spatialRel`: Spatial relationship (intersects, contains, etc.)
- `where`: SQL-like attribute filtering
- `outFields`: Field selection (* for all)
- `returnGeometry`: Include/exclude geometry
- `returnCountOnly`: Count-only queries for performance
- `resultRecordCount`: Limit result size

## Implementation Recommendations

### 🎨 Recommended Client Architecture
1. **NonAttainmentAreasClient** class - Main service interface
2. **Layer-specific query methods** - Per-pollutant access
3. **Pollutant-specific analysis functions** - Domain logic
4. **Status classification utilities** - Data interpretation
5. **Geographic aggregation capabilities** - Spatial analysis

### ⚡ Performance Considerations
- **Max record count:** 2000 per query - implement pagination
- **Use spatial indexing** for large area queries
- **Cache frequently accessed data** to reduce API calls
- **Implement pagination** for large result sets
- **Consider layer-specific queries** for better performance
- **Use count queries** before full data retrieval

### 🔧 Error Handling
- Some layers experience intermittent 500 errors
- Implement retry logic with exponential backoff
- Graceful degradation when specific layers are unavailable
- Validate geometry before spatial queries

### 🗺️ Map Generation Considerations
- **Active vs. Revoked Standards:** Filter layers appropriately
- **Pollutant-specific symbology:** Different colors per pollutant type
- **Status-based styling:** Visual distinction for nonattainment vs. maintenance
- **Classification severity:** Color intensity based on severity level
- **Multi-layer support:** Overlay multiple pollutants when relevant

## Data Quality Notes

### ✅ Reliable Data
- Consistent field structure across all layers
- Comprehensive geographic coverage
- Regular updates from EPA
- Standardized pollutant naming

### ⚠️ Considerations
- Some query endpoints experience intermittent errors
- Historical (revoked) standards still contain data
- Population data varies by vintage (2010, 2020, 2024)
- Design values may be incomplete for some areas

## Next Steps

1. **Implement NonAttainmentAreasClient** based on this analysis
2. **Create layer-specific query methods** for each pollutant
3. **Develop map generation module** with proper symbology
4. **Add error handling and retry logic** for service reliability
5. **Implement caching strategy** for performance optimization
6. **Create comprehensive test suite** covering all layers and scenarios

## Files Generated
- `NonAttainmentINFO/explore_epa_services.py` - Initial service exploration
- `NonAttainmentINFO/analyze_epa_services.py` - Detailed service analysis
- `NonAttainmentINFO/EPA_SERVICE_ANALYSIS_SUMMARY.md` - This summary document

---

**Analysis Date:** January 2025  
**EPA Service Version:** Current as of analysis date  
**Total Layers Analyzed:** 12  
**Total Fields per Layer:** ~64  
**Geographic Test Locations:** 5 major metropolitan areas 