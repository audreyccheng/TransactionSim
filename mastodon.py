"""
Transaction simulations for Mastodon: https://github.com/mastodon/mastodon/tree/main
Uses PostgreSQL
Analyzed in Tang et al. Ad Hoc Transactions in Web Applications: The Good, 
the Bad, and the Ugly: https://ipads.se.sjtu.edu.cn/_media/publications/concerto-sigmod22.pdf

### EXAMPLE OUTPUT ###

Generating Mastodon increment counter cache simulation
['w-cached_tallies(92, 66)', 'r-poll(92)', 'w-cached_tallies(92, 66)']
['w-cached_tallies(98, 24)']
['w-cached_tallies(79, 16)']
['w-cached_tallies(17, 93)']
['w-cached_tallies(32, 66)']

Generating Mastodon create account simulation
['w-account(10)']
['w-account(860)']
['w-account(338)']
['w-account(380)']
['w-account(550)']

Generating Mastodon update account simulation
['w-account(513)']
['w-account(308)']
['w-account(948)']
['w-account(848)']
['w-account(835)']

Generating Mastodon call simulation
['w-[account(138), choice(9)]', 'w-[account(138), choice(0)]']
['w-[account(796), choice(6)]', 'w-[account(796), choice(7)]', 'w-[account(796), choice(6)]']
['w-[account(386), choice(9)]', 'w-[account(386), choice(7)]', 'w-[account(386), choice(3)]']
['w-[account(231), choice(1)]', 'w-[account(231), choice(3)]']
['w-[account(837), choice(9)]', 'w-[account(837), choice(9)]', 'w-[account(837), choice(0)]']
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

### Transaction 3 ###
def update_account():
    """
    Purpose: update an account
    Source code: https://github.com/mastodon/mastodon/blob/main/app/services/activitypub/process_account_service.rb#L87C3-L98C6 

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

def update_account_sim(num_transactions: int):
    """
    Example output:

    ['w-account(937)']
    ['w-account(316)']
    ['w-account(91)']
    ['w-account(83)']
    ['w-account(563)']
    """
    for _ in range(num_transactions):
        t = create_account()
        print(t)

### Transaction 4 ###
def call(account, poll, choices):
    """
    Purpose: update vote totals
    Source code: https://github.com/mastodon/mastodon/blob/main/app/services/vote_service.rb#L9C1-L43C10

    Pseudocode:
    # Update values and acquire lock
    TRANSACTION START
    for choice in choices:
        INSERT INTO poll VALUES (account, choice)
    TRANSACTION COMMIT
    # Update values and release lock
    """
    t = Transaction()
    for choice in choices:
        t.append_write(f"[account({account}), choice({choice})]")
    return t

def call_sim(num_transactions: int):
    """
    Example output:

    ['w-[account(138), choice(9)]', 'w-[account(138), choice(0)]']
    ['w-[account(796), choice(6)]', 'w-[account(796), choice(7)]', 'w-[account(796), choice(6)]']
    ['w-[account(386), choice(9)]', 'w-[account(386), choice(7)]', 'w-[account(386), choice(3)]']
    ['w-[account(231), choice(1)]', 'w-[account(231), choice(3)]']
    ['w-[account(837), choice(9)]', 'w-[account(837), choice(9)]', 'w-[account(837), choice(0)]']
    """
    for _ in range(num_transactions):
        t = call(np.random.choice(1000), None, [np.random.choice(10) for _ in range(int(round(np.random.normal(3, 1))))])
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
    num_transactions_3 = 5
    num_transactions_4 = 5
    # num_transactions_5 = 5
    # num_transactions_6 = 5
    # num_transactions_7 = 5 

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

    # Transaction 3
    print("Generating Mastodon update account simulation")
    update_account_sim(num_transactions_3)
    print()

    # Transaction 4
    print("Generating Mastodon call simulation")
    call_sim(num_transactions_4)
    print()
    
if __name__ == "__main__":
    main()