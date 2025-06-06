#!/usr/bin/env python3
"""
Comprehensive Environmental Screening Report Generator

This tool takes as input multiple JSON files from a given directory and generates
a comprehensive environmental screening report following the specified schema.
"""

import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import argparse
from pathlib import Path


@dataclass
class ProjectInfo:
    """Project Information section of the report"""
    project_name: str
    analysis_date_time: str
    longitude: float
    latitude: float
    cadastral_numbers: List[str]
    location_name: str
    project_directory: str


@dataclass
class ExecutiveSummary:
    """Executive Summary section of the report"""
    property_overview: str
    key_environmental_constraints: List[str]
    regulatory_highlights: List[str]
    risk_assessment: str
    primary_recommendations: List[str]


@dataclass
class CadastralAnalysis:
    """Property & Cadastral Analysis section"""
    cadastral_numbers: List[str]
    municipality: str
    neighborhood: str
    region: str
    land_use_classification: str
    zoning_designation: str
    area_square_meters: float
    area_hectares: float
    area_acres: float
    regulatory_status: str


@dataclass
class FloodZoneDetail:
    """Individual flood zone information"""
    zone_code: str
    description: str
    base_flood_elevation_ft: Optional[float]
    depth_ft: Optional[float]
    velocity_fps: Optional[float]
    coastal: bool
    source: str

@dataclass
class FloodDataSource:
    """Flood data source information"""
    source: str
    query_time: str
    effective_date: Optional[str] = None
    accuracy: Optional[str] = None
    applicable: Optional[bool] = None

@dataclass
class FloodAnalysisExpanded:
    """Expanded Flood Analysis section with detailed information"""
    location: Dict[str, Any]
    flood_zones: List[FloodZoneDetail]
    primary_flood_zone: str
    base_flood_elevation: Optional[float]
    risk_assessment: Dict[str, Any]
    regulatory_info: Dict[str, Any]
    data_sources: Dict[str, FloodDataSource]
    recommendations: List[str]
    generated_files: List[str]
    flood_reports_generated: Dict[str, str]
    map_generation_parameters: Dict[str, Any]
    firm_panel: str
    effective_date: str
    community_name: str
    preliminary_vs_effective: str
    abfe_data_available: bool
    flood_risk_assessment: str


@dataclass
class WetlandDetail:
    """Individual wetland information"""
    wetland_id: str
    nwi_code: str
    wetland_type: str
    system: str
    subsystem: Optional[str]
    wetland_class: str
    water_regime: Optional[str]
    area_acres: Optional[float]
    jurisdiction: str
    habitat_value: Optional[str]
    vegetation: Optional[str]
    distance_miles: float
    coordinates: List[float]

@dataclass
class WetlandAnalysisExpanded:
    """Expanded Wetland Analysis section"""
    location: Dict[str, Any]
    wetland_analysis: Dict[str, Any]
    wetlands_at_location: List[WetlandDetail]
    nearby_wetlands: List[WetlandDetail]
    directly_on_property: bool
    within_search_radius: bool
    distance_to_nearest: Optional[float]
    environmental_significance: str
    regulatory_assessment: Dict[str, Any]
    wetland_classifications: List[str]
    regulatory_significance: List[str]
    development_guidance: List[str]
    map_reference: str
    map_generation_parameters: Dict[str, Any]


@dataclass
class CriticalHabitatAnalysis:
    """Critical Habitat Analysis section"""
    within_designated_habitat: bool
    within_proposed_habitat: bool
    distance_to_nearest: Optional[float]
    affected_species: List[str]
    regulatory_implications: List[str]
    development_constraints: List[str]
    map_reference: str


@dataclass
class SpeciesDetail:
    """Individual species information"""
    species: str
    scientific_name: str
    habitat_type: str
    designation_date: str
    distance_miles: float
    status: str

@dataclass
class CriticalHabitatAnalysisExpanded:
    """Expanded Critical Habitat Analysis section"""
    location: Dict[str, Any]
    critical_habitat_areas: List[SpeciesDetail]
    endangered_species: List[SpeciesDetail]
    habitat_assessment: Dict[str, Any]
    regulatory_assessment: Dict[str, Any]
    within_designated_habitat: bool
    within_proposed_habitat: bool
    distance_to_nearest: Optional[float]
    affected_species: List[str]
    regulatory_implications: List[str]
    development_constraints: List[str]
    map_reference: str
    map_generation_parameters: Dict[str, Any]


@dataclass
class NonattainmentAreaDetail:
    """Individual nonattainment area information"""
    pollutant: str
    classification: str
    designation_date: str
    attainment_status: str
    monitoring_site: str
    area_name: str
    county: str
    state: str

@dataclass
class MonitoringSiteDetail:
    """Air quality monitoring site information"""
    site_id: str
    site_name: str
    distance_miles: float
    pollutants_monitored: List[str]
    recent_data: Dict[str, float]
    exceedances_2023: Dict[str, int]

@dataclass
class AirQualityAnalysis:
    """Air Quality (Nonattainment) Analysis section"""
    nonattainment_status: bool
    affected_pollutants: List[str]
    area_classification: str
    regulatory_implications: List[str]
    map_reference: str


@dataclass
class AirQualityAnalysisExpanded:
    """Expanded Air Quality Analysis section"""
    location: Dict[str, Any]
    nonattainment_areas: List[NonattainmentAreaDetail]
    air_quality_assessment: Dict[str, Any]
    regulatory_requirements: Dict[str, Any]
    monitoring_data: List[MonitoringSiteDetail]
    naaqs_standards: Dict[str, Any]
    data_sources: Dict[str, Any]
    nonattainment_status: bool
    affected_pollutants: List[str]
    area_classification: str
    regulatory_implications: List[str]
    map_reference: str
    map_generation_parameters: Dict[str, Any]


@dataclass
class KarstAnalysis:
    """Karst Analysis section"""
    within_karst_area_general: bool 
    karst_status_general: str 
    karst_type_detailed: Optional[str] 
    specific_zone_description: Optional[str] 
    regulatory_impact_level: Optional[str] 
    primary_regulation_info: Optional[str] 
    summary_message: Optional[str] 
    development_constraints: List[str]
    geological_significance: str
    permit_requirements: List[str]
    map_reference: str
    interpretation_guidance: Optional[str] = None
    nearest_karst_details: Optional[Dict[str, Any]] = None # To store info about nearest features


@dataclass
class ComprehensiveReport:
    """Complete environmental screening report"""
    project_info: ProjectInfo
    executive_summary: ExecutiveSummary
    cadastral_analysis: CadastralAnalysis
    karst_analysis: Optional[KarstAnalysis]
    flood_analysis: FloodAnalysisExpanded
    wetland_analysis: WetlandAnalysisExpanded
    critical_habitat_analysis: CriticalHabitatAnalysisExpanded
    air_quality_analysis: AirQualityAnalysisExpanded
    cumulative_risk_assessment: Dict[str, Any]
    recommendations: List[str]
    generated_files: List[str]


class ComprehensiveReportGenerator:
    """Generator for comprehensive environmental screening reports"""
    
    def __init__(self, data_directory: str):
        self.data_directory = data_directory
        self.json_files = {}
        self.load_json_files()
    
    def load_json_files(self):
        """Load all JSON files from the data directory, prioritizing comprehensive results file."""
        json_pattern = os.path.join(self.data_directory, "*.json")
        json_files_found = glob.glob(json_pattern)
        
        # First, try to load the main comprehensive query results file
        comprehensive_results_file = os.path.join(self.data_directory, "comprehensive_query_results.json")
        if comprehensive_results_file in json_files_found:
            try:
                with open(comprehensive_results_file, 'r', encoding='utf-8') as f:
                    comprehensive_data = json.load(f)
                    
                # Extract data from the comprehensive results structure
                query_results = comprehensive_data.get('query_results', {})
                project_info = comprehensive_data.get('project_info', {})
                
                # Store project info for coordinate extraction
                self.json_files['project_info'] = project_info
                
                # Extract individual analysis results from query_results
                if 'flood' in query_results:
                    self.json_files['flood_comprehensive'] = query_results['flood']
                if 'wetland' in query_results:
                    self.json_files['wetland_comprehensive'] = query_results['wetland']
                if 'air_quality' in query_results:
                    self.json_files['air_quality_comprehensive'] = query_results['air_quality']
                if 'habitat' in query_results:
                    self.json_files['habitat_comprehensive'] = query_results['habitat']
                if 'cadastral' in query_results:
                    self.json_files['cadastral_comprehensive'] = query_results['cadastral']
                
                json_files_found.remove(comprehensive_results_file)
                print(f"✅ Loaded main comprehensive results file with {len(query_results)} analysis sections")
                
            except Exception as e:
                print(f"Error loading comprehensive_query_results.json: {e}")
        
        # Load individual comprehensive files as additional/backup data
        comprehensive_files = {
            'flood_analysis_comprehensive.json': 'flood_comprehensive_backup',
            'wetland_analysis_comprehensive.json': 'wetland_comprehensive_backup', 
            'air_quality_analysis_comprehensive.json': 'air_quality_comprehensive_backup',
            'critical_habitat_analysis_comprehensive.json': 'habitat_comprehensive_backup',
            'karst_analysis_comprehensive.json': 'karst_comprehensive',  # Keep this as primary for karst
            'cadastral_analysis.json': 'cadastral_comprehensive_backup'
        }
        
        # Load comprehensive files 
        for filename, key in comprehensive_files.items():
            file_path = os.path.join(self.data_directory, filename)
            if file_path in json_files_found:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.json_files[key] = json.load(f)
                    json_files_found.remove(file_path)
                    print(f"✅ Loaded additional file: {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

        # Process remaining files with legacy naming patterns
        for file_path in json_files_found:
            filename = os.path.basename(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Categorize legacy files (fallback)
                if 'cadastral_search' in filename and 'cadastral_comprehensive' not in self.json_files:
                    self.json_files['cadastral'] = data
                elif 'panel_info' in filename and 'flood_comprehensive' not in self.json_files:
                    self.json_files['flood'] = data
                elif 'wetland_summary' in filename and 'wetland_comprehensive' not in self.json_files:
                    self.json_files['wetland'] = data
                elif 'critical_habitat' in filename and 'habitat_comprehensive' not in self.json_files:
                    self.json_files['habitat'] = data
                elif ('nonattainment_summary' in filename or 'nonattainment_analysis' in filename) and 'air_quality_comprehensive' not in self.json_files:
                    self.json_files['air_quality'] = data
                elif 'karst_analysis' in filename and 'karst_comprehensive' not in self.json_files:
                    self.json_files['karst_legacy'] = data 
                    
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        print(f"📊 Loaded {len(self.json_files)} environmental data files")
        for key in self.json_files.keys():
            print(f"   • {key}")
    
    def extract_project_info(self) -> ProjectInfo:
        """Extract project information from loaded data"""
        # Get coordinates from any available source
        coords = self._get_coordinates()
        
        # Get cadastral numbers
        cadastral_numbers = []
        if 'cadastral' in self.json_files:
            cadastral_numbers = [self.json_files['cadastral'].get('search_cadastral', '')]
        
        # Generate project name
        project_name = self._generate_project_name(cadastral_numbers, coords)
        
        # Get location name
        location_name = self._get_location_name()
        
        return ProjectInfo(
            project_name=project_name,
            analysis_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            longitude=coords[0] if coords else 0.0,
            latitude=coords[1] if coords else 0.0,
            cadastral_numbers=cadastral_numbers,
            location_name=location_name,
            project_directory=os.path.dirname(self.data_directory)
        )
    
    def extract_cadastral_analysis(self) -> Optional[CadastralAnalysis]:
        """Extract cadastral/property analysis"""
        # Check for comprehensive cadastral data first
        if 'cadastral_comprehensive' in self.json_files:
            data = self.json_files['cadastral_comprehensive']
            
            # Extract from comprehensive format
            cadastral_info = data.get('cadastral_info', {})
            land_use = data.get('land_use', {})
            location_details = data.get('location_details', {})
            area_measurements = data.get('area_measurements', {})
            regulatory_status = data.get('regulatory_status', {})
            
            if not cadastral_info:
                return None
            
            cadastral_number = cadastral_info.get('cadastral_number', '')
            municipality = location_details.get('municipality', cadastral_info.get('municipality', ''))
            neighborhood = location_details.get('neighborhood', cadastral_info.get('neighborhood', ''))
            region = location_details.get('region', cadastral_info.get('region', ''))
            
            land_use_classification = land_use.get('classification_description', '')
            zoning_designation = land_use.get('classification_code', '')
            
            area_m2 = area_measurements.get('area_square_meters', 0)
            area_hectares = area_measurements.get('area_hectares', 0)
            area_acres = area_measurements.get('area_acres', 0)
            
            # Get regulatory status
            status_text = regulatory_status.get('status', 'No specific cases identified')
            regulatory_implications = regulatory_status.get('regulatory_implications', [])
            if regulatory_implications:
                status_text += f" - {'; '.join(regulatory_implications)}"
            
            return CadastralAnalysis(
                cadastral_numbers=[cadastral_number],
                municipality=municipality,
                neighborhood=neighborhood,
                region=region,
                land_use_classification=land_use_classification,
                zoning_designation=zoning_designation,
                area_square_meters=area_m2,
                area_hectares=area_hectares,
                area_acres=area_acres,
                regulatory_status=status_text
            )
        
        # Fallback to legacy format
        if 'cadastral' not in self.json_files:
            return None
            
        data = self.json_files['cadastral']
        results = data.get('results', [])
        
        if not results:
            return None
            
        # Use first result for primary data
        primary = results[0]
        
        # Calculate acres from square meters
        area_m2 = data.get('total_area_m2', 0)
        area_hectares = data.get('total_area_hectares', 0)
        area_acres = area_m2 * 0.000247105  # Convert m2 to acres
        
        return CadastralAnalysis(
            cadastral_numbers=[data.get('search_cadastral', '')],
            municipality=primary.get('municipality', ''),
            neighborhood=primary.get('neighborhood', ''),
            region=primary.get('region', ''),
            land_use_classification=primary.get('classification_description', ''),
            zoning_designation=primary.get('classification_code', ''),
            area_square_meters=area_m2,
            area_hectares=area_hectares,
            area_acres=area_acres,
            regulatory_status=primary.get('status', 'No specific cases identified')
        )
    
    def extract_flood_analysis(self) -> Optional[FloodAnalysisExpanded]:
        """Extract flood analysis from comprehensive flood data"""
        # Check for comprehensive flood data first
        if 'flood_comprehensive' in self.json_files:
            data = self.json_files['flood_comprehensive']
            
            # Extract from comprehensive format
            flood_zones_data = data.get('flood_zones', [])
            if not flood_zones_data:
                return None
            
            # Create FloodZoneDetail objects
            flood_zones = []
            for zone_data in flood_zones_data:
                flood_zones.append(FloodZoneDetail(
                    zone_code=zone_data.get('zone_code', 'Unknown'),
                    description=zone_data.get('description', ''),
                    base_flood_elevation_ft=zone_data.get('base_flood_elevation_ft'),
                    depth_ft=zone_data.get('depth_ft'),
                    velocity_fps=zone_data.get('velocity_fps'),
                    coastal=zone_data.get('coastal', False),
                    source=zone_data.get('source', 'Unknown')
                ))
            
            # Get primary flood zone (first one or highest risk)
            primary_zone = flood_zones_data[0]
            primary_flood_zone = primary_zone.get('zone_code', 'Unknown')
            bfe = primary_zone.get('base_flood_elevation_ft')
            
            # Get regulatory info
            regulatory_info = data.get('regulatory_info', {})
            risk_assessment = data.get('risk_assessment', {})
            
            # Generate regulatory requirements
            regulatory_requirements = self._get_flood_regulatory_requirements(primary_flood_zone)
            
            # Get risk assessment
            risk_level = risk_assessment.get('overall_level', 'Unknown')
            flood_risk_assessment = f"{risk_level} flood risk"
            if risk_assessment.get('coastal_hazards'):
                flood_risk_assessment += " with coastal hazards"
            
            # Check for ABFE data
            abfe_available = any('abfe' in str(source).lower() for source in data.get('data_sources', {}).values())
            
            # Create FloodDataSource objects
            data_sources = {}
            for source_key, source_data in data.get('data_sources', {}).items():
                if isinstance(source_data, dict):
                    data_sources[source_key] = FloodDataSource(
                        source=source_data.get('source', ''),
                        query_time=source_data.get('query_time', ''),
                        effective_date=source_data.get('effective_date'),
                        accuracy=source_data.get('accuracy'),
                        applicable=source_data.get('applicable')
                    )
            
            return FloodAnalysisExpanded(
                location=data.get('location', {}),
                flood_zones=flood_zones,
                primary_flood_zone=primary_flood_zone,
                base_flood_elevation=bfe,
                risk_assessment=risk_assessment,
                regulatory_info=regulatory_info,
                data_sources=data_sources,
                recommendations=data.get('recommendations', []),
                generated_files=data.get('generated_files', []),
                flood_reports_generated=data.get('flood_reports_generated', {}),
                map_generation_parameters=data.get('map_generation_parameters', {}),
                firm_panel=regulatory_info.get('crs_rating', 'Unknown'),
                effective_date=data_sources.get('nfhl', FloodDataSource('', '')).effective_date or 'Unknown',
                community_name='Puerto Rico Municipality',  # Default for PR
                preliminary_vs_effective="Effective FIRM data",
                abfe_data_available=abfe_available,
                flood_risk_assessment=flood_risk_assessment
            )
        
        # Fallback to legacy format
        if 'flood' not in self.json_files:
            return None
            
        data = self.json_files['flood']
        current_effective = data.get('current_effective_data', {})
        
        # Get flood zone information
        flood_zones = current_effective.get('flood_zones', [])
        flood_zone = flood_zones[0].get('flood_zone', 'Unknown') if flood_zones else 'Unknown'
        
        # Get BFE
        bfe = None
        if flood_zones:
            bfe_value = flood_zones[0].get('base_flood_elevation', -9999.0)
            if bfe_value != -9999.0:
                bfe = bfe_value
        
        # Get panel information
        panels = current_effective.get('panel_information', [])
        firm_panel = 'Unknown'
        effective_date = 'Unknown'
        
        for panel in panels:
            if panel.get('firm_panel'):
                firm_panel = panel['firm_panel']
                effective_date = panel.get('effective_date', 'Unknown')
                break
        
        # Get community name
        jurisdictions = current_effective.get('political_jurisdictions', [])
        community_name = 'Unknown'
        if jurisdictions:
            community_name = jurisdictions[0].get('jurisdiction_name_2', 'Unknown')
        
        # Determine regulatory requirements based on flood zone
        regulatory_requirements = self._get_flood_regulatory_requirements(flood_zone)
        
        # Assess flood risk
        risk_assessment = self._assess_flood_risk(flood_zone, bfe)
        
        # Check for preliminary vs effective data
        preliminary_data = data.get('preliminary_data', {})
        preliminary_comparison = "Preliminary data available" if preliminary_data else "No preliminary data"
        
        return FloodAnalysisExpanded(
            location=data.get('location', {}),
            flood_zones=flood_zones,
            primary_flood_zone=flood_zone,
            base_flood_elevation=bfe,
            risk_assessment=risk_assessment,
            regulatory_info=data.get('regulatory_info', {}),
            data_sources=data.get('data_sources', {}),
            recommendations=data.get('recommendations', []),
            generated_files=data.get('generated_files', []),
            flood_reports_generated=data.get('flood_reports_generated', {}),
            map_generation_parameters=data.get('map_generation_parameters', {}),
            firm_panel=firm_panel,
            effective_date=effective_date,
            community_name=community_name,
            preliminary_vs_effective=preliminary_comparison,
            abfe_data_available=True,  # Based on file listing
            flood_risk_assessment=risk_assessment
        )
    
    def extract_wetland_analysis(self) -> Optional[WetlandAnalysisExpanded]:
        """Extract wetland analysis from comprehensive wetland data"""
        # Check for comprehensive wetland data first
        if 'wetland_comprehensive' in self.json_files:
            data = self.json_files['wetland_comprehensive']
            
            # Extract from comprehensive format
            wetland_analysis = data.get('wetland_analysis', {})
            if not wetland_analysis:
                return None
            
            directly_on_property = wetland_analysis.get('is_in_wetland', False)
            
            # Get wetlands at location and nearby
            wetlands_at_location = wetland_analysis.get('wetlands_at_location', [])
            nearby_wetlands = wetland_analysis.get('nearby_wetlands', [])
            all_wetlands = wetlands_at_location + nearby_wetlands
            
            within_radius = len(all_wetlands) > 0
            
            # Get distance to nearest wetland
            distance_to_nearest = None
            if all_wetlands:
                distances = [w.get('distance_miles', 0) for w in all_wetlands if 'distance_miles' in w]
                if distances:
                    distance_to_nearest = min(distances)
            
            # Get wetland classifications
            classifications = []
            for wetland in all_wetlands:
                wetland_details = wetland.get('wetland_details', {})
                wetland_type = wetland_details.get('wetland_type', 'Unknown')
                nwi_code = wetland_details.get('nwi_code', 'Unknown')
                full_classification = f"{wetland_type} ({nwi_code})"
                if full_classification not in classifications:
                    classifications.append(full_classification)
            
            # Get regulatory significance
            regulatory_assessment = wetland_analysis.get('regulatory_assessment', {})
            environmental_significance = wetland_analysis.get('environmental_significance', '')
            
            regulatory_significance = [
                f"Impact Level: {regulatory_assessment.get('impact_level', 'Unknown')}",
                f"Environmental Significance: {environmental_significance}",
                f"USACE Jurisdiction: {regulatory_assessment.get('usace_jurisdiction', False)}"
            ]
            
            # Get development guidance from recommendations
            recommendations = data.get('recommendations', [])
            if not recommendations:
                recommendations = wetland_analysis.get('recommendations', [])
            
            # Clean recommendations text
            development_guidance = []
            for rec in recommendations:
                cleaned = rec.replace('🚨', '').replace('⚖️', '').replace('📋', '').replace('📞', '').replace('🌱', '').strip()
                if cleaned:
                    development_guidance.append(cleaned)
            
            return WetlandAnalysisExpanded(
                location=data.get('location', {}),
                wetland_analysis=wetland_analysis,
                wetlands_at_location=wetlands_at_location,
                nearby_wetlands=nearby_wetlands,
                directly_on_property=directly_on_property,
                within_search_radius=within_radius,
                distance_to_nearest=distance_to_nearest,
                environmental_significance=environmental_significance,
                regulatory_assessment=regulatory_assessment,
                wetland_classifications=classifications,
                regulatory_significance=regulatory_significance,
                development_guidance=development_guidance,
                map_reference="wetland_map_embed.png",  # Default for comprehensive format
                map_generation_parameters=data.get('map_generation_parameters', {})
            )
        
        # Fallback to legacy format
        if 'wetland' not in self.json_files:
            return None
            
        data = self.json_files['wetland']
        location_analysis = data.get('location_analysis', {})
        
        directly_on_property = location_analysis.get('is_in_wetland', False)
        total_wetlands = location_analysis.get('total_wetlands_found', 0)
        within_radius = total_wetlands > 0
        
        # Get distance to nearest wetland
        wetlands_in_radius = data.get('wetlands_in_radius', [])
        distance_to_nearest = None
        if wetlands_in_radius:
            distance_to_nearest = wetlands_in_radius[0].get('distance_miles', None)
        
        # Get wetland classifications
        classifications = []
        for wetland in wetlands_in_radius:
            wetland_type = wetland.get('wetland_type', 'Unknown')
            nwi_code = wetland.get('nwi_code', 'Unknown')
            # Create full classification string and check for duplicates
            full_classification = f"{wetland_type} ({nwi_code})"
            if full_classification not in classifications:
                classifications.append(full_classification)
        
        # Get regulatory significance
        regulatory_assessment = data.get('regulatory_assessment', {})
        regulatory_significance = [
            f"Impact Risk: {regulatory_assessment.get('immediate_impact_risk', 'Unknown')}",
            f"Found {total_wetlands} wetlands within search radius"
        ]
        
        # Get development guidance from recommendations
        recommendations = data.get('recommendations', [])
        development_guidance = [rec.replace('🔍', '').replace('📋', '').replace('📚', '').replace('🗺️', '').replace('📞', '').replace('💾', '').strip() for rec in recommendations]
        
        return WetlandAnalysisExpanded(
            location=data.get('location', {}),
            wetland_analysis=data.get('wetland_analysis', {}),
            wetlands_at_location=data.get('wetlands_at_location', []),
            nearby_wetlands=data.get('nearby_wetlands', []),
            directly_on_property=directly_on_property,
            within_search_radius=within_radius,
            distance_to_nearest=distance_to_nearest,
            environmental_significance=data.get('environmental_significance', ''),
            regulatory_assessment=regulatory_assessment,
            wetland_classifications=classifications,
            regulatory_significance=regulatory_significance,
            development_guidance=development_guidance,
            map_reference="wetland_map_Dynamic_Payments_Project_20250528_030451.pdf",
            map_generation_parameters=data.get('map_generation_parameters', {})
        )
    
    def extract_critical_habitat_analysis(self) -> Optional[CriticalHabitatAnalysisExpanded]:
        """Extract critical habitat analysis from comprehensive data"""
        # Check for comprehensive habitat data first
        if 'habitat_comprehensive' in self.json_files:
            data = self.json_files['habitat_comprehensive']
            
            # Extract from comprehensive format
            habitat_assessment = data.get('habitat_assessment', {})
            critical_habitat_areas = data.get('critical_habitat_areas', [])
            
            within_designated = habitat_assessment.get('is_in_critical_habitat', False)
            within_proposed = False  # Check if there's proposed habitat info
            
            # Get distance to nearest habitat
            distance_miles = habitat_assessment.get('nearest_habitat_distance_miles', 0)
            
            # Get affected species from critical habitat areas
            affected_species = []
            for area in critical_habitat_areas:
                species_name = area.get('species', 'Unknown')
                scientific_name = area.get('scientific_name', '')
                if scientific_name:
                    species_entry = f"{species_name} ({scientific_name})"
                else:
                    species_entry = species_name
                if species_entry not in affected_species:
                    affected_species.append(species_entry)
            
            # Get regulatory assessment
            regulatory_assessment = data.get('regulatory_assessment', {})
            regulatory_implications = [
                f"ESA Consultation Required: {regulatory_assessment.get('esa_consultation_required', False)}",
                f"Distance: {distance_miles} miles",
                f"Status: {habitat_assessment.get('is_in_critical_habitat', 'Not in habitat')}"
            ]
            
            # Get development constraints from recommendations
            recommended_surveys = regulatory_assessment.get('recommended_surveys', [])
            development_constraints = []
            for survey in recommended_surveys:
                development_constraints.append(f"Recommended: {survey}")
            
            return CriticalHabitatAnalysisExpanded(
                location=data.get('location', {}),
                critical_habitat_areas=critical_habitat_areas,
                endangered_species=[],
                habitat_assessment=habitat_assessment,
                regulatory_assessment=regulatory_assessment,
                within_designated_habitat=within_designated,
                within_proposed_habitat=within_proposed,
                distance_to_nearest=distance_miles,
                affected_species=affected_species,
                regulatory_implications=regulatory_implications,
                development_constraints=development_constraints,
                map_reference="critical_habitat_map_embed.png",  # Default for comprehensive format
                map_generation_parameters=data.get('map_generation_parameters', {})
            )
        
        # Fallback to legacy format
        if 'habitat' not in self.json_files:
            return None
            
        data = self.json_files['habitat']
        habitat_analysis = data.get('critical_habitat_analysis', {})
        
        status = habitat_analysis.get('status', '')
        within_designated = status == 'within_critical_habitat'
        within_proposed = status == 'within_proposed_habitat'
        
        distance_miles = habitat_analysis.get('distance_to_nearest_habitat_miles', 0)
        
        # Get affected species
        nearest_habitat = habitat_analysis.get('nearest_habitat', {})
        affected_species = []
        if nearest_habitat:
            common_name = nearest_habitat.get('species_common_name', '')
            scientific_name = nearest_habitat.get('species_scientific_name', '')
            if common_name or scientific_name:
                affected_species.append(f"{common_name} ({scientific_name})")
        
        # Get regulatory implications
        reg_implications = habitat_analysis.get('regulatory_implications', {})
        regulatory_implications = [
            f"ESA Consultation Required: {reg_implications.get('esa_consultation_required', False)}",
            f"Impact Assessment Recommended: {reg_implications.get('impact_assessment_recommended', False)}",
            f"Distance Category: {reg_implications.get('distance_category', 'Unknown')}"
        ]
        
        # Get development constraints from recommendations
        recommendations = habitat_analysis.get('recommendations', [])
        development_constraints = [rec.replace('✅', '').replace('📋', '').replace('🔍', '').replace('🦎', '').strip() for rec in recommendations]
        
        return CriticalHabitatAnalysisExpanded(
            location=data.get('location', {}),
            critical_habitat_areas=[],
            endangered_species=[],
            habitat_assessment=habitat_analysis,
            regulatory_assessment=habitat_analysis,
            within_designated_habitat=within_designated,
            within_proposed_habitat=within_proposed,
            distance_to_nearest=distance_miles,
            affected_species=affected_species,
            regulatory_implications=regulatory_implications,
            development_constraints=development_constraints,
            map_reference="critical_habitat_map_20250528_030539.pdf",
            map_generation_parameters=data.get('map_generation_parameters', {})
        )
    
    def extract_air_quality_analysis(self) -> Optional[AirQualityAnalysisExpanded]:
        """Extract air quality/nonattainment analysis from comprehensive data"""
        # Check for comprehensive air quality data first
        if 'air_quality_comprehensive' in self.json_files:
            data = self.json_files['air_quality_comprehensive']
            
            # Extract from comprehensive format
            air_quality_assessment = data.get('air_quality_assessment', {})
            nonattainment_areas = data.get('nonattainment_areas', [])
            
            has_violations = air_quality_assessment.get('overall_status') == 'Nonattainment'
            
            # Get affected pollutants from nonattainment areas
            affected_pollutants = []
            for area in nonattainment_areas:
                pollutant = area.get('pollutant', 'Unknown')
                if pollutant not in affected_pollutants:
                    affected_pollutants.append(pollutant)
            
            if not affected_pollutants:
                affected_pollutants = ['None - Meets all NAAQS']
            
            # Get area classification
            highest_classification = air_quality_assessment.get('highest_classification', 'Attainment')
            
            # Generate regulatory implications
            regulatory_requirements = data.get('regulatory_requirements', {})
            regulatory_implications = [
                f"Overall Status: {air_quality_assessment.get('overall_status', 'Unknown')}",
                f"Number of Nonattainment Areas: {air_quality_assessment.get('number_of_nonattainment_areas', 0)}",
                f"Enhanced Permitting Required: {regulatory_requirements.get('enhanced_permitting', False)}"
            ]
            
            return AirQualityAnalysisExpanded(
                location=data.get('location', {}),
                nonattainment_areas=nonattainment_areas,
                air_quality_assessment=air_quality_assessment,
                regulatory_requirements=regulatory_requirements,
                monitoring_data=[],
                naaqs_standards={},
                data_sources=data.get('data_sources', {}),
                nonattainment_status=has_violations,
                affected_pollutants=affected_pollutants,
                area_classification=highest_classification,
                regulatory_implications=regulatory_implications,
                map_reference="air_quality_map_embed.png",  # Default for comprehensive format
                map_generation_parameters=data.get('map_generation_parameters', {})
            )
        
        # Fallback to legacy format
        # Check for both air_quality and air_quality_detailed formats
        data = None
        if 'air_quality' in self.json_files:
            data = self.json_files['air_quality']
            data_format = 'summary'
        elif 'air_quality_detailed' in self.json_files:
            data = self.json_files['air_quality_detailed']
            data_format = 'detailed'
        else:
            return None
        
        if data_format == 'summary':
            # Original format for nonattainment_summary files
            location_analysis = data.get('location_analysis', {})
            has_violations = location_analysis.get('has_violations', False)
            
            # Get affected pollutants from violations
            violations_summary = data.get('violations_summary', {})
            violations = violations_summary.get('violations', [])
            affected_pollutants = [v.get('pollutant_name', v.get('pollutant', 'Unknown')) for v in violations]
            
            # Get regulatory assessment
            reg_assessment = data.get('regulatory_assessment', {})
            area_classification = reg_assessment.get('compliance_status', 'Unknown')
            
            # Get regulatory implications - handle both string and list formats
            regulatory_requirements = reg_assessment.get('regulatory_requirements', 'Unknown')
            if isinstance(regulatory_requirements, list):
                regulatory_requirements = '; '.join(regulatory_requirements)
            
            air_quality_status = reg_assessment.get('air_quality_status', 'Unknown')
            
            regulatory_implications = [
                f"Compliance Status: {reg_assessment.get('compliance_status', 'Unknown')}",
                f"Requirements: {regulatory_requirements}",
                f"Air Quality Status: {air_quality_status}"
            ]
            
        else:  # detailed format
            # New format for nonattainment_analysis files
            has_violations = data.get('has_violations', False)
            
            # Get affected pollutants from violations_details
            violations_details = data.get('violations_details', [])
            affected_pollutants = []
            for violation in violations_details:
                pollutant = violation.get('pollutant', 'Unknown')
                if pollutant not in affected_pollutants:
                    affected_pollutants.append(pollutant)
            
            # Get area classification from EPA summary
            epa_summary = data.get('epa_summary', {})
            area_classification = epa_summary.get('status', 'Attainment')
            
            # Generate regulatory implications based on violations
            if has_violations:
                regulatory_implications = [
                    f"Compliance Status: Nonattainment area identified",
                    f"Total Areas: {data.get('total_areas', 0)} nonattainment areas",
                    f"Air Quality Status: Violations of NAAQS standards"
                ]
            else:
                regulatory_implications = [
                    f"Compliance Status: No nonattainment areas identified",
                    f"Total Areas: {data.get('total_areas', 0)} nonattainment areas",
                    f"Air Quality Status: Meets all NAAQS standards"
                ]
        
        # Set default pollutants if none found
        if not affected_pollutants:
            affected_pollutants = ['None - Meets all NAAQS']
        
        return AirQualityAnalysisExpanded(
            location=data.get('location', {}),
            nonattainment_areas=[],
            air_quality_assessment=data.get('air_quality_assessment', {}),
            regulatory_requirements=data.get('regulatory_requirements', {}),
            monitoring_data=[],
            naaqs_standards={},
            data_sources=data.get('data_sources', {}),
            nonattainment_status=has_violations,
            affected_pollutants=affected_pollutants,
            area_classification=area_classification,
            regulatory_implications=regulatory_implications,
            map_reference="nonattainment_map_20250528_030558.pdf",
            map_generation_parameters=data.get('map_generation_parameters', {})
        )
    
    def extract_karst_analysis(self) -> Optional[KarstAnalysis]:
        """Extract karst analysis, prioritizing comprehensive data and including nearest feature info."""
        data = None
        is_comprehensive_format = False

        if 'karst_comprehensive' in self.json_files:
            data = self.json_files['karst_comprehensive']
            is_comprehensive_format = True
        elif 'karst_legacy' in self.json_files:
            data = self.json_files['karst_legacy']
            print("Note: Using legacy karst_analysis.json format.")
        else:
            return None 

        if not data: return None

        dev_constraints = []
        permits = []
        geo_significance = "Karst features are geologically sensitive. Precise significance depends on proximity and type."
        nearest_karst_info_for_report = None
        karst_map_ref = "N/A"

        # Prioritize specific embeddable map path, then archive, then generic search
        if is_comprehensive_format and data.get('karst_map_embed_path'):
            karst_map_ref = data['karst_map_embed_path']
        elif is_comprehensive_format and data.get('karst_map_archive_path'): # Fallback to PDF if PNG not there
            karst_map_ref = data['karst_map_archive_path']
        else: # Fallback to general search for older data or if specific paths missing
            project_dir_path = Path(self.data_directory).parent 
            maps_dir = project_dir_path / "maps"
            if maps_dir.exists():
                png_maps = list(maps_dir.glob("karst_map_embed_*.png*")) # Allow .png or .png32
                if png_maps:
                    karst_map_ref = f"maps/{png_maps[0].name}"
                else:
                    pdf_maps = list(maps_dir.glob("karst_map_archive_*.pdf"))
                    if pdf_maps:
                        karst_map_ref = f"maps/{pdf_maps[0].name}"
                    else: # Last resort, older naming convention
                        generic_pdf_maps = list(maps_dir.glob("karst_map_*.pdf"))
                        if generic_pdf_maps:
                            karst_map_ref = f"maps/{generic_pdf_maps[0].name}"
                        else:
                            generic_png_maps = list(maps_dir.glob("karst_map_*.png*"))
                            if generic_png_maps:
                                karst_map_ref = f"maps/{generic_png_maps[0].name}"
                            else:
                                html_maps = list(maps_dir.glob("karst_map_*.html")) 
                                if html_maps:
                                    karst_map_ref = f"maps/{html_maps[0].name} (HTML - View in Browser)"
        
        if is_comprehensive_format:
            status_general = data.get('karst_status_general', 'none')
            type_detailed = data.get('karst_type_detailed', 'N/A')
            zone_desc = data.get('specific_zone_description', 'N/A')
            impact_level = data.get('regulatory_impact_level', 'none')
            regulation_info = data.get('primary_regulation', 'N/A')
            message = data.get('message', 'N/A')
            guidance = data.get('interpretation_guidance', '')
            nearest_search_data = data.get('nearest_karst_search_results')

            within_general = (status_general == 'direct') or (status_general == 'buffer' and 'APE-ZC' in type_detailed) 
            
            if impact_level == 'high':
                dev_constraints.extend([
                    "Development activities likely restricted or require special permits/EIAs.",
                    "Geotechnical studies for karst geohazards are essential.",
                    "Foundation designs must account for potential sinkholes/instability.",
                    "Stormwater management needs careful design to prevent groundwater contamination.",
                    f"Specific Zone Identified: {zone_desc}"
                ])
                permits.append(f"PRAPEC permits / DNER endorsements highly likely. Regulation: {regulation_info}")
                geo_significance = f"Area is part of or near highly significant karst formations ({type_detailed}). Crucial for groundwater and ecosystems."
            elif impact_level == 'moderate':
                dev_constraints.extend([
                    "Proximity to sensitive karst features may require buffer zones or modified site plans.",
                    "Assess potential for indirect hydrological impacts on karst features.",
                    f"Specific Zone Identified: {zone_desc}"
                ])
                permits.append(f"Consultation with Planning Board/DNER recommended. Regulation: {regulation_info}")
                geo_significance = f"Area is near karst formations ({type_detailed}). Prudent site assessment advised."
            elif status_general == 'nearby_extended_search':
                 dev_constraints.append("Location is not directly in a mapped karst/buffer zone, but karst features were found nearby.")
                 geo_significance = f"Karst features identified in the vicinity ({type_detailed if type_detailed != 'None' else 'general PRAPEC/Zone0'}). Evaluate potential indirect impacts."
                 permits.append("Review proximity findings; standard permits apply unless indirect impacts trigger specific karst considerations.")
            else: # Low or None impact initially
                dev_constraints.append("Standard development practices may apply regarding karst, but always verify with PRAPEC master plan & Planning Board.")
            
            eo_note = "EO OE-2014-022 Note: This Executive Order established APE-RC (Restricted Karst), APE-ZC, and ZA. Consult official PRAPEC maps/documents for precise APE-RC boundaries & regulations. APE-ZC identified by this tool are key restricted zones."
            if eo_note not in dev_constraints : dev_constraints.insert(0, eo_note)

            if nearest_search_data:
                nearest_prapec = nearest_search_data.get('nearest_prapec_l15')
                nearest_zone0 = nearest_search_data.get('nearest_zone_l0')
                details_parts = []
                if nearest_prapec and nearest_prapec.get('found_within_radius'):
                    details_parts.append(f"Nearest PRAPEC (L15): Name '{nearest_prapec.get('Nombre', 'N/A')}', Regla {nearest_prapec.get('Regla', 'N/A')}. {nearest_prapec.get('estimated_distance_note')}")
                if nearest_zone0 and nearest_zone0.get('found_within_radius'):
                    details_parts.append(f"Nearest Zone (L0): Type '{nearest_zone0.get('CALI_SOBRE', 'N/A')}' (Project: {nearest_zone0.get('Proyecto', 'N/A')}, Description: {nearest_zone0.get('DES_SOBRE','N/A')}). {nearest_zone0.get('estimated_distance_note')}")
                if details_parts:
                    nearest_karst_info_for_report = {
                        "summary": "Karst features identified within extended search radius.",
                        "details": " ".join(details_parts),
                        "search_radius_miles": nearest_search_data.get("max_search_radius_miles")
                    }
            # Ensure guidance is a string
            guidance_str = guidance if isinstance(guidance, str) else "\n".join(guidance) if isinstance(guidance, list) else ""

            return KarstAnalysis(
                within_karst_area_general=within_general,
                karst_status_general=status_general,
                karst_type_detailed=type_detailed,
                specific_zone_description=zone_desc,
                regulatory_impact_level=impact_level,
                primary_regulation_info=regulation_info,
                summary_message=message,
                development_constraints=dev_constraints,
                geological_significance=geo_significance,
                permit_requirements=permits,
                map_reference=karst_map_ref, 
                interpretation_guidance=guidance_str,
                nearest_karst_details=nearest_karst_info_for_report
            )
        elif 'processed_summary' in data: # Handling for the older legacy format
            summary = data.get('processed_summary', {})
            legacy_status = summary.get('karst_status', 'no_karst')
            within_legacy = legacy_status in ['direct_intersection', 'in_karst']
            
            dev_constraints.append("Legacy Karst Data: Detailed zone type not available in this format.")
            dev_constraints.append("EO OE-2014-022 Note: Consult official PRAPEC maps/documents for precise APE-RC boundaries & regulations.")
            if within_legacy:
                dev_constraints.append("Development activities may be restricted.")
                permits.append("PRAPEC permit likely required.")
            
            return KarstAnalysis(
                within_karst_area_general=within_legacy,
                karst_status_general=legacy_status,
                karst_type_detailed=summary.get('karst_area_details',{}).get('official_name', 'PRAPEC Legacy'),
                specific_zone_description=summary.get('karst_area_details',{}).get('description', 'Legacy Data - APE-ZC/ZA not distinguished'),
                regulatory_impact_level=summary.get('regulatory_impact', 'unknown'),
                primary_regulation_info=summary.get('karst_area_details',{}).get('regulation_number', 'Legacy - See PRAPEC'),
                summary_message=summary.get('message', 'Legacy Karst Data - Details on specific zones (APE-ZC, ZA) may be limited.'),
                development_constraints=dev_constraints,
                geological_significance=geo_significance,
                permit_requirements=permits,
                map_reference=karst_map_ref,
                interpretation_guidance="Legacy data format. For detailed zone types (APE-ZC, ZA) and nearest feature analysis, re-process with current tools if possible. Always consult official PRAPEC documentation."
            )

        return None
    
    def generate_executive_summary(self, project_info: ProjectInfo, 
                                 cadastral: Optional[CadastralAnalysis],
                                 flood: Optional[FloodAnalysisExpanded],
                                 wetland: Optional[WetlandAnalysisExpanded],
                                 habitat: Optional[CriticalHabitatAnalysisExpanded],
                                 air_quality: Optional[AirQualityAnalysisExpanded],
                                 karst: Optional[KarstAnalysis] = None) -> ExecutiveSummary:
        """Generate executive summary based on all analyses"""
        
        property_overview = f"Environmental screening analysis for cadastral {project_info.project_name if project_info.project_name else 'N/A'} "
        if cadastral:
            property_overview += f"located in {cadastral.neighborhood if cadastral.neighborhood else 'N/A'}, {cadastral.municipality if cadastral.municipality else 'N/A'}, {cadastral.region if cadastral.region else 'N/A'}. "
            property_overview += f"The property is classified as {cadastral.land_use_classification if cadastral.land_use_classification else 'N/A'} "
            property_overview += f"with a total area of {cadastral.area_acres:.2f} acres ({cadastral.area_hectares:.2f} hectares)."
        else:
            property_overview += f"at coordinates {project_info.latitude:.4f}, {project_info.longitude:.4f}."

        constraints = []
        if flood and flood.primary_flood_zone != 'X' and flood.primary_flood_zone != 'Unknown':
            constraints.append(f"Located in FEMA Flood Zone {flood.primary_flood_zone}")
        if wetland and wetland.within_search_radius:
            constraints.append(f"Wetlands identified within search radius ({wetland.distance_to_nearest if wetland.distance_to_nearest is not None else 'N/A'} miles away)")
        if habitat and habitat.within_designated_habitat:
            constraints.append("Located within designated critical habitat")
        elif habitat and habitat.within_proposed_habitat:
            constraints.append("Located within proposed critical habitat")
        if air_quality and air_quality.nonattainment_status:
            constraints.append(f"Located in air quality nonattainment area for: { ', '.join(air_quality.affected_pollutants) if air_quality.affected_pollutants else 'N/A'}")
        
        if karst:
            if karst.karst_status_general == 'direct' or (karst.karst_status_general == 'buffer' and 'APE-ZC' in karst.karst_type_detailed):
                constraints.append(f"Located within/directly impacting a high-concern karst zone: {karst.karst_type_detailed} ({karst.regulatory_impact_level} impact)")
            elif karst.karst_status_general == 'buffer' and 'ZA' in karst.karst_type_detailed:
                constraints.append(f"Located within a karst buffer zone (ZA): {karst.specific_zone_description} ({karst.regulatory_impact_level} impact)")
            elif karst.karst_status_general == 'nearby_extended_search':
                constraints.append(f"Karst features identified nearby (extended search): {karst.summary_message} ({karst.regulatory_impact_level} impact)")
        
        if not constraints:
            constraints.append("No major environmental constraints identified from available data.")
        
        regulatory_highlights = []
        if flood and flood.regulatory_info:
            # Access regulatory info as dictionary
            reg_info = flood.regulatory_info
            if isinstance(reg_info, dict):
                highlights = []
                if reg_info.get('nfip_participation'):
                    highlights.append("NFIP participation required")
                if reg_info.get('permit_required'):
                    highlights.append("Special flood permit required")
                if reg_info.get('elevation_certificate_needed'):
                    highlights.append("Elevation certificate needed")
                regulatory_highlights.extend(highlights[:1])  # Take first one
            else:
                regulatory_highlights.append(str(reg_info))
        if wetland and wetland.regulatory_significance:
            regulatory_highlights.extend(wetland.regulatory_significance[:1]) 
        if habitat and habitat.regulatory_implications:
            regulatory_highlights.extend(habitat.regulatory_implications[:1]) 
        if air_quality and air_quality.regulatory_implications:
            regulatory_highlights.extend(air_quality.regulatory_implications[:1]) 
        if karst and karst.permit_requirements:
            regulatory_highlights.extend(karst.permit_requirements[:1])
        if not regulatory_highlights: regulatory_highlights.append("Standard regulatory processes apply.")
        
        risk_assessment_parts = []
        overall_risk_level = "Low"
        num_high_moderate_constraints = 0

        if flood and flood.primary_flood_zone not in ['X', 'C', 'Unknown']: num_high_moderate_constraints +=1
        if wetland and wetland.directly_on_property: num_high_moderate_constraints +=1
        if habitat and (habitat.within_designated_habitat or habitat.within_proposed_habitat): num_high_moderate_constraints +=1
        if air_quality and air_quality.nonattainment_status: num_high_moderate_constraints +=1
        if karst and karst.regulatory_impact_level in ['high', 'moderate']: num_high_moderate_constraints +=1

        if num_high_moderate_constraints >=3: overall_risk_level = "High"
        elif num_high_moderate_constraints >=1: overall_risk_level = "Moderate"
        
        risk_assessment_parts.append(f"Overall environmental risk profile assessed as: {overall_risk_level}.")
        if karst and karst.summary_message: risk_assessment_parts.append(f"Karst: {karst.summary_message}")
        # Add more specific risk details here if needed from other sections
        risk_assessment_final = " ".join(risk_assessment_parts)

        primary_recommendations = [
            "Conduct detailed site-specific environmental due diligence.",
            "Consult with qualified environmental professionals.",
            "Engage relevant regulatory agencies (e.g., Planning Board, DNER, USFWS, EPA, USACE) early in the planning process."
        ]
        if karst and karst.regulatory_impact_level in ['high', 'moderate']:
            primary_recommendations.append("Address specific PRAPEC karst regulations and recommendations detailed in the karst section.")
        
        return ExecutiveSummary(
            property_overview=property_overview,
            key_environmental_constraints=constraints,
            regulatory_highlights=regulatory_highlights,
            risk_assessment=risk_assessment_final,
            primary_recommendations=primary_recommendations
        )
    
    def generate_cumulative_risk_assessment(self, flood: Optional[FloodAnalysisExpanded],
                                          wetland: Optional[WetlandAnalysisExpanded],
                                          habitat: Optional[CriticalHabitatAnalysisExpanded],
                                          air_quality: Optional[AirQualityAnalysisExpanded],
                                          karst: Optional[KarstAnalysis] = None) -> Dict[str, Any]:
        """Generate cumulative environmental risk assessment"""
        
        risk_factors = []
        complexity_score = 0
        
        if flood:
            if flood.primary_flood_zone in ['AE', 'VE', 'A', 'V'] or (hasattr(flood, 'flood_risk_assessment') and 'High' in flood.flood_risk_assessment):
                risk_factors.append("High flood risk area")
                complexity_score += 3
            elif flood.primary_flood_zone in ['AH', 'AO'] or (hasattr(flood, 'flood_risk_assessment') and 'Moderate' in flood.flood_risk_assessment):
                risk_factors.append("Moderate flood risk area")
                complexity_score += 2
        
        if wetland:
            if wetland.directly_on_property:
                risk_factors.append("Direct wetland impacts identified on property")
                complexity_score += 4
            elif wetland.within_search_radius:
                risk_factors.append("Wetlands identified within search radius, proximity assessment needed")
                complexity_score += 1
        
        if habitat:
            if habitat.within_designated_habitat:
                risk_factors.append("Property within USFWS Designated Critical Habitat")
                complexity_score += 4
            elif habitat.within_proposed_habitat:
                risk_factors.append("Property within USFWS Proposed Critical Habitat")
                complexity_score += 3
            elif habitat.distance_to_nearest is not None and habitat.distance_to_nearest < 0.5:
                risk_factors.append("Property in very close proximity ( <0.5 miles) to Critical Habitat")
                complexity_score += 2
        
        if air_quality and air_quality.nonattainment_status:
            risk_factors.append(f"Property in EPA Nonattainment Area for: { ', '.join(air_quality.affected_pollutants) if air_quality.affected_pollutants else 'N/A'}")
            complexity_score += 2
        
        if karst:
            if karst.regulatory_impact_level == 'high':
                risk_factors.append(f"High karst regulatory impact: {karst.karst_type_detailed}")
                complexity_score += 4
            elif karst.regulatory_impact_level == 'moderate':
                risk_factors.append(f"Moderate karst regulatory impact: {karst.karst_type_detailed}")
                complexity_score += 2
            elif karst.karst_status_general == 'nearby_extended_search':
                risk_factors.append(f"Karst features found nearby (extended search), requires review.")
                complexity_score += 1
        
        if not risk_factors: risk_factors.append("No significant direct environmental risk factors identified from available data overlays.")

        overall_risk_profile = "Low"
        if complexity_score >= 10: overall_risk_profile = "High - Multiple significant environmental constraints"
        elif complexity_score >= 5: overall_risk_profile = "Moderate - Some environmental considerations required"
        elif complexity_score > 0 : overall_risk_profile = "Low to Moderate - Few specific constraints identified, standard diligence advised"
        
        development_feasibility = "Straightforward - Routine environmental compliance expected"
        if complexity_score >= 10: development_feasibility = "Complex - Extensive environmental studies and permitting likely required"
        elif complexity_score >= 5: development_feasibility = "Moderate - Standard environmental compliance with specific attention to identified factors needed"
        
        return {
            "risk_factors": risk_factors,
            "complexity_score": complexity_score,
            "overall_risk_profile": overall_risk_profile,
            "development_feasibility": development_feasibility,
            "integrated_assessment": f"Analysis identified {len(risk_factors)} primary environmental risk factors with a complexity score of {complexity_score} (out of a potential ~19 based on current factors)."
        }
    
    def collect_generated_files(self) -> List[str]:
        """Collect list of all generated files in the project directory"""
        project_dir = os.path.dirname(self.data_directory)
        generated_files = []
        
        # Check maps directory
        maps_dir = os.path.join(project_dir, "maps")
        if os.path.exists(maps_dir):
            for file in os.listdir(maps_dir):
                if file.endswith(('.pdf', '.png', '.jpg')):
                    generated_files.append(f"maps/{file}")
        
        # Check reports directory
        reports_dir = os.path.join(project_dir, "reports")
        if os.path.exists(reports_dir):
            for file in os.listdir(reports_dir):
                if file.endswith('.pdf'):
                    generated_files.append(f"reports/{file}")
        
        # Check logs directory
        logs_dir = os.path.join(project_dir, "logs")
        if os.path.exists(logs_dir):
            for file in os.listdir(logs_dir):
                if file.endswith('.json'):
                    generated_files.append(f"logs/{file}")
        
        return generated_files
    
    def generate_comprehensive_report(self) -> ComprehensiveReport:
        """Generate the complete comprehensive environmental screening report"""
        
        # Extract all sections
        project_info = self.extract_project_info()
        cadastral = self.extract_cadastral_analysis()
        flood = self.extract_flood_analysis()
        wetland = self.extract_wetland_analysis()
        habitat = self.extract_critical_habitat_analysis()
        air_quality = self.extract_air_quality_analysis()
        karst = self.extract_karst_analysis()
        
        # Generate executive summary
        executive_summary = self.generate_executive_summary(
            project_info, cadastral, flood, wetland, habitat, air_quality, karst
        )
        
        # Generate cumulative risk assessment
        cumulative_risk = self.generate_cumulative_risk_assessment(
            flood, wetland, habitat, air_quality, karst
        )
        
        # Compile comprehensive recommendations
        comprehensive_recommendations = [
            "Conduct site-specific environmental assessments before development",
            "Engage qualified environmental consultants early in project planning",
            "Coordinate with regulatory agencies for permit requirements"
        ]
        
        # Add specific recommendations from each analysis
        if flood and flood.flood_risk_assessment != "Low":
            comprehensive_recommendations.append("Obtain FEMA Elevation Certificate for construction planning")
        
        if wetland and wetland.within_search_radius:
            comprehensive_recommendations.append("Consider wetland delineation study if development near wetlands")
        
        if habitat and (habitat.within_designated_habitat or habitat.within_proposed_habitat):
            comprehensive_recommendations.append("Initiate ESA Section 7 consultation with USFWS/NOAA Fisheries")
        
        # Collect generated files
        generated_files = self.collect_generated_files()
        
        return ComprehensiveReport(
            project_info=project_info,
            executive_summary=executive_summary,
            cadastral_analysis=cadastral,
            karst_analysis=karst,
            flood_analysis=flood,
            wetland_analysis=wetland,
            critical_habitat_analysis=habitat,
            air_quality_analysis=air_quality,
            cumulative_risk_assessment=cumulative_risk,
            recommendations=comprehensive_recommendations,
            generated_files=generated_files
        )
    
    def export_to_json(self, output_file: str = None) -> str:
        """Export the comprehensive report to JSON format"""
        report = self.generate_comprehensive_report()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comprehensive_environmental_report_{timestamp}.json"
        
        # Convert dataclasses to dictionaries
        report_dict = self._dataclass_to_dict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def export_to_markdown(self, output_file: str = None) -> str:
        """Export the comprehensive report to Markdown format"""
        report = self.generate_comprehensive_report()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comprehensive_environmental_report_{timestamp}.md"
        
        markdown_content = self._generate_markdown_report(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return output_file
    
    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convert dataclass objects to dictionaries recursively"""
        if hasattr(obj, '__dataclass_fields__'):
            return {k: self._dataclass_to_dict(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [self._dataclass_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._dataclass_to_dict(v) for k, v in obj.items()}
        else:
            return obj
    
    def _generate_markdown_report(self, report: ComprehensiveReport) -> str:
        """Generate markdown format of the comprehensive report"""
        md = []
        
        # Title
        md.append(f"# Comprehensive Environmental Screening Report")
        md.append(f"## {report.project_info.project_name}")
        md.append(f"**Analysis Date & Time:** {report.project_info.analysis_date_time}")
        md.append("")
        
        # Project Information
        md.append("## 1. Project Information")
        md.append(f"- **Project Name:** {report.project_info.project_name}")
        md.append(f"- **Analysis Date & Time:** {report.project_info.analysis_date_time}")
        md.append(f"- **Location:** {report.project_info.longitude}, {report.project_info.latitude}")
        md.append(f"- **Cadastral Number(s):** {', '.join(report.project_info.cadastral_numbers)}")
        md.append(f"- **Location Name:** {report.project_info.location_name}")
        md.append(f"- **Project Directory:** {report.project_info.project_directory}")
        md.append("")
        
        # Executive Summary
        md.append("## 2. Executive Summary")
        md.append(f"**Property Overview:** {report.executive_summary.property_overview}")
        md.append("")
        md.append("**Key Environmental Constraints:**")
        for constraint in report.executive_summary.key_environmental_constraints:
            md.append(f"- {constraint}")
        md.append("")
        md.append("**Regulatory Highlights:**")
        for highlight in report.executive_summary.regulatory_highlights:
            md.append(f"- {highlight}")
        md.append("")
        md.append(f"**Risk Assessment:** {report.executive_summary.risk_assessment}")
        md.append("")
        md.append("**Primary Recommendations:**")
        for rec in report.executive_summary.primary_recommendations:
            md.append(f"- {rec}")
        md.append("")
        
        # Cadastral Analysis
        if report.cadastral_analysis:
            ca = report.cadastral_analysis
            md.append("## 3. Property & Cadastral Analysis")
            md.append(f"- **Cadastral Number(s):** {', '.join(ca.cadastral_numbers)}")
            md.append(f"- **Municipality:** {ca.municipality}")
            md.append(f"- **Neighborhood:** {ca.neighborhood}")
            md.append(f"- **Region:** {ca.region}")
            md.append(f"- **Land Use Classification:** {ca.land_use_classification}")
            md.append(f"- **Zoning Designation:** {ca.zoning_designation}")
            md.append(f"- **Area:** {ca.area_acres:.2f} acres ({ca.area_hectares:.2f} hectares, {ca.area_square_meters:.0f} m²)")
            md.append(f"- **Regulatory Status:** {ca.regulatory_status}")
            md.append("")
        
        # Karst Analysis
        if report.karst_analysis:
            ka = report.karst_analysis
            md.append("## 4. Karst Analysis (Applicable to Puerto Rico)")
            md.append(f"- **Overall Karst Status:** {ka.karst_status_general.capitalize() if ka.karst_status_general else 'N/A'}")
            md.append(f"- **Detailed Karst Zone Type:** {ka.karst_type_detailed if ka.karst_type_detailed else 'N/A'}")
            if ka.specific_zone_description and ka.specific_zone_description != 'N/A':
                 md.append(f"- **Specific Zone Details:** {ka.specific_zone_description}")
            md.append(f"- **Regulatory Impact Level:** {ka.regulatory_impact_level.capitalize() if ka.regulatory_impact_level else 'N/A'}")
            md.append(f"- **Primary Regulation(s):** {ka.primary_regulation_info if ka.primary_regulation_info else 'N/A'}")
            md.append(f"- **Summary Message:** {ka.summary_message if ka.summary_message else 'N/A'}")
            md.append("")
            if ka.nearest_karst_details and ka.nearest_karst_details.get('summary'):
                md.append("**Nearest Karst Features (Extended Search):**")
                md.append(f"- {ka.nearest_karst_details['summary']}")
                md.append(f"  - Details: {ka.nearest_karst_details.get('details', 'N/A')}")
                md.append(f"  - Searched up to: {ka.nearest_karst_details.get('search_radius_miles', 'N/A')} miles")
                md.append("")

            md.append("**Geological Significance Notes:**")
            md.append(f"- {ka.geological_significance if ka.geological_significance else 'Not assessed'}")
            md.append("")
            md.append("**Development Constraints & Considerations:**")
            for constraint in ka.development_constraints:
                md.append(f"- {constraint}")
            md.append("")
            md.append("**Potential Permit Requirements:**")
            for req in ka.permit_requirements:
                md.append(f"- {req}")
            md.append("")
            if ka.interpretation_guidance:
                md.append("**Interpretation Guidance:**")
                # Split guidance into lines for proper markdown list if it's a multi-line string formatted with newlines
                for line in ka.interpretation_guidance.split('\n'):
                    if line.strip().startswith("**") and not line.strip().startswith("- "):
                        md.append(line) # Main headers in guidance
                    elif line.strip().startswith("-"):
                        md.append(f"  {line}") # List items
                    elif line.strip():
                        md.append(f"  {line}") # Other lines indented
                    else:
                        md.append("") # Keep blank lines for spacing
                md.append("")
            md.append(f"**Map Reference:** {ka.map_reference}")
            md.append("")
        
        # Flood Analysis
        if report.flood_analysis:
            fa = report.flood_analysis
            md.append("## 5. Flood Analysis")
            md.append(f"- **FEMA Flood Zone:** {fa.primary_flood_zone}")
            if fa.base_flood_elevation:
                md.append(f"- **Base Flood Elevation (BFE):** {fa.base_flood_elevation} feet")
            else:
                md.append("- **Base Flood Elevation (BFE):** Not applicable")
            md.append(f"- **FIRM Panel:** {fa.firm_panel}")
            md.append(f"- **Effective Date:** {fa.effective_date}")
            md.append(f"- **Community:** {fa.community_name}")
            md.append(f"- **Preliminary vs. Effective:** {fa.preliminary_vs_effective}")
            md.append(f"- **ABFE Data Available:** {'Yes' if fa.abfe_data_available else 'No'}")
            md.append("")
            md.append("**Regulatory Requirements:**")
            # Handle regulatory_info as dictionary
            if hasattr(fa, 'regulatory_info') and isinstance(fa.regulatory_info, dict):
                reg_info = fa.regulatory_info
                if reg_info.get('nfip_participation'):
                    md.append("- NFIP participation required")
                if reg_info.get('permit_required'):
                    md.append("- Special flood permits required")
                if reg_info.get('elevation_certificate_needed'):
                    md.append("- Elevation certificate needed")
                if reg_info.get('crs_rating'):
                    md.append(f"- CRS Rating: {reg_info['crs_rating']}")
            else:
                md.append("- Standard flood requirements apply")
            md.append("")
            md.append(f"**Flood Risk Assessment:** {fa.flood_risk_assessment}")
            md.append("")
        
        # Wetland Analysis
        if report.wetland_analysis:
            wa = report.wetland_analysis
            md.append("## 6. Wetland Analysis")
            md.append(f"- **Directly on Property:** {'Yes' if wa.directly_on_property else 'No'}")
            md.append(f"- **Within Search Radius:** {'Yes' if wa.within_search_radius else 'No'}")
            if wa.distance_to_nearest:
                md.append(f"- **Distance to Nearest:** {wa.distance_to_nearest} miles")
            md.append("")
            md.append("**Wetland Classifications:**")
            for classification in wa.wetland_classifications:
                md.append(f"- {classification}")
            md.append("")
            md.append("**Regulatory Significance:**")
            for sig in wa.regulatory_significance:
                md.append(f"- {sig}")
            md.append("")
            md.append("**Development Guidance:**")
            for guidance in wa.development_guidance:
                md.append(f"- {guidance}")
            md.append("")
            md.append(f"**Map Reference:** {wa.map_reference}")
            md.append("")
        
        # Critical Habitat Analysis
        if report.critical_habitat_analysis:
            cha = report.critical_habitat_analysis
            md.append("## 7. Critical Habitat Analysis")
            md.append(f"- **Within Designated Critical Habitat:** {'Yes' if cha.within_designated_habitat else 'No'}")
            md.append(f"- **Within Proposed Critical Habitat:** {'Yes' if cha.within_proposed_habitat else 'No'}")
            if cha.distance_to_nearest:
                md.append(f"- **Distance to Nearest Habitat:** {cha.distance_to_nearest:.2f} miles")
            md.append("")
            md.append("**Affected Species:**")
            for species in cha.affected_species:
                md.append(f"- {species}")
            md.append("")
            md.append("**Regulatory Implications:**")
            for implication in cha.regulatory_implications:
                md.append(f"- {implication}")
            md.append("")
            md.append("**Development Constraints:**")
            for constraint in cha.development_constraints:
                md.append(f"- {constraint}")
            md.append("")
            md.append(f"**Map Reference:** {cha.map_reference}")
            md.append("")
        
        # Air Quality Analysis
        if report.air_quality_analysis:
            aqa = report.air_quality_analysis
            md.append("## 8. Air Quality (Nonattainment) Analysis")
            md.append(f"- **Nonattainment Status:** {'Yes' if aqa.nonattainment_status else 'No'}")
            md.append("**Affected Pollutants:**")
            for pollutant in aqa.affected_pollutants:
                md.append(f"- {pollutant}")
            md.append(f"- **Area Classification:** {aqa.area_classification}")
            md.append("")
            md.append("**Regulatory Implications:**")
            for implication in aqa.regulatory_implications:
                md.append(f"- {implication}")
            md.append("")
            md.append(f"**Map Reference:** {aqa.map_reference}")
            md.append("")
        
        # Cumulative Risk Assessment
        md.append("## 9. Cumulative Environmental Risk & Development Implications")
        cra = report.cumulative_risk_assessment
        integrated_assessment = cra.get('integrated_assessment', 'Comprehensive environmental analysis completed. See individual sections for detailed findings.')
        md.append(f"**Integrated Assessment:** {integrated_assessment}")
        md.append(f"**Overall Risk Profile:** {cra['overall_risk_profile']}")
        md.append(f"**Development Feasibility:** {cra['development_feasibility']}")
        md.append("")
        md.append("**Identified Risk Factors:**")
        for factor in cra['risk_factors']:
            md.append(f"- {factor}")
        md.append("")
        
        # Recommendations
        md.append("## 10. Recommendations & Compliance Guidance")
        for rec in report.recommendations:
            md.append(f"- {rec}")
        md.append("")
        
        # Generated Files
        md.append("## 11. Appendices / Generated Files")
        md.append("**File Inventory:**")
        for file in report.generated_files:
            md.append(f"- {file}")
        md.append("")
        
        return "\n".join(md)
    
    def _get_coordinates(self) -> Optional[List[float]]:
        """Extract coordinates from any available data source"""
        # Try project_info from comprehensive results first
        if 'project_info' in self.json_files:
            project_info = self.json_files['project_info']
            latitude = project_info.get('latitude')
            longitude = project_info.get('longitude')
            if latitude is not None and longitude is not None:
                return [longitude, latitude]
        
        # Try flood data from comprehensive results
        if 'flood_comprehensive' in self.json_files:
            location = self.json_files['flood_comprehensive'].get('location', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')
            if latitude is not None and longitude is not None:
                return [longitude, latitude]
        
        # Try flood data (legacy)
        if 'flood' in self.json_files:
            query_metadata = self.json_files['flood'].get('query_metadata', {})
            coords = query_metadata.get('coordinates', {})
            if coords:
                return [coords.get('longitude', 0), coords.get('latitude', 0)]
        
        # Try wetland data from comprehensive results
        if 'wetland_comprehensive' in self.json_files:
            location = self.json_files['wetland_comprehensive'].get('location', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')
            if latitude is not None and longitude is not None:
                return [longitude, latitude]
        
        # Try wetland data (legacy)
        if 'wetland' in self.json_files:
            location_analysis = self.json_files['wetland'].get('location_analysis', {})
            coords = location_analysis.get('coordinates', [])
            if len(coords) == 2:
                return coords
        
        # Try habitat data from comprehensive results
        if 'habitat_comprehensive' in self.json_files:
            location = self.json_files['habitat_comprehensive'].get('location', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')
            if latitude is not None and longitude is not None:
                return [longitude, latitude]
        
        # Try habitat data (legacy)
        if 'habitat' in self.json_files:
            habitat_analysis = self.json_files['habitat'].get('critical_habitat_analysis', {})
            location = habitat_analysis.get('location', [])
            if len(location) == 2:
                return location
        
        return None
    
    def _get_location_name(self) -> str:
        """Get location name from available data"""
        # Try project_info from comprehensive results first
        if 'project_info' in self.json_files:
            project_info = self.json_files['project_info']
            location = project_info.get('location', '')
            if location:
                return location
            # Also try project_name if location not available
            project_name = project_info.get('project_name', '')
            if project_name:
                return project_name
        
        # Try cadastral data from comprehensive results
        if 'cadastral_comprehensive' in self.json_files:
            cadastral_info = self.json_files['cadastral_comprehensive'].get('cadastral_info', {})
            municipality = cadastral_info.get('municipality', '')
            neighborhood = cadastral_info.get('neighborhood', '')
            if municipality and neighborhood:
                return f"{neighborhood}, {municipality}"
            elif municipality:
                return municipality
        
        # Try flood data (legacy)
        if 'flood' in self.json_files:
            query_metadata = self.json_files['flood'].get('query_metadata', {})
            location = query_metadata.get('location', '')
            if location:
                return location
        
        # Try wetland data (legacy)
        if 'wetland' in self.json_files:
            location_analysis = self.json_files['wetland'].get('location_analysis', {})
            location = location_analysis.get('location', '')
            if location:
                return location
        
        return "Environmental Screening Project"
    
    def _generate_project_name(self, cadastral_numbers: List[str], coords: Optional[List[float]]) -> str:
        """Generate a project name based on available information"""
        if cadastral_numbers and cadastral_numbers[0]:
            return f"Environmental Screening - Cadastral {cadastral_numbers[0]}"
        elif coords:
            return f"Environmental Screening - {coords[1]:.4f}, {coords[0]:.4f}"
        else:
            return "Environmental Screening Project"
    
    def _get_flood_regulatory_requirements(self, flood_zone: str) -> List[str]:
        """Get regulatory requirements based on flood zone"""
        requirements = []
        
        if flood_zone in ['AE', 'A', 'AH', 'AO']:
            requirements.extend([
                "Special Flood Hazard Area - NFIP compliance required",
                "Flood insurance mandatory for federally-backed mortgages",
                "Substantial improvement/damage rules apply",
                "Local floodplain management ordinances apply"
            ])
        elif flood_zone in ['VE', 'V']:
            requirements.extend([
                "High-velocity wave action area - enhanced construction standards",
                "Flood insurance mandatory for federally-backed mortgages",
                "No fill allowed below BFE",
                "Breakaway walls below BFE required"
            ])
        elif flood_zone == 'X':
            requirements.extend([
                "Outside Special Flood Hazard Area",
                "Standard building codes apply",
                "Flood insurance optional but recommended"
            ])
        else:
            requirements.append("Flood zone requirements to be determined")
        
        return requirements
    
    def _assess_flood_risk(self, flood_zone: str, bfe: Optional[float]) -> str:
        """Assess flood risk based on zone and BFE"""
        if flood_zone in ['VE', 'V']:
            return "High - High-velocity wave action area with significant coastal flood risk"
        elif flood_zone in ['AE', 'A']:
            return "Moderate to High - Located in 100-year floodplain"
        elif flood_zone in ['AH', 'AO']:
            return "Moderate - Shallow flooding area"
        elif flood_zone == 'X':
            return "Low - Outside Special Flood Hazard Area"
        else:
            return "Unknown - Flood zone classification unclear"


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Generate comprehensive environmental screening report from JSON data')
    parser.add_argument('data_directory', help='Directory containing JSON data files')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both', 
                       help='Output format (default: both)')
    parser.add_argument('--output', help='Output filename (without extension)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_directory):
        print(f"Error: Directory {args.data_directory} does not exist")
        return 1
    
    generator = ComprehensiveReportGenerator(args.data_directory)
    
    if not generator.json_files:
        print(f"Error: No valid JSON files found in {args.data_directory}")
        return 1
    
    print(f"Found {len(generator.json_files)} JSON data files")
    print("Generating comprehensive environmental screening report...")
    
    output_files = []
    
    if args.format in ['json', 'both']:
        json_file = generator.export_to_json(f"{args.output}.json" if args.output else None)
        output_files.append(json_file)
        print(f"JSON report exported to: {json_file}")
    
    if args.format in ['markdown', 'both']:
        md_file = generator.export_to_markdown(f"{args.output}.md" if args.output else None)
        output_files.append(md_file)
        print(f"Markdown report exported to: {md_file}")
    
    print(f"\nReport generation complete. Generated {len(output_files)} file(s).")
    return 0


if __name__ == "__main__":
    exit(main()) 