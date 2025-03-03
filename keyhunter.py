#!/usr/bin/env python3

import os
import argparse
from colorama import init, Fore, Style
from datetime import datetime
from tqdm import tqdm
import mmap
import multiprocessing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import grey
import re

# Initialize colorama
init(autoreset=True)

# Version of the script
VERSION = "1.4"

# Global multiprocessing lock for safe writing
lock = multiprocessing.Lock()

def print_logo():
    logo = rf"""
 _  __          _   _             _            
| |/ /___ _   _| | | |_   _ _ __ | |_ ___ _ __    
| ' // _ | | | | |_| | | | | '_ \| __/ _ | '__| __
| . |  __| |_| |  _  | |_| | | | | ||  __| |   /o \_____
|_|\_\___|\__, |_| |_|\__,_|_| |_|\__\___|_|   \__/-="="
          |___/                                
                                         @gitblanc, v{VERSION}
    """
    print(Fore.MAGENTA + logo + Style.RESET_ALL)

def export_to_pdf(txt_file, pdf_file, search_term, logo_path=None):
    """
    Converts a text file to a formatted PDF, highlighting the search term in red.
    """
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter
    y_position = height - 50  # Start below header

    # Add header
    add_header(c, width, height)

    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)  # Ensure initial text color is black
    
    # Add the logo if provided
    if logo_path and os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 50, height - 100, width=70, height=70, mask='auto')

    # Add report title and date
    c.drawString(50, height - 120, f"Search Report for \"{search_term}\"- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.line(50, height - 130, width - 50, height - 130)  # Add separator line

    y_position = height - 150  # Adjust for content

    c.setFont("Helvetica", 10)
    
    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            clean_line = remove_ansi_codes(line).strip()  # Remove ANSI codes

            # If too low, start a new page
            if y_position < 50:
                c.showPage()
                add_header(c, width, height)  # Add header on the new page
                c.setFont("Helvetica", 10)
                c.setFillColor(colors.black)  # Ensure initial text color is black
                y_position = height - 50

            # Highlight search term in red
            if search_term in clean_line:
                parts = clean_line.split(search_term)
                x_position = 50
                for i, part in enumerate(parts):
                    c.drawString(x_position, y_position, part)
                    x_position += c.stringWidth(part, "Helvetica", 10)
                    
                    if i < len(parts) - 1:
                        c.setFillColor(colors.red)
                        c.drawString(x_position, y_position, search_term)
                        c.setFillColor(colors.black)
                        x_position += c.stringWidth(search_term, "Helvetica", 10)
            else:
                c.drawString(50, y_position, clean_line)
            
            y_position -= 15  # Line spacing
    
    c.save()
    print(f"{Fore.GREEN}PDF saved at: {pdf_file}{Style.RESET_ALL}")

def add_header(c, width, height):
    """
    Adds the header text "KeyHunter vX.X by gitblanc" to the top-right corner of each page.
    """
    header_text = f"KeyHunter v{VERSION} by gitblanc"
    c.setFont("Helvetica", 10)  # Fuente más pequeña
    c.setFillColor(grey)  # Color gris
    text_width = c.stringWidth(header_text, "Helvetica", 10)  # Obtener el ancho del texto
    padding = 20  # Margen desde el borde derecho

    # Dibujar el texto en la parte superior derecha
    c.drawString(width - text_width - padding, height - 20, header_text)

def remove_ansi_codes(text):
    """
    Removes ANSI escape codes from a given text.
    
    Args:
        text (str): The input text containing ANSI codes.
        
    Returns:
        str: Cleaned text without ANSI codes.
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def print_with_timestamp(message, color=Fore.RESET):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{color}[{timestamp}] {message}{Style.RESET_ALL}"
    print(formatted_message)

def search_in_file(file_path, search_term, output_file, block_size=1024 * 1024, verbose=False):
    search_term_bytes = search_term.encode()
    line_number = 0
    occurrences_count = 0  

    with open(file_path, 'rb') as f:
        size = os.path.getsize(file_path)
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            pbar = tqdm(total=size, unit='B', unit_scale=True, desc=f'Searching in {os.path.basename(file_path)}', leave=False)

            buffer = b""
            offset = 0

            while offset < size:
                chunk_size = min(block_size, size - offset)
                chunk = mm[offset:offset + chunk_size]
                buffer += chunk
                lines = buffer.split(b'\n')
                buffer = lines.pop()  

                for line in lines:
                    line_number += 1
                    if search_term_bytes in line:
                        occurrences_count += 1
                        line_decoded = line.decode(errors='ignore')
                        
                        # Highlight search term in console
                        highlighted_line = line_decoded.replace(
                            search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}"
                        )

                        # Console output with colors
                        occurrence_message = f"{highlighted_line}"
                        occurrence_message_verbose = f"{highlighted_line} \n [{Fore.YELLOW}Found at {file_path}{Style.RESET_ALL}] [{Fore.YELLOW}Line {line_number}{Style.RESET_ALL}]"

                        # Save clean version to file
                        clean_message = remove_ansi_codes(occurrence_message)
                        clean_message_verbose = remove_ansi_codes(f"{highlighted_line} [Found at {file_path}] [Line {line_number}]\n")

                        with lock:
                            with open(output_file, 'a', encoding='utf-8') as out_f:
                                if verbose:
                                    out_f.write(f"{clean_message_verbose}\n")
                                else:
                                    out_f.write(f"{clean_message}\n")

                        tqdm.write(occurrence_message_verbose if verbose else occurrence_message)

                pbar.update(chunk_size)
                offset += chunk_size

            if buffer and search_term_bytes in buffer:
                line_number += 1
                occurrences_count += 1
                last_line = buffer.decode(errors='ignore')
                highlighted_last_line = last_line.replace(
                        search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}"
                    )
                occurrence_message = f"{highlighted_last_line}"
                occurrence_message_verbose = f"[{Fore.YELLOW}Line {line_number}{Style.RESET_ALL}] {highlighted_last_line} [{Fore.YELLOW}Found at {file_path}{Style.RESET_ALL}]"

                with lock:
                    with open(output_file, 'a', encoding='utf-8') as out_f:
                        if verbose:
                            out_f.write(f"{occurrence_message_verbose}\n")
                        else:
                            out_f.write(f"{occurrence_message}\n")

                if verbose:
                    tqdm.write(f"{occurrence_message_verbose}")
                else:
                    tqdm.write(f"{occurrence_message}")

            pbar.close()

            if verbose:
                print(f"{Fore.GREEN}Matches found in {file_path}: {occurrences_count}{Style.RESET_ALL}")

def process_file(args):
    file_path, search_term, output_file, block_size, verbose = args
    search_in_file(file_path, search_term, output_file, block_size, verbose)
    

def split_wordlist(file_path, max_size_mb=100):
    """
    Splits a large file into smaller chunks stored in a new folder with a structured naming convention.

    Args:
        file_path (str): Path to the input file.
        max_size_mb (int): Maximum size of each split file in MB. Default is 100MB.

    Returns:
        list: List of created file parts with their paths.
    """
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    file_size = os.path.getsize(file_path)  # Get the total file size
    num_parts = (file_size + max_size_bytes - 1) // max_size_bytes  # Compute minimum number of parts
    num_digits = len(str(num_parts))  # Determine padding for filenames

    # Create output directory: filename_part/
    base_name = os.path.basename(file_path)
    output_folder = f"{base_name}_part"
    os.makedirs(output_folder, exist_ok=True)  # Ensure the directory exists

    part_files = []

    with open(file_path, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        print(f"Splitting '{file_path}' ({file_size} bytes) into {num_parts} parts of ~{max_size_bytes} bytes each.")
        pbar = tqdm(total=file_size, unit='B', unit_scale=True, desc="Splitting")

        for i in range(num_parts):
            part_name = os.path.join(output_folder, f"{base_name}_{str(i+1).zfill(num_digits)}")
            with open(part_name, 'wb') as part:
                start = i * max_size_bytes
                end = min(start + max_size_bytes, file_size)
                part.write(mm[start:end])  # Efficient writing using mmap
                pbar.update(end - start)
            
            part_files.append(part_name)

        pbar.close()

    print(f"Files saved in: {output_folder}")


# CLI commands configuration
parser = argparse.ArgumentParser(description="Search for a password inside a [massive] wordlist.")
parser.add_argument("file_path", help="The path to the wordlist.")
parser.add_argument("search_term", nargs="?", help="The password (or part of the password) to search for.")
parser.add_argument("-b", "--block_size", type=int, default=1024*1024, help="Reading block size in bytes (default 1 MB).")
parser.add_argument("--output", type=str, help="Specify output file name. Default: keyhunter_results/result_<date>.txt")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose.")
parser.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 4), help="Number of parallel workers (default: CPU count - 4).")
parser.add_argument("--pdf", action="store_true", help="Export results to a PDF file.")

parser.add_argument("-s", "--split", action="store_true", help="Split a wordlist in multiple small parts.")
parser.add_argument("--max_size", type=int, default=100, help="Max size per split file in MB (default: 100MB).") # Max size Github allows

args = parser.parse_args()

print_logo()

# Ensure output directory exists
output_dir = "keyhunter_results"
os.makedirs(output_dir, exist_ok=True)
# Default output
output_file = args.output if args.output else os.path.join(output_dir, f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")


# Determinar si el input es un solo archivo o un directorio
if os.path.isdir(args.file_path):
    files = []
    for root, _, filenames in os.walk(args.file_path):
        for filename in filenames:
            if filename.lower().endswith(('.csv', '.txt')):  # Filtra solo .csv y .txt
                file_path = os.path.join(root, filename)
                files.append(file_path)
else:
    files = [args.file_path] if args.file_path.lower().endswith(('.csv', '.txt')) else []

# Si no hay archivos válidos, mostrar error y salir
if not files:
    print(f"{Fore.RED}Error: No hay archivos .csv o .txt para procesar en '{args.file_path}'{Style.RESET_ALL}")
    exit(1)

# Procesar archivos en paralelo
with multiprocessing.Pool(args.workers) as pool:
    pool.map(process_file, [(file, args.search_term, output_file, args.block_size, args.verbose) for file in files])

print(f"{Fore.BLUE}Results saved at: {output_file}{Style.RESET_ALL}")

if args.pdf:
    pdf_output_file = output_file.replace(".txt", ".pdf")

    # Get the absolute path of the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path for the logo
    logo_path = os.path.join(script_dir, "img", "logo.png")
    # Call the function using the dynamically resolved path
    export_to_pdf(output_file, pdf_output_file, args.search_term, logo_path=logo_path)

