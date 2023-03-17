#!/usr/bin/python
import model
import time
import numpy as np

num_iter = int(input("Enter the number of simulations to run: "))

scores = []

for i in range(num_iter):
    print(f'Game {i + 1}')
    start = time.time()
    score = model.main()
    end = time.time()
    print(f'Elapsed time: {end - start}')
    scores.append(score)

print(f'Average score: {np.mean(scores)}')
