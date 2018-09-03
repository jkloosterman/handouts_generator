#!/usr/bin/python3

import sys
import os
import json
from PyPDF2 import PdfFileWriter, PdfFileReader

def split_pdf(pdf, pdf_pages):
    inputpdf = PdfFileReader(open(pdf, "rb"))
    
    for i in range(inputpdf.numPages):
        output = PdfFileWriter()
        output.addPage(inputpdf.getPage(i))
        with open("%s/slide_%d.pdf" % (pdf_pages, i), "wb") as outputStream:
            output.write(outputStream)

    return inputpdf.numPages

class HandoutGenerator(object):
    def __init__(self, folder):
        self.fp = open(folder + "/handouts.tex", "w")
        self.folder = folder
        self.slides = []
        self.write_header()
        
    def write_header(self):
        self.fp.write(r"""
        \documentclass[12pt]{article}
        \usepackage[left=1cm, right=1cm, top=1cm, bottom=2cm]{geometry}
        \usepackage{graphicx}
        \usepackage{palatino}
        
        \pagestyle{plain}
        \begin{document}
        \noindent
        """)

    # sizes are "thumbnail", "normal", "large"
    def add_slide(self, pdf_file, size):
        self.slides.append({ "pdf": pdf_file, "size": size })

    def emit_pages(self):
        i = 0
        while i < len(self.slides):
            # Just emit each type, but if there is a run of thumbnails, emit them
            # all, then a newline
            if self.slides[i]["size"] == "thumbnail":
#                self.fp.write("{\n")
                num_thumbnails = 0
                while self.slides[i]["size"] == "thumbnail" and i < len(self.slides):
                     self.emit_thumbnail(self.slides[i]["pdf"])
                     if num_thumbnails % 2 == 1:
                         self.fp.write("\\vspace{.5in}\n")
                     else:
                         self.fp.write("\\hfill\n")
                         
                     num_thumbnails += 1
                     i += 1

                if num_thumbnails % 2 == 1:
                    self.fp.write(r"\includegraphics[width=3.5in]{lines.pdf}")
                     
                self.fp.write("\\vspace{.5in}\n")

                i -= 1
            elif self.slides[i]["size"] == "normal":
                self.emit_normal(self.slides[i]["pdf"])
            elif self.slides[i]["size"] == "large":
                self.emit_large(self.slides[i]["pdf"])
            else:
                assert("Unknown page type")

            i += 1

    def emit_thumbnail(self, pdf_file):
        self.fp.write(
            "\\fbox{\\includegraphics[width=3.5in]{%s}}" % (pdf_file,))
        
    def emit_normal(self, pdf_file):
        self.fp.write(
            r"""\fbox{\includegraphics[width=3.5in]{%s}}
            \hfill
            \includegraphics[width=3.5in]{lines.pdf}
            \vspace{.5in} \\
            """ % (pdf_file,))

    def emit_large(self, pdf_file):
        self.fp.write(
            r"""\centering {
            \hspace*{\fill}
            \fbox{\includegraphics[width=6.5in]{%s}}
            \hspace*{\fill}
            \vspace{1in} \\
            }""" % (pdf_file,))        

    def close(self):
        self.fp.write("\\end{document}\n")
        self.fp.close()

    def create_pdf(self):
        saved_path = os.getcwd()
        os.chdir(self.folder)
        os.system("pdflatex handouts.tex")
        os.system("mv handouts.pdf handouts.orig.pdf")
        os.system("gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=handouts.pdf handouts.orig.pdf")
        os.chdir(saved_path)
        
def main():
    json_filename = sys.argv[1]

    with open(json_filename, "r") as fp:
        config = json.load(fp)

    pdf = config["pdf"]
    folder = config["folder"]

    # create folder
    os.mkdir(folder)

    # create page pdfs folder
    pdf_pages = folder + "/pdf_pages/"
    os.mkdir(pdf_pages)
    os.system("cp lines.pdf %s" % (folder,))
    
    # split the PDF into individual pages
    num_pages = split_pdf(pdf, pdf_pages)

    # Note slides are 1-indexed!
    thumbnails = set(config["thumbnail"])
    normals = set(config["normal"])
    larges = set(config["large"])
    
    generator = HandoutGenerator(folder)
    for i in range(num_pages):
        page = i + 1

        pdf = "pdf_pages/slide_%d.pdf" % (i,)
        if page in thumbnails:
            generator.add_slide(pdf, "thumbnail")
        elif page in normals:
            generator.add_slide(pdf, "normal")
        elif page in larges:
            generator.add_slide(pdf, "large")

    generator.emit_pages()
    generator.close()
    generator.create_pdf()
            
main()
