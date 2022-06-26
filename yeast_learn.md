# Learning Yeast

To learn how and why Yeast wor the way it does, the best way is to Do It Yourself.
Take your favorite programing language and implement your version of Yeast.

Doing this you will have to fiddle with the details of the language itself and the interaction a user can have with the system.
You will have to make choices, which could be different than the one made here (there exist more than one type of yeast !), but you will understand the tradeoffs.
Along the way you will gain a deep understanding of how programming and computer work and the kind of interactions that are possible with the users and their environment

# Writing Yeast

## Step 1: Unlambda

Take your favorite language and implement [Unlambda](http://www.madore.org/~david/programs/unlambda)

One can consider a few different levels of complexity of the implementation:
- continuations: one argument functions, supporting currying
- functions: multi-argument fonctions
- closures: multi-argument fonctions with environment captured

Interestingly these can be built one on top of the other ... TODO !
However, the implementation in your language of choice can be simplify when carefully choosing the implementation of each of these concepts.



You will soon feel the need to see the stack contents pretty often.
Luckily we planned from the beginning to design an inteeractive REPL.


## Step 2: Unlambda in Forth

Take Forth and implement [Unlambda](http://www.madore.org/~david/programs/unlambda) again, close to the machine.


## Step 3: Choose the best way to implement Unlambda

Choose a minimalist host language, and use it to implement [Unlambda](http://www.madore.org/~david/programs/unlambda), again.
You might decide to write your own Forth System from scratch while you are at it...

