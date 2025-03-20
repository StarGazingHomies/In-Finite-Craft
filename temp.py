import random


def generate_cons_expr(bigit_list):
    return f"cons_bigit({bigit_list[-1]}, {generate_cons_expr(bigit_list[:-1])})" if bigit_list else "NULL"

def generate_bigit_list(n: int):
    if n == 0:
        return []
    s = str(n)
    if len(s) % 4:
        s = "0" * (4 - len(s) % 4) + s
    for a, b, c, d in zip(*[iter(s)]*4):
        yield int(f"{a}{b}{c}{d}")

print(generate_cons_expr(list(generate_bigit_list(1234567890))))

# results = []
# for i in range(1000):
#     a = random.randint(0, 10**(i//10))
#     b = random.randint(0, 10**(i//10))
#     a_expr = generate_cons_expr(list(generate_bigit_list(a)))
#     b_expr = generate_cons_expr(list(generate_bigit_list(b)))
#     print(f"""
# struct Node* a_expr{i} = {a_expr};
# struct Node* b_expr{i} = {b_expr};
# print_and_free(mult(a_expr{i}, b_expr{i}));
# free_num(b_expr{i});
# free_num(a_expr{i});""")
#     results.append(a * b)
#
# print("\n".join([str(i) for i in results]))


a = 100000000000000000000000000012345
b = 10000000000000000000000000000000000067890
a_expr = generate_cons_expr(list(generate_bigit_list(a)))
b_expr = generate_cons_expr(list(generate_bigit_list(b)))
i = 0
print(f"""
struct Node* a_expr{i} = {a_expr};
struct Node* b_expr{i} = {b_expr};
print_and_free(add(a_expr{i}, b_expr{i}));
free_num(b_expr{i});
free_num(a_expr{i});""")

print(a + b)
