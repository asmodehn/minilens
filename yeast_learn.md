# Learning Yeast

To learn how and why Yeast wor the way it does, the best way is to Do It Yourself.
Take your favorite programing language and implement your version of Yeast.

Doing this you will have to fiddle with the details of the language itself and the interaction a user can have with the system.
You will have to make choices, which could be different than the one made here (there exist more than one type of yeast !), but you will understand the tradeoffs.
Along the way you will gain a deep understanding of how programming and computer work and the kind of interactions that are possible with the users and their environment

# Writing Yeast

## Step 1: Unlambda

Take your favorite language and implement [Unlambda](http://www.madore.org/~david/programs/unlambda)

Beside the usual combinators (IKWCB -in order- might be simpler to implement than SKI at first), for which rules are easily found and implementable, one tricky part seem to be "`" which is effectively a structural character (representing "(" and ")" implicitely) along with a call/cc semantics: it evaluates the next combinator.

If implementing it in a functional language with continuation, mapping unlambda semantics to the host language might relatively straight forward.

However, to implement it in an imperative language (as an appetizer before rewriting it in Forth in Step 2), it seems useful to consider implementing continuations as closures in the host language, as a form of "ideal compilation".
This makes the interpreter easier to write in an imperative settings, while keeping in mind this underlying CPS structure of our interpreted unlambda code.
A good resource on how to understand and implement continuations is [Categorical-Structure-of-Continuation-Passing-Style from Hayo-Thielecke](https://www.researchgate.net/profile/Hayo-Thielecke/publication/2869296_Categorical_Structure_of_Continuation_Passing_Style/links/53e12db90cf2235f352738e3/Categorical-Structure-of-Continuation-Passing-Style.pdf?origin=publication_detail)

With the same idea of preparing for a very imperative minimal implementation, relying on stacks instead of function params and returns might expose some interesting structure.
Therefore each partial application consumes the input to produce a continuation Just-In-Time (no waiting to have all params)
However this makes it harder to test, and should probably be implemented after getting a simpler version working...

The implementation in your language of choice can be simplified when carefully choosing the implementation of the main concepts to match the host language.
Depending if this is a final goal, or just a stepping stone for another implementation (as in this document), the choices you make will be different.

While debugging interactively your implementation, you will soon feel the need to see the stack contents pretty often.
Luckily we planned from the beginning to design an interactive REPL.

Keeping the unnlambda approach of "one character at a time", we can see there are 3 levels of interaction/implementations:
- char by char continuation, with single input, single output
- char by char continuation, multiple input (closures), multiple output (generators)
- string by string continuation, multiple input, multiple output

The latter one is the only one necessary to consider when implementing unlambda in a high level language.
However to be able to implement it in a lower level language, we feel it necessary to deep dive into the simplest implementation...
Even when doing it in high level language, this forces us to expose the structure of the underlying computation, as well as the interaction when these are implemented along with their REPL.

Roadmap:
- Python prototype WIP
- Julia implementation with Visual Structure (leveraging CatLab) somehow integrated in the REPL.

## Step 2: Unlambda in Forth

Take Forth and implement [Unlambda](http://www.madore.org/~david/programs/unlambda) again, close to the machine.


## Step 3: Choose the best way to implement Unlambda

Choose a minimalist host language, and use it to implement [Unlambda](http://www.madore.org/~david/programs/unlambda), again.
You might decide to write your own Forth System from scratch while you are at it...

