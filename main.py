import requests
from bs4 import BeautifulSoup
import csv
import re
import json
from urllib.parse import urljoin, urlparse
from collections import Counter
import os
import sys

def fetch_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_html(soup):
    return soup.prettify()

def extract_css(soup, base_url):
    css_contents = []
    
    # Extract CSS from <style> tags.
    for style in soup.find_all('style'):
        if style.string:
            css_contents.append(style.string)
    
    # Extract CSS from linked stylesheets.
    for link in soup.find_all('link', rel='stylesheet'):
        css_url = link.get('href')
        if css_url:
            full_css_url = urljoin(base_url, css_url)  # Handle relative URLs.
            css_text = fetch_content(full_css_url)
            if css_text:
                css_contents.append(css_text)
    
    return '\n'.join(css_contents)

def extract_apis(soup):
    apis = []
    scripts = soup.find_all('script')
    api_pattern = re.compile(r'https?://[^\s\'"<>]*api[^\s\'"<>]*', re.IGNORECASE)
    
    for script in scripts:
        if script.string:
            found_apis = api_pattern.findall(script.string)
            apis.extend(found_apis)
    
    # Remove duplicates.
    return list(set(apis))

def extract_metadata(soup):
    title = soup.title.string.strip() if soup.title and soup.title.string else ''
    
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag['content'].strip() if description_tag and description_tag.get('content') else ''
    
    keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    keywords = keywords_tag['content'].strip() if keywords_tag and keywords_tag.get('content') else ''
    
    return {
        'title': title,
        'description': description,
        'keywords': keywords  
    }

def extract_content(soup):
    paragraphs = soup.find_all('p')
    return ' '.join(p.get_text(separator=' ', strip=True) for p in paragraphs)

def extract_links(soup, base_url):
    internal_links = set()
    external_links = set()
    parsed_base = urlparse(base_url)
    
    for link in soup.find_all('a', href=True):
        href = link['href'].strip()
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('javascript:'):
            continue  # Skip non-HTTP links.
        
        full_url = urljoin(base_url, href)
        parsed_href = urlparse(full_url)
        
        if parsed_href.netloc == parsed_base.netloc:
            internal_links.add(full_url)
        else:
            external_links.add(full_url)
    
    return list(internal_links), list(external_links)

def analyze_structure(soup):
    structure = {
        'head': bool(soup.head),
        'body': bool(soup.body),
        'header': bool(soup.header),
        'nav': bool(soup.nav),
        'main': bool(soup.main),
        'footer': bool(soup.footer),
    }
    return structure

def find_top_keywords(content, top_n=10):
    words = re.findall(r'\w+', content.lower())
    filtered_words = [word for word in words if len(word) > 3]  # Ignore short words.
    
    word_counts = Counter(filtered_words)
    return word_counts.most_common(top_n)

def scrape_website(url):
    # 1. Fetch the webpage.
    html_content = fetch_content(url)
    if not html_content:
        print("Failed to retrieve the webpage content.")
        sys.exit(1) 
    
    soup = BeautifulSoup(html_content, 'html.parser')

    # 2. Extract HTML.
    html = extract_html(soup)

    # 3. Extract CSS.
    css = extract_css(soup, url)

    # 4. Extract any information on APIs.
    apis = extract_apis(soup)

    # 6. Extract metadata.
    metadata = extract_metadata(soup)

    # 7. Extract contents.
    content = extract_content(soup)

    # 8. Extract any links.
    internal_links, external_links = extract_links(soup, url)

    # 9. Analyse the structure of the website.
    structure = analyze_structure(soup)

    # 10. Find keywords using simple frequency analysis.
    top_keywords = find_top_keywords(content)
    metadata['keywords'] = top_keywords  # Overwrite metadata keywords with top keywords

    return {
        'html': html,
        'css': css,
        'apis': apis,
        'metadata': metadata,
        'content': content,
        'internal_links': internal_links,
        'external_links': external_links,
        'structure': structure,
        'top_keywords': top_keywords
    }

def save_to_csv(data, filename):
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Category', 'Data'])
            
            # Write HTML.
            writer.writerow(['HTML', data['html']])
            
            # Write CSS.
            writer.writerow(['CSS', data['css']])
            
            # Write APIs as JSON string.
            writer.writerow(['APIs', json.dumps(data['apis'], ensure_ascii=False)])
            
            # Write metadata.
            writer.writerow(['Title', data['metadata']['title']])
            writer.writerow(['Description', data['metadata']['description']])
            # Convert top keywords to JSON.
            writer.writerow(['Keywords', json.dumps(data['metadata']['keywords'], ensure_ascii=False)])
            
            # Write content.
            writer.writerow(['Content', data['content']])
            
            # Write internal links as JSON string.
            writer.writerow(['Internal Links', json.dumps(data['internal_links'], ensure_ascii=False)])
            
            # Write external links as JSON string.
            writer.writerow(['External Links', json.dumps(data['external_links'], ensure_ascii=False)])
            
            # Write structure as JSON string.
            writer.writerow(['Structure', json.dumps(data['structure'], ensure_ascii=False)])
            
            # Write top Keywords as JSON string.
            writer.writerow(['Top Keywords', json.dumps(data['top_keywords'], ensure_ascii=False)])
        print(f"Data successfully saved to CSV at {filename}")
    except Exception as e:
        print(f"Failed to save CSV file: {e}")

def save_to_json(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to JSON at {filename}")
    except Exception as e:
        print(f"Failed to save JSON file: {e}")

def display_analysis(data):
    print("\nKey Findings:")
    print(
        f"1. The website has {len(data['internal_links'])} internal links and {len(data['external_links'])} external links.")
    print(f"2. Top 5 keywords: {', '.join([word for word, _ in data['top_keywords'][:5]])}")
    print(f"3. The website {'has' if data['structure']['nav'] else 'does not have'} a navigation menu.")
    print(f"4. {len(data['apis'])} potential API endpoints were detected.")
    
    print("\nRecommendations:")
    print("1. Review the extracted APIs to ensure they are not exposing sensitive information.")
    print("2. Consider optimizing the content for the top keywords if they align with your website's purpose.")
    print("3. Ensure all internal links are functional to improve user experience and SEO.")
    print(
        f"4. {'Consider adding' if not data['structure']['nav'] else 'Optimize'} the navigation menu for better user experience.")
    
    print("\nActionable Plan:")
    print("1. Conduct a thorough review of the extracted data in the output file.")
    print("2. Analyze the website structure and consider improvements based on best practices.")
    print("3. Optimize content around the identified top keywords.")
    print("4. Review and potentially optimize the use of internal and external links.")
    print("5. Ensure all detected APIs are secure and necessary.")

def main():
    # Display the current working directory.
    current_dir = os.getcwd()
    print(f"Current Working Directory: {current_dir}")
    
    url = input("Enter the website URL to scrape: ").strip()
    
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url  # Default to HTTP if scheme not provided
    
    save_dir = input("Enter the directory where you want to save the output file (press Enter to use current directory): ").strip()
    if not save_dir:
        save_dir = current_dir  # Use current directory if no input received.
    else:
        # Expand user tilde (~) and make absolute path.
        save_dir = os.path.abspath(os.path.expanduser(save_dir))
        # Create directory if it doesn't exist.
        os.makedirs(save_dir, exist_ok=True)
    
    # Get user input for file format (.csv or .json)
    while True:
        file_format = input("Choose the output file format ([C]SV / [J]SON): ").strip().lower()
        if file_format in ['c', 'csv']:
            file_format = 'csv'
            break
        elif file_format in ['j', 'json']:
            file_format = 'json'
            break
        else:
            print("Invalid input. Please enter 'C' for CSV or 'J' for JSON.")
    
    default_filename = "website_analysis." + file_format
    filename = input(f"Enter the output filename (press Enter to use '{default_filename}'): ").strip()
    if not filename:
        filename = default_filename
    else:
        if not filename.lower().endswith(f".{file_format}"):
            filename += f".{file_format}"
    
    output_file = os.path.join(save_dir, filename)
    
    print(f"\nScraping {url}...")
    scraped_data = scrape_website(url)
    
    if file_format == 'csv':
        save_to_csv(scraped_data, output_file)
    else:
        save_to_json(scraped_data, output_file)
    
    display_analysis(scraped_data)

if __name__ == "__main__":
    main()
