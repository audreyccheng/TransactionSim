"""
Transaction simulations for Mastodon: https://github.com/mastodon/mastodon/tree/main
Uses PostgreSQL
Analyzed in Tang et al. Ad Hoc Transactions in Web Applications: The Good, 
the Bad, and the Ugly: https://ipads.se.sjtu.edu.cn/_media/publications/concerto-sigmod22.pdf

### EXAMPLE OUTPUT ###

Generating Mastodon increment counter cache simulation
['w-cached_tallies(173, 27)', 'r-poll(173)', 'w-cached_tallies(173, 27)']
['w-cached_tallies(114, 71)', 'r-poll(114)', 'w-cached_tallies(114, 71)']
['w-cached_tallies(128, 62)', 'r-poll(128)', 'w-cached_tallies(128, 62)']
['w-cached_tallies(106, 36)', 'r-poll(106)', 'w-cached_tallies(106, 36)']
['w-cached_tallies(42, 52)', 'r-poll(42)', 'w-cached_tallies(42, 52)']

Generating Mastodon create account simulation
['w-account(841)']
['w-account(577)']
['w-account(366)']
['w-account(327)']
['w-account(847)']
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
    Purpose: increment poll counter cache
    Source code: https://github.com/mastodon/mastodon/blob/main/app/models/poll_vote.rb#L34C3-L41C4

    Pseudocode:
    In: poll

    TRANSACTION START
    try:
        UPDATE poll SET cached_tallies = cached_tallies + 1 WHERE poll_id=poll_id AND choice=choice
    except:
        SELECT * FROM poll WHERE poll_id=poll_id
        UPDATE poll SET cached_tallies = cached_tallies + 1 WHERE poll_id=poll_id AND choice=choice
    TRANSACTION COMMIT

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

### Transaction 2 ###
def create_account():
    """
    Purpose: create an account
    Source code: https://github.com/mastodon/mastodon/blob/main/app/services/activitypub/process_account_service.rb#L72C3-L85C6

    Pseudocode:
    In: accounts

    account = Account()
    # Set account attributes
    TRANSACTION START
    INSERT INTO accounts VALUES account
    TRANSACTION COMMIT

    We represent every account as an integer between 1 and 1000.
    """
    t = Transaction()
    account_id = np.random.choice(1000)
    t.append_write(f"account({account_id})")
    return t

def create_account_sim(num_transactions: int):
    """
    Example output:

    ['w-account(841)']
    ['w-account(577)']
    ['w-account(366)']
    ['w-account(327)']
    ['w-account(847)']
    """
    for _ in range(num_transactions):
        t = create_account()
        print(t)

#######################
####   Simulation  ####
#######################

def main():
    """
    Generate Mastodon transaction traces
    """
    num_transactions_1 = 5
    num_transactions_2 = 5

    # Extra space for formatting
    print()

    # Transaction 1
    print("Generating Mastodon increment counter cache simulation")
    increment_counter_cache_sim(num_transactions_1)
    print()

    # Transaction 2
    print("Generating Mastodon create account simulation")
    create_account_sim(num_transactions_2)
    print()

if __name__ == "__main__":
    main()