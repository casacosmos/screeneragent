#!/usr/bin/env python3
"""
LLM-Enhanced Comprehensive Environmental Screening Report Generator

This enhanced version leverages LangChain Expression Language (LCEL) and Large Language Models
to improve data extraction, synthesis, and report generation capabilities.

Features:
- Structured data extraction using LLM chain components
- Intelligent executive summary generation
- Automated risk assessment with LLM reasoning
- Enhanced report narrative using AI synthesis
- Flexible data retrieval chains for missing information
"""

import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import argparse

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableSequence, RunnableParallel, RunnableLambda
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model

# Import existing dataclasses from the original generator
from comprehensive_report_generator import (
    ProjectInfo, ExecutiveSummary, CadastralAnalysis, FloodAnalysis,
    WetlandAnalysis, CriticalHabitatAnalysis, AirQualityAnalysis,
    ComprehensiveReport, ComprehensiveReportGenerator
)


# Pydantic models for structured LLM outputs
class EnvironmentalRiskAssessment(BaseModel):
    """LLM-generated environmental risk assessment"""
    
    risk_level: str = Field(description="Overall risk level: Low, Moderate, or High")
    complexity_score: int = Field(description="Numerical complexity score from 0-12")
    key_risk_factors: List[str] = Field(description="Primary environmental risk factors identified")
    regulatory_concerns: List[str] = Field(description="Key regulatory compliance concerns")
    development_feasibility: str = Field(description="Assessment of development feasibility")
    reasoning: str = Field(description="Detailed reasoning behind the risk assessment")


class ExecutiveSummaryGeneration(BaseModel):
    """LLM-generated executive summary components"""
    
    property_overview: str = Field(description="Comprehensive property overview paragraph")
    key_constraints: List[str] = Field(description="List of key environmental constraints")
    regulatory_highlights: List[str] = Field(description="Most important regulatory requirements")
    risk_summary: str = Field(description="Summary of overall environmental risk")
    recommendations: List[str] = Field(description="Primary recommendations for project development")


class DataExtractionSummary(BaseModel):
    """LLM-processed summary of environmental data findings"""
    
    flood_summary: str = Field(description="Summary of flood analysis findings")
    wetland_summary: str = Field(description="Summary of wetland analysis findings")
    habitat_summary: str = Field(description="Summary of critical habitat findings")
    air_quality_summary: str = Field(description="Summary of air quality findings")
    integrated_assessment: str = Field(description="Integrated assessment of all environmental factors")


class EnhancedComprehensiveReportGenerator(ComprehensiveReportGenerator):
    """Enhanced report generator with LLM capabilities"""
    
    def __init__(self, data_directory: str, model_name: str = "gpt-4o-mini", use_llm: bool = True):
        super().__init__(data_directory)
        self.use_llm = use_llm
        
        if self.use_llm:
            try:
                # Initialize LLM
                self.llm = init_chat_model(model_name, model_provider="openai")
                
                # Set up LLM chains
                self._setup_llm_chains()
                
                print(f"✅ LLM initialized: {model_name}")
            except Exception as e:
                print(f"⚠️ Warning: LLM initialization failed: {e}")
                print("Falling back to standard processing without LLM enhancement")
                self.use_llm = False
    
    def _setup_llm_chains(self):
        """Set up LCEL chains for various LLM tasks"""
        
        # Risk Assessment Chain
        risk_prompt = ChatPromptTemplate.from_template(
            """You are an environmental compliance expert analyzing a property for development potential.

Based on the following environmental data, provide a comprehensive risk assessment:

PROPERTY DATA:
{property_data}

FLOOD DATA:
{flood_data}

WETLAND DATA:
{wetland_data}

HABITAT DATA:
{habitat_data}

AIR QUALITY DATA:
{air_quality_data}

Analyze these factors and provide a structured assessment considering:
1. Regulatory compliance complexity
2. Potential development constraints
3. Required permits and studies
4. Timeline and cost implications
5. Overall project viability

Provide specific reasoning for your assessment based on the data provided."""
        )
        
        risk_parser = PydanticOutputParser(pydantic_object=EnvironmentalRiskAssessment)
        
        self.risk_assessment_chain = RunnableSequence([
            risk_prompt,
            self.llm.with_structured_output(EnvironmentalRiskAssessment),
        ])
        
        # Executive Summary Chain
        summary_prompt = ChatPromptTemplate.from_template(
            """You are creating an executive summary for an environmental screening report.

Based on the comprehensive environmental analysis below, create a professional executive summary that would be suitable for regulatory submission and stakeholder presentation.

PROPERTY INFORMATION:
{property_info}

ENVIRONMENTAL ANALYSIS:
{environmental_analysis}

RISK ASSESSMENT:
{risk_assessment}

Create a compelling, professional executive summary that:
1. Clearly describes the property and project scope
2. Identifies key environmental constraints in priority order
3. Highlights the most critical regulatory requirements
4. Provides a clear risk assessment summary
5. Offers actionable recommendations for project success

Focus on practical implications for development and regulatory compliance."""
        )
        
        self.executive_summary_chain = RunnableSequence([
            summary_prompt,
            self.llm.with_structured_output(ExecutiveSummaryGeneration),
        ])
        
        # Data Integration Chain
        integration_prompt = ChatPromptTemplate.from_template(
            """You are synthesizing environmental data from multiple sources for a comprehensive analysis.

Raw Environmental Data:
{raw_data}

Create integrated summaries that:
1. Synthesize findings from each environmental domain
2. Identify cross-cutting issues and interactions
3. Highlight data gaps or inconsistencies
4. Provide context for regulatory implications

Focus on creating clear, technical summaries suitable for environmental professionals."""
        )
        
        self.data_integration_chain = RunnableSequence([
            integration_prompt,
            self.llm.with_structured_output(DataExtractionSummary),
        ])
        
        # Missing Data Chain for handling incomplete information
        data_gap_prompt = ChatPromptTemplate.from_template(
            """You are helping to identify and address data gaps in an environmental analysis.

Available Data:
{available_data}

Missing or Incomplete Data:
{missing_data}

Based on the available information, provide:
1. Reasonable assumptions for missing data points
2. Recommendations for additional data collection
3. Risk implications of data gaps
4. Interim conclusions that can be drawn

Be conservative in your assumptions and clearly flag areas needing additional investigation."""
        )
        
        self.data_gap_chain = RunnableSequence([
            data_gap_prompt,
            self.llm,
        ])
    
    def extract_with_llm_enhancement(self) -> Dict[str, Any]:
        """Extract and enhance data using LLM chains"""
        
        if not self.use_llm:
            return self._extract_standard_data()
        
        try:
            # Get base data
            base_data = self._extract_standard_data()
            
            # Prepare data for LLM processing
            llm_input = self._prepare_llm_input(base_data)
            
            # Run LLM enhancement chains in parallel for efficiency
            enhanced_data = self._run_enhancement_chains(llm_input)
            
            # Merge base data with LLM enhancements
            return self._merge_enhanced_data(base_data, enhanced_data)
            
        except Exception as e:
            print(f"⚠️ LLM enhancement failed: {e}")
            print("Falling back to standard data extraction")
            return self._extract_standard_data()
    
    def _extract_standard_data(self) -> Dict[str, Any]:
        """Extract standard data without LLM enhancement"""
        
        return {
            'project_info': self.extract_project_info(),
            'cadastral': self.extract_cadastral_analysis(),
            'flood': self.extract_flood_analysis(),
            'wetland': self.extract_wetland_analysis(),
            'habitat': self.extract_critical_habitat_analysis(),
            'air_quality': self.extract_air_quality_analysis(),
        }
    
    def _prepare_llm_input(self, base_data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare data for LLM processing"""
        
        def safe_serialize(obj):
            if obj is None:
                return "No data available"
            if hasattr(obj, '__dict__'):
                return json.dumps(asdict(obj), indent=2, default=str)
            return str(obj)
        
        return {
            'property_data': safe_serialize(base_data['project_info']),
            'flood_data': safe_serialize(base_data['flood']),
            'wetland_data': safe_serialize(base_data['wetland']),
            'habitat_data': safe_serialize(base_data['habitat']),
            'air_quality_data': safe_serialize(base_data['air_quality']),
            'raw_data': json.dumps({k: safe_serialize(v) for k, v in base_data.items()}, indent=2)
        }
    
    def _run_enhancement_chains(self, llm_input: Dict[str, str]) -> Dict[str, Any]:
        """Run LLM enhancement chains"""
        
        # Risk assessment
        risk_assessment = self.risk_assessment_chain.invoke(llm_input)
        
        # Data integration
        data_summary = self.data_integration_chain.invoke(llm_input)
        
        # Executive summary generation
        enhanced_input = {
            **llm_input,
            'environmental_analysis': data_summary.integrated_assessment,
            'risk_assessment': risk_assessment.reasoning
        }
        
        executive_summary = self.executive_summary_chain.invoke(enhanced_input)
        
        return {
            'risk_assessment': risk_assessment,
            'data_summary': data_summary,
            'executive_summary': executive_summary
        }
    
    def _merge_enhanced_data(self, base_data: Dict[str, Any], enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base data with LLM enhancements"""
        
        # Update executive summary with LLM-generated content
        if enhanced_data.get('executive_summary'):
            es = enhanced_data['executive_summary']
            base_data['executive_summary'] = ExecutiveSummary(
                property_overview=es.property_overview,
                key_environmental_constraints=es.key_constraints,
                regulatory_highlights=es.regulatory_highlights,
                risk_assessment=es.risk_summary,
                primary_recommendations=es.recommendations
            )
        
        # Add enhanced risk assessment
        if enhanced_data.get('risk_assessment'):
            base_data['enhanced_risk'] = enhanced_data['risk_assessment']
        
        # Add data summaries
        if enhanced_data.get('data_summary'):
            base_data['llm_summaries'] = enhanced_data['data_summary']
        
        return base_data
    
    def generate_enhanced_comprehensive_report(self) -> ComprehensiveReport:
        """Generate enhanced comprehensive report with LLM capabilities"""
        
        # Extract enhanced data
        enhanced_data = self.extract_with_llm_enhancement()
        
        # Generate cumulative risk assessment (enhanced if LLM available)
        if self.use_llm and enhanced_data.get('enhanced_risk'):
            risk = enhanced_data['enhanced_risk']
            cumulative_risk = {
                "risk_factors": risk.key_risk_factors,
                "complexity_score": risk.complexity_score,
                "overall_risk_profile": risk.risk_level + " - " + risk.reasoning[:100] + "...",
                "development_feasibility": risk.development_feasibility,
                "enhanced_assessment": True,
                "llm_reasoning": risk.reasoning
            }
        else:
            # Fall back to standard risk assessment
            cumulative_risk = self.generate_cumulative_risk_assessment(
                enhanced_data.get('flood'),
                enhanced_data.get('wetland'),
                enhanced_data.get('habitat'),
                enhanced_data.get('air_quality')
            )
            cumulative_risk["enhanced_assessment"] = False
        
        # Generate comprehensive recommendations
        recommendations = self._generate_enhanced_recommendations(enhanced_data)
        
        # Collect generated files
        generated_files = self.collect_generated_files()
        
        return ComprehensiveReport(
            project_info=enhanced_data['project_info'],
            executive_summary=enhanced_data.get('executive_summary') or self.generate_executive_summary(
                enhanced_data['project_info'],
                enhanced_data.get('cadastral'),
                enhanced_data.get('flood'),
                enhanced_data.get('wetland'),
                enhanced_data.get('habitat'),
                enhanced_data.get('air_quality')
            ),
            cadastral_analysis=enhanced_data.get('cadastral'),
            karst_analysis=None,  # Not implemented in current data
            flood_analysis=enhanced_data.get('flood'),
            wetland_analysis=enhanced_data.get('wetland'),
            critical_habitat_analysis=enhanced_data.get('habitat'),
            air_quality_analysis=enhanced_data.get('air_quality'),
            cumulative_risk_assessment=cumulative_risk,
            recommendations=recommendations,
            generated_files=generated_files
        )
    
    def _generate_enhanced_recommendations(self, enhanced_data: Dict[str, Any]) -> List[str]:
        """Generate enhanced recommendations using available data"""
        
        recommendations = []
        
        # Use LLM-generated recommendations if available
        if enhanced_data.get('executive_summary') and hasattr(enhanced_data['executive_summary'], 'recommendations'):
            recommendations.extend(enhanced_data['executive_summary'].recommendations)
        
        # Add standard recommendations as fallback/supplement
        standard_recommendations = [
            "Conduct detailed environmental due diligence prior to development",
            "Engage qualified environmental consultants early in project planning",
            "Coordinate with regulatory agencies for permit requirements"
        ]
        
        # Add specific recommendations based on findings
        flood = enhanced_data.get('flood')
        if flood and flood.flood_risk_assessment != "Low":
            recommendations.append("Obtain FEMA Elevation Certificate for construction planning")
        
        wetland = enhanced_data.get('wetland')
        if wetland and wetland.within_search_radius:
            recommendations.append("Consider wetland delineation study if development near wetlands")
        
        habitat = enhanced_data.get('habitat')
        if habitat and (habitat.within_designated_habitat or habitat.within_proposed_habitat):
            recommendations.append("Initiate ESA Section 7 consultation with USFWS/NOAA Fisheries")
        
        # Merge and deduplicate
        all_recommendations = recommendations + standard_recommendations
        return list(dict.fromkeys(all_recommendations))  # Remove duplicates while preserving order
    
    def export_enhanced_report_to_json(self, output_file: str = None) -> str:
        """Export enhanced report to JSON format"""
        
        report = self.generate_enhanced_comprehensive_report()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"enhanced_environmental_report_{timestamp}.json"
        
        # Convert to dict with special handling for enhanced fields
        report_dict = self._dataclass_to_dict(report)
        
        # Add LLM enhancement metadata
        report_dict['_metadata'] = {
            'generated_with_llm': self.use_llm,
            'generation_timestamp': datetime.now().isoformat(),
            'generator_version': 'enhanced_v1.0'
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def export_enhanced_report_to_markdown(self, output_file: str = None) -> str:
        """Export enhanced report to Markdown format with LLM improvements"""
        
        report = self.generate_enhanced_comprehensive_report()
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"enhanced_environmental_report_{timestamp}.md"
        
        markdown_content = self._generate_enhanced_markdown_report(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return output_file
    
    def _generate_enhanced_markdown_report(self, report: ComprehensiveReport) -> str:
        """Generate enhanced markdown format with LLM-generated sections"""
        
        md = []
        
        # Title and header
        md.append(f"# Enhanced Environmental Screening Report")
        md.append(f"## {report.project_info.project_name}")
        md.append(f"**Analysis Date & Time:** {report.project_info.analysis_date_time}")
        
        # Add LLM enhancement indicator
        if report.cumulative_risk_assessment.get('enhanced_assessment'):
            md.append("*🤖 This report includes AI-enhanced analysis and synthesis*")
        
        md.append("")
        
        # Use standard markdown generation but with enhanced content
        standard_md = self._generate_markdown_report(report)
        
        # Insert enhanced sections
        if report.cumulative_risk_assessment.get('llm_reasoning'):
            reasoning_section = f"""
## 🤖 AI-Enhanced Risk Analysis

**Advanced Risk Assessment:**
{report.cumulative_risk_assessment['llm_reasoning']}

"""
            # Insert after executive summary
            sections = standard_md.split("## 3. Property & Cadastral Analysis")
            if len(sections) == 2:
                enhanced_md = sections[0] + reasoning_section + "## 3. Property & Cadastral Analysis" + sections[1]
                return enhanced_md
        
        return standard_md


def main():
    """Main function for command-line usage with LLM enhancement"""
    
    parser = argparse.ArgumentParser(description='Generate enhanced environmental screening report with LLM capabilities')
    parser.add_argument('data_directory', help='Directory containing JSON data files')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both', 
                       help='Output format (default: both)')
    parser.add_argument('--output', help='Output filename (without extension)')
    parser.add_argument('--model', default='gpt-4o-mini', 
                       help='LLM model to use (default: gpt-4o-mini)')
    parser.add_argument('--no-llm', action='store_true', 
                       help='Disable LLM enhancement and use standard processing')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_directory):
        print(f"Error: Directory {args.data_directory} does not exist")
        return 1
    
    # Initialize enhanced generator
    generator = EnhancedComprehensiveReportGenerator(
        args.data_directory, 
        model_name=args.model,
        use_llm=not args.no_llm
    )
    
    if not generator.json_files:
        print(f"Error: No valid JSON files found in {args.data_directory}")
        return 1
    
    print(f"Found {len(generator.json_files)} JSON data files")
    enhancement_status = "with LLM enhancement" if generator.use_llm else "without LLM enhancement"
    print(f"Generating comprehensive environmental screening report {enhancement_status}...")
    
    output_files = []
    
    if args.format in ['json', 'both']:
        json_file = generator.export_enhanced_report_to_json(
            f"{args.output}.json" if args.output else None
        )
        output_files.append(json_file)
        print(f"Enhanced JSON report exported to: {json_file}")
    
    if args.format in ['markdown', 'both']:
        md_file = generator.export_enhanced_report_to_markdown(
            f"{args.output}.md" if args.output else None
        )
        output_files.append(md_file)
        print(f"Enhanced Markdown report exported to: {md_file}")
    
    print(f"\n✅ Enhanced report generation complete. Generated {len(output_files)} file(s).")
    
    if generator.use_llm:
        print("\n🤖 This report includes AI-enhanced analysis:")
        print("   • Intelligent risk assessment")
        print("   • LLM-generated executive summary")
        print("   • Enhanced data synthesis")
        print("   • Automated reasoning for conclusions")
    
    return 0


if __name__ == "__main__":
    exit(main()) 