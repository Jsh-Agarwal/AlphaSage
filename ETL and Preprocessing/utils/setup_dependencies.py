import importlib
import subprocess
import sys
import os

def check_dependency(package_name, package_import=None, is_optional=False):
    """Check if a dependency is installed."""
    if package_import is None:
        package_import = package_name
        
    try:
        importlib.import_module(package_import)
        return True
    except ImportError:
        status = "OPTIONAL" if is_optional else "REQUIRED"
        print(f"[{status}] {package_name} is not installed")
        return False

def install_package(package_name):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {package_name}")
        return False

def check_dependencies():
    """Check all dependencies and provide installation options."""
    core_dependencies = [
        ("requests", "requests", False),
        ("pandas", "pandas", False),
        ("numpy", "numpy", False),
        ("yfinance", "yfinance", False),
        ("beautifulsoup4", "bs4", False),
        ("python-dateutil", "dateutil", False),
        ("neo4j", "neo4j", False),
        ("PyPDF2", "PyPDF2", True),
        ("GoogleNews", "GoogleNews", True)
    ]
    
    optional_dependencies = [
        ("transformers", "transformers", True),
        ("torch", "torch", True),
        ("pytesseract", "pytesseract", True),
        ("Pillow", "PIL", True),
        ("pdf2image", "pdf2image", True),
        ("edgar", "edgar", True),
        ("nselib", "nselib", True),
        ("selenium", "selenium", True),
        ("nltk", "nltk", True)
    ]
    
    missing_core = []
    missing_optional = []
    
    # Check core dependencies
    print("Checking core dependencies...")
    for package, module, optional in core_dependencies:
        if not check_dependency(package, module, optional):
            if optional:
                missing_optional.append(package)
            else:
                missing_core.append(package)
    
    # Check optional dependencies
    print("\nChecking optional dependencies...")
    for package, module, optional in optional_dependencies:
        if not check_dependency(package, module, optional):
            missing_optional.append(package)
    
    # Provide installation options
    if missing_core:
        print(f"\n{len(missing_core)} missing core dependencies. These are required for basic functionality.")
        install_choice = input("Install missing core dependencies? (y/n): ")
        if install_choice.lower() == 'y':
            for package in missing_core:
                install_package(package)
    
    if missing_optional:
        print(f"\n{len(missing_optional)} missing optional dependencies. These enable additional features.")
        print("Note: Some packages like talib may require special installation steps.")
        install_choice = input("Install missing optional dependencies? (y/n): ")
        if install_choice.lower() == 'y':
            for package in missing_optional:
                if package != "talib":  # Skip talib as it's special
                    install_package(package)
            
            # Provide instructions for talib
            if "talib" in missing_optional:
                print("\nSpecial instructions for TA-Lib:")
                print("TA-Lib requires separate installation steps:")
                print("1. Windows: Download and install from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib")
                print("2. Linux: Run 'apt-get install ta-lib' before pip install")
                print("3. Mac: Run 'brew install ta-lib' before pip install")
                print("\nAfter installing the dependencies, run: pip install TA-Lib")
    
    if not missing_core and not missing_optional:
        print("\nAll dependencies are installed! Your environment is ready.")
    else:
        print("\nAfter installing dependencies, restart your application.")

if __name__ == "__main__":
    print("Dependency Checker for Airavat Financial ETL Pipeline")
    print("=====================================================")
    check_dependencies()
