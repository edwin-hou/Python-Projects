import math
def move(n, post_from, post_to, post_via):
    if n < 1:
        return
    # Move n-1 pieces "from post" to "via post":
    move(n-1, post_from, post_via, post_to)
    # Move the nth piece "from post" to "to post":
    print("Moving piece [%s] from [%s] to [%s]" % (n, post_from, post_to))
    # Move n-1 pieces "via post" to "to post":
    move(n-1, post_via, post_to, post_from)
