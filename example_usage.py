#!/usr/bin/env python3
"""
Example Usage of Comprehensive Environmental Screening Report Generator

This script demonstrates how to use the ComprehensiveReportGenerator class
to create environmental screening reports from JSON data.
"""

from comprehensive_report_generator import ComprehensiveReportGenerator
import os


def main():
    """Example usage of the comprehensive report generator"""
    
    # Example 1: Generate report from a specific data directory
    data_directory = "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17/data"
    
    if os.path.exists(data_directory):
        print(f"🔍 Analyzing data directory: {data_directory}")
        
        # Initialize the generator
        generator = ComprehensiveReportGenerator(data_directory)
        
        # Check what data was loaded
        print(f"📊 Found {len(generator.json_files)} data files:")
        for key, data in generator.json_files.items():
            print(f"   - {key}: {type(data).__name__}")
        
        # Generate the comprehensive report object
        print("\n📋 Generating comprehensive report...")
        report = generator.generate_comprehensive_report()
        
        # Display key findings
        print(f"\n🏠 Project: {report.project_info.project_name}")
        print(f"📍 Location: {report.project_info.latitude:.4f}, {report.project_info.longitude:.4f}")
        
        if report.cadastral_analysis:
            print(f"🗺️  Cadastral: {report.cadastral_analysis.cadastral_numbers[0]}")
            print(f"🏘️  Municipality: {report.cadastral_analysis.municipality}")
            print(f"📐 Area: {report.cadastral_analysis.area_acres:.2f} acres")
        
        # Environmental constraints summary
        print(f"\n⚠️  Environmental Constraints:")
        for constraint in report.executive_summary.key_environmental_constraints:
            print(f"   - {constraint}")
        
        # Risk assessment
        print(f"\n📊 Risk Assessment: {report.cumulative_risk_assessment['overall_risk_profile']}")
        print(f"🏗️  Development Feasibility: {report.cumulative_risk_assessment['development_feasibility']}")
        
        # Export reports
        print(f"\n💾 Exporting reports...")
        json_file = generator.export_to_json("example_comprehensive_report.json")
        md_file = generator.export_to_markdown("example_comprehensive_report.md")
        
        print(f"   ✅ JSON report: {json_file}")
        print(f"   ✅ Markdown report: {md_file}")
        
        # Show generated files
        print(f"\n📁 Generated Files ({len(report.generated_files)}):")
        for file in report.generated_files:
            print(f"   - {file}")
        
    else:
        print(f"❌ Data directory not found: {data_directory}")
        print("   Please run the environmental screening tools first to generate data.")


def demonstrate_data_access():
    """Demonstrate how to access specific data sections"""
    
    data_directory = "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17/data"
    
    if not os.path.exists(data_directory):
        print("❌ Data directory not found for demonstration")
        return
        
    generator = ComprehensiveReportGenerator(data_directory)
    
    print("\n🔬 Detailed Data Access Examples:")
    
    # Access flood analysis
    flood_analysis = generator.extract_flood_analysis()
    if flood_analysis:
        print(f"\n🌊 Flood Analysis:")
        print(f"   Zone: {flood_analysis.fema_flood_zone}")
        print(f"   Risk: {flood_analysis.flood_risk_assessment}")
        print(f"   Panel: {flood_analysis.firm_panel}")
    
    # Access wetland analysis
    wetland_analysis = generator.extract_wetland_analysis()
    if wetland_analysis:
        print(f"\n🌿 Wetland Analysis:")
        print(f"   On Property: {wetland_analysis.directly_on_property}")
        print(f"   Nearby: {wetland_analysis.within_search_radius}")
        if wetland_analysis.distance_to_nearest:
            print(f"   Distance: {wetland_analysis.distance_to_nearest} miles")
    
    # Access critical habitat analysis
    habitat_analysis = generator.extract_critical_habitat_analysis()
    if habitat_analysis:
        print(f"\n🦎 Critical Habitat Analysis:")
        print(f"   In Designated: {habitat_analysis.within_designated_habitat}")
        print(f"   In Proposed: {habitat_analysis.within_proposed_habitat}")
        if habitat_analysis.distance_to_nearest:
            print(f"   Distance: {habitat_analysis.distance_to_nearest:.2f} miles")
        if habitat_analysis.affected_species:
            print(f"   Species: {', '.join(habitat_analysis.affected_species)}")
    
    # Access air quality analysis
    air_quality = generator.extract_air_quality_analysis()
    if air_quality:
        print(f"\n🌬️  Air Quality Analysis:")
        print(f"   Nonattainment: {air_quality.nonattainment_status}")
        print(f"   Classification: {air_quality.area_classification}")
        print(f"   Pollutants: {', '.join(air_quality.affected_pollutants)}")


if __name__ == "__main__":
    print("🌍 Comprehensive Environmental Screening Report Generator")
    print("=" * 60)
    
    main()
    demonstrate_data_access()
    
    print("\n" + "=" * 60)
    print("✅ Example completed successfully!")
    print("\n💡 Usage Tips:")
    print("   1. Run environmental screening tools first to generate JSON data")
    print("   2. Use the command line tool for batch processing")
    print("   3. Use the Python classes for custom integrations")
    print("   4. Check generated maps and reports in output directories") 