import asyncio
import json
from pathlib import Path
import sys
import os
import datetime

# Add the project root to the sys.path to allow importing modules
sys.path.append(str(Path(__file__).parent.parent))

from comprehensive_query_tool import ComprehensiveQueryTool
from html_report_generator.generate_environmental_report import EnvironmentalReportGenerator

# LangChain Imports
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI # Assuming you are using Google Generative AI

# Configure your Google Generative AI model
# Replace with your actual model name and ensure your API key is set in environment variables
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

def llm_fill_template(template_content: str, data: dict) -> str:
    """Fills an HTML template using an LLM based on provided JSON data.

    Args:
        template_content: The content of the HTML template.
        data: The JSON data to use for filling the template.

    Returns:
        The filled HTML content.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HTML template filling assistant. Your task is to meticulously populate an HTML template with the provided JSON data. "
                   "It is crucial that you use ALL relevant data points from the JSON to fill in every corresponding placeholder in the HTML template. "
                   "Pay special attention to nested data structures, such as flood analysis data, ensuring all sub-fields are accurately represented in the template. "
                   "The final output must be only the complete, valid HTML content."),
        ("user", f"Here is the HTML template:\n\n{{template_content}}\n\nHere is the JSON data:\n\n{{data}}\n\nCarefully fill in the template using all available data from the JSON. Provide only the resulting HTML output.")
    ])

    chain = prompt | llm | StrOutputParser()

    # Convert data dictionary to a JSON string for the prompt
    data_json_string = json.dumps(data, indent=2)

    filled_template = chain.invoke({"template_content": template_content, "data": data_json_string})

    return filled_template


async def main():
    """
    Demonstrates the full workflow: query data and generate HTML report.
    """
    print("🌍 Starting Environmental Report Generation Workflow")
    print("=" * 60)

    # --- 1. Define Location and Project ---
    location = "18.229400, -65.926600" # Example coordinates (Juncos, PR)
    project_name = "Workflow Test Project"
    output_base_dir = "workflow_output" # Base directory for all workflow output

    print(f"📍 Location: {location}")
    print(f"🏗️ Project: {project_name}")
    print(f"📁 Output will be in: {output_base_dir}")

    # --- 2. Retrieve Environmental Data ---
    print("\n🔍 Running Comprehensive Query Tool...")
    try:
        query_tool = ComprehensiveQueryTool(output_directory=output_base_dir, include_maps=False) # Set include_maps to False for faster testing
        query_results = await query_tool.query_all_environmental_data(
            location=location,
            project_name=project_name
        )

        # Check if comprehensive queries were successful (0 failed queries)
        if query_results.get('summary', {}).get('failed_queries', 1) == 0:
            print("✅ Comprehensive queries completed successfully.")
            template_data_file = query_results.get('template_data_file')
            project_directory = query_results.get('project_info', {}).get('project_directory')
            if template_data_file and project_directory:
                print(f"📊 Template data generated: {template_data_file}")
                print(f"📁 Project directory: {project_directory}")
            else:
                print("❌ Could not get template data file path or project directory from query results.")
                return
        else:
            print(f"❌ Comprehensive queries failed: {query_results.get('error', 'Unknown error')}")
            if query_results.get('errors'):
                 print("   Details:")
                 for err in query_results['errors']:
                     print(f"     - Tool '{err.get('tool')}': {err.get('error')}")
            return

    except Exception as e:
        print(f"❌ An error occurred during comprehensive queries: {e}")
        return

    # --- 3. Generate HTML Report ---
    print("\n📄 Generating HTML Report...")
    try:
        # The EnvironmentalReportGenerator will use the template and schema paths
        # relative to its own location or the cwd, or as specified.
        # We should ensure it can find them. They are in html_report_generator/.
        # The script itself is in the root, so relative paths from here are:
        template_path = "complete_environmental_template.html"
        schema_path = "html_report_generator/improved_template_data_schema.json"

        # Generate HTML report content using the LLM
        # Read the HTML template content
        with open(template_path, 'r') as f:
            html_template_content = f.read()

        # Read the generated JSON data
        with open(template_data_file, 'r') as f:
            template_data_structure = json.load(f)

        # Use the LLM to fill the template
        html_content = llm_fill_template(html_template_content, template_data_structure)

        # Define output paths
        report_output_path = Path(project_directory) / "reports"
        report_output_path.mkdir(parents=True, exist_ok=True)

        # Use the generate_report function to create both HTML and PDF
        # Instantiate the EnvironmentalReportGenerator
        report_generator = EnvironmentalReportGenerator(
            template_file="complete_environmental_template.html",
            schema_file="html_report_generator/improved_template_data_schema.json"
        )

        # Define base filename (mimicking logic from EnvironmentalReportGenerator)
        project_name_cleaned = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{project_name_cleaned}_{timestamp}"

        html_output_file = report_output_path / f"{base_filename}.html"
        pdf_output_file = report_output_path / f"{base_filename}.pdf"

        # Save the LLM-generated HTML content
        report_generator.save_html(html_content, str(html_output_file))
        print(f"✅ HTML Report saved: {html_output_file}")

        # Generate PDF from the LLM-generated HTML content
        report_generator.generate_pdf(html_content, str(pdf_output_file), method="weasyprint") # Explicitly use weasyprint
        print(f"✅ PDF Report generated: {pdf_output_file}")

        print(f"✅ Reports generated successfully in: {report_output_path}")

    except Exception as e:
        print(f"❌ An error occurred during report generation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 