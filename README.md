# 🔍 KeyHunter - Password Scanner for Wordlists

![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2Fgitblanc%2FKeyHunter%2F&label=Total%20visits&labelColor=%23697689&countColor=%23d9e3f0)

![keyhunter-removebg-preview](https://github.com/user-attachments/assets/5dc4b0f6-dec5-4aef-9dba-9ac489f868ff)


KeyHunter is a powerful command-line tool designed to efficiently and stylishly search for passwords in massive wordlist files. Perfect for security researchers, password auditors, and anyone interested in scanning large datasets for specific terms.

## 🚀 Key Features:

- 🔎 **Efficient Searching**: Scans large files in blocks, optimizing memory usage and maximizing speed.
- 🎳 **Parallel Searching**: Scans multiple files in blocks, optimizing memory 15x times more than the efficient searching.
- 📈 **Progress Bar**: Visualize the real time scanning progress for a more engaging experience.
- 🔴 **Term Highlighting**: Highlights search terms found in red, making them easy to spot in the output.
- 💡 **Detailed Reports**: Displays the total number of occurrences found and details of each match.
- 🔧 **Configurable Options**: Adjust block size and enable verbose mode to see detailed progress of each step.

## 🛠 Requirements

- **Python version**: `Python 3.x`
- **Libraries**: `colorama`, `tqdm`, `Pillow`, `mmap`

## 📥 Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/keyhunter.git
cd keyhunter
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```
Run the script:

```bash
python3 keyhunter.py <path-to-file> <search-term> [options]
```

## 📜 Usage Examples
- Search for passwords across multiple and different files (**_FASTER_**):

>[!Note]
>For this option you should separate the wordlist in multiple files using the `--split` functionality (or by yourself) and then pass the folder as path.

```shell
python3 keyhunter.py /path/to/wordlist_parts/ password [-v] [--output /path/to/scan.txt]
```

- Search for passwords in a file (**_SLOWER_**):

```bash
python3 keyhunter.py /path/to/wordlist.txt password [-v] [--output /path/to/scan.txt]
```

- Split a file in multiple smaller ones (to split massive wordlists):

```bash
python3 keyhunter.py /path/to/wordlist.txt --split [--max_size 50]
```

- Export results to pdf:

```bash
python3 keyhunter.py /path/to/wordlist.txt search_term --pdf
```
