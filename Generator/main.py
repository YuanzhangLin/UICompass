# This file is used for processing the app source code.
from utils import general_utils
import config
import extract_info
import analyzer
import generate_element_description 
import UiMapGeneration
import time
import datetime
import llm

import xml.etree.ElementTree as ET
from pathlib import Path

import xml.etree.ElementTree as ET

import xml.etree.ElementTree as ET

def extract_package_names_from_manifest(xml_file_path: str, target_package_from_config: str) -> list[str]:
    """
    Extract all relevant package names from the AndroidManifest.xml file.
    (Version 4: Precisely find component tags, filter out intent-filter, etc., and force inclusion of the main package name from configuration file)
    
    Args:
        xml_file_path: Path to the AndroidManifest.xml file.
        target_package_from_config: Main package name read from the configuration file, ensuring it will be included.

    Returns:
        A deduplicated and sorted list of package name strings.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except (FileNotFoundError, ET.ParseError) as e:
        print(f"Error: Unable to read or parse file {xml_file_path}. {e}")
        return [target_package_from_config] if target_package_from_config else []

    ANDROID_NAMESPACE = '{http://schemas.android.com/apk/res/android}'
    packages = set()

    # 1. Force add the main package name from the configuration file
    if target_package_from_config:
        packages.add(target_package_from_config)

    # 2. Attempt to get the main package name from the Manifest file
    main_package_from_manifest = root.attrib.get('package')
    if main_package_from_manifest:
        packages.add(main_package_from_manifest)
    else:
        print("Info: Main 'package' attribute not found in <manifest> tag. Will only extract package names from full class names of components.")

    # If there's no main package name from both sources, subsequent relative paths cannot be resolved
    effective_main_package = main_package_from_manifest or target_package_from_config

    # 3. Find specific component tags under <application>
    application_element = root.find('application')
    if application_element is not None:
        # --- Key modification here: explicitly specify component types to find ---
        component_tags = [
            'activity'
        ]
        
        for tag in component_tags:
            for component in application_element.findall(tag):
                component_name = component.get(f'{ANDROID_NAMESPACE}name')
                if not component_name:
                    continue

                if '.' in component_name:
                    if component_name.startswith('.'):
                        if effective_main_package:
                            packages.add(effective_main_package)
                    else:
                        package = component_name.rsplit('.', 1)[0]
                        packages.add(package)  # Replace path separator with dot

    if not packages:
        print(f"Warning: Failed to extract any package names from '{xml_file_path}'.")
        return []

    return sorted(list(packages))

def load_app_config(app_config):
    config.app_name = app_config.get("app_name")
    config.target_project = '.' + app_config.get("target_project")
    config.target_project_source_code = config.target_project + app_config.get("source_code")
    config.target_package = app_config.get("target_package")
    config.target_project_AndroidManifest = config.target_project + 'AndroidManifest.xml'
    config.save_path = "./program_analysis_results/" + config.target_package.replace('.','_') + '/'
    # 2. Automatically extract analysis scope (package name list)
    print("\nExtracting analysis scope from Manifest file...")
    manifest_path = config.target_project_AndroidManifest
    # Call our core function
    package_list = extract_package_names_from_manifest(
        manifest_path, 
        config.target_package  # Pass in the main package name from the configuration
    )
    if package_list:
        print(f"  - Successfully extracted {len(package_list)} unique package names.")
        # 3. Update config object
        config.analysis_packages = package_list
        print("  - Configuration item 'analysis_packages' has been updated.")
    else:
        print("  - Failed to extract package names from Manifest, 'analysis_packages' will be empty.")
        config.analysis_packages = []
    if config.target_package:
        config.analysis_packages.append(config.target_package)

    print(f"  - Analysis scope (package name list): {config.analysis_packages}")
    print("\nApplication configuration loaded successfully.")
    print("-" * 30)


if __name__ == '__main__':
    app_configs = general_utils.read_json('./app_config.json')

    for app_config in app_configs:
        overall_start_time = time.monotonic()
        app_name_for_log = app_config.get('app_name', 'Unknown App')
        print("="*60)
        print(f"🚀 Starting processing for: {app_name_for_log} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        print("[1/5] App config loaded.")
        load_app_config(app_config)

        print("[2/5] Running extract_info...")
        current_time = time.monotonic()
        extract_info.extract()
        print(f"      ✅ Done in {time.monotonic() - current_time:.2f} seconds.")
        
        print("[3/5] Running analyzer_app...")
        current_time = time.monotonic()
        analyzer.analyzer_app()
        print(f"      ✅ Done in {time.monotonic() - current_time:.2f} seconds.")

        print("[4/5] Generating UI Map structure...")
        current_time = time.monotonic()
        code_map = UiMapGeneration.process_project()
        print(f"      ✅ Done in {time.monotonic() - current_time:.2f} seconds.")

        print("[5/5] Adding LLM-based activity summaries (this may take a while)...")
        current_time = time.monotonic()
        UiMapGeneration.add_activity_summary(code_map)
        print(f"      ✅ Done in {time.monotonic() - current_time:.2f} seconds.")
        if config.target_package:
            appname = config.target_package#.rsplit('.',1)[1]
        else:
            appname = config.app_name
        save_path = f'./code_maps/{appname}.json'
        UiMapGeneration.save_code_map(code_map, save_path)
        print(f"      💾 Code Map saved to '{save_path}'")
        
        overall_end_time = time.monotonic()
        total_duration_seconds = overall_end_time - overall_start_time
        formatted_total_duration = str(datetime.timedelta(seconds=total_duration_seconds))

        print("\n" + "="*60)
        print(f"🎉 Processing Complete for: {app_name_for_log}")
        print(f"Total time elapsed: {formatted_total_duration} (or {total_duration_seconds:.2f} seconds)")
        
        final_cost_summary = llm.cost_tracker.get_summary()
        print(final_cost_summary)
        print("="*60 + "\n")

        break