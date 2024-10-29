import wikipedia
import json
import re
import time
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WikipediaArticleCrawler:
    def __init__(self):
        wikipedia.set_lang("en")
        self.retry_count = 3
        self.delay = 2  # seconds between requests
        
    def clean_text(self, text):
        """Membersihkan teks dari karakter yang tidak diinginkan"""
        # Hapus referensi Wikipedia [1], [2], dst
        text = re.sub(r'\[\d+\]', '', text)
        
        # Hapus multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Hapus multiple newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Hapus spasi di awal dan akhir setiap baris
        text = '\n'.join(line.strip() for line in text.split('\n'))
        
        return text.strip()
    
    def clean_section(self, section_text):
        """Membersihkan konten section"""
        # Hapus citation needed tags
        text = re.sub(r'\[citation needed\]', '', section_text)
        
        # Hapus edit tags
        text = re.sub(r'\[edit\]', '', text)
        
        # Hapus referensi
        text = re.sub(r'\[\d+\]', '', text)
        
        # Hapus URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Bersihkan teks
        text = self.clean_text(text)
        
        return text

    def _format_article(self, title, sections):
        """Format artikel dengan format yang lebih clean"""
        # Mulai dengan title
        lines = [f"Title: {title}"]
        
        # Tambahkan setiap section
        for section in sections:
            if section["title"] and section["content"]:
                lines.append(f"Section: {section['title']}")
                lines.append(section["content"])
        
        return '\n'.join(lines)

    def _verify_article_quality(self, article):
        """Verifikasi kualitas artikel"""
        if not article:
            return False, "Article is None"
            
        completion = article['completion']
        
        # Cek panjang minimal
        word_count = len(completion.split())
        if word_count < 100:
            return False, f"Article too short ({word_count} words)"
        
        # Cek jumlah section minimal
        section_count = completion.count('Section:')
        if section_count < 2:
            return False, f"Too few sections ({section_count})"
        
        # Cek rasio kata unik
        words = completion.lower().split()
        unique_words = len(set(words))
        word_ratio = unique_words / len(words)
        if word_ratio < 0.3:
            return False, f"Low word diversity ({word_ratio:.2f})"
        
        return True, f"Passed all checks ({word_count} words, {section_count} sections)"

    def get_article_structure(self, topic):
        """Get article with improved error handling"""
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Processing article: {topic} (Attempt {attempt + 1}/{self.retry_count})")
                
                # Cari artikel
                search_results = wikipedia.search(topic, results=1)
                if not search_results:
                    logger.warning(f"No results found for: {topic}")
                    return None
                
                page_title = search_results[0]
                logger.info(f"Found article: {page_title}")
                
                try:
                    page = wikipedia.page(page_title, auto_suggest=False)
                except wikipedia.DisambiguationError as e:
                    logger.info(f"Disambiguation found for {topic}, trying first option: {e.options[0]}")
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                    except Exception as inner_e:
                        logger.error(f"Failed to get disambiguation page for {topic}: {inner_e}")
                        continue
                except wikipedia.PageError:
                    logger.error(f"Page not found for: {topic}")
                    return None
                
                time.sleep(self.delay)
                
                content = page.content
                sections = self._parse_sections(content)
                
                if not sections:
                    logger.warning(f"No valid sections found for: {topic}")
                    return None
                    
                article = {
                    "prompt": f"Write a detailed article about {topic}",
                    "completion": self._format_article(page_title, sections)
                }
                
                # Verify article quality
                is_valid, message = self._verify_article_quality(article)
                if not is_valid:
                    logger.warning(f"Article quality check failed for {topic}: {message}")
                    continue
                
                logger.info(f"Successfully processed {topic}: {message}")
                return article
                    
            except Exception as e:
                logger.error(f"Error processing {topic} (Attempt {attempt + 1}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.delay)
                    continue
                return None
        
        return None
    
    def _parse_sections(self, content):
        """Parse sections with improved handling"""
        sections = []
        current_section = None
        current_text = ""
        
        for line in content.split('\n'):
            if line.startswith('== ') and line.endswith(' =='):
                if current_section:
                    cleaned_text = self.clean_section(current_text)
                    if cleaned_text:
                        sections.append({
                            "title": current_section,
                            "content": cleaned_text
                        })
                
                current_section = line.strip('= ')
                current_text = ""
            else:
                current_text += line + "\n"
        
        if current_section:
            cleaned_text = self.clean_section(current_text)
            if cleaned_text:
                sections.append({
                    "title": current_section,
                    "content": cleaned_text
                })
        
        return sections

    def crawl_multiple_articles(self, topics, output_file):
        """Crawl multiple articles with progress tracking"""
        success_count = 0
        failed_count = 0
        failed_topics = []
        progress_file = 'crawling_progress.txt'
        
        logger.info(f"Starting to crawl {len(topics)} articles...")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        def update_progress():
            with open(progress_file, 'w', encoding='utf-8') as prog:
                prog.write(f"Progress: {success_count + failed_count}/{len(topics)}\n")
                prog.write(f"Successful: {success_count}\n")
                prog.write(f"Failed: {failed_count}\n")
                prog.write("\nFailed topics:\n")
                prog.write('\n'.join(failed_topics))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, topic in enumerate(topics, 1):
                logger.info(f"\nProcessing {i}/{len(topics)}: {topic}")
                article = self.get_article_structure(topic)
                
                if article and len(article['completion'].split()) > 100:
                    f.write(json.dumps(article, ensure_ascii=False) + '\n')
                    success_count += 1
                    logger.info(f"[OK] Successfully saved article about {topic}")
                else:
                    failed_count += 1
                    failed_topics.append(topic)
                    logger.warning(f"[FAIL] Failed to process {topic}")
                
                update_progress()
        
        logger.info("\nCrawling Summary:")
        logger.info(f"Total topics: {len(topics)}")
        logger.info(f"Successfully processed: {success_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info("\nFailed topics:")
        for topic in failed_topics:
            logger.info(f"- {topic}")
        
        return success_count

if __name__ == "__main__":
    topics = [
        # Previous topics
        "Cloud computing",
        "Artificial intelligence",
        "Machine learning",
        "Deep learning",
        "Neural networks",
        "Big data",
        "Data mining",
        "Internet of things",
        "Blockchain",
        "Edge computing",
        "Quantum computing",
        "5G technology",
        # Fundamental CS
        "Computer architecture",
        "Operating systems",
        "Data structures",
        "Algorithms",
        "Database systems",
        "Computer networks",
        "Software engineering",
        "Programming paradigms",
        "Distributed systems",
        "Information security",
        # Development & Programming
        "Web development",
        "Mobile development",
        "Software testing",
        "Version control",
        "Agile methodology",
        "DevOps",
        "RESTful API",
        "GraphQL",
        "Microservices architecture",
        "Continuous integration",
        # Data & Analytics
        "Data analytics",
        "Business intelligence",
        "Data visualization",
        "Statistical computing",
        "Predictive analytics",
        "Data warehousing",
        "ETL processing",
        "Real time analytics",
        "Data modeling",
        "Database optimization",
        # AI & ML Detail
        "Computer vision",
        "Natural language processing",
        "Reinforcement learning",
        "Genetic algorithms",
        "Expert systems",
        "Pattern recognition",
        "Speech recognition",
        "Machine translation",
        "Robotics",
        "Autonomous systems",
        # Security & Privacy
        "Cybersecurity",
        "Network security",
        "Cryptography",
        "Information privacy",
        "Security protocols",
        "Ethical hacking",
        "Digital forensics",
        "Malware analysis",
        "Identity management",
        "Security architecture",
        # Modern Technologies
        "Container orchestration",
        "Serverless computing",
        "Cloud native",
        "Progressive web apps",
        "AR/VR technology",
        "Internet of behaviors",
        "Digital twins",
        "Low code platforms",
        "Edge AI",
        "Green computing",
        # Emerging Tech
        "Metaverse",
        "Web3",
        "Decentralized systems",
        "Smart contracts",
        "Zero trust security",
        "Quantum cryptography",
        "Bioinformatics",
        "Brain computer interface",
        "Swarm intelligence",
        "Fog computing",
        # Software Architecture
        "Design patterns",
        "System architecture",
        "Enterprise architecture",
        "Service oriented architecture",
        "Event driven architecture",
        "Domain driven design",
        "Clean architecture",
        "SOLID principles",
        "Scalable systems",
        "High availability systems",
        # Additional Topics
        "High performance computing",
        "Parallel computing",
        "Infrastructure as code",
        "Site reliability engineering",
        "Quantum machine learning",
        "Federated learning",
        "Compiler design",
        "Computer graphics"
    ]
    
    logger.info("Starting Wikipedia article crawler...")
    crawler = WikipediaArticleCrawler()
    output_file = "clean_wikipedia_dataset3.jsonl"
    num_articles = crawler.crawl_multiple_articles(topics, output_file)
    logger.info(f"\nTotal articles successfully crawled: {num_articles}")
