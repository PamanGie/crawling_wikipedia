import wikipedia
import json
import re
import time

class WikipediaArticleCrawler:
    def __init__(self):
        wikipedia.set_lang("en")
    
    def clean_text(self, text):
        """
        Membersihkan teks dari karakter yang tidak diinginkan
        """
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
        """
        Membersihkan konten section
        """
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
        """
        Format artikel dengan format yang lebih clean
        """
        # Mulai dengan title
        lines = [f"Title: {title}"]
        
        # Tambahkan setiap section
        for section in sections:
            if section["title"] and section["content"]:
                # Tambahkan section title
                lines.append(f"Section: {section['title']}")
                # Tambahkan content yang sudah dibersihkan
                lines.append(section["content"])
        
        # Gabungkan dengan single newline
        return '\n'.join(lines)

    def get_article_structure(self, topic):
        try:
            print(f"\nProcessing article: {topic}")
            
            # Cari artikel
            search_results = wikipedia.search(topic, results=1)
            if not search_results:
                return None
            
            page_title = search_results[0]
            print(f"Found article: {page_title}")
            
            time.sleep(1)  # Avoid rate limiting
            
            page = wikipedia.page(page_title, auto_suggest=False)
            content = page.content
            sections = self._parse_sections(content)
            
            # Format artikel
            article = {
                "prompt": f"Write a detailed article about {topic}",
                "completion": self._format_article(page_title, sections)
            }
            
            print(f"Successfully processed {topic}")
            return article
            
        except Exception as e:
            print(f"Error processing {topic}: {e}")
            return None
    
    def _parse_sections(self, content):
        sections = []
        current_section = None
        current_text = ""
        
        for line in content.split('\n'):
            # Deteksi section baru
            if line.startswith('== ') and line.endswith(' =='):
                if current_section:
                    # Simpan section sebelumnya setelah dibersihkan
                    cleaned_text = self.clean_section(current_text)
                    if cleaned_text:  # Hanya simpan jika ada konten
                        sections.append({
                            "title": current_section,
                            "content": cleaned_text
                        })
                
                current_section = line.strip('= ')
                current_text = ""
            else:
                current_text += line + "\n"
        
        # Tambahkan section terakhir
        if current_section:
            cleaned_text = self.clean_section(current_text)
            if cleaned_text:
                sections.append({
                    "title": current_section,
                    "content": cleaned_text
                })
        
        return sections

    def crawl_multiple_articles(self, topics, output_file):
        success_count = 0
        
        print(f"Starting to crawl {len(topics)} articles...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for topic in topics:
                article = self.get_article_structure(topic)
                if article and len(article['completion'].split()) > 100:
                    f.write(json.dumps(article, ensure_ascii=False) + '\n')
                    success_count += 1
                    print(f"Saved article about {topic}")
        
        print(f"\nCrawling completed. Successfully processed {success_count} out of {len(topics)} articles.")
        return success_count

# Contoh penggunaan
if __name__ == "__main__":
    topics = [
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
        "5G technology"
    ]
    
    print("Starting Wikipedia article crawler...")
    crawler = WikipediaArticleCrawler()
    num_articles = crawler.crawl_multiple_articles(topics, "clean_wikipedia_dataset.jsonl")
    print(f"\nTotal articles successfully crawled: {num_articles}")
