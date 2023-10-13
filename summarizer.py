import asyncio
import time
from typing import Dict, List

from models.cleanupModel import PageCleanup, cleanup_chain

# Model deps
from models.linkModel import link_chain
from models.sectionModel import PageSection, section_chain
from models.summarizeModel import PageSummary, summarize_chain

# Scraper deps
from scraper.scraper_bs4 import ScraperBS4
from scraper.scraper_types import PageContent

"""
    Generates the company summary in markdown:
    
    Getting all valid links
    1.) Scrape links from main page
    2.) Filter for duplicates
    3.) Remove main page link if it exists
    4.) Filter for only valid link (ones that return status 200)
    
    Prioritizing links to scrape
    1.) Choose <=10 links to use in the summary - LinkPrioritizationModel
    2.) Add main page link to prioritizedLinks
    
    Scrape pages
    1.) Scrape all prioritized links (using a headless browser
        want JS to load and hydrate)* not anymore
    2.) Clean up scraped data to only include body text(possibly metadata?)
    
    Page summaries
    1.) Summarize all pages in 2-3 paragraphs - PageSummaryModel
    2.) Include which sections this page will be useful for
    
    Section Generation
    1.) Format each sections prompt with relevant page summaries
    2.) Generate sections concurrently as markdown
    
    Document Stitching
    1.) Stitch together sections in order
    
    Cleanup
    1.) Clean up the whole markdown document to make it easier to read
    
    Return
"""


async def generateCompanySummary(company_url: str):
    start_time = time.time()
    # ------------ GETTING ALL VALID LINKS --------------
    print(f"[INFO] Getting and validating links from {company_url}")
    validate_links_start_time = time.time()

    # create scraper object
    scraper = ScraperBS4()

    # Scrape links from main page
    main_page_internal_links = await scraper.scrapeInternalLinks(company_url)

    # Remove duplicates and main page link if it exists
    unique_links = list(set(main_page_internal_links))
    if company_url in unique_links:
        unique_links.remove(company_url)

    # Keep all links that return status 200 & filter out duplicates from redirects
    valid_links = await scraper.filterValidLinks(unique_links)

    validate_links_end_time = time.time() - validate_links_start_time
    print(
        f"[INFO] Getting and validating links took {validate_links_end_time} seconds with {len(valid_links)} valid links"
    )

    # ------------ PRIORITIZING LINKS TO SCRAPE --------------
    print(f"[INFO] Prioritizing links from {len(valid_links)} links")
    prioritize_link_start_time = time.time()
    prioritizedLinks = await getPrioritizedLinks(company_url, valid_links)
    prioritizedLinks.append(company_url)
    prioritize_link_elapsed_time = time.time() - prioritize_link_start_time
    print(
        f"[INFO] Prioritizing links took {prioritize_link_elapsed_time} seconds with {len(prioritizedLinks)} links chosen"
    )

    # ------------ SCRAPE PAGES --------------
    # Scrape and clean body content for each page
    # Also truncates if too large
    print(f"[INFO] Scraping {len(prioritizedLinks)} pages")
    scrape_links_start_time = time.time()
    pages = scraper.scrape(prioritizedLinks)
    scrape_links_elapsed_time = time.time() - scrape_links_start_time
    print(f"[INFO] Scraping links took {scrape_links_elapsed_time} seconds")

    # ------------ PAGE SUMMARIES --------------
    # Summarize all pages in 2-3 paragraphs - PageSummaryModel
    print("[INFO] Summarizing pages")
    summarize_page_start_time = time.time()
    pages_with_summaries = await summarizePages(pages)
    summarize_page_elapsed_time = time.time() - summarize_page_start_time
    print(f"[INFO] Summarizing pages took {summarize_page_elapsed_time} seconds")

    # ------------ SECTION GENERATION --------------
    print("[INFO] Generating sections")
    generate_sections_start_time = time.time()

    # Split up content for each sections
    section_labels = [
        "Company Summary",
        "Products and Services",
        "Business Model",
        "Target Audience",
        "Key Competitors",
        "Contact Information and Company Details",
    ]
    section_content_lists = {}
    for section_label in section_labels:
        section_content_lists[section_label] = []

    for page in pages_with_summaries:
        for section in page.sections:
            if section not in section_labels:
                continue
            section_content_lists[section].append("<br>".join([page.url, page.summary]))

    # aggregate each sections content
    section_content = {}
    for key, value in section_content_lists.items():
        section_content[key] = "<br><br>".join(value)

    # generate sections concurrently as markdown
    sections: Dict[str, str] = await generateSections(section_content)

    generate_sections_elapsed_time = time.time() - generate_sections_start_time
    print(f"[INFO] Generating sections took {generate_sections_elapsed_time} seconds")

    # ------------ DOCUMENT STITCHING --------------
    print("[INFO] Stitching sections together")
    stitch_sections_start_time = time.time()

    company_summary_raw = ""

    generated_section_labels = list(sections.keys())
    for section_label in section_labels:
        if section_label in generated_section_labels:
            company_summary_raw += f"<br>{sections[section_label]}<br>"

    # Replace \n with <br>
    company_summary_raw = company_summary_raw.replace("\n", "<br>")

    stitch_sections_start_time = time.time() - stitch_sections_start_time
    print(f"[INFO] Stitching sections took {stitch_sections_start_time} seconds")

    # ------------ CLEANUP --------------
    print("[INFO] Cleaning up markdown")
    cleanup_start_time = time.time()

    company_summary = await cleanupSummary(company_summary_raw)

    cleanup_end_time = time.time() - cleanup_start_time
    print(f"[INFO] Cleaning up markdown took {cleanup_end_time} seconds")

    # End timer
    elapsed_time = time.time() - start_time
    print("[INFO] Total time elapsed: ", elapsed_time)

    # TODO: Maybe add a cleanup step to make the markdown easier to read
    return company_summary


async def cleanupSummary(company_summary: str) -> str:
    page_cleanup: PageCleanup = cleanup_chain.run(company_summary=company_summary)

    return page_cleanup.cleaned_content


"""
    Takes in all the section content and generates the sections concurrently
    Input: Dict[section_name, section_content]
    Output: Dict[section_name, section_markdown]
"""


async def generateSections(section_content: Dict[str, str]) -> Dict[str, str]:
    tasks = []
    for key, value in section_content.items():
        tasks.append(generateSection(key, value))

    sections = await asyncio.gather(*tasks)

    result = {}
    for section in sections:
        result[section[0]] = section[1]

    return result


"""
    Returns a list of [section_name, section_markdown]
"""


async def generateSection(section_name: str, section_content: str) -> List[str]:
    page_section: PageSection = await section_chain.arun(
        section_name=section_name, page_summaries=section_content
    )
    section_markdown = page_section.section

    return [section_name, section_markdown]


async def summarizePages(pages: List[PageContent]) -> List[PageContent]:
    # ------------ PAGE SUMMARIES --------------
    # Summarize all pages in 2-3 paragraphs - PageSummaryModel
    # Include which sections this page will be useful for
    tasks = [summarizePage(page) for page in pages]

    pageContents: List[PageSummary] = await asyncio.gather(*tasks)

    return pageContents


async def summarizePage(page: PageContent) -> PageContent:
    pageSummary: PageSummary = await summarize_chain.arun(
        page_url=page.url, page_text=page.bodyContent
    )

    page.summary = pageSummary.summary
    page.sections = pageSummary.sections

    return page


async def getPrioritizedLinks(url: str, links: List[str], num_links=10):
    links_input = "\n".join(links)

    link_resp = link_chain.run(url=url, links=links_input, num_links=num_links)

    return link_resp
