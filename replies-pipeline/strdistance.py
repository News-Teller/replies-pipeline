from __future__ import division
import math

def jaro_sim(s_1, s_2):
    s_1_len = len(s_1)
    s_2_len = len(s_2)
 
    if s_1_len == 0 and s_2_len == 0:
        return 1
    
    matches = 0
    transpositions = 0

    match_distance = math.floor(max(s_1_len, s_2_len) // 2) - 1

    matches_1 = [False] * s_1_len
    matches_2 = [False] * s_2_len
 
    for i in range(s_1_len):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, s_2_len)
 
        for j in range(start, end):
            if matches_2[j]:
                continue
            if s_1[i] != s_2[j]:
                continue
            matches_1[i] = True
            matches_2[j] = True
            matches += 1
            break
 
    if matches == 0:
        return 0
 
    k = 0
    for i in range(s_1_len):
        if not matches_1[i]:
            continue
        while not matches_2[k]:
            k += 1
        if s_1[i] != s_2[k]:
            transpositions += 1
        k += 1
 
    return ((matches / s_1_len) + (matches / s_2_len) + ((matches - transpositions) / matches)) / 3
