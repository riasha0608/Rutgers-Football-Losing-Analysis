import subprocess
import sys
import os

#treating each script as a subprocess
#will run the scripts one by one but in automated way like what is done in terminal but automated in this file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#includes proper formatting
#runs the script and gives error of respective script if error were to occur
def run_script(script_path):
    print(f"\n========== Running {script_path} ==========\n")

    try:
        subprocess.run([sys.executable, script_path], check = True)
    except subprocess.CalledProcessError as e:
        print(f"\n FAILED: {script_path}")
        print(e)
        exit(1)

#defines path of each script and then puts them through run_script to run one by one
def main():
    scripts = [
        os.path.join(BASE_DIR, "data_ingestion.py"),
        os.path.join(BASE_DIR, "data_cleaning.py"),
        os.path.join(BASE_DIR, "feature_engineering.py"),
        os.path.join(BASE_DIR, "sqlqueries.py"),
        os.path.join(BASE_DIR, "queryanalysis.py"),
        os.path.join(BASE_DIR, "eda.py"),
        os.path.join(BASE_DIR, "visualizations.py"),
        os.path.join(BASE_DIR, "machinelearningmodels.py")
    ]

    for script in scripts:
        run_script(script)
    
    print("\n========== ALL SCRIPTS COMPLETED ==========\n")

if __name__ == "__main__":
    main()