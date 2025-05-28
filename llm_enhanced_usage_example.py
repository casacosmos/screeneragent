#!/usr/bin/env python3
"""
LLM-Enhanced Report Generator Usage Examples

This script demonstrates how to use the enhanced comprehensive report generator
with LLM capabilities for environmental screening analysis.
"""

import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_enhanced_report_generator import EnhancedComprehensiveReportGenerator


def example_1_basic_enhanced_report():
    """Example 1: Basic enhanced report generation with LLM"""
    
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Enhanced Report Generation")
    print("="*60)
    
    # Test data directory (adjust path as needed)
    data_directory = "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17/data"
    
    if not os.path.exists(data_directory):
        print(f"⚠️ Warning: Test data directory {data_directory} not found.")
        print("Please adjust the path to point to your JSON data directory.")
        return
    
    # Create enhanced generator
    print("Initializing LLM-enhanced report generator...")
    generator = EnhancedComprehensiveReportGenerator(
        data_directory=data_directory,
        model_name="gpt-4o-mini",  # Use efficient model for testing
        use_llm=True
    )
    
    # Generate enhanced report
    print("Generating enhanced comprehensive report...")
    try:
        report = generator.generate_enhanced_comprehensive_report()
        
        # Export to both formats
        json_file = generator.export_enhanced_report_to_json("example_enhanced_report.json")
        md_file = generator.export_enhanced_report_to_markdown("example_enhanced_report.md")
        
        print(f"✅ Enhanced report generated successfully!")
        print(f"   JSON: {json_file}")
        print(f"   Markdown: {md_file}")
        
        # Display some enhanced features
        if report.cumulative_risk_assessment.get('enhanced_assessment'):
            print("\n🤖 LLM-Enhanced Features Detected:")
            print(f"   Risk Level: {report.cumulative_risk_assessment.get('overall_risk_profile', 'N/A')}")
            print(f"   Development Feasibility: {report.cumulative_risk_assessment.get('development_feasibility', 'N/A')}")
            
            if 'llm_reasoning' in report.cumulative_risk_assessment:
                reasoning = report.cumulative_risk_assessment['llm_reasoning']
                print(f"   AI Reasoning: {reasoning[:150]}..." if len(reasoning) > 150 else f"   AI Reasoning: {reasoning}")
        
    except Exception as e:
        print(f"❌ Error generating enhanced report: {e}")
        print("This might be due to missing OpenAI API key or network issues.")


def example_2_comparison_with_without_llm():
    """Example 2: Compare reports with and without LLM enhancement"""
    
    print("\n" + "="*60)
    print("EXAMPLE 2: Comparison - With vs Without LLM")
    print("="*60)
    
    data_directory = "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17/data"
    
    if not os.path.exists(data_directory):
        print(f"⚠️ Warning: Test data directory {data_directory} not found.")
        return
    
    # Generate standard report (without LLM)
    print("1. Generating standard report (no LLM)...")
    standard_generator = EnhancedComprehensiveReportGenerator(
        data_directory=data_directory,
        use_llm=False
    )
    
    try:
        standard_report = standard_generator.generate_enhanced_comprehensive_report()
        standard_file = standard_generator.export_enhanced_report_to_json("standard_report_comparison.json")
        print(f"   Standard report: {standard_file}")
    except Exception as e:
        print(f"   ❌ Error with standard report: {e}")
        return
    
    # Generate enhanced report (with LLM)
    print("2. Generating enhanced report (with LLM)...")
    enhanced_generator = EnhancedComprehensiveReportGenerator(
        data_directory=data_directory,
        use_llm=True
    )
    
    try:
        enhanced_report = enhanced_generator.generate_enhanced_comprehensive_report()
        enhanced_file = enhanced_generator.export_enhanced_report_to_json("enhanced_report_comparison.json")
        print(f"   Enhanced report: {enhanced_file}")
        
        # Compare key differences
        print("\n📊 Comparison Results:")
        
        # Executive Summary Quality
        print(f"   Executive Summary:")
        print(f"     Standard: {len(standard_report.executive_summary.property_overview)} chars")
        print(f"     Enhanced: {len(enhanced_report.executive_summary.property_overview)} chars")
        
        # Risk Assessment
        standard_enhanced = standard_report.cumulative_risk_assessment.get('enhanced_assessment', False)
        enhanced_enhanced = enhanced_report.cumulative_risk_assessment.get('enhanced_assessment', False)
        print(f"   Risk Assessment Enhancement:")
        print(f"     Standard: {standard_enhanced}")
        print(f"     Enhanced: {enhanced_enhanced}")
        
        # Recommendations
        print(f"   Recommendations Count:")
        print(f"     Standard: {len(standard_report.recommendations)}")
        print(f"     Enhanced: {len(enhanced_report.recommendations)}")
        
    except Exception as e:
        print(f"   ❌ Error with enhanced report: {e}")


def example_3_different_models():
    """Example 3: Testing different LLM models"""
    
    print("\n" + "="*60)
    print("EXAMPLE 3: Testing Different LLM Models")
    print("="*60)
    
    data_directory = "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17/data"
    
    if not os.path.exists(data_directory):
        print(f"⚠️ Warning: Test data directory {data_directory} not found.")
        return
    
    # Test different models (uncomment available models)
    models_to_test = [
        "gpt-4o-mini",  # Fast and efficient
        # "gpt-4o",     # More capable but slower
        # "gpt-3.5-turbo",  # Alternative option
    ]
    
    for model_name in models_to_test:
        print(f"\nTesting model: {model_name}")
        
        try:
            generator = EnhancedComprehensiveReportGenerator(
                data_directory=data_directory,
                model_name=model_name,
                use_llm=True
            )
            
            # Quick test - just generate the enhanced data
            enhanced_data = generator.extract_with_llm_enhancement()
            
            if enhanced_data.get('enhanced_risk'):
                risk = enhanced_data['enhanced_risk']
                print(f"   ✅ Success! Risk Level: {risk.risk_level}")
                print(f"   Reasoning length: {len(risk.reasoning)} characters")
            else:
                print("   ⚠️ No enhanced risk assessment generated")
                
        except Exception as e:
            print(f"   ❌ Error with {model_name}: {e}")


def example_4_programmatic_usage():
    """Example 4: Programmatic usage with custom processing"""
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Programmatic Usage with Custom Processing")
    print("="*60)
    
    data_directory = "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17/data"
    
    if not os.path.exists(data_directory):
        print(f"⚠️ Warning: Test data directory {data_directory} not found.")
        return
    
    try:
        # Initialize generator
        generator = EnhancedComprehensiveReportGenerator(
            data_directory=data_directory,
            use_llm=True
        )
        
        # Extract enhanced data
        print("Extracting enhanced environmental data...")
        enhanced_data = generator.extract_with_llm_enhancement()
        
        # Process specific components
        print("\n📋 Processing Individual Components:")
        
        # 1. Project Information
        project_info = enhanced_data.get('project_info')
        if project_info:
            print(f"   📍 Property: {project_info.cadastral_numbers}")
            print(f"   📅 Analysis Date: {project_info.analysis_date_time}")
        
        # 2. Enhanced Risk Assessment
        if enhanced_data.get('enhanced_risk'):
            risk = enhanced_data['enhanced_risk']
            print(f"   🎯 Risk Level: {risk.risk_level}")
            print(f"   📊 Complexity Score: {risk.complexity_score}/12")
            print(f"   ⚠️ Key Risk Factors: {len(risk.key_risk_factors)} identified")
            
            # Display top risk factors
            for i, factor in enumerate(risk.key_risk_factors[:3], 1):
                print(f"      {i}. {factor}")
        
        # 3. LLM Summaries
        if enhanced_data.get('llm_summaries'):
            summaries = enhanced_data['llm_summaries']
            print(f"   💧 Flood Summary: {summaries.flood_summary[:100]}...")
            print(f"   🌊 Wetland Summary: {summaries.wetland_summary[:100]}...")
        
        # 4. Generate custom output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        custom_output = {
            'analysis_timestamp': timestamp,
            'property_id': project_info.cadastral_numbers[0] if project_info and project_info.cadastral_numbers else 'Unknown',
            'risk_summary': {
                'level': enhanced_data['enhanced_risk'].risk_level if enhanced_data.get('enhanced_risk') else 'Not assessed',
                'score': enhanced_data['enhanced_risk'].complexity_score if enhanced_data.get('enhanced_risk') else 0,
                'ai_enhanced': bool(enhanced_data.get('enhanced_risk'))
            },
            'regulatory_priorities': enhanced_data['enhanced_risk'].regulatory_concerns[:5] if enhanced_data.get('enhanced_risk') else []
        }
        
        # Save custom summary
        import json
        with open(f"custom_analysis_summary_{timestamp}.json", 'w') as f:
            json.dump(custom_output, f, indent=2)
        
        print(f"   💾 Custom summary saved: custom_analysis_summary_{timestamp}.json")
        
    except Exception as e:
        print(f"❌ Error in programmatic usage: {e}")


def example_5_batch_processing():
    """Example 5: Batch processing multiple directories"""
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Batch Processing Multiple Directories")
    print("="*60)
    
    # Define multiple test directories (adjust paths as needed)
    batch_directories = [
        "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17/data",
        # Add more directories as available
        # "output/Test_Comprehensive_Screening_20250528/data",
    ]
    
    results = []
    
    for i, data_dir in enumerate(batch_directories, 1):
        print(f"\nProcessing directory {i}/{len(batch_directories)}: {data_dir}")
        
        if not os.path.exists(data_dir):
            print(f"   ⚠️ Directory not found, skipping...")
            continue
        
        try:
            # Generate enhanced report
            generator = EnhancedComprehensiveReportGenerator(
                data_directory=data_dir,
                use_llm=True
            )
            
            # Quick processing
            enhanced_data = generator.extract_with_llm_enhancement()
            
            # Collect results
            result = {
                'directory': data_dir,
                'project_name': enhanced_data['project_info'].project_name if enhanced_data.get('project_info') else 'Unknown',
                'success': True,
                'risk_level': enhanced_data['enhanced_risk'].risk_level if enhanced_data.get('enhanced_risk') else 'Not assessed',
                'llm_enhanced': bool(enhanced_data.get('enhanced_risk'))
            }
            
            results.append(result)
            print(f"   ✅ Success - Risk Level: {result['risk_level']}")
            
        except Exception as e:
            result = {
                'directory': data_dir,
                'success': False,
                'error': str(e)
            }
            results.append(result)
            print(f"   ❌ Error: {e}")
    
    # Summary
    print(f"\n📊 Batch Processing Summary:")
    print(f"   Total directories processed: {len(results)}")
    print(f"   Successful: {sum(1 for r in results if r.get('success', False))}")
    print(f"   Failed: {sum(1 for r in results if not r.get('success', False))}")
    print(f"   LLM enhanced: {sum(1 for r in results if r.get('llm_enhanced', False))}")


def main():
    """Run all examples"""
    
    print("🤖 LLM-Enhanced Environmental Report Generator Examples")
    print("=" * 60)
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ Warning: OPENAI_API_KEY environment variable not set.")
        print("LLM features will be disabled. Set your API key to test LLM capabilities.")
        print("\nExport your API key with: export OPENAI_API_KEY='your-api-key-here'")
    
    # Run examples
    try:
        example_1_basic_enhanced_report()
        example_2_comparison_with_without_llm()
        example_3_different_models()
        example_4_programmatic_usage()
        example_5_batch_processing()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Examples interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print("\n" + "="*60)
    print("Examples completed! Check the generated files for results.")
    print("="*60)


if __name__ == "__main__":
    main() 