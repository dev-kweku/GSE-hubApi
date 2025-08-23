import time
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
import os
import re

def setup_driver():
    """Set up the Chrome WebDriver with robust error handling"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("Successfully set up ChromeDriver using webdriver-manager")
            return driver
        except Exception as e:
            print(f"webdriver-manager failed: {e}")
            raise
    except Exception as e:
        print(f"Error setting up ChromeDriver: {e}")
        raise

def clean_numeric_value(value_str):
    """Convert numeric strings with commas to float"""
    if pd.isna(value_str) or value_str == '':
        return 0.0
    
    # Remove commas and any non-numeric characters except decimal point
    cleaned = re.sub(r'[^\d.]', '', str(value_str))
    
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def scrape_all_gse_data():
    base_url = "https://gse.com.gh/trading-and-data/"
    driver = None
    all_data = []
    page_count = 0
    total_records = 0
    records_per_page = 26  # Based on our observation
    
    try:
        driver = setup_driver()
        print(f"Successfully initialized WebDriver. Version: {driver.capabilities['browserVersion']}")
        
        # Load the page
        print(f"Loading page: {base_url}")
        driver.get(base_url)
        time.sleep(10)  # Initial wait for page load
        
        # Find the table using the correct class
        try:
            print("Looking for the data table...")
            table_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.wpDataTable"))
            )
            print("Found the data table!")
        except TimeoutException:
            print("Could not find the data table. Saving debug info...")
            driver.save_screenshot("gse_no_table.png")
            with open("gse_no_table.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return None
        
        # Get total records from pagination info - try multiple selectors
        pagination_info_selectors = [
            ".dataTables_info",
            ".wpDataTable-info",
            ".table-info",
            ".pagination-info"
        ]
        
        for selector in pagination_info_selectors:
            try:
                pagination_info = driver.find_element(By.CSS_SELECTOR, selector).text
                print(f"Pagination info: {pagination_info}")
                
                # Extract total records from pagination info
                match = re.search(r'of (\d+) entries', pagination_info)
                if match:
                    total_records = int(match.group(1))
                    print(f"Total records available: {total_records}")
                    
                    # Calculate expected number of pages
                    expected_pages = (total_records + records_per_page - 1) // records_per_page
                    print(f"Expected number of pages: {expected_pages}")
                    break
            except NoSuchElementException:
                continue
        
        # If we couldn't get pagination info, try to get it from the page source
        if total_records == 0:
            try:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                # Look for any element that might contain pagination info
                pagination_elements = soup.find_all(class_=re.compile(r'(info|pagination)'))
                for elem in pagination_elements:
                    text = elem.get_text(strip=True)
                    match = re.search(r'of (\d+) entries', text)
                    if match:
                        total_records = int(match.group(1))
                        print(f"Found total records in page source: {total_records}")
                        expected_pages = (total_records + records_per_page - 1) // records_per_page
                        print(f"Expected number of pages: {expected_pages}")
                        break
            except Exception as e:
                print(f"Error getting pagination info from page source: {e}")
        
        # Now proceed with pagination
        consecutive_empty_pages = 0
        max_empty_pages = 3  # Stop after this many consecutive empty pages
        
        while consecutive_empty_pages < max_empty_pages:
            page_count += 1
            print(f"\nScraping page {page_count}...")
            
            try:
                # Get page source and parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                table = soup.find('table', {'class': 'wpDataTable'})
                
                if not table:
                    print("Table not found in parsed HTML. Saving debug info...")
                    driver.save_screenshot(f"gse_no_table_page_{page_count}.png")
                    with open(f"gse_no_table_page_{page_count}.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    consecutive_empty_pages += 1
                    continue
                
                # Extract headers (only from first page)
                if page_count == 1:
                    header_row = table.find('tr')
                    if not header_row:
                        print("No header row found. Skipping...")
                        break
                    headers_list = [th.get_text(strip=True) for th in header_row.find_all('th')]
                    print(f"Headers found: {headers_list}")
                    data_rows = table.find_all('tr')[1:]  # Skip header row
                else:
                    data_rows = table.find_all('tr')[1:]  # Skip header row on subsequent pages
                
                # Extract data from rows
                page_data = []
                for row in data_rows:
                    row_data = [td.get_text(strip=True) for td in row.find_all('td')]
                    if row_data and len(row_data) > 1:  # Only add non-empty rows with data
                        page_data.append(row_data)
                
                if not page_data:
                    print("No data rows found on this page.")
                    consecutive_empty_pages += 1
                else:
                    consecutive_empty_pages = 0  # Reset counter if we found data
                    all_data.extend(page_data)
                    print(f"Scraped {len(page_data)} records from page {page_count}")
                    print(f"Total records collected so far: {len(all_data)}")
                
                # Check if we've collected all records
                if total_records > 0 and len(all_data) >= total_records:
                    print("All records have been scraped. Ending pagination.")
                    break
                
                # Try to find and click the "Next" button - try multiple selectors
                try:
                    print("Looking for next page button...")
                    
                    # Try multiple selectors for next button
                    next_selectors = [
                        (By.CSS_SELECTOR, ".paginate_button.next"),
                        (By.ID, "table_1_next"),
                        (By.XPATH, "//a[contains(@class, 'next') and contains(@class, 'paginate_button')]"),
                        (By.XPATH, "//a[contains(text(), 'Next')]"),
                        (By.XPATH, "//li[contains(@class, 'next')]/a"),
                        (By.XPATH, "//span[contains(@class, 'next')]/parent::a")
                    ]
                    
                    next_button = None
                    for selector_type, selector in next_selectors:
                        try:
                            next_button = driver.find_element(selector_type, selector)
                            # Check if the button is disabled
                            if "disabled" in next_button.get_attribute("class"):
                                print("Next button is disabled. Assuming this is the last page.")
                                next_button = None
                                break
                            else:
                                print(f"Found next button using selector: {selector}")
                                break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue
                    
                    if next_button:
                        print("Attempting to click next button...")
                        
                        # Try multiple methods to click the button
                        click_methods = [
                            lambda: next_button.click(),  # Normal click
                            lambda: driver.execute_script("arguments[0].click();", next_button),  # JavaScript click
                            lambda: driver.execute_script("var evt = document.createEvent('MouseEvents');" +
                                                          "evt.initMouseEvent('click',true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);" +
                                                          "arguments[0].dispatchEvent(evt);", next_button)  # Dispatch event
                        ]
                        
                        click_success = False
                        for i, method in enumerate(click_methods):
                            try:
                                print(f"Trying click method {i+1}...")
                                method()
                                click_success = True
                                print("Successfully clicked next button.")
                                break
                            except Exception as e:
                                print(f"Click method {i+1} failed: {e}")
                        
                        if click_success:
                            print("Waiting for page to load...")
                            time.sleep(5)  # Wait for next page to load
                        else:
                            print("All click methods failed. Assuming this is the last page.")
                            break
                    else:
                        print("No next button found. Assuming this is the last page.")
                        break
                        
                except Exception as e:
                    print(f"Error with pagination: {e}")
                    print("Assuming this is the last page.")
                    break
            
            except Exception as e:
                print(f"Error processing page {page_count}: {e}")
                driver.save_screenshot(f"gse_error_page_{page_count}.png")
                with open(f"gse_error_page_{page_count}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                consecutive_empty_pages += 1
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        if driver:
            driver.save_screenshot("gse_error.png")
            with open("gse_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")
    
    # Create DataFrame if we have data
    if all_data:
        df = pd.DataFrame(all_data, columns=headers_list)
        df['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Clean numeric columns
        numeric_columns = [
            'Year High (GH¢)', 'Year Low (GH¢)', 'Previous Closing Price - VWAP (GH¢)',
            'Opening Price (GH¢)', 'Last Transaction Price (GH¢)', 'Closing Price - VWAP (GH¢)',
            'Price Change (GH¢)', 'Closing Bid Price (GH¢)', 'Closing Offer Price (GH¢)',
            'Total Shares Traded', 'Total Value Traded (GH¢)'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric_value)
        
        # Convert Daily Date to datetime - skip the header row
        if 'Daily Date' in df.columns:
            try:
                # Skip the first row if it's the header
                if df['Daily Date'].iloc[0] == 'Daily Date':
                    df = df.iloc[1:].reset_index(drop=True)
                
                df['Daily Date'] = pd.to_datetime(df['Daily Date'], format='%d/%m/%Y')
            except Exception as e:
                print(f"Error converting date format: {e}")
        
        print(f"\nTotal records scraped: {len(df)}")
        print(f"Expected total records: {total_records}")
        print(f"Completion percentage: {len(df)/total_records*100:.2f}%" if total_records > 0 else "")
        return df
    else:
        print("No data was scraped.")
        return None

def save_to_csv(dataframe, filename=None):
    if dataframe is None:
        print("No data to save")
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gse_trading_data_full_{timestamp}.csv"
    
    try:
        dataframe.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def save_to_excel(dataframe, filename=None):
    if dataframe is None:
        print("No data to save")
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gse_trading_data_full_{timestamp}.xlsx"
    
    try:
        dataframe.to_excel(filename, index=False)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def save_to_json(dataframe, filename=None):
    if dataframe is None:
        print("No data to save")
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gse_trading_data_full_{timestamp}.json"
    
    try:
        dataframe.to_json(filename, orient='records', date_format='iso')
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def analyze_data(dataframe):
    """Perform basic analysis on the scraped data"""
    if dataframe is None:
        print("No data to analyze")
        return
    
    print("\n=== Data Analysis ===")
    
    # Basic statistics
    print("\nBasic Statistics:")
    print(dataframe.describe())
    
    # Share codes
    if 'Share Code' in dataframe.columns:
        print("\nUnique Share Codes:")
        print(dataframe['Share Code'].unique())
        print(f"\nNumber of unique stocks: {dataframe['Share Code'].nunique()}")
    
    # Date range
    if 'Daily Date' in dataframe.columns:
        print(f"\nDate Range: {dataframe['Daily Date'].min()} to {dataframe['Daily Date'].max()}")
    
    # Most active stocks by volume
    if 'Total Shares Traded' in dataframe.columns and 'Share Code' in dataframe.columns:
        print("\nMost Active Stocks by Volume:")
        volume_by_stock = dataframe.groupby('Share Code')['Total Shares Traded'].sum().sort_values(ascending=False)
        print(volume_by_stock.head(10))
    
    # Top gainers and losers
    if 'Price Change (GH¢)' in dataframe.columns and 'Share Code' in dataframe.columns:
        # Get the latest data for each stock
        latest_data = dataframe.groupby('Share Code').last()
        
        print("\nTop Gainers:")
        gainers = latest_data[latest_data['Price Change (GH¢)'] > 0].sort_values('Price Change (GH¢)', ascending=False)
        print(gainers[['Price Change (GH¢)']].head(5))
        
        print("\nTop Losers:")
        losers = latest_data[latest_data['Price Change (GH¢)'] < 0].sort_values('Price Change (GH¢)')
        print(losers[['Price Change (GH¢)']].head(5))

# Main execution
if __name__ == "__main__":
    print("Starting enhanced GSE trading data scraper with complete data extraction...")
    try:
        gse_data = scrape_all_gse_data()
        
        if gse_data is not None:
            print("\nSample of scraped data:")
            print(gse_data.head())
            
            # Save to multiple formats
            save_to_csv(gse_data)
            save_to_excel(gse_data)
            save_to_json(gse_data)
            
            # Analyze the data
            analyze_data(gse_data)
            
            # Print summary statistics
            print("\nData Summary:")
            print(f"Total records: {len(gse_data)}")
            print(f"Columns: {', '.join(gse_data.columns)}")
        else:
            print("Failed to retrieve data")
    except Exception as e:
        print(f"Fatal error: {e}")
        print("\nDebug files may have been saved for inspection.")