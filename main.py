import requests
from bs4 import BeautifulSoup
import csv
import re
import json


def scrape_website(url):
    # 1. Fetch the webpage.
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 2. Extract HTML.
    html = soup.prettify()

    # 3. Extract CSS.
    css = []
    for style in soup.find_all('style'):
        css.append(style.string)
    for link in soup.find_all('link', rel='stylesheet'):
        css_url = link.get('href')
        if css_url:
            if css_url.startswith('http'):
                css_response = requests.get(css_url)
            else:
                css_response = requests.get(f"{url}/{css_url}")
            css.append(css_response.text)

    # 4. Extract any information on APIs.
    apis = []
    scripts = soup.find_all('script')
    api_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*api[^\s]*')
    for script in scripts:
        if script.string:
            apis.extend(api_pattern.findall(script.string))

    # 6. Extract metadata.
    title = soup.title.string if soup.title else ''
    description = soup.find('meta', attrs={'name': 'description'})
    description = description['content'] if description else ''
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    keywords = keywords['content'] if keywords else ''

    # 7. Extract contents.
    content = ' '.join([p.text for p in soup.find_all('p')])

    # 8. Extract any links.
    internal_links = []
    external_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith(url) or href.startswith('/'):
            internal_links.append(href)
        elif href.startswith('http'):
            external_links.append(href)

    # 9. Analyse the structure of the website.
    structure = {
        'head': bool(soup.head),
        'body': bool(soup.body),
        'header': bool(soup.header),
        'nav': bool(soup.nav),
        'main': bool(soup.main),
        'footer': bool(soup.footer),
    }

    # 10. Find keywords using simple frequency analysis.
    words = re.findall(r'\w+', content.lower())
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Ignore short words
            word_freq[word] = word_freq.get(word, 0) + 1
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'html': html,
        'css': '\n'.join(css),
        'apis': apis,
        'metadata': {
            'title': title,
            'description': description,
            'keywords': keywords
        },
        'content': content,
        'internal_links': internal_links,
        'external_links': external_links,
        'structure': structure,
        'top_keywords': keywords
    }


def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Category', 'Data'])
        writer.writerow(['HTML', data['html']])
        writer.writerow(['CSS', data['css']])
        writer.writerow(['APIs', json.dumps(data['apis'])])
        writer.writerow(['Title', data['metadata']['title']])
        writer.writerow(['Description', data['metadata']['description']])
        writer.writerow(['Keywords', data['metadata']['keywords']])
        writer.writerow(['Content', data['content']])
        writer.writerow(['Internal Links', json.dumps(data['internal_links'])])
        writer.writerow(['External Links', json.dumps(data['external_links'])])
        writer.writerow(['Structure', json.dumps(data['structure'])])
        writer.writerow(['Top Keywords', json.dumps(data['top_keywords'])])



url = input("Enter the website URL to scrape: ")
output_file = "website_analysis.csv"

print(f"Scraping {url}...")
scraped_data = scrape_website(url)
save_to_csv(scraped_data, output_file)
print(f"Analysis complete. Results saved to {output_file}")


print("\nKey Findings:")
print(
    f"1. The website has {len(scraped_data['internal_links'])} internal links and {len(scraped_data['external_links'])} external links.")
print(f"2. Top 5 keywords: {', '.join([word for word, _ in scraped_data['top_keywords'][:5]])}")
print(f"3. The website {'has' if scraped_data['structure']['nav'] else 'does not have'} a navigation menu.")
print(f"4. {len(scraped_data['apis'])} potential API endpoints were detected.")

print("\nRecommendations:")
print("1. Review the extracted APIs to ensure they are not exposing sensitive information.")
print("2. Consider optimizing the content for the top keywords if they align with your website's purpose.")
print("3. Ensure all internal links are functional to improve user experience and SEO.")
print(
    f"4. {'Consider adding' if not scraped_data['structure']['nav'] else 'Optimize'} the navigation menu for better user experience.")

print("\nActionable Plan:")
print("1. Conduct a thorough review of the extracted data in the CSV file.")
print("2. Analyze the website structure and consider improvements based on best practices.")
print("3. Optimize content around the identified top keywords.")
print("4. Review and potentially optimize the use of internal and external links.")
print("5. Ensure all detected APIs are secure and necessary.")