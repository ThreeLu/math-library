# Common tasks. Quarto may live in ~/.local/quarto/bin (installed without sudo).
export PATH := $(HOME)/.local/quarto/bin:$(PATH)

.PHONY: site fast preview clean

# Compile all LaTeX, convert, and render the site into site/_site/
site:
	python3 tools/build.py --render

# Same, but reuse existing build/*.aux and PDFs (after you compiled yourself)
fast:
	python3 tools/build.py --no-latex --render

# Live preview at http://localhost:4200 (rebuild with `make fast` after editing .tex)
preview:
	python3 tools/build.py --no-latex
	cd site && quarto preview --port 4200

clean:
	rm -rf site/_site site/books site/.quarto site/_quarto.yml site/index.qmd
