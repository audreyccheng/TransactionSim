"""
Transaction simulations for Mastodon: https://github.com/mastodon/mastodon/tree/main
Uses PostgreSQL
Analyzed in Tang et al. Ad Hoc Transactions in Web Applications: The Good, 
the Bad, and the Ugly: https://ipads.se.sjtu.edu.cn/_media/publications/concerto-sigmod22.pdf

### EXAMPLE OUTPUT ###

Generating Mastodon increment counter cache simulation
['w-cached_tallies(7, 82)']
['w-cached_tallies(169, 83)', 'r-poll(169)', 'w-cached_tallies(169, 83)']
['w-cached_tallies(102, 32)', 'r-poll(102)', 'w-cached_tallies(102, 32)']
['w-cached_tallies(36, 2)', 'r-poll(36)', 'w-cached_tallies(36, 2)']
['w-cached_tallies(191, 17)']

Generating Mastodon create account simulation
['w-account(516)']
['w-account(126)']
['w-account(36)']
['w-account(110)']
['w-account(93)']

Generating Mastodon update account simulation
['w-account(341)']
['w-account(992)']
['w-account(611)']
['w-account(58)']
['w-account(651)']

Generating Mastodon call simulation
['w-[account(106), choice(2)]', 'w-[account(106), choice(2)]']
['w-[account(109), choice(4)]', 'w-[account(109), choice(4)]', 'w-[account(109), choice(2)]']
['w-[account(342), choice(1)]', 'w-[account(342), choice(3)]']
['w-[account(44), choice(4)]', 'w-[account(44), choice(8)]']
['w-[account(535), choice(2)]', 'w-[account(535), choice(8)]', 'w-[account(535), choice(4)]', 'w-[account(535), choice(4)]']

Generating Mastodon process status simulation
['w-status(916)']
['w-status(459)']
['w-status(970)']
['w-status(683)']
['w-status(719)']

Generating Mastodon process emoji simulation
['w-emoji(60)']
['w-emoji(949)']
['w-emoji(173)']
['w-emoji(698)']
['w-emoji(620)']

Generating Mastodon create backup simulation
['w-backup(671)']
['w-backup(573)']
['w-backup(54)']
['w-backup(261)']
['w-backup(101)']
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

### Transaction 5 ###
def process_status():
    """
    Purpose: Update activity with new status
    Source code: https://github.com/mastodon/mastodon/blob/main/app/lib/activitypub/activity/create.rb#L42C3-L69C6

    Pseudocode:
    In: status, new_status

    # Miscellaneous processing
    TRANSACTION START
    INSERT INTO status VALUES new_status
    TRANSACTION COMMIT
    # Miscellaneous processing
    """
    t = Transaction()
    new_status = np.random.choice(1000)
    t.append_write(f"status({new_status})")
    return t

def process_status_sim(num_transactions: int):
    """
    Example output:

    ['w-status(585)']
    ['w-status(83)']
    ['w-status(660)']
    ['w-status(805)']
    ['w-status(315)']
    """
    for _ in range(num_transactions):
        t = process_status()
        print(t)

### Transaction 6 ###
def process_emoji(tag):
    """
    Purpose: Process emoji
    Source code: https://github.com/mastodon/mastodon/blob/main/app/lib/activitypub/activity/create.rb#L254C1-L272C6

    Pseudocode:
    In: emojis
    # Check if emoji already exists and return if so
    # Otherwise:
    emoji = new_emoji()
    TRANSACTION START
    INSERT INTO emojis VALUES emoji
    TRANSACTION COMMIT
    """
    emoji = np.random.choice(1000)
    t = Transaction()
    t.append_write(f"emoji({emoji})")
    return t

def process_emoji_sim(num_transactions: int):
    """
    Example output:

    ['w-emoji(204)']
    ['w-emoji(660)']
    ['w-emoji(872)']
    ['w-emoji(968)']
    ['w-emoji(699)']
    """
    for _ in range(num_transactions):
        t = process_emoji(None)
        print(t)

### Transaction 7 ###
def create_backup():
    """
    Purpose: Create a backup
    Source code: https://github.com/mastodon/mastodon/blob/main/app/controllers/settings/exports_controller.rb#L16C1-L27C6
    
    Pseudocode:
    In: backups
    backup = new_backup()
    TRANSACTION START
    INSERT INTO backups VALUES backup
    TRANSACTION COMMIT
    """
    t = Transaction()
    backup_id = np.random.choice(1000)
    t.append_write(f"backup({backup_id})")
    return t

def create_backup_sim(num_transactions: int):
    """
    Example output:

    ['w-backup(671)']
    ['w-backup(573)']
    ['w-backup(54)']
    ['w-backup(261)']
    ['w-backup(101)']
    """
    for _ in range(num_transactions):
        t = create_backup()
        print(t)

### Transaction 8 ###
def show_media_attachment(id):
    """
    Purpose: Show the media attachment with the given ID.
    Source code: https://github.com/mastodon/mastodon/blob/main/app/controllers/media_proxy_controller.rb#L18C3-L34C6

    Pseudocode:
    In: media_attachments

    lock_acquire(media_attachments)
    media_attachment = SELECT * FROM media_attachments WHERE id=id
    authorize(media_attachment)
    if media_attachment.needs_redownload:
        download_file(id)
        media_attachment.created_at = now
        INSERT INTO media_attachments VALUES media_attachment, id
    lock_release(media_attachments)
    return
    """
    t = Transaction()
    t.append_read(f"media_attachments({id})")
    needs_redownload = np.random.binomial(1, 0.2)
    if needs_redownload:
        t.append_write(f"media_attachments({id})")
    return t

def show_media_attachment_sim(num_transactions: int):
    """
    Example output:

    ['r-media_attachments(490)']
    ['r-media_attachments(160)', 'w-media_attachments(160)']
    ['r-media_attachments(137)']
    ['r-media_attachments(231)']
    ['r-media_attachments(611)']
    """
    for _ in range(num_transactions):
        t = show_media_attachment(np.random.choice(1000))
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
    num_transactions_5 = 5
    num_transactions_6 = 5
    num_transactions_7 = 5 
    num_transactions_8 = 5

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

    # Transaction 5
    print("Generating Mastodon process status simulation")
    process_status_sim(num_transactions_5)
    print()

    # Transaction 6
    print("Generating Mastodon process emoji simulation")
    process_emoji_sim(num_transactions_6)
    print()

    # Transaction 7
    print("Generating Mastodon create backup simulation")
    create_backup_sim(num_transactions_7)
    print()

    # Transaction 8
    print("Generating Mastodon show media attachment simulation")
    show_media_attachment_sim(num_transactions_8)
    print()

if __name__ == "__main__":
    main()