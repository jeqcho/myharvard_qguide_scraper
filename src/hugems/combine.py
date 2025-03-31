import pandas as pd
import os

def combine_csv_files(myharvard_year, myharvard_term, qguide_year, qguide_term):
    # Get the repository root directory (assuming this script is in src/hugems)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Define input and output paths relative to repo root
    qguide_path = os.path.join(repo_root, "release", "qguide", f"{qguide_year}_{qguide_term}.csv")
    myharvard_path = os.path.join(repo_root, "release", "myharvard", f"{myharvard_year}_{myharvard_term}.csv")
    folder_name = f"{myharvard_year}_{myharvard_term}_{qguide_year}_{qguide_term}"
    output_dir = os.path.join(repo_root, "release", "hugems", folder_name)
    
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract years and terms from input filenames
    myharvard_year_term = f"{myharvard_year}_{myharvard_term}"
    qguide_year_term = f"{qguide_year}_{qguide_term}"
    
    # Read the CSV files
    qguide_df = pd.read_csv(qguide_path)
    qguide_df = qguide_df.drop_duplicates(subset=['unique_code'])
    myharvard_df = pd.read_csv(myharvard_path)
    
    # Perform a left merge to keep all QGuide entries (including duplicates)
    # and match with MyHarvard data where possible
    # The only duplicate column should only be course_title
    # which can change over the years
    combined_df = pd.merge(
        qguide_df,
        myharvard_df,
        on='course_id',
        how='inner',
        suffixes=(f'_{qguide_year}', f'_{myharvard_year}')
    )
    
    # Save the combined dataset
    output_filename = "qguide_myharvard.csv"
    output_path = os.path.join(output_dir, output_filename)
    combined_df.to_csv(output_path, index=False)
    print(f"Combined CSV saved to: {output_path}")
    print(f"Total rows in combined file: {len(combined_df)}")
    print(f"Rows from QGuide 2024: {len(qguide_df)}")
    print(f"Rows from MyHarvard 2025: {len(myharvard_df)}")
    print(f"Rows with matches: {len(combined_df)}")

if __name__ == "__main__":
    # Specify years and terms
    myharvard_year = "2025"
    myharvard_term = "Fall"
    qguide_year = "2024"
    qguide_term = "Fall"
    
    combine_csv_files(
        myharvard_year=myharvard_year,
        myharvard_term=myharvard_term,
        qguide_year=qguide_year,
        qguide_term=qguide_term
    )