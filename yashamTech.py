# Imports

from bs4 import BeautifulSoup
from openai import OpenAI
import json
from dotenv import load_dotenv
from IPython.display import display, Markdown
import os
import requests

# Initializing the OpenAI client for Google Gemini

MODEL = "gemini-2.5-flash"

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

gemini = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key= google_api_key
)

# Website class to scrape and process web content

class Website:
    def __init__(self, url):
        self.url = url

        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.find('title')
        self.title = title_tag.get_text(strip=True) if title_tag else "unknown"

        for tag in soup(['style', 'script', 'img', 'input']):
            tag.decompose()

        self.text = soup.get_text(separator="\n", strip=True)

        self.links = [link.get('href') for link in soup.find_all('a', href=True)]

    def get_contents(self):
        return f"Title: {self.title}\n\nText: {self.text}"
    
# System and user prompts for the link extraction task

link_system_prompt = "You are provided with a list of links found on a webpage. \
Your task is to identify and extract links that directly point to recycling centers or organizations offering recycling services. \
These links typically correspond to specific listings of recycling providers and may lead to more details about the center, contact info, or services offered.\n"

link_system_prompt += "Ignore any links that are related to navigation, login, terms, privacy policies, or advertisements.\n"

link_system_prompt += "You should respond in JSON format as in the following example:"
link_system_prompt += """
{
    "links": [
        {"name": "IMobile LLC", "url": "https://example.com/centers/imobile-llc"},
        {"name": "The 4th Bin", "url": "https://example.com/centers/the-4th-bin"}
    ]
}
"""

def get_links_user_prompt(website):
    user_prompt = f"Here is a list of links from the website {website.url}.\n"
    user_prompt += "Can you help extract only the links that point to actual recycling centers listed on the page? \
I’m interested in links that go to specific recycling service providers such as 'IMobile LLC', 'The 4th Bin', or 'NYC Bulk Item Program'.\n"
    user_prompt += "Ignore links that lead to maps, login pages, legal documents, FAQs, or general navigation.\n"
    user_prompt += "Also, convert any relative URLs to full `https://` URLs based on the page's domain.\n"
    user_prompt += "Please return results in JSON format as:\n"
    user_prompt += '{"links": [{"name": "<center name>", "url": "<full url>"}]}\n\n'
    user_prompt += "Here are the links:\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

# Function to extract JSON from the result string

def to_json(result):
    json_string = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL).group(1)
    json_data = json.loads(json_string)
    return json_data

def extract_json_array(text):
    match = re.search(r'(\[\s*{.*?}\s*\])', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return data
        except json.JSONDecodeError:
            print("Matched text is not valid JSON.")
            return None
    else:
        print("No JSON array found in the input.")
        return None
    
# Function to get links from a given URL using the Gemini model

def get_links(url):
    website = Website(url)
    user_prompt = get_links_user_prompt(website)
    if user_prompt:
        response = gemini.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": link_system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        result =  response.choices[0].message.content
        return result
    
# Function to get all details from a given URL, including the landing page and links

def get_all_details(url):
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = to_json(get_links(url))
    
    for link in links["links"]:
        result += f"\n\n{link['name']}\n"
        result += Website(link["url"]).get_contents()
    return result

# System and user prompts for the recycling facility extraction task

scraper_system_prompt = """
            You are an intelligent assistant designed to extract structured recycling facility data from semi-structured or unstructured web content such as search result pages or listings.
            
            Your task is to extract **only relevant recycling facility entries** and convert them into JSON records following the exact format provided below.
            
            Each facility should include:
            - business_name: Official name of the recycling center
            - last_update_date: The last date when the listing or information was updated (if not available, write "unknown")
            - street_address: The full physical address of the center
            - materials_category: One or more main categories (choose only from the predefined list below)
            - materials_accepted: Exact matches from the allowed material options listed under the categories
            
            Match and classify listed materials with the **most appropriate sub-categories** provided below. Avoid vague generalizations — match as specifically as possible.
            
            ---
            
            ### Allowed Categories and Accepted Materials
            
            Electronics:
            1. Computers, Laptops, Tablets
            2. Monitors, TVs (CRT & Flat Screen)
            3. Cell Phones, Smartphones
            4. Printers, Copiers, Fax Machines
            5. Audio/Video Equipment
            6. Gaming Consoles
            7. Small Appliances (Microwaves, Toasters, etc.)
            8. Computer Peripherals (Keyboards, Mice, Cables, etc.)
            
            Batteries:
            1. Household Batteries (AA, AAA, 9V, etc.)
            2. Rechargeable Batteries
            3. Lithium-ion Batteries
            4. Button/Watch Batteries
            5. Power Tool Batteries
            6. E-bike/Scooter Batteries
            7. Car/Automotive Batteries
            
            Paint & Chemicals:
            1. Latex/Water-based Paint
            2. Oil-based Paint and Stains
            3. Spray Paint
            4. Paint Thinners and Solvents
            5. Household Cleaners
            6. Pool Chemicals
            7. Pesticides and Herbicides
            8. Automotive Fluids (Oil, Antifreeze)
            
            Medical Sharps:
            1. Needles and Syringes
            2. Lancets
            3. Auto-injectors (EpiPens)
            4. Insulin Pens
            5. Home Dialysis Equipment
            
            Textiles & Clothing:
            1. Clothing and Shoes
            2. Household Textiles (Towels, Bedding)
            3. Fabric Scraps
            4. Accessories (Belts, Bags, etc.)
            
            Other Important Materials:
            1. Fluorescent Bulbs and CFLs
            2. Mercury Thermometers
            3. Smoke Detectors
            4. Fire Extinguishers
            5. Propane Tanks
            6. Mattresses and Box Springs
            7. Large Appliances (Fridges, Washers, etc.)
            8. Construction Debris (Residential Quantities)
            
            ---
            
            ### Output Format Example:
            
            [
              {
                "business_name": "Green Earth Recyclers",
                "last_update_date": "2023-11-04",
                "street_address": "123 5th Ave, New York, NY 10001",
                "materials_category": ["Electronics", "Batteries"],
                "materials_accepted": ["Computers, Laptops, Tablets", "Cell Phones, Smartphones", "Lithium-ion Batteries"]
              }
            ]
            
            ---
            
            If a facility only mentions general items (e.g., “electronics” or “batteries”), try to reasonably infer the correct materials_accepted using common-sense mapping based on industry practices.
            
            If a category or material cannot be clearly identified, **exclude that item**.
            
            Return **only an array of 3 or more valid facilities** in the JSON structure shown.
            """


def get_facility_extraction_user_prompt(scraped_text):
    return f"""
            Below is the raw text content extracted from a webpage listing recycling centers for "Electronics" near ZIP code 10001 within 100 miles:
            
            ---
            {scraped_text}
            ---
            
            Please read the listings and extract details for at least 3 unique recycling facilities.
            
            For each facility, include the following fields in the output:
            - business_name
            - last_update_date (if missing, write "unknown")
            - street_address
            - materials_category (only from the allowed categories)
            - materials_accepted (only from the allowed options under those categories)
            
            Make sure to classify the materials into the **correct predefined categories** and return the output in **clean structured JSON format** as shown in the example:
            
            [
              {{
                "business_name": "Sample Facility",
                "last_update_date": "unknown",
                "street_address": "123 4th Ave, New York, NY 10001",
                "materials_category": ["Electronics"],
                "materials_accepted": ["Cell Phones, Smartphones", "Computers, Laptops, Tablets"]
              }}
            ]
            
            If some details (like update date) are not mentioned, use "unknown". Do not hallucinate or guess names — only use what is clearly present.
            """

# Function to get facilities from a given URL using the Gemini model

def get_facilities(url):
    website = Website(url)
    user_prompt = get_links_user_prompt(website)
    text = get_all_details(url)
    if user_prompt:
        response = gemini.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": scraper_system_prompt},
                {"role": "user", "content": get_facility_extraction_user_prompt(text)}
            ]
        )
        result = response.choices[0].message.content
        result = extract_json_array(result)
        return result
    
if __name__ == "__main__":
    # Example usage
    url = "https://search.earth911.com/?what=Electronics&where=10001&list_filter=all&max_distance=100&family_id=&latitude=&longitude=&country=&province=&city=&sponsor="
    print("Extracting recycling facilities from:", url)
    facilities = get_facilities(url)
    print("Found facilities:", json.dumps(facilities, indent=2))


