# manifest_utils.py
import xml.etree.ElementTree as ET

def get_package_from_manifest(manifest_path):
    """
    Parses an AndroidManifest.xml file to extract the package name from the <manifest> tag.

    Args:
        manifest_path (str): The full path to the AndroidManifest.xml file.

    Returns:
        str: The package name if found, otherwise None.
    """
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        # The package name is a direct attribute of the root 'manifest' tag.
        package_name = root.get('package')
        return package_name
    except ET.ParseError as e:
        print(f"      ❌ Error parsing AndroidManifest.xml: {e}")
        return None
    except FileNotFoundError:
        print(f"      ❌ AndroidManifest.xml not found at: {manifest_path}")
        return None