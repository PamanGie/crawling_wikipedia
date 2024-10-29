# Wikipedia Article Crawler for GPT-2 Training

A Python tool to crawl Wikipedia articles and format them into a structured dataset suitable for training GPT-2 models. The crawler extracts articles with their sections and subsections, cleans the content, and outputs them in JSONL format.

## Features

- Crawls Wikipedia articles based on specified topics
- Extracts article structure (title, sections, content)
- Cleans and formats text (removes references, URLs, special characters)
- Outputs in JSONL format suitable for GPT-2 training
- Handles error cases and rate limiting
- Progress tracking and logging

## Requirements

```bash
pip install wikipedia-api
```

## Usage

### Basic Usage

```python
from wikipedia_crawler import WikipediaArticleCrawler

# Define topics to crawl
topics = [
    "Cloud computing",
    "Artificial intelligence",
    "Machine learning",
    "Deep learning",
    "Neural networks"
]

# Initialize and run crawler
crawler = WikipediaArticleCrawler()
num_articles = crawler.crawl_multiple_articles(topics, "wikipedia_dataset.jsonl")
```

### Output Format

The crawler generates a JSONL file where each line is a JSON object with the following structure:

```json
{
    "prompt": "Write a detailed article about Cloud Computing",
    "completion": "Title: Cloud Computing\nSection: Overview\nCloud computing is a technology...\nSection: History\nThe concept of cloud computing..."
}
```

## Training with the Dataset

The generated dataset can be used directly with the provided training script:

```python
from cloud_model_trainer import CloudModelTrainer

trainer = CloudModelTrainer(
    model_name="gpt2",
    dataset_path="wikipedia_dataset.jsonl"
)

trainer.setup()
trainer.train(output_dir="./cloud_model")
```

## Project Structure

```
├── wikipedia_crawler.py     # Main crawler implementation
├── requirements.txt        # Project dependencies
└── README.md              # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Known Limitations

1. Rate limiting from Wikipedia API
2. Some articles might not be available or might be disambiguation pages
3. Special characters handling might need adjustment for specific languages

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   - The crawler includes a delay between requests
   - Increase `time.sleep()` if you encounter rate limiting

2. **Memory Issues**
   - Adjust chunk size in training script
   - Process fewer articles at once

3. **Encoding Issues**
   - The crawler uses UTF-8 encoding
   - Check your file system encoding if you see strange characters

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Wikipedia API for providing access to article content
- Hugging Face Transformers library for GPT-2 implementation
- All contributors to this project

## Example Output

### Sample Crawled Article

```json
{
    "prompt": "Write a detailed article about Artificial Intelligence",
    "completion": "Title: Artificial Intelligence\nSection: Definition\nArtificial intelligence (AI) is intelligence demonstrated by machines...\nSection: History\nThe field of AI research was founded at a workshop held on the campus of Dartmouth College in 1956..."
}
```

### Training Metrics

The training script generates:
- Loss curves
- Perplexity metrics
- Evaluation result
