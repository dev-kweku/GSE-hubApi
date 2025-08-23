# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
# from datetime import datetime, timedelta
# import os
# from pathlib import Path
# import warnings
# warnings.filterwarnings('ignore')

# # Set up paths
# data_dir = Path('gse_data')  # Updated to match your directory
# processed_dir = Path('processed_data')
# processed_dir.mkdir(exist_ok=True)

# def load_data(file_path=None):
#     """Load the scraped data from CSV file"""
#     if file_path is None:
#         # Look for the latest data file in the gse_data directory
#         csv_files = list(data_dir.glob('*.csv'))
#         if not csv_files:
#             raise FileNotFoundError("No CSV files found in the gse_data directory")
        
#         # Use the most recently modified file
#         latest_file = max(csv_files, key=os.path.getctime)
#         file_path = latest_file
#         print(f"Loading data from: {file_path}")
    
#     # Load the data
#     df = pd.read_csv(file_path)
    
#     # Check if the first row contains headers by looking for "Daily Date" in the first row
#     if "Daily Date" in df.iloc[0].values:
#         print("Detected header row in data, removing it...")
#         df = df.iloc[1:].reset_index(drop=True)
    
#     # Also check if "wdt_ID" is in the first row as an additional check
#     if "wdt_ID" in df.iloc[0].values:
#         print("Detected header row in data, removing it...")
#         df = df.iloc[1:].reset_index(drop=True)
    
#     # Convert date columns to datetime with error handling
#     if 'Daily Date' in df.columns:
#         try:
#             # First, let's check if there are any non-date values in the column
#             non_date_mask = ~df['Daily Date'].str.match(r'\d{2}/\d{2}/\d{4}', na=False)
#             if non_date_mask.any():
#                 print(f"Found {non_date_mask.sum()} non-date values in Daily Date column")
#                 # For debugging, let's see what these values are
#                 print("Non-date values:", df.loc[non_date_mask, 'Daily Date'].unique())
#                 # Remove these rows
#                 df = df[~non_date_mask].reset_index(drop=True)
            
#             # Now convert the dates
#             df['Daily Date'] = pd.to_datetime(df['Daily Date'], format='%d/%m/%Y')
#             print("Successfully converted Daily Date to datetime")
#         except Exception as e:
#             print(f"Error converting Daily Date: {e}")
#             # Try a different approach - skip the column for now
#             print("Skipping Daily Date conversion for now")
    
#     if 'Scraped_Date' in df.columns:
#         try:
#             df['Scraped_Date'] = pd.to_datetime(df['Scraped_Date'])
#             print("Successfully converted Scraped_Date to datetime")
#         except Exception as e:
#             print(f"Error converting Scraped_Date: {e}")
    
#     print(f"Data loaded successfully. Shape: {df.shape}")
#     return df

# def explore_data(df):
#     """Explore the data and print summary statistics"""
#     print("\n=== Data Exploration ===")
#     print(f"Shape: {df.shape}")
#     print(f"Columns: {list(df.columns)}")
    
#     print("\n=== Data Types ===")
#     print(df.dtypes)
    
#     print("\n=== Missing Values ===")
#     missing = df.isnull().sum()
#     missing_pct = (missing / len(df)) * 100
#     missing_info = pd.DataFrame({
#         'Missing Values': missing,
#         'Percentage': missing_pct
#     })
#     print(missing_info[missing_info['Missing Values'] > 0])
    
#     print("\n=== Basic Statistics ===")
#     print(df.describe())
    
#     print("\n=== Unique Share Codes ===")
#     if 'Share Code' in df.columns:
#         print(f"Number of unique stocks: {df['Share Code'].nunique()}")
#         print(df['Share Code'].value_counts().head(10))
    
#     print("\n=== Date Range ===")
#     if 'Daily Date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Daily Date']):
#         print(f"From: {df['Daily Date'].min()} to {df['Daily Date'].max()}")
#         print(f"Number of trading days: {df['Daily Date'].nunique()}")

# def clean_data(df):
#     """Clean the data by handling missing values and outliers"""
#     print("\n=== Cleaning Data ===")
    
#     # Make a copy to avoid modifying the original
#     df_clean = df.copy()
    
#     # 1. Handle missing values
#     # For numeric columns, fill with 0 (assuming no trading means 0 volume/value)
#     numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
#     for col in numeric_cols:
#         if col in df_clean.columns:
#             df_clean[col] = df_clean[col].fillna(0)
    
#     # For categorical columns, fill with 'Unknown'
#     categorical_cols = df_clean.select_dtypes(include=['object']).columns
#     for col in categorical_cols:
#         if col in df_clean.columns:
#             df_clean[col] = df_clean[col].fillna('Unknown')
    
#     # 2. Remove duplicates
#     initial_shape = df_clean.shape
#     df_clean = df_clean.drop_duplicates()
#     print(f"Removed {initial_shape[0] - df_clean.shape[0]} duplicate rows")
    
#     # 3. Handle outliers in numeric columns
#     # We'll use IQR method to identify and cap outliers
#     for col in ['Total Shares Traded', 'Total Value Traded (GH¢)']:
#         if col in df_clean.columns:
#             Q1 = df_clean[col].quantile(0.25)
#             Q3 = df_clean[col].quantile(0.75)
#             IQR = Q3 - Q1
#             lower_bound = Q1 - 1.5 * IQR
#             upper_bound = Q3 + 1.5 * IQR
            
#             # Cap outliers
#             df_clean[col] = np.where(df_clean[col] < lower_bound, lower_bound, df_clean[col])
#             df_clean[col] = np.where(df_clean[col] > upper_bound, upper_bound, df_clean[col])
#             print(f"Capped outliers in {col}")
    
#     # 4. Ensure all price columns are positive
#     price_cols = [
#         'Year High (GH¢)', 'Year Low (GH¢)', 'Previous Closing Price - VWAP (GH¢)',
#         'Opening Price (GH¢)', 'Last Transaction Price (GH¢)', 'Closing Price - VWAP (GH¢)',
#         'Price Change (GH¢)', 'Closing Bid Price (GH¢)', 'Closing Offer Price (GH¢)'
#     ]
    
#     for col in price_cols:
#         if col in df_clean.columns:
#             df_clean[col] = df_clean[col].abs()
    
#     print(f"Data cleaned. Final shape: {df_clean.shape}")
#     return df_clean

# def feature_engineering(df):
#     """Create new features for modeling"""
#     print("\n=== Feature Engineering ===")
    
#     df_fe = df.copy()
    
#     # 1. Date-based features
#     if 'Daily Date' in df_fe.columns and pd.api.types.is_datetime64_any_dtype(df_fe['Daily Date']):
#         df_fe['Year'] = df_fe['Daily Date'].dt.year
#         df_fe['Month'] = df_fe['Daily Date'].dt.month
#         df_fe['Day'] = df_fe['Daily Date'].dt.day
#         df_fe['DayOfWeek'] = df_fe['Daily Date'].dt.dayofweek
#         df_fe['Quarter'] = df_fe['Daily Date'].dt.quarter
#         df_fe['IsMonthEnd'] = df_fe['Daily Date'].dt.is_month_end.astype(int)
#         df_fe['IsMonthStart'] = df_fe['Daily Date'].dt.is_month_start.astype(int)
    
#     # 2. Price-based features
#     if all(col in df_fe.columns for col in ['Opening Price (GH¢)', 'Closing Price - VWAP (GH¢)']):
#         # Daily price range
#         df_fe['Daily_Price_Range'] = df_fe['Closing Price - VWAP (GH¢)'] - df_fe['Opening Price (GH¢)']
        
#         # Price change percentage
#         df_fe['Price_Change_Pct'] = (df_fe['Price Change (GH¢)'] / df_fe['Previous Closing Price - VWAP (GH¢)']) * 100
#         df_fe['Price_Change_Pct'] = df_fe['Price_Change_Pct'].fillna(0)
        
#         # Volatility (using daily range as a proxy)
#         df_fe['Volatility'] = (df_fe['Daily_Price_Range'] / df_fe['Opening Price (GH¢)']) * 100
#         df_fe['Volatility'] = df_fe['Volatility'].fillna(0).replace([np.inf, -np.inf], 0)
    
#     # 3. Volume-based features
#     if 'Total Shares Traded' in df_fe.columns:
#         # Log transform of volume to handle skewness
#         df_fe['Log_Volume'] = np.log1p(df_fe['Total Shares Traded'])
        
#         # Volume change (requires previous day's data - we'll calculate this later)
#         df_fe['Volume_Change'] = 0  # Placeholder
    
#     # 4. Value-based features
#     if 'Total Value Traded (GH¢)' in df_fe.columns:
#         # Log transform of value
#         df_fe['Log_Value'] = np.log1p(df_fe['Total Value Traded (GH¢)'])
        
#         # Average trade size
#         df_fe['Avg_Trade_Size'] = df_fe['Total Value Traded (GH¢)'] / df_fe['Total Shares Traded']
#         df_fe['Avg_Trade_Size'] = df_fe['Avg_Trade_Size'].fillna(0).replace([np.inf, -np.inf], 0)
    
#     # 5. Technical indicators (simplified versions)
#     if all(col in df_fe.columns for col in ['Closing Price - VWAP (GH¢)', 'Total Shares Traded']):
#         # Price momentum (3-day change)
#         df_fe['Price_Momentum_3d'] = 0  # Placeholder
        
#         # Volume momentum (3-day change)
#         df_fe['Volume_Momentum_3d'] = 0  # Placeholder
        
#         # Price-volume trend (simplified)
#         df_fe['Price_Volume_Trend'] = df_fe['Closing Price - VWAP (GH¢)'] * df_fe['Total Shares Traded']
    
#     # 6. Bid-Ask spread
#     if all(col in df_fe.columns for col in ['Closing Offer Price (GH¢)', 'Closing Bid Price (GH¢)']):
#         df_fe['Bid_Ask_Spread'] = df_fe['Closing Offer Price (GH¢)'] - df_fe['Closing Bid Price (GH¢)']
#         df_fe['Bid_Ask_Spread_Pct'] = (df_fe['Bid_Ask_Spread'] / df_fe['Closing Bid Price (GH¢)']) * 100
#         df_fe['Bid_Ask_Spread_Pct'] = df_fe['Bid_Ask_Spread_Pct'].fillna(0).replace([np.inf, -np.inf], 0)
    
#     print(f"Created {len(df_fe.columns) - len(df.columns)} new features")
#     return df_fe

# def calculate_lag_features(df, group_col='Share Code', date_col='Daily Date', lag_days=[1, 3, 5, 10]):
#     """Calculate lag features for time series analysis"""
#     print("\n=== Calculating Lag Features ===")
    
#     df_lag = df.copy()
    
#     # Sort by stock and date
#     df_lag = df_lag.sort_values([group_col, date_col])
    
#     # Calculate lag features for each stock
#     for lag in lag_days:
#         # Price lag
#         if 'Closing Price - VWAP (GH¢)' in df_lag.columns:
#             df_lag[f'Price_Lag_{lag}d'] = df_lag.groupby(group_col)['Closing Price - VWAP (GH¢)'].shift(lag)
        
#         # Volume lag
#         if 'Total Shares Traded' in df_lag.columns:
#             df_lag[f'Volume_Lag_{lag}d'] = df_lag.groupby(group_col)['Total Shares Traded'].shift(lag)
        
#         # Value lag
#         if 'Total Value Traded (GH¢)' in df_lag.columns:
#             df_lag[f'Value_Lag_{lag}d'] = df_lag.groupby(group_col)['Total Value Traded (GH¢)'].shift(lag)
        
#         # Volatility lag
#         if 'Volatility' in df_lag.columns:
#             df_lag[f'Volatility_Lag_{lag}d'] = df_lag.groupby(group_col)['Volatility'].shift(lag)
    
#     # Calculate rolling averages
#     for window in [3, 5, 10]:
#         if 'Closing Price - VWAP (GH¢)' in df_lag.columns:
#             df_lag[f'Price_MA_{window}d'] = df_lag.groupby(group_col)['Closing Price - VWAP (GH¢)'].transform(
#                 lambda x: x.rolling(window=window, min_periods=1).mean()
#             )
        
#         if 'Total Shares Traded' in df_lag.columns:
#             df_lag[f'Volume_MA_{window}d'] = df_lag.groupby(group_col)['Total Shares Traded'].transform(
#                 lambda x: x.rolling(window=window, min_periods=1).mean()
#             )
    
#     # Calculate momentum features
#     if all(col in df_lag.columns for col in ['Closing Price - VWAP (GH¢)', 'Price_Lag_1d']):
#         df_lag['Price_Momentum_1d'] = (
#             (df_lag['Closing Price - VWAP (GH¢)'] - df_lag['Price_Lag_1d']) / df_lag['Price_Lag_1d']
#         ) * 100
#         df_lag['Price_Momentum_1d'] = df_lag['Price_Momentum_1d'].fillna(0).replace([np.inf, -np.inf], 0)
    
#     if all(col in df_lag.columns for col in ['Total Shares Traded', 'Volume_Lag_1d']):
#         df_lag['Volume_Momentum_1d'] = (
#             (df_lag['Total Shares Traded'] - df_lag['Volume_Lag_1d']) / df_lag['Volume_Lag_1d']
#         ) * 100
#         df_lag['Volume_Momentum_1d'] = df_lag['Volume_Momentum_1d'].fillna(0).replace([np.inf, -np.inf], 0)
    
#     print(f"Calculated lag features for {lag_days} days")
#     return df_lag

# def create_target_variable(df, horizon=1):
#     """Create target variable for prediction"""
#     print(f"\n=== Creating Target Variable (horizon={horizon} days) ===")
    
#     df_target = df.copy()
    
#     # Sort by stock and date
#     df_target = df_target.sort_values(['Share Code', 'Daily Date'])
    
#     # Calculate future returns
#     if 'Closing Price - VWAP (GH¢)' in df_target.columns:
#         df_target['Future_Price'] = df_target.groupby('Share Code')['Closing Price - VWAP (GH¢)'].shift(-horizon)
#         df_target['Future_Return'] = (
#             (df_target['Future_Price'] - df_target['Closing Price - VWAP (GH¢)']) / 
#             df_target['Closing Price - VWAP (GH¢)']
#         ) * 100
        
#         # Create binary target (1 if positive return, 0 otherwise)
#         df_target['Target'] = (df_target['Future_Return'] > 0).astype(int)
        
#         # Create multi-class target (1: strong buy, 2: buy, 3: hold, 4: sell, 5: strong sell)
#         # Using return percentiles with handling for duplicate percentiles
#         for stock in df_target['Share Code'].unique():
#             stock_data = df_target[df_target['Share Code'] == stock].copy()
#             if len(stock_data) > 10:  # Only for stocks with sufficient data
#                 # Get percentiles
#                 percentiles = stock_data['Future_Return'].quantile([0.2, 0.4, 0.6, 0.8]).values
                
#                 # Remove duplicates while preserving order
#                 unique_percentiles = []
#                 for p in percentiles:
#                     if p not in unique_percentiles:
#                         unique_percentiles.append(p)
                
#                 # If we have less than 4 unique percentiles, create custom bins
#                 if len(unique_percentiles) < 4:
#                     # Use fixed bins based on return distribution
#                     returns = stock_data['Future_Return'].dropna()
#                     if len(returns) > 0:
#                         # Create bins based on standard deviations from mean
#                         mean_return = returns.mean()
#                         std_return = returns.std()
                        
#                         # Define bin edges
#                         bin_edges = [
#                             -np.inf,
#                             mean_return - 1.5 * std_return,  # Strong sell
#                             mean_return - 0.5 * std_return,  # Sell
#                             mean_return + 0.5 * std_return,  # Buy
#                             mean_return + 1.5 * std_return,  # Strong buy
#                             np.inf
#                         ]
                        
#                         # Ensure bin edges are unique
#                         bin_edges = sorted(list(set(bin_edges)))
                        
#                         # If we still have duplicates, use evenly spaced bins
#                         if len(bin_edges) < 5:
#                             min_return = returns.min()
#                             max_return = returns.max()
#                             bin_edges = np.linspace(min_return, max_return, 6).tolist()
#                             bin_edges[0] = -np.inf
#                             bin_edges[-1] = np.inf
#                     else:
#                         # Fallback to simple bins
#                         bin_edges = [-np.inf, -1, 0, 1, np.inf]
#                 else:
#                     # Use the unique percentiles as bin edges
#                     bin_edges = [-np.inf] + unique_percentiles + [np.inf]
                
#                 # Create the target classes
#                 try:
#                     df_target.loc[df_target['Share Code'] == stock, 'Target_Class'] = pd.cut(
#                         stock_data['Future_Return'],
#                         bins=bin_edges,
#                         labels=[5, 4, 3, 2, 1],
#                         include_lowest=True
#                     )
#                 except Exception as e:
#                     print(f"Error creating target classes for {stock}: {e}")
#                     # Assign default value (hold)
#                     df_target.loc[df_target['Share Code'] == stock, 'Target_Class'] = 3
        
#         # Fill missing target classes with 3 (hold)
#         df_target['Target_Class'] = df_target['Target_Class'].fillna(3).astype(int)
    
#     print(f"Created target variable with {df_target['Target'].value_counts().to_dict()}")
#     print(f"Target class distribution: {df_target['Target_Class'].value_counts().to_dict()}")
#     return df_target

# def encode_categorical_features(df):
#     """Encode categorical features"""
#     print("\n=== Encoding Categorical Features ===")
    
#     df_encoded = df.copy()
    
#     # Encode Share Code using label encoding
#     if 'Share Code' in df_encoded.columns:
#         from sklearn.preprocessing import LabelEncoder
#         le = LabelEncoder()
#         df_encoded['Share_Code_Encoded'] = le.fit_transform(df_encoded['Share Code'])
        
#         # Save the encoder for future use
#         import joblib
#         joblib.dump(le, processed_dir / 'share_code_encoder.pkl')
#         print("Encoded Share Code and saved encoder")
    
#     # One-hot encode categorical columns with few unique values
#     categorical_cols = ['DayOfWeek', 'Month', 'Quarter']
#     for col in categorical_cols:
#         if col in df_encoded.columns and df_encoded[col].nunique() <= 12:
#             dummies = pd.get_dummies(df_encoded[col], prefix=col)
#             df_encoded = pd.concat([df_encoded, dummies], axis=1)
#             print(f"One-hot encoded {col}")
    
#     return df_encoded

# def finalize_dataset(df):
#     """Finalize the dataset by removing unnecessary columns and handling missing values"""
#     print("\n=== Finalizing Dataset ===")
    
#     df_final = df.copy()
    
#     # Remove rows with missing target values
#     if 'Target' in df_final.columns:
#         initial_rows = len(df_final)
#         df_final = df_final.dropna(subset=['Target'])
#         print(f"Removed {initial_rows - len(df_final)} rows with missing target values")
    
#     # Remove columns with too many missing values
#     missing_pct = df_final.isnull().sum() / len(df_final) * 100
#     cols_to_drop = missing_pct[missing_pct > 50].index
#     if len(cols_to_drop) > 0:
#         df_final = df_final.drop(columns=cols_to_drop)
#         print(f"Dropped columns with >50% missing values: {list(cols_to_drop)}")
    
#     # Fill remaining missing values
#     numeric_cols = df_final.select_dtypes(include=[np.number]).columns
#     for col in numeric_cols:
#         if df_final[col].isnull().sum() > 0:
#             df_final[col] = df_final[col].fillna(df_final[col].median())
    
#     # Remove non-numeric columns that aren't needed
#     non_numeric_cols = df_final.select_dtypes(exclude=[np.number]).columns
#     cols_to_keep = ['Share Code', 'Daily Date', 'Scraped_Date']
#     cols_to_drop = [col for col in non_numeric_cols if col not in cols_to_keep]
#     if len(cols_to_drop) > 0:
#         df_final = df_final.drop(columns=cols_to_drop)
#         print(f"Dropped non-numeric columns: {list(cols_to_drop)}")
    
#     print(f"Final dataset shape: {df_final.shape}")
#     return df_final

# def save_processed_data(df, filename_prefix='processed_data'):
#     """Save the processed data to CSV files"""
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
#     # Save full dataset
#     full_path = processed_dir / f"{filename_prefix}_full_{timestamp}.csv"
#     df.to_csv(full_path, index=False)
#     print(f"Saved full processed data to: {full_path}")
    
#     # Save a sample for quick inspection
#     sample_path = processed_dir / f"{filename_prefix}_sample_{timestamp}.csv"
#     df.sample(min(1000, len(df))).to_csv(sample_path, index=False)
#     print(f"Saved sample data to: {sample_path}")
    
#     # Save feature list
#     feature_cols = [col for col in df.columns if col not in ['Share Code', 'Daily Date', 'Scraped_Date', 'Target', 'Target_Class', 'Future_Return', 'Future_Price']]
#     feature_list_path = processed_dir / f"{filename_prefix}_features_{timestamp}.txt"
#     with open(feature_list_path, 'w') as f:
#         f.write('\n'.join(feature_cols))
#     print(f"Saved feature list to: {feature_list_path}")

# def visualize_data(df):
#     """Create visualizations to understand the data"""
#     print("\n=== Creating Visualizations ===")
    
#     viz_dir = Path('visualizations')
#     viz_dir.mkdir(exist_ok=True)
    
#     # 1. Distribution of returns
#     if 'Future_Return' in df.columns:
#         plt.figure(figsize=(10, 6))
#         sns.histplot(df['Future_Return'].dropna(), bins=50, kde=True)
#         plt.title('Distribution of Future Returns')
#         plt.xlabel('Return (%)')
#         plt.ylabel('Frequency')
#         plt.savefig(viz_dir / 'returns_distribution.png')
#         plt.close()
    
#     # 2. Top stocks by trading volume
#     if 'Total Shares Traded' in df.columns and 'Share Code' in df.columns:
#         volume_by_stock = df.groupby('Share Code')['Total Shares Traded'].sum().sort_values(ascending=False).head(10)
#         plt.figure(figsize=(12, 6))
#         volume_by_stock.plot(kind='bar')
#         plt.title('Top 10 Stocks by Trading Volume')
#         plt.xlabel('Share Code')
#         plt.ylabel('Total Shares Traded')
#         plt.xticks(rotation=45)
#         plt.tight_layout()
#         plt.savefig(viz_dir / 'top_stocks_volume.png')
#         plt.close()
    
#     # 3. Price trends for top stocks
#     if 'Closing Price - VWAP (GH¢)' in df.columns and 'Share Code' in df.columns:
#         top_stocks = df['Share Code'].value_counts().head(5).index
#         plt.figure(figsize=(12, 8))
#         for stock in top_stocks:
#             stock_data = df[df['Share Code'] == stock].sort_values('Daily Date')
#             plt.plot(stock_data['Daily Date'], stock_data['Closing Price - VWAP (GH¢)'], label=stock)
#         plt.title('Price Trends for Top 5 Stocks')
#         plt.xlabel('Date')
#         plt.ylabel('Price (GH¢)')
#         plt.legend()
#         plt.tight_layout()
#         plt.savefig(viz_dir / 'price_trends.png')
#         plt.close()
    
#     # 4. Correlation heatmap
#     numeric_cols = df.select_dtypes(include=[np.number]).columns
#     if len(numeric_cols) > 1:
#         plt.figure(figsize=(12, 10))
#         corr_matrix = df[numeric_cols].corr()
#         sns.heatmap(corr_matrix, cmap='coolwarm', center=0)
#         plt.title('Feature Correlation Matrix')
#         plt.tight_layout()
#         plt.savefig(viz_dir / 'correlation_matrix.png')
#         plt.close()
    
#     # 5. Target class distribution
#     if 'Target_Class' in df.columns:
#         plt.figure(figsize=(10, 6))
#         sns.countplot(x='Target_Class', data=df)
#         plt.title('Target Class Distribution')
#         plt.xlabel('Target Class (1=Strong Buy, 5=Strong Sell)')
#         plt.ylabel('Count')
#         plt.savefig(viz_dir / 'target_class_distribution.png')
#         plt.close()
    
#     print(f"Visualizations saved to: {viz_dir}")

# def main():
#     """Main preprocessing pipeline"""
#     print("Starting data preprocessing pipeline...")
    
#     try:
#         # Step 1: Load data using your specific file path
#         file_path = "gse_data/gse_trading_data_full_20250823_183328.csv"
#         df = load_data(file_path)
        
#         # Step 2: Explore data
#         explore_data(df)
        
#         # Step 3: Clean data
#         df_clean = clean_data(df)
        
#         # Step 4: Feature engineering
#         df_fe = feature_engineering(df_clean)
        
#         # Step 5: Calculate lag features
#         df_lag = calculate_lag_features(df_fe)
        
#         # Step 6: Create target variable
#         df_target = create_target_variable(df_lag)
        
#         # Step 7: Encode categorical features
#         df_encoded = encode_categorical_features(df_target)
        
#         # Step 8: Finalize dataset
#         df_final = finalize_dataset(df_encoded)
        
#         # Step 9: Save processed data
#         save_processed_data(df_final)
        
#         # Step 10: Create visualizations
#         visualize_data(df_final)
        
#         print("\n=== Preprocessing Complete ===")
#         print(f"Final dataset shape: {df_final.shape}")
#         print(f"Number of features: {len([col for col in df_final.columns if col not in ['Share Code', 'Daily Date', 'Scraped_Date', 'Target', 'Target_Class']])}")
        
#     except Exception as e:
#         print(f"Error in preprocessing pipeline: {e}")
#         raise

# if __name__ == "__main__":
#     main()














import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from sklearn.feature_selection import SelectKBest, f_classif
import xgboost as xgb
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set up paths
processed_dir = Path('processed_data')
models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

def load_processed_data():
    """Load the processed data"""
    # Find the latest processed data file
    csv_files = list(processed_dir.glob('processed_data_full_*.csv'))
    if not csv_files:
        raise FileNotFoundError("No processed data files found")
    
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"Loading data from: {latest_file}")
    
    df = pd.read_csv(latest_file)
    print(f"Data loaded successfully. Shape: {df.shape}")
    return df

def clean_infinite_values(df):
    """Clean infinite and very large values"""
    print("\nCleaning infinite and very large values...")
    
    # Replace infinite values with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Check for NaN values
    nan_counts = df.isnull().sum()
    if nan_counts.sum() > 0:
        print(f"Found NaN values in columns: {nan_counts[nan_counts > 0].to_dict()}")
        
        # Fill NaN values with median for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                print(f"Filled NaN values in {col} with median: {median_val}")
    
    return df

def prepare_data(df, target_type='binary'):
    """Prepare data for modeling"""
    print(f"\nPreparing data for {target_type} classification...")
    
    # Clean infinite values first
    df = clean_infinite_values(df)
    
    # Define target variable
    if target_type == 'binary':
        target_col = 'Target'
    else:  # multiclass
        target_col = 'Target_Class'
    
    # Define feature columns (exclude non-numeric and target columns)
    exclude_cols = ['Share Code', 'Daily Date', 'Scraped_Date', 'Target', 'Target_Class', 'Future_Return', 'Future_Price']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Prepare X and y
    X = df[feature_cols]
    y = df[target_col]
    
    print(f"Features shape: {X.shape}")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    
    # Check for any remaining infinite values
    if np.isinf(X.values).any():
        print("Warning: Still found infinite values in X")
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.median())
    
    return X, y, feature_cols

def split_data(X, y, test_size=0.2, random_state=42):
    """Split data into train and test sets"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    print(f"\nData split:")
    print(f"Training set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")
    
    return X_train, X_test, y_train, y_test

def scale_features(X_train, X_test):
    """Scale features using RobustScaler (more robust to outliers)"""
    print("\nScaling features...")
    
    # Use RobustScaler instead of StandardScaler as it's more robust to outliers
    scaler = RobustScaler()
    
    # Check for infinite values before scaling
    if np.isinf(X_train.values).any():
        print("Warning: Found infinite values in training data before scaling")
        X_train = X_train.replace([np.inf, -np.inf], np.nan)
        X_train = X_train.fillna(X_train.median())
    
    if np.isinf(X_test.values).any():
        print("Warning: Found infinite values in test data before scaling")
        X_test = X_test.replace([np.inf, -np.inf], np.nan)
        X_test = X_test.fillna(X_test.median())
    
    # Fit and transform the data
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Convert back to DataFrame with original column names
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
    
    # Save the scaler
    joblib.dump(scaler, models_dir / 'scaler.pkl')
    
    return X_train_scaled, X_test_scaled

def select_features(X_train, y_train, X_test, k=20):
    """Select top k features using f_classif"""
    print(f"\nSelecting top {k} features...")
    
    selector = SelectKBest(score_func=f_classif, k=k)
    X_train_selected = selector.fit_transform(X_train, y_train)
    X_test_selected = selector.transform(X_test)
    
    # Get selected feature names
    feature_names = X_train.columns
    selected_features = feature_names[selector.get_support()].tolist()
    print(f"Selected features: {selected_features}")
    
    # Convert back to DataFrame with selected feature names
    X_train_selected = pd.DataFrame(X_train_selected, columns=selected_features, index=X_train.index)
    X_test_selected = pd.DataFrame(X_test_selected, columns=selected_features, index=X_test.index)
    
    # Save the selector
    joblib.dump(selector, models_dir / 'feature_selector.pkl')
    
    return X_train_selected, X_test_selected, selected_features

def train_models(X_train, y_train, X_test, y_test, target_type='binary'):
    """Train multiple models and evaluate them"""
    print(f"\nTraining models for {target_type} classification...")
    
    # Define models with adjusted parameters for better handling of imbalanced data
    models = {
        'Logistic Regression': LogisticRegression(
            max_iter=1000, 
            random_state=42,
            class_weight='balanced'  # Handle imbalanced classes
        ),
        'Random Forest': RandomForestClassifier(
            random_state=42,
            class_weight='balanced',
            n_estimators=100
        ),
        'Gradient Boosting': GradientBoostingClassifier(
            random_state=42,
            n_estimators=100
        ),
        'XGBoost': xgb.XGBClassifier(
            random_state=42, 
            eval_metric='logloss',
            scale_pos_weight=len(y_train[y_train==0])/len(y_train[y_train==1])  # Handle imbalance
        )
    }
    
    # For binary classification, add SVM
    if target_type == 'binary':
        models['SVM'] = SVC(
            probability=True, 
            random_state=42,
            class_weight='balanced'
        )
    
    results = {}
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        
        # Train the model
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Evaluate the model
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Store results
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'model': model
        }
        
        # Print results
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        
        # Print classification report
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
    
    return results

def hyperparameter_tuning(X_train, y_train, model_name='XGBoost', target_type='binary'):
    """Perform hyperparameter tuning for the best model"""
    print(f"\nPerforming hyperparameter tuning for {model_name}...")
    
    if model_name == 'XGBoost':
        model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5],
            'learning_rate': [0.01, 0.1],
            'subsample': [0.8, 0.9]
        }
    elif model_name == 'Random Forest':
        model = RandomForestClassifier(random_state=42, class_weight='balanced')
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [5, 10],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2]
        }
    elif model_name == 'Gradient Boosting':
        model = GradientBoostingClassifier(random_state=42)
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5],
            'learning_rate': [0.01, 0.1],
            'subsample': [0.8, 0.9]
        }
    elif model_name == 'Logistic Regression':
        model = LogisticRegression(random_state=42, class_weight='balanced', max_iter=1000)
        param_grid = {
            'C': [0.1, 1, 10],
            'penalty': ['l2']
        }
    elif model_name == 'SVM':
        model = SVC(random_state=42, class_weight='balanced', probability=True)
        param_grid = {
            'C': [0.1, 1, 10],
            'kernel': ['rbf', 'linear']
        }
    else:
        print(f"Hyperparameter tuning not implemented for {model_name}")
        return None
    
    # Perform grid search
    grid_search = GridSearchCV(
        model, param_grid, cv=3, scoring='f1_weighted', n_jobs=-1, verbose=1
    )
    grid_search.fit(X_train, y_train)
    
    # Get the best model
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    print(f"Best parameters: {best_params}")
    print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
    
    return best_model, best_params

def save_model(model, model_name, target_type='binary'):
    """Save the trained model"""
    filename = f"{model_name.lower().replace(' ', '_')}_{target_type}.pkl"
    model_path = models_dir / filename
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")

def evaluate_best_model(model, X_test, y_test, target_type='binary'):
    """Evaluate the best model on the test set"""
    print(f"\nEvaluating best model for {target_type} classification...")
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    
    # Print confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.savefig('visualizations/confusion_matrix.png')
    plt.close()
    
    # Print classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'predictions': y_pred,
        'probabilities': y_pred_proba
    }

def feature_importance(model, feature_names):
    """Plot feature importance"""
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
        indices = np.argsort(importance)[::-1]
        
        plt.figure(figsize=(12, 8))
        plt.title('Feature Importance')
        plt.bar(range(len(importance)), importance[indices], align='center')
        plt.xticks(range(len(importance)), [feature_names[i] for i in indices], rotation=90)
        plt.tight_layout()
        plt.savefig('visualizations/feature_importance.png')
        plt.close()
        
        print("\nTop 10 most important features:")
        for i in range(min(10, len(feature_names))):
            print(f"{feature_names[indices[i]]}: {importance[indices[i]]:.4f}")

def main():
    """Main modeling pipeline"""
    print("Starting stock prediction modeling pipeline...")
    
    try:
        # Step 1: Load processed data
        df = load_processed_data()
        
        # Step 2: Prepare data for binary classification
        X, y, feature_names = prepare_data(df, target_type='binary')
        
        # Step 3: Split data
        X_train, X_test, y_train, y_test = split_data(X, y)
        
        # Step 4: Scale features
        X_train_scaled, X_test_scaled = scale_features(X_train, X_test)
        
        # Step 5: Select features
        X_train_selected, X_test_selected, selected_features = select_features(
            X_train_scaled, y_train, X_test_scaled, k=20
        )
        
        # Step 6: Train models
        results = train_models(X_train_selected, y_train, X_test_selected, y_test, target_type='binary')
        
        # Step 7: Find the best model
        best_model_name = max(results, key=lambda x: results[x]['f1'])
        best_model = results[best_model_name]['model']
        print(f"\nBest model: {best_model_name} with F1 score: {results[best_model_name]['f1']:.4f}")
        
        # Step 8: Hyperparameter tuning
        tuned_model, best_params = hyperparameter_tuning(
            X_train_selected, y_train, model_name=best_model_name, target_type='binary'
        )
        
        # Step 9: Evaluate the best model
        if tuned_model:
            evaluation = evaluate_best_model(tuned_model, X_test_selected, y_test, target_type='binary')
            final_model = tuned_model
        else:
            evaluation = evaluate_best_model(best_model, X_test_selected, y_test, target_type='binary')
            final_model = best_model
        
        # Step 10: Save the best model
        save_model(final_model, best_model_name, target_type='binary')
        
        # Step 11: Plot feature importance
        feature_importance(final_model, selected_features)
        
        print("\n=== Modeling Complete ===")
        print(f"Best model: {best_model_name}")
        print(f"F1 Score: {evaluation['f1']:.4f}")
        
    except Exception as e:
        print(f"Error in modeling pipeline: {e}")
        raise

if __name__ == "__main__":
    main()