
IMAGES = lists.svg vector1.svg vector2.svg maps.svg

.PHONY: all
all: slides.html

# Uses graphviz. `brew install graphviz` or `apt install graphviz
%.svg: %.dot
	dot -Tsvg $< > $@


slides.html: slides.md $(IMAGES)
	pandoc -t slidy -s $< -o $@ --metadata title="Pack - A Lisp in Python"

.PHONY: view
view: slides.html
	open -a "Google Chrome" $<
