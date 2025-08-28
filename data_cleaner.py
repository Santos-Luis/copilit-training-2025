#!/usr/bin/env python3

import pandas as pd
import numpy as np

def clean_flight_data(input_file, output_file):
    """
    Clean the flight data by handling null values and missing data.
    """
    print(f"Reading data from {input_file}...")
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    print(f"Original dataset shape: {df.shape}")
    print(f"Original dataset columns: {list(df.columns)}")
    
    # Check for null values in each column
    print("\nNull values per column:")
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            print(f"  {col}: {count} null values")
    
    # Check for empty strings or other missing value indicators
    print("\nChecking for other missing value indicators...")
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            empty_count = (df[col] == '').sum()
            if empty_count > 0:
                print(f"  {col}: {empty_count} empty strings")
    
    # Create a copy for cleaning
    df_clean = df.copy()
    
    # Replace null values with appropriate defaults
    # For numeric columns (delays, times), replace with 0
    numeric_columns = ['DepDelay', 'ArrDelay', 'DepDel15', 'ArrDel15', 'CRSDepTime', 'CRSArrTime']
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna(0)
            print(f"Filled null values in {col} with 0")
    
    # For categorical columns, fill with appropriate defaults
    if 'Cancelled' in df_clean.columns:
        df_clean['Cancelled'] = df_clean['Cancelled'].fillna(0)
        print("Filled null values in Cancelled with 0")
    
    # For string columns, fill with 'Unknown' or appropriate default
    string_columns = ['Carrier', 'OriginAirportName', 'OriginCity', 'OriginState', 
                     'DestAirportName', 'DestCity', 'DestState']
    for col in string_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('Unknown')
            # Also replace empty strings
            df_clean[col] = df_clean[col].replace('', 'Unknown')
            print(f"Filled null/empty values in {col} with 'Unknown'")
    
    # For ID columns, fill with 0
    id_columns = ['OriginAirportID', 'DestAirportID']
    for col in id_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna(0)
            print(f"Filled null values in {col} with 0")
    
    # Verify no null values remain
    remaining_nulls = df_clean.isnull().sum().sum()
    print(f"\nRemaining null values after cleaning: {remaining_nulls}")
    
    if remaining_nulls > 0:
        print("Warning: Some null values still remain:")
        for col, count in df_clean.isnull().sum().items():
            if count > 0:
                print(f"  {col}: {count}")
    
    # Save the cleaned data
    print(f"\nSaving cleaned data to {output_file}...")
    df_clean.to_csv(output_file, index=False)
    
    print(f"Cleaned dataset shape: {df_clean.shape}")
    print("Data cleaning completed successfully!")
    
    # Show some basic statistics
    print(f"\nBasic statistics:")
    print(f"Total flights: {len(df_clean)}")
    print(f"Unique carriers: {df_clean['Carrier'].nunique()}")
    print(f"Unique origin airports: {df_clean['OriginAirportName'].nunique()}")
    print(f"Unique destination airports: {df_clean['DestAirportName'].nunique()}")
    print(f"Flights delayed > 15 min: {df_clean['ArrDel15'].sum()}")
    print(f"Percentage of flights delayed > 15 min: {(df_clean['ArrDel15'].sum() / len(df_clean) * 100):.2f}%")

if __name__ == "__main__":
    # Clean the data
    clean_flight_data("flights.csv", "clean-flights.csv")
