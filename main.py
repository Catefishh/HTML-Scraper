import os
import sys
import csv
import json
import re
from collections import Counter
from urllib.parse import urljoin, urlparse
from typing import Tuple, List, Dict, Any, Set

import requests
from bs4 import BeautifulSoup

# Step 1: Fetch content from a given URL.
def fetch_content(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

# Step 2: Extract HTML and prettify using Beautifulsoup.
def extract_html(soup: BeautifulSoup) -> str:
    return soup.prettify()

# Step 3: Extract CSS from <style> and <link rel="stylesheet"> tags.
def extract_css(soup: BeautifulSoup, base_url: str) -> str:
    css_contents = []

    # Extract inline CSS from <style> tags.
    css_contents.extend(style.string for style in soup.find_all('style') if style.string)

    # Extract CSS from external linked stylesheets.
    for link in soup.find_all('link', rel='stylesheet'):
        css_url = link.get('href')
        if css_url:
            full_css_url = urljoin(base_url, css_url)  # Handle relative URLs.
            css_text = fetch_content(full_css_url)
            if css_text:
                css_contents.append(css_text)

    return '\n'.join(css_contents)

# Step 4: Identifying and extracting API endpoints.
def extract_apis(soup: BeautifulSoup) -> List[str]:
    api_pattern = re.compile(r'https?://[^\s\'"<>]*api[^\s\'"<>]*', re.IGNORECASE)
    scripts = (script.string for script in soup.find_all('script') if script.string)
    # Use a set to avoid duplicate API endpoints.
    apis = {match for script_content in scripts for match in api_pattern.findall(script_content)}
    return list(apis)

# Step 5: Extracting metadata from the webpage.
def extract_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    def meta_content(name: str) -> str:
        tag = soup.find('meta', attrs={'name': name})
        return tag['content'].strip() if tag and tag.get('content') else ''

    title = soup.title.string.strip() if soup.title and soup.title.string else ''
    return {
        'title': title,
        'description': meta_content('description'),
        'keywords': meta_content('keywords')
    }

# Step 6: Extracting text content from paragraph tags.
def extract_content(soup: BeautifulSoup) -> str:
    paragraphs = soup.find_all('p')
    return ' '.join(p.get_text(separator=' ', strip=True) for p in paragraphs)

# Step 7: Extract all internal and external links from the webpage.
def extract_links(soup: BeautifulSoup, base_url: str) -> Tuple[List[str], List[str]]:
    internal_links: Set[str] = set()
    external_links: Set[str] = set()
    parsed_base = urlparse(base_url)

    for link in soup.find_all('a', href=True):
        href = link['href'].strip()
        # Skip any non-navigational links.
        if any(href.startswith(prefix) for prefix in ('#', 'mailto:', 'javascript:')):
            continue

        full_url = urljoin(base_url, href)
        parsed_href = urlparse(full_url)
        # Categorize as internal or external links based on the domain.
        if parsed_href.netloc == parsed_base.netloc:
            internal_links.add(full_url)
        else:
            external_links.add(full_url)

    return list(internal_links), list(external_links)

# Step 8: Analyse the HTML structure of the page.
def analyze_structure(soup: BeautifulSoup) -> Dict[str, bool]:
    tags = ['head', 'body', 'header', 'nav', 'main', 'footer']
    return {tag: bool(soup.find(tag)) for tag in tags}

# Step 9: Find the most frequent keywords in the text content.
def find_top_keywords(content: str, top_n: int = 10) -> List[Tuple[str, int]]:
    words = re.findall(r'\w+', content.lower())
    filtered_words = [word for word in words if len(word) > 3]  # Exclude very short words.
    return Counter(filtered_words).most_common(top_n)

# Step 10: Website scraping process.
def scrape_website(url: str) -> Dict[str, Any]:
    html_content = fetch_content(url)
    if not html_content:
        print("Failed to retrieve the webpage content.")
        sys.exit(1)

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract various data from the page.
    html = extract_html(soup)
    css = extract_css(soup, url)
    apis = extract_apis(soup)
    metadata = extract_metadata(soup)
    content = extract_content(soup)
    internal_links, external_links = extract_links(soup, url)
    structure = analyze_structure(soup)
    top_keywords = find_top_keywords(content)

    # Overwrite metadata keywords with top keywords for analysis context.
    metadata['keywords'] = str(top_keywords)

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

# Step 11: Save the scraped data to either a CSV or JSON file for analysis.
def save_to_csv(data: Dict[str, Any], filename: str) -> None:
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Category', 'Data'])

            writer.writerow(['HTML', data['html']])
            writer.writerow(['CSS', data['css']])
            writer.writerow(['APIs', json.dumps(data['apis'], ensure_ascii=False)])
            writer.writerow(['Title', data['metadata']['title']])
            writer.writerow(['Description', data['metadata']['description']])
            writer.writerow(['Keywords', data['metadata']['keywords']])
            writer.writerow(['Content', data['content']])
            writer.writerow(['Internal Links', json.dumps(data['internal_links'], ensure_ascii=False)])
            writer.writerow(['External Links', json.dumps(data['external_links'], ensure_ascii=False)])
            writer.writerow(['Structure', json.dumps(data['structure'], ensure_ascii=False)])
            writer.writerow(['Top Keywords', json.dumps(data['top_keywords'], ensure_ascii=False)])
        print(f"Data successfully saved to CSV at {filename}")
    except Exception as e:
        print(f"Failed to save CSV file: {e}")

def save_to_json(data: Dict[str, Any], filename: str) -> None:
    try:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to JSON at {filename}")
    except Exception as e:
        print(f"Failed to save JSON file: {e}")

# Step 12: Display key findings, recommendations and actionable plans to the user.
def display_analysis(data: Dict[str, Any]) -> None:
    print("\nKey Findings:")
    print(f"1. The website has {len(data['internal_links'])} internal links and {len(data['external_links'])} external links.")
    top_five = ', '.join(word for word, _ in data['top_keywords'][:5])
    print(f"2. The top 5 keywords are: {top_five}")
    nav_status = 'has' if data['structure'].get('nav') else 'does not have'
    print(f"3. The website {nav_status} a navigation menu.")
    print(f"4. {len(data['apis'])} potential API endpoints were detected.")

    print("\nRecommendations:")
    print("1. Review the extracted APIs to ensure they are not exposing sensitive information.")
    print("2. Consider optimizing the content for the top keywords if they align with your website's purpose.")
    print("3. Ensure all internal links are functional to improve user experience and SEO.")
    nav_message = "Consider adding" if not data['structure'].get('nav') else "Optimize"
    print(f"4. {nav_message} the navigation menu for better user experience.")

    print("\nActionable Plan:")
    print("1. Conduct a thorough review of the extracted data in the output file.")
    print("2. Analyze the website structure and consider improvements based on best practices.")
    print("3. Optimize content around the identified top keywords.")
    print("4. Review and potentially optimize the use of internal and external links.")
    print("5. Ensure all detected APIs are secure and necessary.")


def main() -> None:
    current_dir = os.getcwd()
    print(f"Current Working Directory: {current_dir}")

    url = input("Enter the website URL to scrape: ").strip()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    save_dir = input(
        "Enter the directory where you want to save the output file (press Enter to use current directory): "
    ).strip() or current_dir
    save_dir = os.path.abspath(os.path.expanduser(save_dir))
    os.makedirs(save_dir, exist_ok=True)

    file_format = ''
    while file_format not in ['csv', 'json']:
        choice = input("Choose the output file format ([C]SV / [J]SON): ").strip().lower()
        if choice in ['c', 'csv']:
            file_format = 'csv'
        elif choice in ['j', 'json']:
            file_format = 'json'
        else:
            print("Invalid input. Please enter 'C' for CSV or 'J' for JSON.")

    
    default_filename = f"website_analysis.{file_format}"
    filename = input(f"Enter the output filename (press Enter to use '{default_filename}'): ").strip() or default_filename
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
