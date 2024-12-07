import os
import subprocess
import pypandoc

def preprocess_fb2(file_path):
    """Preprocess .fb2 files to fix LaTeX errors."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Fix malformed lists and quotes
    content = content.replace('<list></list>', '')
    content = content.replace('<item></item>', '')
    content = content.replace('<quote></quote>', '')

    # Save the modified content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def convert_mobi_to_epub(mobi_file, epub_file):
    """Convert .mobi to .epub using Calibre."""
    try:
        subprocess.run(["ebook-convert", mobi_file, epub_file], check=True)
        print(f"Converted {mobi_file} to {epub_file}.")
    except Exception as e:
        print(f"Error converting {mobi_file} to EPUB: {e}")

def convert_djvu_to_pdf(djvu_file, pdf_file):
    """Convert DJVU to PDF using djvups and ps2pdf."""
    try:
        # Step 1: Convert DJVU to PostScript (.ps) file
        ps_file = djvu_file.replace(".djvu", ".ps")
        subprocess.run(["djvups", djvu_file, ps_file], check=True)
        
        # Step 2: Convert PostScript (.ps) to PDF
        subprocess.run(["ps2pdf", ps_file, pdf_file], check=True)
        
        # Step 3: Clean up intermediate PostScript file
        os.remove(ps_file)
        print(f"Successfully converted {djvu_file} to {pdf_file}.")
    except FileNotFoundError as e:
        print(f"Required tool not found: {e}. Please install djvulibre and ghostscript.")
    except Exception as e:
        print(f"Error converting {djvu_file} to PDF: {e}")

def delete_source_file(file_path):
    """Delete the source file."""
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")

def convert_to_pdf(folder_path):
    """Convert all supported files in a folder to PDF."""
    template_path = 'templates/custom-template.tex'

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isdir(file_path):
            continue
        
        output_file = os.path.splitext(file_path)[0] + ".pdf"

        if file_name.lower().endswith(".pdf"):
            print(f"Already PDF: {file_name}")
            continue

        try:
            if file_name.lower().endswith(".mobi"):
                # Convert MOBI to EPUB
                epub_file = file_path.replace(".mobi", ".epub")
                convert_mobi_to_epub(file_path, epub_file)
                file_path = epub_file

            if file_name.lower().endswith(".fb2"):
                preprocess_fb2(file_path)  # Preprocess FB2 files

            if file_name.lower().endswith((".fb2", ".epub", ".txt")):
                # Convert text-based files
                pypandoc.convert_file(
                    file_path,
                    'pdf',
                    format='markdown' if file_name.lower().endswith(".txt") else None,
                    outputfile=output_file,
                    extra_args=[
                        '--pdf-engine=xelatex',
                        f'--template={template_path}'
                    ]
                )
                print(f"Converted {file_name} to PDF.")
                delete_source_file(file_path)

            elif file_name.lower().endswith(".djvu"):
                convert_djvu_to_pdf(file_path, output_file)
                delete_source_file(file_path)

            else:
                print(f"Unsupported format: {file_name}")
                delete_source_file(file_path)

        except Exception as e:
            print(f"Error processing {file_name}: {e}")
            delete_source_file(file_path)

# Define folder path
folder_path = ''
convert_to_pdf(folder_path)
