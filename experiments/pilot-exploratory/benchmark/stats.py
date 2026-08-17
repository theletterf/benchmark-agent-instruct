import math


def wilson(k, n):
    if not n: return [0.0, 0.0]
    p = k / n; z = 1.96; denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    delta = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [round(max(0, centre - delta) * 100, 2), round(min(1, centre + delta) * 100, 2)]


def log_comb(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher(a, b, c, d):
    n = a + b + c + d; row = a + b; col = a + c
    low, high = max(0, row - (n - col)), min(row, col)
    observed = math.exp(log_comb(col, a) + log_comb(n - col, row - a) - log_comb(n, row))
    return round(min(1.0, sum(math.exp(log_comb(col, x) + log_comb(n - col, row - x) - log_comb(n, row)) for x in range(low, high + 1) if math.exp(log_comb(col, x) + log_comb(n - col, row - x) - log_comb(n, row)) <= observed + 1e-12)), 6)
