#!/usr/bin/env python3
"""
Run Comprehensive Environmental Screening for Cytoimmune Toa BAJA Project
"""

from comprehensive_environmental_agent import create_comprehensive_environmental_agent
from langchain_core.messages import HumanMessage

def main():
    """Run the comprehensive environmental screening for Cytoimmune Toa BAJA"""
    
    print("🌍 COMPREHENSIVE ENVIRONMENTAL SCREENING")
    print("=" * 60)
    print("🏢 Project: Cytoimmune Toa BAJA")
    print("🗺️  Cadastral: 060-000-009-58")
    print("📍 Location: Toa Baja, Puerto Rico")
    print()
    
    try:
        # Create agent
        print("🤖 Initializing comprehensive environmental agent...")
        agent = create_comprehensive_environmental_agent()
        print("✅ Agent created successfully!")
        
        # Query for Cytoimmune Toa BAJA project
        query = """Generate a comprehensive environmental screening report for Cytoimmune Toa BAJA project with cadastral 060-000-009-58 in Puerto Rico. I need complete property information, karst analysis, critical habitat analysis, air quality analysis, flood and wetland analysis with all reports, maps, and regulatory assessments."""
        
        print(f"\n📋 Query: {query}")
        print("\n🔄 Processing comprehensive environmental screening...")
        print("   This may take 2-5 minutes to generate all reports and maps...")
        
        # Run with thread_id configuration
        config = {'configurable': {'thread_id': 'cytoimmune_toa_baja_screening'}}
        response = agent.invoke({
            'messages': [HumanMessage(content=query)]
        }, config=config)
        
        # Print result
        last_message = response['messages'][-1]
        print("\n" + "="*80)
        print("✅ COMPREHENSIVE ENVIRONMENTAL SCREENING RESULTS:")
        print("="*80)
        print(last_message.content)
        
    except Exception as e:
        print(f"❌ Error during screening: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 