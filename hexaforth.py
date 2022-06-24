# Small prototype of a minimal 8-bit forth. to see how far we can take it

from prompt_toolkit import PromptSession


stack = []
words = {'+': lambda: stack.append(stack.pop() + stack.pop()),
         '.': lambda: print(f"{stack.pop()} ")
         }

# in python, relying on lambdas for apply implementation
# byteforth={
    # "S": lambda x,y,z, *t: "".join((x, z, "(", y, z, ")", t)),
    # "K": lambda x, y, *t: "".join((x, t))
# }

def eval_token(token: str):
    # execute    the    word if in dictionary
    try:
        words[token]()
        return True
    except KeyError as ke:  # not found in words dict
        # interpret as number otherwise const
        try:
            parsed = int(token)
        except Exception as e:
            # not a  number, complain
            print(str(e) + ' ?')
            return False
        else:
            # push the new token into the stack
            stack.append(parsed)
            return True


def eval_line(code: str):
    tokens = code.split(" ")
    for token in tokens:
        if not eval_token(token):
            break

    # while len(code) > 2:
    #     print(f"{code[0]} < {code[1:]}")
    #     code = byteforth[code[0]](*code[1:])
    # return code


def main():
    session = PromptSession()

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            eval_line(text)

    print('GoodBye!')


if __name__ == '__main__':
    main()


