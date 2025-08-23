# import time
# from datetime import datetime
# import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
# from bs4 import BeautifulSoup
# import os
# import re

# def setup_driver():
#     """Set up the Chrome WebDriver with robust error handling"""
#     try:
#         options = webdriver.ChromeOptions()
#         options.add_argument("--headless")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--disable-dev-shm-usage")
#         options.add_argument("--disable-gpu")
#         options.add_argument("--window-size=1920,1080")
#         options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
#         options.add_argument("--log-level=3")  # Suppress console logs
#         options.add_argument("--disable-extensions")
#         options.add_argument("--disable-infobars")
        
#         try:
#             from webdriver_manager.chrome import ChromeDriverManager
#             service = Service(ChromeDriverManager().install())
#             driver = webdriver.Chrome(service=service, options=options)
#             print("Successfully set up ChromeDriver using webdriver-manager")
#             return driver
#         except Exception as e:
#             print(f"webdriver-manager failed: {e}")
#             raise
#     except Exception as e:
#         print(f"Error setting up ChromeDriver: {e}")
#         raise

# def analyze_page_content(driver, page_num=1):
#     """Analyze the page content to understand what's loaded"""
#     print(f"\n=== Analyzing Page {page_num} Content ===")
    
#     # Check for iframes
#     iframes = driver.find_elements(By.TAG_NAME, "iframe")
#     print(f"Found {len(iframes)} iframe(s) on the page")
#     for i, iframe in enumerate(iframes):
#         try:
#             print(f"  Iframe {i+1}: {iframe.get_attribute('src')}")
#         except:
#             print(f"  Iframe {i+1}: [Could not get src attribute]")
    
#     # Check for tables
#     tables = driver.find_elements(By.TAG_NAME, "table")
#     print(f"Found {len(tables)} table(s) on the page")
#     for i, table in enumerate(tables):
#         try:
#             classes = table.get_attribute("class")
#             print(f"  Table {i+1}: classes='{classes}'")
#         except:
#             print(f"  Table {i+1}: [Could not get class attribute]")
    
#     # Check for specific elements that might indicate data loading
#     elements_to_check = [
#         ("trading data", ["h1", "h2", "h3"]),
#         ("market data", ["div", "span"]),
#         ("stock", ["div", "span", "td"]),
#         ("price", ["div", "span", "td"]),
#         ("tablepress", ["div", "table"]),
#         ("data-table", ["div", "table"])
#     ]
    
#     for text, tags in elements_to_check:
#         for tag in tags:
#             elements = driver.find_elements(By.XPATH, f"//{tag}[contains(text(), '{text}')]")
#             if elements:
#                 print(f"Found {len(elements)} {tag}(s) containing '{text}'")
#                 for elem in elements[:3]:  # Show first 3 matches
#                     print(f"  Text: {elem.text[:100]}...")
    
#     # Check page title
#     try:
#         title = driver.title
#         print(f"Page title: {title}")
#     except:
#         print("Could not get page title")
    
#     # Check URL
#     try:
#         current_url = driver.current_url
#         print(f"Current URL: {current_url}")
#     except:
#         print("Could not get current URL")
    
#     print("=== End Analysis ===\n")

# def scrape_all_gse_data():
#     base_url = "https://gse.com.gh/trading-and-data/"
#     driver = None
#     all_data = []
#     page_count = 0
#     max_pages = 20  # Safety limit
    
#     try:
#         driver = setup_driver()
#         print(f"Successfully initialized WebDriver. Version: {driver.capabilities['browserVersion']}")
        
#         # Load the page
#         print(f"Loading page: {base_url}")
#         driver.get(base_url)
#         time.sleep(10)  # Increased initial wait for page load
        
#         # Analyze initial page content
#         analyze_page_content(driver)
        
#         # Try multiple approaches to find the data
#         approaches = [
#             ("tablepress table", By.CLASS_NAME, "tablepress"),
#             ("any table", By.TAG_NAME, "table"),
#             ("data container", By.XPATH, "//*[contains(@class, 'data')]"),
#             ("trading data section", By.XPATH, "//*[contains(text(), 'Trading Data')]"),
#             ("market data section", By.XPATH, "//*[contains(text(), 'Market Data')]")
#         ]
        
#         table_found = False
#         for approach_name, by_type, selector in approaches:
#             try:
#                 print(f"\nTrying approach: {approach_name}")
                
#                 if by_type == By.CLASS_NAME:
#                     element = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((by_type, selector))
#                     )
#                 else:
#                     element = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((by_type, selector))
#                     )
                
#                 print(f"Found element using {approach_name}")
                
#                 # If we found a table, try to extract data
#                 if "table" in approach_name.lower():
#                     table_found = True
#                     break
#                 else:
#                     # Look for a table near this element
#                     try:
#                         parent = element.find_element(By.XPATH, "./ancestor::div[1]")
#                         table = parent.find_element(By.TAG_NAME, "table")
#                         print("Found table near the element")
#                         table_found = True
#                         break
#                     except:
#                         print("No table found near the element")
#                         continue
                        
#             except TimeoutException:
#                 print(f"Timeout using approach: {approach_name}")
#             except Exception as e:
#                 print(f"Error using approach {approach_name}: {e}")
        
#         if not table_found:
#             print("Could not find any table using all approaches. Saving debug info...")
#             driver.save_screenshot("gse_no_table.png")
#             with open("gse_no_table.html", "w", encoding="utf-8") as f:
#                 f.write(driver.page_source)
#             return None
        
#         # Now proceed with pagination
#         while page_count < max_pages:
#             page_count += 1
#             print(f"\nScraping page {page_count}...")
            
#             try:
#                 # Get page source and parse with BeautifulSoup
#                 soup = BeautifulSoup(driver.page_source, 'html.parser')
#                 table = soup.find('table', {'class': 'tablepress'})
                
#                 if not table:
#                     # Try to find any table
#                     table = soup.find('table')
#                     if not table:
#                         print("No tables found on page. Saving debug info...")
#                         driver.save_screenshot(f"gse_no_table_page_{page_count}.png")
#                         with open(f"gse_no_table_page_{page_count}.html", "w", encoding="utf-8") as f:
#                             f.write(driver.page_source)
#                         break
                
#                 # Extract headers (only from first page)
#                 if page_count == 1:
#                     header_row = table.find('tr')
#                     if not header_row:
#                         print("No header row found. Skipping...")
#                         break
#                     headers_list = [th.get_text(strip=True) for th in header_row.find_all('th')]
#                     print(f"Headers found: {headers_list}")
#                     data_rows = table.find_all('tr')[1:]  # Skip header row
#                 else:
#                     data_rows = table.find_all('tr')[1:]  # Skip header row on subsequent pages
                
#                 # Extract data from rows
#                 page_data = []
#                 for row in data_rows:
#                     row_data = [td.get_text(strip=True) for td in row.find_all('td')]
#                     if row_data:  # Only add non-empty rows
#                         page_data.append(row_data)
                
#                 if not page_data:
#                     print("No data rows found on this page.")
#                 else:
#                     all_data.extend(page_data)
#                     print(f"Scraped {len(page_data)} records from page {page_count}")
                
#                 # Try to find and click the "Next" button
#                 try:
#                     print("Looking for next page button...")
                    
#                     # Try multiple selectors for next button
#                     next_selectors = [
#                         (By.CSS_SELECTOR, ".tablepress-nav a.next"),
#                         (By.XPATH, "//a[contains(text(), 'Next')]"),
#                         (By.XPATH, "//a[contains(@class, 'next')]"),
#                         (By.XPATH, "//a[contains(@href, 'page')]")
#                     ]
                    
#                     next_button = None
#                     for selector_type, selector in next_selectors:
#                         try:
#                             next_button = driver.find_element(selector_type, selector)
#                             if "disabled" not in next_button.get_attribute("class"):
#                                 break
#                             else:
#                                 next_button = None
#                         except:
#                             continue
                    
#                     if next_button:
#                         print("Found next button. Clicking...")
#                         driver.execute_script("arguments[0].scrollIntoView();", next_button)
#                         time.sleep(1)
#                         next_button.click()
#                         print("Clicked next button. Waiting for page to load...")
#                         time.sleep(5)  # Wait for next page to load
#                     else:
#                         print("No next button found or it's disabled. Assuming this is the last page.")
#                         break
                        
#                 except Exception as e:
#                     print(f"Could not find or click next button: {e}")
#                     print("Assuming this is the last page.")
#                     break
            
#             except Exception as e:
#                 print(f"Error processing page {page_count}: {e}")
#                 driver.save_screenshot(f"gse_error_page_{page_count}.png")
#                 with open(f"gse_error_page_{page_count}.html", "w", encoding="utf-8") as f:
#                     f.write(driver.page_source)
#                 break
        
#     except Exception as e:
#         print(f"Error during scraping: {e}")
#         if driver:
#             driver.save_screenshot("gse_error.png")
#             with open("gse_error.html", "w", encoding="utf-8") as f:
#                 f.write(driver.page_source)
#     finally:
#         if driver:
#             driver.quit()
#             print("WebDriver closed.")
    
#     # Create DataFrame if we have data
#     if all_data:
#         df = pd.DataFrame(all_data, columns=headers_list)
#         df['Scraped_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         print(f"\nTotal records scraped: {len(df)}")
#         return df
#     else:
#         print("No data was scraped.")
#         return None

# def save_to_csv(dataframe, filename=None):
#     if dataframe is None:
#         print("No data to save")
#         return
    
#     if filename is None:
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"gse_trading_data_full_{timestamp}.csv"
    
#     try:
#         dataframe.to_csv(filename, index=False)
#         print(f"Data saved to {filename}")
#     except Exception as e:
#         print(f"Error saving data: {e}")

# # Main execution
# if __name__ == "__main__":
#     print("Starting enhanced GSE trading data scraper...")
#     try:
#         gse_data = scrape_all_gse_data()
        
#         if gse_data is not None:
#             print("\nSample of scraped data:")
#             print(gse_data.head())
            
#             # Save to CSV
#             save_to_csv(gse_data)
            
#             # Print summary statistics
#             print("\nData Summary:")
#             print(f"Total records: {len(gse_data)}")
#             print(f"Columns: {', '.join(gse_data.columns)}")
#         else:
#             print("Failed to retrieve data")
#             print("\nPlease check the debug files:")
#             print("- gse_no_table.png: Screenshot when no table was found")
#             print("- gse_no_table.html: HTML source when no table was found")
#             print("- gse_error.png: Screenshot if an error occurred")
#             print("- gse_error.html: HTML source if an error occurred")
#     except Exception as e:
#         print(f"Fatal error: {e}")
#         print("\nDebug files have been saved for inspection.")







import time
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

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
        options.add_argument("--log-level=3")  # Suppress console logs
        
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

def scrape_all_gse_data():
    base_url = "https://gse.com.gh/trading-and-data/"
    driver = None
    all_data = []
    page_count = 0
    max_pages = 20  # Safety limit
    
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
        
        # Now proceed with pagination
        while page_count < max_pages:
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
                    break
                
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
                    if row_data:  # Only add non-empty rows
                        page_data.append(row_data)
                
                if not page_data:
                    print("No data rows found on this page.")
                else:
                    all_data.extend(page_data)
                    print(f"Scraped {len(page_data)} records from page {page_count}")
                
                # Try to find and click the "Next" button
                try:
                    print("Looking for next page button...")
                    
                    # Try multiple selectors for next button
                    next_selectors = [
                        (By.CSS_SELECTOR, ".paginate_button.next"),
                        (By.ID, "table_1_next"),
                        (By.XPATH, "//a[contains(@class, 'next') and contains(@class, 'paginate_button')]"),
                        (By.XPATH, "//a[contains(text(), 'Next')]")
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
                        except NoSuchElementException:
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
                break
        
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
        print(f"\nTotal records scraped: {len(df)}")
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

# Main execution
if __name__ == "__main__":
    print("Starting enhanced GSE trading data scraper with improved pagination...")
    try:
        gse_data = scrape_all_gse_data()
        
        if gse_data is not None:
            print("\nSample of scraped data:")
            print(gse_data.head())
            
            # Save to CSV
            save_to_csv(gse_data)
            
            # Also save to Excel
            save_to_excel(gse_data)
            
            # Print summary statistics
            print("\nData Summary:")
            print(f"Total records: {len(gse_data)}")
            print(f"Columns: {', '.join(gse_data.columns)}")
        else:
            print("Failed to retrieve data")
    except Exception as e:
        print(f"Fatal error: {e}")
        print("\nDebug files may have been saved for inspection.")