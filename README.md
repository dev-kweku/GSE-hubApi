# GSE-DAILY DATA API



# GSE Stock Prediction Pipeline: 

## Table of Contents
1. [Introduction](#introduction)
2. [Data Scraping](#data-scraping)
3. [Data Preprocessing](#data-preprocessing)
4. [Feature Engineering](#feature-engineering)
5. [Model Building](#model-building)
6. [Model Evaluation](#model-evaluation)
7. [Deployment](#deployment)
8. [Future Improvements](#future-improvements)
9. [Conclusion](#conclusion)

---

## Introduction

This document provides a comprehensive overview of the Ghana Stock Exchange (GSE) stock prediction pipeline. The pipeline includes:
- Web scraping of historical trading data from the GSE website
- Data preprocessing and cleaning
- Feature engineering for predictive modeling
- Building and evaluating machine learning models
- Deployment considerations for production use

The goal is to predict whether to BUY, SELL, or HOLD a particular stock based on historical trading patterns and technical indicators.

### System Architecture
```
GSE Website → Scraper → Raw Data → Preprocessing → Feature Engineering → Model Building → Evaluation → Deployment
```

---

## Data Scraping

### Overview
The scraper extracts historical trading data from the GSE website (https://gse.com.gh/trading-and-data/). The data includes daily trading information for all listed stocks.

### Technology Stack
- **Language**: Python 3.8+
- **Libraries**:
  - `selenium`: For browser automation and JavaScript rendering
  - `beautifulsoup4`: For HTML parsing
  - `pandas`: For data manipulation
  - `webdriver-manager`: For automatic ChromeDriver management

### Implementation Details

#### 1. Setup
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
```

#### 2. Driver Initialization
```python
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver
```

#### 3. Scraping Process
The scraper:
1. Loads the GSE trading data page
2. Handles pagination to collect all available data
3. Extracts table data including:
   - Daily Date
   - Share Code
   - Price information (Open, High, Low, Close)
   - Volume and value traded
   - Bid/Ask prices

```python
def scrape_all_gse_data():
    base_url = "https://gse.com.gh/trading-and-data/"
    driver = setup_driver()
    all_data = []
    
    try:
        driver.get(base_url)
        time.sleep(10)  # Wait for page to load
        
        while True:
            # Parse table
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table', {'class': 'wpDataTable'})
            
            # Extract headers
            if not all_data:
                header_row = table.find('tr')
                headers_list = [th.get_text(strip=True) for th in header_row.find_all('th')]
            
            # Extract data rows
            data_rows = table.find_all('tr')[1:]
            page_data = []
            for row in data_rows:
                row_data = [td.get_text(strip=True) for td in row.find_all('td')]
                if row_data:
                    page_data.append(row_data)
            
            all_data.extend(page_data)
            
            # Check for next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, ".paginate_button.next")
                if "disabled" in next_button.get_attribute("class"):
                    break
                else:
                    next_button.click()
                    time.sleep(5)
            except:
                break
                
    finally:
        driver.quit()
    
    # Create DataFrame
    df = pd.DataFrame(all_data, columns=headers_list)
    df['Scraped_Date'] = pd.datetime.now()
    return df
```

### Data Output
The scraper produces a CSV file with the following columns:
```
Daily Date, Share Code, Year High (GH¢), Year Low (GH¢), Previous Closing Price - VWAP (GH¢), Opening Price (GH¢), Last Transaction Price (GH¢), Closing Price - VWAP (GH¢), Price Change (GH¢), Closing Bid Price (GH¢), Closing Offer Price (GH¢), Total Shares Traded, Total Value Traded (GH¢), Scraped_Date
```

### Challenges and Solutions
1. **JavaScript Rendering**: The GSE website uses JavaScript to load data tables. Solved by using Selenium for browser automation.
2. **Pagination**: Data is split across multiple pages. Solved by implementing pagination detection and navigation.
3. **Rate Limiting**: Added delays between requests to avoid being blocked.

---

## Data Preprocessing

### Overview
The preprocessing stage cleans and transforms raw scraped data into a format suitable for feature engineering and modeling.

### Technology Stack
- **Language**: Python 3.8+
- **Libraries**:
  - `pandas`: For data manipulation
  - `numpy`: For numerical operations
  - `matplotlib` & `seaborn`: For data visualization

### Implementation Details

#### 1. Loading Data
```python
def load_data(file_path):
    df = pd.read_csv(file_path)
    
    # Remove header rows if present
    if "Daily Date" in df.iloc[0].values:
        df = df.iloc[1:].reset_index(drop=True)
    
    # Convert date columns
    df['Daily Date'] = pd.to_datetime(df['Daily Date'], format='%d/%m/%Y')
    df['Scraped_Date'] = pd.to_datetime(df['Scraped_Date'])
    
    return df
```

#### 2. Data Cleaning
```python
def clean_data(df):
    # Handle missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = df[col].fillna(0)
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Handle outliers using IQR method
    for col in ['Total Shares Traded', 'Total Value Traded (GH¢)']:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df[col] = np.where(df[col] < lower_bound, lower_bound, df[col])
        df[col] = np.where(df[col] > upper_bound, upper_bound, df[col])
    
    # Ensure price columns are positive
    price_cols = ['Year High (GH¢)', 'Year Low (GH¢)', 'Previous Closing Price - VWAP (GH¢)',
                 'Opening Price (GH¢)', 'Last Transaction Price (GH¢)', 'Closing Price - VWAP (GH¢)',
                 'Price Change (GH¢)', 'Closing Bid Price (GH¢)', 'Closing Offer Price (GH¢)']
    
    for col in price_cols:
        df[col] = df[col].abs()
    
    return df
```

#### 3. Handling Infinite Values
```python
def clean_infinite_values(df):
    # Replace infinite values with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Fill NaN values with median
    nan_counts = df.isnull().sum()
    for col in nan_counts[nan_counts > 0].index:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)
    
    return df
```

### Data Quality Checks
- **Missing Values**: Checked and filled with appropriate values (0 for numeric, median for outliers)
- **Duplicates**: Removed duplicate records
- **Outliers**: Capped using IQR method
- **Data Types**: Ensured correct data types (dates as datetime, numbers as float)

### Output
Cleaned dataset ready for feature engineering with:
- 8,425 records
- 14 original columns
- Date range: 2024-07-31 to 2025-08-22
- 46 unique stock symbols

---

## Feature Engineering

### Overview
Feature engineering creates predictive features from the cleaned data, including technical indicators, time-based features, and lag variables.

### Implementation Details

#### 1. Date-Based Features
```python
def create_date_features(df):
    df['Year'] = df['Daily Date'].dt.year
    df['Month'] = df['Daily Date'].dt.month
    df['Day'] = df['Daily Date'].dt.day
    df['DayOfWeek'] = df['Daily Date'].dt.dayofweek
    df['Quarter'] = df['Daily Date'].dt.quarter
    df['IsMonthEnd'] = df['Daily Date'].dt.is_month_end.astype(int)
    df['IsMonthStart'] = df['Daily Date'].dt.is_month_start.astype(int)
    return df
```

#### 2. Price-Based Features
```python
def create_price_features(df):
    # Daily price range
    df['Daily_Price_Range'] = df['Closing Price - VWAP (GH¢)'] - df['Opening Price (GH¢)']
    
    # Price change percentage
    df['Price_Change_Pct'] = (df['Price Change (GH¢)'] / df['Previous Closing Price - VWAP (GH¢)']) * 100
    df['Price_Change_Pct'] = df['Price_Change_Pct'].fillna(0)
    
    # Volatility
    df['Volatility'] = (df['Daily_Price_Range'] / df['Opening Price (GH¢)']) * 100
    df['Volatility'] = df['Volatility'].fillna(0).replace([np.inf, -np.inf], 0)
    
    return df
```

#### 3. Volume-Based Features
```python
def create_volume_features(df):
    # Log transform of volume
    df['Log_Volume'] = np.log1p(df['Total Shares Traded'])
    
    # Average trade size
    df['Avg_Trade_Size'] = df['Total Value Traded (GH¢)'] / df['Total Shares Traded']
    df['Avg_Trade_Size'] = df['Avg_Trade_Size'].fillna(0).replace([np.inf, -np.inf], 0)
    
    return df
```

#### 4. Lag Features
```python
def create_lag_features(df, lag_days=[1, 3, 5, 10]):
    df = df.sort_values(['Share Code', 'Daily Date'])
    
    for lag in lag_days:
        # Price lags
        df[f'Price_Lag_{lag}d'] = df.groupby('Share Code')['Closing Price - VWAP (GH¢)'].shift(lag)
        
        # Volume lags
        df[f'Volume_Lag_{lag}d'] = df.groupby('Share Code')['Total Shares Traded'].shift(lag)
        
        # Value lags
        df[f'Value_Lag_{lag}d'] = df.groupby('Share Code')['Total Value Traded (GH¢)'].shift(lag)
    
    # Moving averages
    for window in [3, 5, 10]:
        df[f'Price_MA_{window}d'] = df.groupby('Share Code')['Closing Price - VWAP (GH¢)'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )
        df[f'Volume_MA_{window}d'] = df.groupby('Share Code')['Total Shares Traded'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )
    
    # Momentum features
    df['Price_Momentum_1d'] = (
        (df['Closing Price - VWAP (GH¢)'] - df['Price_Lag_1d']) / df['Price_Lag_1d']
    ) * 100
    df['Price_Momentum_1d'] = df['Price_Momentum_1d'].fillna(0).replace([np.inf, -np.inf], 0)
    
    return df
```

#### 5. Target Variable Creation
```python
def create_target_variable(df, horizon=1):
    df = df.sort_values(['Share Code', 'Daily Date'])
    
    # Calculate future returns
    df['Future_Price'] = df.groupby('Share Code')['Closing Price - VWAP (GH¢)'].shift(-horizon)
    df['Future_Return'] = (
        (df['Future_Price'] - df['Closing Price - VWAP (GH¢)']) / 
        df['Closing Price - VWAP (GH¢)']
    ) * 100
    
    # Binary target (1 if positive return, 0 otherwise)
    df['Target'] = (df['Future_Return'] > 0).astype(int)
    
    # Multi-class target (1: strong buy, 2: buy, 3: hold, 4: sell, 5: strong sell)
    for stock in df['Share Code'].unique():
        stock_data = df[df['Share Code'] == stock].copy()
        if len(stock_data) > 10:
            percentiles = stock_data['Future_Return'].quantile([0.2, 0.4, 0.6, 0.8]).values
            df.loc[df['Share Code'] == stock, 'Target_Class'] = pd.cut(
                stock_data['Future_Return'],
                bins=[-np.inf, percentiles[0], percentiles[1], percentiles[2], percentiles[3], np.inf],
                labels=[5, 4, 3, 2, 1]
            )
    
    df['Target_Class'] = df['Target_Class'].fillna(3).astype(int)
    return df
```

### Feature List
The final dataset includes 55 features:
- **Original Features**: 14 (from scraped data)
- **Date Features**: 7 (Year, Month, Day, etc.)
- **Price Features**: 3 (Price range, change %, volatility)
- **Volume Features**: 2 (Log volume, average trade size)
- **Lag Features**: 16 (Price, volume, value lags at 1, 3, 5, 10 days)
- **Moving Averages**: 6 (Price and volume moving averages)
- **Momentum Features**: 1 (Price momentum)
- **Target Variables**: 2 (Binary and multi-class)
- **Other**: 4 (Bid-ask spread, price-volume trend, etc.)

---

## Model Building

### Overview
We build machine learning models to predict stock price movements using the engineered features.

### Technology Stack
- **Language**: Python 3.8+
- **Libraries**:
  - `scikit-learn`: For machine learning algorithms
  - `xgboost`: For gradient boosting
  - `joblib`: For model persistence
  - `matplotlib` & `seaborn`: For visualization

### Implementation Details

#### 1. Data Preparation
```python
def prepare_data(df, target_type='binary'):
    # Define target variable
    if target_type == 'binary':
        target_col = 'Target'
    else:
        target_col = 'Target_Class'
    
    # Define feature columns
    exclude_cols = ['Share Code', 'Daily Date', 'Scraped_Date', 'Target', 'Target_Class', 'Future_Return', 'Future_Price']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols]
    y = df[target_col]
    
    return X, y, feature_cols
```

#### 2. Train-Test Split
```python
from sklearn.model_selection import train_test_split

def split_data(X, y, test_size=0.2, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    return X_train, X_test, y_train, y_test
```

#### 3. Feature Scaling
```python
from sklearn.preprocessing import RobustScaler

def scale_features(X_train, X_test):
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Convert back to DataFrame
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns)
    
    return X_train_scaled, X_test_scaled
```

#### 4. Feature Selection
```python
from sklearn.feature_selection import SelectKBest, f_classif

def select_features(X_train, y_train, X_test, k=20):
    selector = SelectKBest(score_func=f_classif, k=k)
    X_train_selected = selector.fit_transform(X_train, y_train)
    X_test_selected = selector.transform(X_test)
    
    # Get selected feature names
    selected_features = X_train.columns[selector.get_support()].tolist()
    
    return X_train_selected, X_test_selected, selected_features
```

#### 5. Model Training
```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import xgboost as xgb

def train_models(X_train, y_train, X_test, y_test):
    models = {
        'Logistic Regression': LogisticRegression(
            max_iter=1000, random_state=42, class_weight='balanced'
        ),
        'Random Forest': RandomForestClassifier(
            random_state=42, class_weight='balanced', n_estimators=100
        ),
        'Gradient Boosting': GradientBoostingClassifier(
            random_state=42, n_estimators=100
        ),
        'XGBoost': xgb.XGBClassifier(
            random_state=42, eval_metric='logloss',
            scale_pos_weight=len(y_train[y_train==0])/len(y_train[y_train==1])
        ),
        'SVM': SVC(
            probability=True, random_state=42, class_weight='balanced'
        )
    }
    
    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Evaluate model
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'model': model
        }
    
    return results
```

#### 6. Hyperparameter Tuning
```python
from sklearn.model_selection import GridSearchCV

def hyperparameter_tuning(X_train, y_train, model_name='Gradient Boosting'):
    if model_name == 'Gradient Boosting':
        model = GradientBoostingClassifier(random_state=42)
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 5],
            'learning_rate': [0.01, 0.1],
            'subsample': [0.8, 0.9]
        }
    
    grid_search = GridSearchCV(
        model, param_grid, cv=3, scoring='f1_weighted', n_jobs=-1, verbose=1
    )
    grid_search.fit(X_train, y_train)
    
    return grid_search.best_estimator_, grid_search.best_params_
```

### Model Performance
We evaluated five models on the binary classification task (BUY/SELL):

| Model                | Accuracy | Precision | Recall | F1 Score |
|----------------------|----------|-----------|--------|----------|
| Logistic Regression | 0.7656   | 0.9153    | 0.7656 | 0.8236   |
| Random Forest       | 0.9383   | 0.9146    | 0.9383 | 0.9196   |
| Gradient Boosting   | 0.9418   | 0.9240    | 0.9418 | 0.9227   |
| XGBoost             | 0.9027   | 0.9119    | 0.9027 | 0.9071   |
| SVM                 | 0.7395   | 0.9189    | 0.7395 | 0.8063   |

**Gradient Boosting** was selected as the best model with an F1 score of 0.9227.

### Feature Importance
The top 10 most important features for prediction:
1. Previous Closing Price - VWAP (GH¢)
2. Opening Price (GH¢)
3. Last Transaction Price (GH¢)
4. Closing Price - VWAP (GH¢)
5. Price_Lag_1d
6. Volume_Lag_1d
7. Price_MA_3d
8. Volume_MA_3d
9. Price_MA_5d
10. Price_Momentum_1d

---

## Model Evaluation

### Evaluation Metrics
We used multiple metrics to evaluate model performance:
- **Accuracy**: Overall correctness of predictions
- **Precision**: Ability to avoid false positives
- **Recall**: Ability to detect all positive instances
- **F1 Score**: Harmonic mean of precision and recall

### Confusion Matrix
For the Gradient Boosting model:
```
Actual/Predicted | SELL | BUY
----------------|------|-----
SELL           | 1569 | 15
BUY            | 90   | 11
```

### Classification Report
```
              precision    recall  f1-score   support
           0       0.95      0.99      0.97      1584
           1       0.58      0.11      0.18       101
    accuracy                           0.94      1685
   macro avg       0.76      0.55      0.58      1685
weighted avg       0.92      0.94      0.92      1685
```

### Challenges and Observations
1. **Class Imbalance**: The dataset is highly imbalanced (94% SELL, 6% BUY signals)
2. **BUY Signal Detection**: The model struggles to identify BUY signals (low recall for class 1)
3. **Feature Importance**: Price-related features dominate the predictions

---

## Deployment

### Overview
The model can be deployed as a web service or integrated into a larger trading platform.

### Technology Stack
- **Backend**: Flask/FastAPI for API
- **Frontend**: React for web interface
- **Containerization**: Docker for consistent deployment
- **Cloud**: AWS/GCP for scalable hosting

### API Implementation
```python
from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

# Load model and preprocessing objects
model = joblib.load('models/gradient_boosting_binary.pkl')
scaler = joblib.load('models/scaler.pkl')
feature_selector = joblib.load('models/feature_selector.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    
    # Convert to DataFrame
    df = pd.DataFrame([data])
    
    # Preprocess
    df_scaled = scaler.transform(df)
    df_selected = feature_selector.transform(df_scaled)
    
    # Predict
    prediction = model.predict(df_selected)[0]
    probability = model.predict_proba(df_selected)[0][1]
    
    return jsonify({
        'prediction': int(prediction),
        'confidence': float(probability),
        'recommendation': 'BUY' if prediction == 1 else 'SELL'
    })

if __name__ == '__main__':
    app.run(debug=True)
```

### Deployment Steps
1. **Containerize the Application**:
   ```dockerfile
   FROM python:3.8-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 5000
   CMD ["python", "app.py"]
   ```

2. **Cloud Deployment**:
   - Build Docker image
   - Push to container registry
   - Deploy to cloud service (AWS ECS, Google Cloud Run)

3. **Monitoring**:
   - Set up logging and monitoring
   - Implement health checks
   - Track model performance over time

### Security Considerations
- **Authentication**: Implement JWT-based authentication
- **Rate Limiting**: Prevent abuse of the API
- **Data Encryption**: Encrypt sensitive data in transit and at rest
- **Input Validation**: Validate all input data

---

## Future Improvements

### Model Enhancements
1. **Alternative Algorithms**: Experiment with LSTM networks for time series prediction
2. **Ensemble Methods**: Combine multiple models for better performance
3. **Feature Engineering**: Add more technical indicators (RSI, MACD, Bollinger Bands)
4. **Sentiment Analysis**: Incorporate news sentiment scores

### Data Improvements
1. **Additional Data Sources**:
   - Macroeconomic indicators
   - Company financial statements
   - Social media sentiment
   - News articles

2. **Real-time Data**:
   - Implement real-time data streaming
   - Update predictions intraday

### Platform Features
1. **User Interface**:
   - Interactive dashboard
   - Portfolio tracking
   - Alert system
   - Backtesting capabilities

2. **Advanced Analytics**:
   - Risk assessment tools
   - Portfolio optimization
   - What-if analysis

### Business Expansion
1. **Market Expansion**: Extend to other African stock markets
2. **Institutional Features**: API access for enterprise clients
3. **Mobile Application**: Native iOS/Android apps

---

## Conclusion

This documentation outlines the complete pipeline from scraping GSE data to building a predictive stock trading model. The Gradient Boosting model achieved an F1 score of 0.9227 in predicting BUY/SELL signals, with price-related features being the most important predictors.

Key achievements:
- Successfully scraped and processed 8,425 historical records
- Engineered 55 predictive features
- Built and evaluated multiple machine learning models
- Identified Gradient Boosting as the best performing algorithm
- Provided a deployment roadmap for production use

The model shows promise for assisting investors in making informed trading decisions on the Ghana Stock Exchange. Future work should focus on improving BUY signal detection and expanding the feature set with additional data sources.