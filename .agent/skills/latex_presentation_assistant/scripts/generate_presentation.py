
import argparse
import sys
import os

def read_template(filename):
    """Reads a template file from the examples directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    examples_dir = os.path.join(script_dir, "..", "examples")
    file_path = os.path.join(examples_dir, filename)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Template file '{filename}' not found in {examples_dir}.")
        return ""

def main():
    parser = argparse.ArgumentParser(description="Generate a LaTeX Beamer presentation from templates.")
    parser.add_argument("--week", required=True, help="Week number (e.g., 1)")
    parser.add_argument("--topic", required=True, help="Topic title (e.g., 'Introduction to Probability')")
    parser.add_argument("--output", help="Output filename (default: X-hafta.tex)")
    
    args = parser.parse_args()
    
    output_filename = args.output if args.output else f"{args.week}-hafta.tex"
    
    print(f"Generating presentation for Week {args.week}: {args.topic}...")
    
    # 1. Base Preamble
    content = []
    content.append("% !TeX program = xelatex")
    content.append("% !BIB program = biber")
    content.append(r"""\documentclass[light]{lutbeamer}
\usepackage{pgfpages}
\usepackage{ragged2e}
\usepackage{booktabs}
\usepackage{amssymb}
\usepackage{fontawesome5}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\addbibresource{refs.bib}
""")

    # 2. Metadata (from 01_baslangic_ve_kapak.tex)
    # We parse the template or just manually reconstruct the metadata block for safety/simplicity
    # but let's try to reuse the skill logic.
    t01 = read_template("01_baslangic_ve_kapak.tex")
    
    # Extract metadata block roughly or just inject our own
    content.append("% --- METADATA ---")
    content.append(r"\setdepartment{OSTİM TEKNİK ÜNİVERSİTESİ}")
    content.append(r"\institute[Yazılım Mühendisliği]{YAZILIM MÜHENDİSLİĞİ BÖLÜMÜ}")
    content.append(r"\author[Mühendislik Fakültesi]{\\Prof.~Dr.~Yalçın ATA,\\ ")
    content.append(r"Prof.~Dr.~Arif DEMİR,\\ Dr.~Öğr.~Üyesi~Muhammed ELMNEFİ,\\ Dr.~Öğr.~Üyesi~Haydar KILIÇ,\\ Dr.~Öğr.~Üyesi~Emel GÜVEN,\\ Dr.~Öğr.~Üyesi~Ufuk ASIL,\\ Öğr.~Gör.~Sema ÇİFTÇİ}")
    content.append(r"\title{MATH 204 -- Olasılık ve İstatistik}")
    content.append(f"\\subtitle{{Hafta {args.week}: {args.topic}}}")
    content.append(r"\date{2026 Bahar}")
    content.append("")
    
    # 3. AtBeginSection (from 02_sunum_akisi_ve_bolumler.tex)
    t02 = read_template("02_sunum_akisi_ve_bolumler.tex")
    # We want the AtBeginSection part. It's usually distinctive.
    if "\\AtBeginSection" in t02:
        start = t02.find("\\AtBeginSection")
        # simple heuristic: take until end of brace? No, it's nested.
        # Let's just hardcode the standard TOC logic for reliability, 
        # or grab the whole block if possible.
        # For now, I'll inject the standard TOC block defined in the skill file manually
        # to ensure it compiles correctly without complex parsing.
        content.append(r"""% --- TOC SETUP ---
\AtBeginSection[]{
  \begin{frame}{Sunum Akışı}
  \footnotesize
  \addtobeamertemplate{section in toc}{}{\vspace{0.15cm}}
  \begin{columns}[t]
    \column{.5\textwidth}
    \tableofcontents[sections={1-3},currentsection]
    \column{.5\textwidth}
    \tableofcontents[sections={4-10},currentsection]
  \end{columns}
  \end{frame}
}
""")
    
    content.append(r"\begin{document}")
    
    # 4. Cover (from 01)
    content.append(r"""
% --- COVER ---
\setbeamertemplate{navigation symbols}{}
\begin{frame}<article:0>[plain,noframenumbering]
    \begin{tikzpicture}[remember picture,overlay]
        \node[anchor=center, at=(current page.center), inner sep=0pt] {
            \includegraphics[width=\paperwidth, height=\paperheight]{logos/background_figure.jpg}
        };
        \node[anchor=center, at=(current page.center), inner sep=0pt] {
            \includegraphics[keepaspectratio, width=0.65\paperwidth, height=\paperheight]{logos/LUT-LOGO-WHITE-PNG.png}
        };
    \end{tikzpicture}
\end{frame}
\maketitle
""")

    # 5. Content Body
    content.append(f"\\section{{Giriş}}\n")
    content.append(r"\begin{frame}{Giriş}")
    content.append(f"Bu sunum {args.topic} konusunu ele almaktadır.")
    content.append(r"\end{frame}")
    
    # 6. Closing (from 03_kapanis_ve_kaynakca.tex)
    t03 = read_template("03_kapanis_ve_kaynakca.tex")
    content.append("\n% --- CLOSING ---")
    # Again, simple extraction is hard, better to provide standard closing.
    # But since the user wants to use the files, maybe I should just dump the file content? 
    # No, the files contain comments and are not just pure code.
    # For a robust tool, I'll implement the "Closing" logic directly but referencing the template style.
    
    content.append(r"""
\begin{frame}{Teşekkürler}
    \centering
    \Huge Teşekkürler!
\end{frame}

\begin{frame}[allowframebreaks]{Kaynaklar}
    \printbibliography
\end{frame}
""")
    
    content.append(r"\end{document}")
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
        
    print(f"Successfully created: {output_filename}")

if __name__ == "__main__":
    main()
