import pandas as pd

try:
    df1 = pd.read_excel(r"C:\Users\bgiglio\.gemini\antigravity\scratch\medication-lookup\app\storage\documents\NHS Drug Tariff List Jan 2026.xlsx")
    print("--- NHS Drug Tariff List Jan 2026.xlsx ---")
    print(df1.columns.tolist())
    print(df1.head(3).to_string())
except Exception as e:
    print(e)
    
try:
    df2 = pd.read_excel(r"C:\Users\bgiglio\.gemini\antigravity\scratch\medication-lookup\app\storage\documents\2025 ATC index with DDDs_english_download date 06112025.xlsx")
    print("\n--- 2025 ATC index with DDDs ---")
    print(df2.columns.tolist())
    print(df2.head(3).to_string())
except Exception as e:
    print(e)
