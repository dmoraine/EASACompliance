# 🚀 Quick Start - EASA Parser

## Installation

No installation required! The module uses only Python standard library.

```bash
# Verify that Python 3.8+ is installed
python --version
```

## Usage in 30 seconds

### 1. View the table of contents

```python
from easacompliance import EASAParser

# Initialize
parser = EASAParser("Easy Access Rules for Air Operations - February 2025 - xml.xml")

# Get the complete table of contents
toc = parser.get_table_of_contents()
print(f"Total: {len(toc)} paragraphs")

# Or filter by category
ftl_toc = parser.get_table_of_contents(pattern=r"ORO\.FTL\.[0-9]+")
for item in ftl_toc:
    print(f"{item['reference']}: {item['title']}")
```

### 2. Extract a paragraph

```python
from easacompliance import EASAParser

# Initialize
parser = EASAParser("Easy Access Rules for Air Operations - February 2025 - xml.xml")

# Extract
paragraph = parser.extract_paragraph("ORO.FTL.110")

# Display
print(f"{paragraph.reference}: {paragraph.title}")
print(paragraph.content)
```

### 3. Search paragraphs

```python
# Search all ORO.FTL.1xx paragraphs
results = parser.search_paragraphs(r"ORO\.FTL\.1[0-9]{2}")

for para in results:
    print(f"• {para.reference} - {para.title}")
```

### 4. Export JSON

```python
import json

paragraph = parser.extract_paragraph("ORO.FTL.110")

# Convert to dict
data = paragraph.to_dict()

# Save
with open("output.json", "w") as f:
    json.dump(data, f, indent=2)
```

### 5. Text for embeddings

```python
# Get the complete text
paragraph = parser.extract_paragraph("ORO.FTL.110")
full_text = paragraph.get_full_text()

# Use with your embeddings model
# embeddings = model.encode(full_text)
```

## Ready-to-Use Examples

### Run the simple example
```bash
python example_usage.py
```

### Run all tests
```bash
python test_parser.py
```

## Paragraph Structure

```python
paragraph = parser.extract_paragraph("ORO.FTL.110")

# Access properties
paragraph.reference        # "ORO.FTL.110"
paragraph.title           # "Operator responsibilities"
paragraph.content         # Textual content
paragraph.paragraph_type  # ParagraphType.MAIN
paragraph.subparagraphs   # List of AMC/GM
paragraph.metadata        # {'regulation': '...'}
```

## Advanced Options

### Extract without AMC/GM

```python
# Regulation only
regulation = parser.extract_paragraph("ORO.FTL.110", include_amc_gm=False)
```

### Access subparagraphs

```python
paragraph = parser.extract_paragraph("ORO.FTL.110")

# Iterate through AMC/GM
for sub in paragraph.subparagraphs:
    print(f"{sub.reference} ({sub.paragraph_type.value})")
    print(sub.content)
```

## Typical Use Cases

### 1. Complete workflow: TOC → Extraction → RAG

```python
# 1. Get the list of all paragraphs
toc = parser.get_table_of_contents(pattern=r"ORO\.FTL\.[0-9]+")

# 2. Extract each paragraph
documents = []
for item in toc:
    paragraph = parser.extract_paragraph(item['reference'])
    if paragraph:
        documents.append({
            "id": paragraph.reference,
            "text": paragraph.get_full_text(),
            "metadata": paragraph.to_dict()
        })

# 3. Ready to create embeddings
print(f"{len(documents)} documents ready for RAG")
```

### 2. Create a knowledge base

```python
# Extract all FTL paragraphs
all_ftl = parser.search_paragraphs(r"ORO\.FTL\.[0-9]+")

# Create an index
knowledge_base = {}
for para in all_ftl:
    knowledge_base[para.reference] = {
        "title": para.title,
        "content": para.get_full_text(),
        "metadata": para.metadata
    }
```

### 3. View all available categories

```python
# Get the list of categories
categories = parser.get_categories()

for cat, count in categories.items():
    print(f"{cat}: {count} paragraphs")

# Result:
# ORO.FTL: 17 paragraphs
# ORO.GEN: 25 paragraphs
# etc.
```

### 4. Compare regulation and guidance

```python
# Regulation only
reg = parser.extract_paragraph("ORO.FTL.110", include_amc_gm=False)

# With guidance
full = parser.extract_paragraph("ORO.FTL.110", include_amc_gm=True)

print(f"Regulation: {len(reg.content)} characters")
print(f"With AMC/GM: {len(full.get_full_text())} characters")
```

## Quick References

### Useful Regex Patterns

```python
# All ORO.FTL
r"ORO\.FTL\.[0-9]+"

# ORO.FTL.1xx (100-199)
r"ORO\.FTL\.1[0-9]{2}"

# ORO.FTL.2xx (200-299)
r"ORO\.FTL\.2[0-9]{2}"

# All ORO
r"ORO\.[A-Z]+\.[0-9]+"
```

### Paragraph Types

```python
from easacompliance import ParagraphType

ParagraphType.MAIN          # Main paragraph
ParagraphType.AMC           # Acceptable Means of Compliance
ParagraphType.GM            # Guidance Material
ParagraphType.SUBPARAGRAPH  # Subparagraph (a), (b), etc.
ParagraphType.CONTENT       # Textual content
```

## Troubleshooting

### Error: File not found
```python
# Verify the path
import os
xml_path = "Easy Access Rules for Air Operations - February 2025 - xml.xml"
print(f"File exists: {os.path.exists(xml_path)}")
```

### Paragraph not found
```python
# Verify the exact reference
paragraph = parser.extract_paragraph("ORO.FTL.110")
if paragraph is None:
    print("Paragraph not found - verify the reference")
```

### Slow performance
```python
# The parser loads the entire XML at startup
# Reuse the same instance for multiple extractions
parser = EASAParser("regulations.xml")  # Once only

# Then extract multiple paragraphs
para1 = parser.extract_paragraph("ORO.FTL.110")
para2 = parser.extract_paragraph("ORO.FTL.115")
# etc.
```

## Next Steps

1. **Read the complete documentation**: `README_PARSER.md`
2. **See the tests**: `test_parser.py`
3. **Explore the examples**: `example_usage.py`
4. **Integrate into your RAG project**

## Support

- 📖 Documentation: `README_PARSER.md`
- 🧪 Tests: `python test_parser.py`
- 💡 Examples: `example_usage.py`
- 📊 Structure: `PROJECT_STRUCTURE.md`

---

**Startup time**: < 5 minutes
**Prerequisites**: Python 3.8+
**Dependencies**: None (standard library)
