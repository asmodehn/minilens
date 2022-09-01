# Brain dump

Trying to see the categorical structure of user interactions, 
as well as user's representation of operational semantics,
in no particular order:

- poly (container) structure for the stack semantics
- poly (container) structure for the window (tiling / embedding) behaviour
- update monad for input/output flow on a character cell / word / line, etc. (lower levels of poly structure of windows ?)
- lens/optics structure in input/output user interactions (maybe evolutive auto complete ?)
- bimonadic structure for input (here via iterator / stream), at different levels (chars, words, lines ...)


# Design notes:
File is not the principal / main unit of code now. Instead we rely on the REPL first, meaning the terminal is...
-> interactivity is key and interaction reification comes before "ex nihilo" language semantics.