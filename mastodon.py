"""
Transaction simulations for Mastodon: https://github.com/mastodon/mastodon/tree/main
Uses PostgreSQL
Analyzed in Tang et al. Ad Hoc Transactions in Web Applications: The Good,
the Bad, and the Ugly: https://ipads.se.sjtu.edu.cn/_media/publications/concerto-sigmod22.pdf

### EXAMPLE OUTPUT ###

Generating Mastodon increment counter cache simulation
['w-cached_tallies(17, 84)']
['w-cached_tallies(47, 10)']
['w-cached_tallies(143, 61)', 'r-poll(143)', 'w-cached_tallies(143, 61)']
['w-cached_tallies(8, 70)', 'r-poll(8)', 'w-cached_tallies(8, 70)']
['w-cached_tallies(93, 58)']

Generating Mastodon create account simulation
['w-account(781)']
['w-account(769)']
['w-account(516)']
['w-account(317)']
['w-account(582)']

Generating Mastodon update account simulation
['w-account(591)']
['w-account(727)']
['w-account(388)']
['w-account(816)']
['w-account(392)']

Generating Mastodon call simulation
['w-[account(468), choice(4)]', 'w-[account(468), choice(2)]', 'w-[account(468), choice(1)]', 'w-[account(468), choice(8)]']
['w-[account(624), choice(7)]', 'w-[account(624), choice(5)]', 'w-[account(624), choice(0)]', 'w-[account(624), choice(1)]']
['w-[account(664), choice(7)]', 'w-[account(664), choice(0)]', 'w-[account(664), choice(4)]', 'w-[account(664), choice(3)]']
['w-[account(515), choice(5)]', 'w-[account(515), choice(0)]', 'w-[account(515), choice(6)]']
['w-[account(393), choice(1)]', 'w-[account(393), choice(0)]', 'w-[account(393), choice(8)]', 'w-[account(393), choice(8)]']

Generating Mastodon process status simulation
['w-status(122)']
['w-status(23)']
['w-status(840)']
['w-status(378)']
['w-status(558)']

Generating Mastodon process emoji simulation
['w-emoji(529)']
['w-emoji(886)']
['w-emoji(280)']
['w-emoji(203)']
['w-emoji(364)']

Generating Mastodon create backup simulation
['w-backup(873)']
['w-backup(413)']
['w-backup(508)']
['w-backup(384)']
['w-backup(356)']

Generating Mastodon show media attachment simulation
['r-media_attachments(110)']
['r-media_attachments(497)']
['r-media_attachments(935)']
['r-media_attachments(200)']
['r-media_attachments(439)', 'w-media_attachments(439)']

Generating Mastodon create marker simulation
['r-markers(780)', 'w-markers(780)']
['r-markers(794)', 'w-markers(794)', 'r-markers(58)', 'w-markers(58)']
['r-markers(746)', 'w-markers(746)', 'r-markers(540)', 'w-markers(540)', 'r-markers(982)', 'w-markers(982)']
['r-markers(174)', 'w-markers(174)']
['r-markers(924)', 'w-markers(924)', 'r-markers(344)', 'w-markers(344)']
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

    We represent every account as an integer between 1 and 1000. The read occurs in update_account().
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
    In: accounts, account_id

    TRANSACTION START
    account = SELECT * FROM accounts WHERE id = account_id
    // ... Set account attributes
    INSERT INTO accounts VALUES account
    TRANSACTION COMMIT

    We represent every account as an integer between 1 and 1000.
    """
    t = Transaction()
    account_id = np.random.choice(1000)
    t.append_read(f"account({account_id})")
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
        t = call(
            np.random.choice(1000),
            None,
            [np.random.choice(10) for _ in range(int(round(np.random.normal(3, 1))))],
        )
        print(t)


### Transaction 4.5 ###
def deliver_votes():
    """
    Deliver vote totals
    Source code: https://github.com/mastodon/mastodon/blob/main/app/services/vote_service.rb#L9C1-L43C10

    Pseudocode:
    votes = SELECT * FROM poll
    for vote in votes:
        send(vote)

    This is the associated read for transaction 4.
    """
    t = Transaction()
    t.append_read(f"votes")
    return t


def deliver_votes_sim(num_transactions):
    for _ in range(num_transactions):
        t = deliver_votes()
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


### Transaction 5.5 ###
def find_existing_status():
    """
    Find status that was inserted using Transaction 5. This is the read associated with Transaction 5.
    Source code: https://github.com/mastodon/mastodon/blob/main/app/lib/activitypub/activity/create.rb#L79C1-L83C6

    Pseudocode:
    In: status, status_id
    SELECT * FROM status WHERE id=status_id
    """
    t = Transaction()
    new_status = np.random.choice(1000)
    t.append_write(f"status({new_status})")
    return t


def find_existing_status_sim(num_transactions: int):
    for _ in range(num_transactions):
        t = find_existing_status()
        print(t)


### Transaction 6 ###
def process_emoji(tag):
    """
    Purpose: Process emoji
    Source code: https://github.com/mastodon/mastodon/blob/main/app/lib/activitypub/activity/create.rb#L254C1-L272C6

    Pseudocode:
    In: emojis
    emoji = SELECT * FROM emojis WHERE tag=tag
    return if emoji is not nil
    # Otherwise:
    TRANSACTION START
    INSERT INTO emojis VALUES new_emoji()
    TRANSACTION COMMIT
    """
    emoji = np.random.choice(1000)
    t = Transaction()
    t.append_read(f"emoji{emoji}")
    if np.random.choice(2):
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
    TRANSACTION START
    media_attachment = SELECT * FROM media_attachments WHERE id=id
    authorize(media_attachment)
    if media_attachment.needs_redownload:
        download_file(id)
        media_attachment.created_at = now
        INSERT INTO media_attachments VALUES media_attachment, id
    TRANSACTION COMMIT
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


### Transaction 9 ###
def create_marker(request):
    """
    Purpose: Create a marker
    Source code: https://github.com/mastodon/mastodon/blob/main/app/controllers/api/v1/markers_controller.rb#L17C2-L31C1
    Pseudocode:
    In: markers
    TRANSACTION START
    for timeline in range(request):
        marker = SELECT * FROM markers WHERE timeline=timeline
        set_attributes(marker, request)
        UPDATE markers SET marker = marker WHERE timeline = timeline
    TRANSACTION COMMIT
    """
    t = Transaction()
    for _ in range(request):
        marker = np.random.choice(1000)
        t.append_read(f"markers({marker})")
        t.append_write(f"markers({marker})")
    return t


def create_marker_sim(num_transactions: int):
    """
    Example output:

    ['r-markers(780)', 'w-markers(780)']
    ['r-markers(794)', 'w-markers(794)', 'r-markers(58)', 'w-markers(58)']
    ['r-markers(746)', 'w-markers(746)', 'r-markers(540)', 'w-markers(540)', 'r-markers(982)', 'w-markers(982)']
    ['r-markers(174)', 'w-markers(174)']
    ['r-markers(924)', 'w-markers(924)', 'r-markers(344)', 'w-markers(344)']
    """
    for _ in range(num_transactions):
        t = create_marker(round(np.random.normal(2, 0.75)))
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
    num_transactions_9 = 5

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

    # Transaction 9
    print("Generating Mastodon create marker simulation")
    create_marker_sim(num_transactions_9)
    print()


if __name__ == "__main__":
    main()
