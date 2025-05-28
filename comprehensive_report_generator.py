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
class FloodAnalysis:
    """Flood Analysis section"""
    fema_flood_zone: str
    base_flood_elevation: Optional[float]
    firm_panel: str
    effective_date: str
    community_name: str
    preliminary_vs_effective: str
    abfe_data_available: bool
    regulatory_requirements: List[str]
    flood_risk_assessment: str


@dataclass
class WetlandAnalysis:
    """Wetland Analysis section"""
    directly_on_property: bool
    within_search_radius: bool
    distance_to_nearest: Optional[float]
    wetland_classifications: List[str]
    regulatory_significance: List[str]
    development_guidance: List[str]
    map_reference: str


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
class AirQualityAnalysis:
    """Air Quality (Nonattainment) Analysis section"""
    nonattainment_status: bool
    affected_pollutants: List[str]
    area_classification: str
    regulatory_implications: List[str]
    map_reference: str


@dataclass
class KarstAnalysis:
    """Karst Analysis section"""
    within_karst_area: bool
    karst_proximity: str
    distance_to_nearest: Optional[float]
    regulatory_impact: str
    development_constraints: List[str]
    geological_significance: str
    permit_requirements: List[str]
    map_reference: str


@dataclass
class ComprehensiveReport:
    """Complete environmental screening report"""
    project_info: ProjectInfo
    executive_summary: ExecutiveSummary
    cadastral_analysis: CadastralAnalysis
    karst_analysis: Optional[KarstAnalysis]
    flood_analysis: FloodAnalysis
    wetland_analysis: WetlandAnalysis
    critical_habitat_analysis: CriticalHabitatAnalysis
    air_quality_analysis: AirQualityAnalysis
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
        """Load all JSON files from the data directory"""
        json_pattern = os.path.join(self.data_directory, "*.json")
        json_files = glob.glob(json_pattern)
        
        for file_path in json_files:
            filename = os.path.basename(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Categorize files based on their content/filename
                if 'cadastral_search' in filename:
                    self.json_files['cadastral'] = data
                elif 'panel_info' in filename:
                    self.json_files['flood'] = data
                elif 'wetland_summary' in filename:
                    self.json_files['wetland'] = data
                elif 'critical_habitat' in filename:
                    self.json_files['habitat'] = data
                elif 'nonattainment_summary' in filename:
                    self.json_files['air_quality'] = data
                elif 'nonattainment_analysis' in filename:
                    self.json_files['air_quality_detailed'] = data
                elif 'karst_analysis' in filename or 'batch_karst_analysis' in filename:
                    self.json_files['karst'] = data
                    
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
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
    
    def extract_flood_analysis(self) -> Optional[FloodAnalysis]:
        """Extract flood analysis from panel info data"""
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
        
        return FloodAnalysis(
            fema_flood_zone=flood_zone,
            base_flood_elevation=bfe,
            firm_panel=firm_panel,
            effective_date=effective_date,
            community_name=community_name,
            preliminary_vs_effective=preliminary_comparison,
            abfe_data_available=True,  # Based on file listing
            regulatory_requirements=regulatory_requirements,
            flood_risk_assessment=risk_assessment
        )
    
    def extract_wetland_analysis(self) -> Optional[WetlandAnalysis]:
        """Extract wetland analysis"""
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
        
        return WetlandAnalysis(
            directly_on_property=directly_on_property,
            within_search_radius=within_radius,
            distance_to_nearest=distance_to_nearest,
            wetland_classifications=classifications,
            regulatory_significance=regulatory_significance,
            development_guidance=development_guidance,
            map_reference="wetland_map_Dynamic_Payments_Project_20250528_030451.pdf"
        )
    
    def extract_critical_habitat_analysis(self) -> Optional[CriticalHabitatAnalysis]:
        """Extract critical habitat analysis"""
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
        
        return CriticalHabitatAnalysis(
            within_designated_habitat=within_designated,
            within_proposed_habitat=within_proposed,
            distance_to_nearest=distance_miles,
            affected_species=affected_species,
            regulatory_implications=regulatory_implications,
            development_constraints=development_constraints,
            map_reference="critical_habitat_map_20250528_030539.pdf"
        )
    
    def extract_air_quality_analysis(self) -> Optional[AirQualityAnalysis]:
        """Extract air quality/nonattainment analysis"""
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
        
        return AirQualityAnalysis(
            nonattainment_status=has_violations,
            affected_pollutants=affected_pollutants,
            area_classification=area_classification,
            regulatory_implications=regulatory_implications,
            map_reference="nonattainment_map_20250528_030558.pdf"
        )
    
    def extract_karst_analysis(self) -> Optional[KarstAnalysis]:
        """Extract karst analysis from karst data files"""
        if 'karst' not in self.json_files:
            return None
            
        data = self.json_files['karst']
        
        # Handle both single and batch karst analysis formats
        if 'processed_summary' in data:
            # Single karst analysis format
            summary = data['processed_summary']
            raw_result = data.get('raw_result', {})
            
            # Fix karst status detection - handle all possible values
            karst_status = summary.get('karst_status', 'no_karst')
            within_karst = karst_status in ['direct_intersection', 'in_karst']
            
            karst_proximity = summary.get('karst_proximity', 'none')
            distance_str = summary.get('distance_miles', '> 0.5')
            regulatory_impact = summary.get('regulatory_impact', 'none')
            
            # Parse distance - handle string values like "within 0.5"
            distance_to_nearest = None
            if distance_str and distance_str not in ['> 0.5', 'none', 'within 0.5']:
                try:
                    # Try to extract numeric value from string
                    if isinstance(distance_str, str) and 'within' in distance_str:
                        # Extract number from "within X" format
                        import re
                        match = re.search(r'within\s+([\d.]+)', distance_str)
                        if match:
                            distance_to_nearest = float(match.group(1))
                    else:
                        distance_to_nearest = float(distance_str)
                except (ValueError, TypeError):
                    distance_to_nearest = None
            
            # Generate development constraints based on karst status
            development_constraints = []
            if within_karst:
                development_constraints = [
                    "Property is within PRAPEC karst area - Regulation 259 applies",
                    "Geological studies required before development",
                    "Special foundation and construction requirements",
                    "Environmental impact assessment may be required"
                ]
            elif karst_proximity in ['nearby', 'high', 'moderate']:
                development_constraints = [
                    "Property is near karst area - geological assessment recommended",
                    "Consider karst-related risks in site design",
                    "Monitor for subsidence or sinkhole potential"
                ]
            else:
                development_constraints = [
                    "No immediate karst-related development constraints identified"
                ]
            
            # Generate permit requirements
            permit_requirements = []
            if within_karst:
                permit_requirements = [
                    "PRAPEC karst area permit required (Regulation 259)",
                    "Geological study by licensed professional",
                    "Environmental impact assessment",
                    "Construction permit with special conditions"
                ]
            elif karst_proximity in ['nearby', 'high', 'moderate']:
                permit_requirements = [
                    "Geological assessment recommended",
                    "Standard construction permits with karst considerations"
                ]
            else:
                permit_requirements = [
                    "Standard permitting process - no special karst requirements"
                ]
            
            # Geological significance
            geological_significance = "Low"
            if within_karst:
                geological_significance = "High - Property within designated karst area"
            elif karst_proximity in ['nearby', 'high']:
                geological_significance = "Moderate - Close proximity to karst features"
            elif karst_proximity == 'moderate':
                geological_significance = "Low-Moderate - Some karst influence possible"
            
            return KarstAnalysis(
                within_karst_area=within_karst,
                karst_proximity=karst_proximity,
                distance_to_nearest=distance_to_nearest,
                regulatory_impact=regulatory_impact,
                development_constraints=development_constraints,
                geological_significance=geological_significance,
                permit_requirements=permit_requirements,
                map_reference="karst_analysis_map.pdf"  # Default reference
            )
            
        elif 'batch_summary' in data:
            # Batch karst analysis format
            batch_summary = data['batch_summary']
            overall_assessment = batch_summary.get('overall_assessment', {})
            
            # Use overall assessment for batch analysis
            high_risk = overall_assessment.get('high_risk_cadastrals', 0)
            moderate_risk = overall_assessment.get('moderate_risk_cadastrals', 0)
            
            within_karst = high_risk > 0
            karst_proximity = 'high' if high_risk > 0 else ('moderate' if moderate_risk > 0 else 'low')
            regulatory_impact = overall_assessment.get('overall_risk_level', 'low')
            
            # Generate constraints based on batch results
            development_constraints = []
            if high_risk > 0:
                development_constraints.append(f"{high_risk} cadastral(s) within karst areas")
            if moderate_risk > 0:
                development_constraints.append(f"{moderate_risk} cadastral(s) near karst areas")
            
            if not development_constraints:
                development_constraints = ["No significant karst constraints identified"]
            
            return KarstAnalysis(
                within_karst_area=within_karst,
                karst_proximity=karst_proximity,
                distance_to_nearest=None,  # Not available in batch format
                regulatory_impact=regulatory_impact,
                development_constraints=development_constraints,
                geological_significance=f"Batch analysis - {regulatory_impact} risk level",
                permit_requirements=["Refer to individual cadastral assessments"],
                map_reference="batch_karst_analysis_map.pdf"
            )
        
        return None
    
    def generate_executive_summary(self, project_info: ProjectInfo, 
                                 cadastral: Optional[CadastralAnalysis],
                                 flood: Optional[FloodAnalysis],
                                 wetland: Optional[WetlandAnalysis],
                                 habitat: Optional[CriticalHabitatAnalysis],
                                 air_quality: Optional[AirQualityAnalysis],
                                 karst: Optional[KarstAnalysis] = None) -> ExecutiveSummary:
        """Generate executive summary based on all analyses"""
        
        # Property overview
        property_overview = f"Environmental screening analysis for cadastral {', '.join(project_info.cadastral_numbers)} "
        if cadastral:
            property_overview += f"located in {cadastral.neighborhood}, {cadastral.municipality}, {cadastral.region}. "
            property_overview += f"The property is classified as {cadastral.land_use_classification} "
            property_overview += f"with a total area of {cadastral.area_acres:.2f} acres ({cadastral.area_hectares:.2f} hectares)."
        
        # Key environmental constraints
        constraints = []
        if flood and flood.fema_flood_zone != 'X':
            constraints.append(f"Located in FEMA Flood Zone {flood.fema_flood_zone}")
        if wetland and wetland.within_search_radius:
            constraints.append(f"Wetlands present within search radius")
        if habitat and habitat.within_designated_habitat:
            constraints.append("Located within designated critical habitat")
        if habitat and habitat.within_proposed_habitat:
            constraints.append("Located within proposed critical habitat")
        if air_quality and air_quality.nonattainment_status:
            constraints.append("Located in air quality nonattainment area")
        if karst and karst.within_karst_area:
            constraints.append("Located within PRAPEC karst area")
        elif karst and karst.karst_proximity in ['high', 'moderate']:
            constraints.append(f"Located near karst area ({karst.karst_proximity} proximity)")
        
        if not constraints:
            constraints.append("No major environmental constraints identified")
        
        # Regulatory highlights
        regulatory_highlights = []
        if flood:
            regulatory_highlights.extend(flood.regulatory_requirements[:2])  # Top 2
        if wetland and wetland.regulatory_significance:
            regulatory_highlights.append(wetland.regulatory_significance[0])
        if habitat:
            regulatory_highlights.extend(habitat.regulatory_implications[:1])  # Top 1
        if air_quality:
            regulatory_highlights.extend(air_quality.regulatory_implications[:1])  # Top 1
        if karst and karst.permit_requirements:
            regulatory_highlights.extend(karst.permit_requirements[:1])  # Top 1
        
        # Risk assessment
        risk_level = "Low"
        if len(constraints) > 3:
            risk_level = "High"
        elif len(constraints) > 1:
            risk_level = "Moderate"
        
        risk_assessment = f"{risk_level} environmental risk profile identified. "
        if flood and flood.fema_flood_zone not in ['X', 'Unknown']:
            risk_assessment += "Flood risk considerations required. "
        if wetland and wetland.directly_on_property:
            risk_assessment += "Direct wetland impacts possible. "
        if habitat and (habitat.within_designated_habitat or habitat.within_proposed_habitat):
            risk_assessment += "Critical habitat consultation required. "
        if karst and karst.within_karst_area:
            risk_assessment += "Karst area regulations apply (Regulation 259). "
        elif karst and karst.karst_proximity in ['high', 'moderate']:
            risk_assessment += "Karst proximity considerations recommended. "
        
        # Primary recommendations
        primary_recommendations = [
            "Conduct detailed environmental due diligence prior to development",
            "Consult with relevant regulatory agencies early in planning process",
            "Consider environmental constraints in site design and engineering"
        ]
        
        return ExecutiveSummary(
            property_overview=property_overview,
            key_environmental_constraints=constraints,
            regulatory_highlights=regulatory_highlights,
            risk_assessment=risk_assessment,
            primary_recommendations=primary_recommendations
        )
    
    def generate_cumulative_risk_assessment(self, flood: Optional[FloodAnalysis],
                                          wetland: Optional[WetlandAnalysis],
                                          habitat: Optional[CriticalHabitatAnalysis],
                                          air_quality: Optional[AirQualityAnalysis],
                                          karst: Optional[KarstAnalysis] = None) -> Dict[str, Any]:
        """Generate cumulative environmental risk assessment"""
        
        risk_factors = []
        complexity_score = 0
        
        # Flood risk
        if flood:
            if flood.fema_flood_zone in ['AE', 'VE', 'A']:
                risk_factors.append("High flood risk area")
                complexity_score += 3
            elif flood.fema_flood_zone in ['AH', 'AO']:
                risk_factors.append("Moderate flood risk area")
                complexity_score += 2
        
        # Wetland risk
        if wetland:
            if wetland.directly_on_property:
                risk_factors.append("Direct wetland impacts")
                complexity_score += 4
            elif wetland.within_search_radius:
                risk_factors.append("Nearby wetland considerations")
                complexity_score += 1
        
        # Habitat risk
        if habitat:
            if habitat.within_designated_habitat:
                risk_factors.append("Critical habitat overlap")
                complexity_score += 4
            elif habitat.within_proposed_habitat:
                risk_factors.append("Proposed critical habitat overlap")
                complexity_score += 3
            elif habitat.distance_to_nearest and habitat.distance_to_nearest < 1:
                risk_factors.append("Very close to critical habitat")
                complexity_score += 2
        
        # Air quality risk
        if air_quality and air_quality.nonattainment_status:
            risk_factors.append("Air quality nonattainment area")
            complexity_score += 2
        
        # Karst risk
        if karst:
            if karst.within_karst_area:
                risk_factors.append("Located within PRAPEC karst area")
                complexity_score += 4
            elif karst.karst_proximity == 'high':
                risk_factors.append("High proximity to karst area")
                complexity_score += 3
            elif karst.karst_proximity == 'moderate':
                risk_factors.append("Moderate proximity to karst area")
                complexity_score += 2
        
        # Overall risk profile (updated scoring to account for karst)
        if complexity_score >= 10:
            overall_risk = "High - Multiple significant environmental constraints"
        elif complexity_score >= 5:
            overall_risk = "Moderate - Some environmental considerations required"
        else:
            overall_risk = "Low - Minimal environmental constraints identified"
        
        # Development feasibility assessment (updated scoring)
        if complexity_score >= 10:
            feasibility = "Complex - Extensive environmental studies and permitting likely required"
        elif complexity_score >= 5:
            feasibility = "Moderate - Standard environmental compliance measures needed"
        else:
            feasibility = "Straightforward - Routine environmental compliance expected"
        
        return {
            "risk_factors": risk_factors,
            "complexity_score": complexity_score,
            "overall_risk_profile": overall_risk,
            "development_feasibility": feasibility,
            "integrated_assessment": f"Analysis identified {len(risk_factors)} primary environmental risk factors with a complexity score of {complexity_score}/16."
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
            md.append(f"- **Within Karst Area:** {'Yes' if ka.within_karst_area else 'No'}")
            md.append(f"- **Karst Proximity:** {ka.karst_proximity}")
            if ka.distance_to_nearest:
                md.append(f"- **Distance to Nearest:** {ka.distance_to_nearest} miles")
            md.append("")
            md.append("**Regulatory Impact:**")
            md.append(f"- {ka.regulatory_impact}")
            md.append("")
            md.append("**Development Constraints:**")
            for constraint in ka.development_constraints:
                md.append(f"- {constraint}")
            md.append("")
            md.append("**Permit Requirements:**")
            for req in ka.permit_requirements:
                md.append(f"- {req}")
            md.append("")
            md.append(f"**Geological Significance:** {ka.geological_significance}")
            md.append("")
            md.append(f"**Map Reference:** {ka.map_reference}")
            md.append("")
        
        # Flood Analysis
        if report.flood_analysis:
            fa = report.flood_analysis
            md.append("## 5. Flood Analysis")
            md.append(f"- **FEMA Flood Zone:** {fa.fema_flood_zone}")
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
            for req in fa.regulatory_requirements:
                md.append(f"- {req}")
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
        md.append(f"**Integrated Assessment:** {cra['integrated_assessment']}")
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
        # Try flood data first
        if 'flood' in self.json_files:
            query_metadata = self.json_files['flood'].get('query_metadata', {})
            coords = query_metadata.get('coordinates', {})
            if coords:
                return [coords.get('longitude', 0), coords.get('latitude', 0)]
        
        # Try wetland data
        if 'wetland' in self.json_files:
            location_analysis = self.json_files['wetland'].get('location_analysis', {})
            coords = location_analysis.get('coordinates', [])
            if len(coords) == 2:
                return coords
        
        # Try habitat data
        if 'habitat' in self.json_files:
            habitat_analysis = self.json_files['habitat'].get('critical_habitat_analysis', {})
            location = habitat_analysis.get('location', [])
            if len(location) == 2:
                return location
        
        return None
    
    def _get_location_name(self) -> str:
        """Get location name from available data"""
        # Try flood data
        if 'flood' in self.json_files:
            query_metadata = self.json_files['flood'].get('query_metadata', {})
            location = query_metadata.get('location', '')
            if location:
                return location
        
        # Try wetland data
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