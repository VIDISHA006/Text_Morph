import pandas as pd
from sklearn.model_selection import train_test_split

# Path to your dataset
dataset_path = r"C:\Users\hp\OneDrive\Desktop\.vscode\new text morph\data\final_cleaned_normalized.csv"

# Load the dataset
df = pd.read_csv(dataset_path)

# Shuffle the dataset
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Split: 80% train, 10% validation, 10% test
train_df, temp_df = train_test_split(df, test_size=0.2, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

# Save the splits back to the data folder
data_folder = r"C:\Users\hp\OneDrive\Desktop\.vscode\new text morph\data"
train_df.to_csv(f"{data_folder}/train.csv", index=False)
val_df.to_csv(f"{data_folder}/val.csv", index=False)
test_df.to_csv(f"{data_folder}/test.csv", index=False)

print("Dataset split complete!")
print(f"Train: {len(train_df)} rows")
print(f"Validation: {len(val_df)} rows")
print(f"Test: {len(test_df)} rows")
