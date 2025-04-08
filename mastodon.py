"""
Transaction simulations for Mastodon: https://github.com/mastodon/mastodon/tree/main
Uses PostgreSQL
Analyzed in Tang et al. Ad Hoc Transactions in Web Applications: The Good, 
the Bad, and the Ugly: https://ipads.se.sjtu.edu.cn/_media/publications/concerto-sigmod22.pdf

### EXAMPLE OUTPUT ###

---
"""

import numpy as np
from transaction import Transaction

#################################
####   Simulator functions   ####
#################################

### Transaction 1 ###
def increment_counter_cache(poll_id, choice):
    """
    Purpose: increment poll cache counter by 1
    Source code: https://github.com/mastodon/mastodon/blob/main/app/models/poll_vote.rb#L34C3-L41C4

    Pseudocode:
    In: poll

    try:
        UPDATE poll SET cached_tallies = cached_tallies + 1 WHERE poll_id=poll_id AND choice=choice
    except:
        SELECT * FROM poll WHERE poll_id=poll_id
        UPDATE poll SET cached_tallies = cached_tallies + 1 WHERE poll_id=poll_id AND choice=choice

    The exception occurs when there is a synchronization error
    """
    t = Transaction()
    t.append_write(f"cached_tallies({poll_id}, {choice})")
    err = np.random.choice(2)
    if err:
        t.append_read(f"poll({poll_id})")
        t.append_write(f"cached_tallies({poll_id}, {choice})")
    return t

def increment_counter_cache_sim(num_transactions: int):
    """
    Example output:

    ['w-cached_tallies(84, 15)', 'r-poll(84)', 'w-cached_tallies(84, 15)']
    ['w-cached_tallies(61, 31)', 'r-poll(61)', 'w-cached_tallies(61, 31)']
    ['w-cached_tallies(81, 95)']
    ['w-cached_tallies(188, 42)', 'r-poll(188)', 'w-cached_tallies(188, 42)']
    ['w-cached_tallies(56, 53)']
    """
    for _ in range(num_transactions):
        t = increment_counter_cache(np.random.choice(200), np.random.choice(100))
        print(t)

#######################
####   Simulation  ####
#######################

def main():
    """
    Generate Mastodon transaction traces
    """
    num_transactions_1 = 5

    # Extra space for formatting
    print()

    # Transaction 1
    print("Generating Mastodon increment counter cache simulation")
    increment_counter_cache_sim(num_transactions_1)
    print()

if __name__ == "__main__":
    main()