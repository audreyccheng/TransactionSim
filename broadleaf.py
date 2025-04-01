"""
Transaction simulations for BroadleafCommerce: https://github.com/BroadleafCommerce
Uses PostgreSQL, MySQL
Analyzed in Tang et al. Ad Hoc Transactions in Web Applications: The Good, the Bad, and the Ugly: https://ipads.se.sjtu.edu.cn/_media/publications/concerto-sigmod22.pdf

### EXAMPLE OUTPUT ###

Generating Broadleaf update cart simulation
['r-cart(95)', 'w-order(41)']
['r-cart(52)', 'w-order(44)']
['r-cart(65)', 'w-order(19)']
['r-cart(93)', 'w-order(42)']
['r-cart(18)', 'w-order(69)']

Generating Broadleaf rate item simulation
['r-summary(70)', 'r-detail(12)', 'w-detail(12)/rating(1)', 'w-summary(70)/rating(1)']
['r-summary(73)', 'r-detail(86)', 'w-detail(86)/rating(7)', 'w-summary(73)/rating(7)']
['r-summary(47)', 'r-detail(66)', 'w-detail(66)/rating(3)', 'w-summary(47)/rating(3)']
['r-summary(10)', 'r-detail(40)', 'w-detail(40)/rating(9)', 'w-summary(10)/rating(9)']
['r-summary(5)', 'r-detail(9)', 'w-detail(9)/rating(0)', 'w-summary(5)/rating(0)']

Generating Broadleaf order payment simulation
['w-amount(280.57)', 'w-unconfirmed type', 'w-orderPayment((381, 463))', 'w-customerPayment(463)']
['w-amount(238.93)', 'w-unconfirmed type', 'w-orderPayment((639, 949))', 'w-customerPayment(949)']
['w-amount(238.13)', 'w-unconfirmed type', 'w-orderPayment((49, 109))', 'w-customerPayment(109)']
['w-amount(89.48)', 'w-unconfirmed type', 'w-orderPayment((914, 721))', 'w-customerPayment(721)']
['w-amount(229.44)', 'w-unconfirmed type', 'w-orderPayment((609, 153))', 'w-customerPayment(153)']

Generating Broadleaf save offer simulation
['w-offerCode(554)', 'w-offer(554)']
['w-offerCode(386)', 'w-offer(386)']
['w-offerCode(896)', 'w-offer(896)']
['w-offerCode(803)', 'w-offer(803)']
['w-offerCode(52)', 'w-offer(52)']

Generating Broadleaf get offer simulation
['r-offer(331)']
['r-offer(683)']
['r-offer(189)']
['r-offer(519)']
['r-offer(188)']
"""

import numpy as np
from transaction import Transaction

#################################
####   Simulator functions   ####
#################################

### Transaction 1 ###
def doFilterInternalUnlessIgnored(request: tuple[int, int], response, chain):
    """
    Purpose: Update cart with new order
    Source code: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework-web/src/main/java/org/broadleafcommerce/core/web/order/security/CartStateFilter.java#L96C1-L126C64

    Pseudocode:
        In: cart_state, new_order, curr_cart

        TRANSACTION START
        old_order = SELECT * FROM cart_state WHERE cart=curr_cart
        // Acquire cart lock
        UPDATE cart_state SET order = new_order WHERE cart_id=curr_cart
        // Release cart lock
        TRANSACTION COMMIT
    
    For simplicity, we pass in the cart and order information using
    the request argument. Request is a tuple where the first argument is
    the cart_id and the second argument is the new order. 
    """
    cart_id, order_id = request[0], request[1]
    t = Transaction()
    t.append_read(f"cart({cart_id})")
    t.append_write(f"order({order_id})")
    return t

def update_order_sim(num_transactions: int):
    """
    Example output:

    ['r-cart(23)', 'w-order(87)']
    ['r-cart(85)', 'w-order(89)']
    ['r-cart(19)', 'w-order(36)']
    ['r-cart(96)', 'w-order(9)']
    ['r-cart(77)', 'w-order(23)']
    """
    num_carts = 100
    num_orders = 100

    cart_ids = range(num_carts)
    order_ids = range(num_orders)

    for _ in range(num_transactions):
        cart_id = np.random.choice(cart_ids)
        order_id = np.random.choice(order_ids)
        transaction = doFilterInternalUnlessIgnored((cart_id, order_id), None, None)
        print(transaction)

### Transaction 2 ###
def rateItem(itemId, type, customer, rating):
    """
    Purpose: Add a new rating to item
    Github: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework/src/main/java/org/broadleafcommerce/core/rating/service/RatingServiceImpl.java#L73C1-L92C6
    
    Pseudocode:
        In: ratings_summary, ratings_detail

        TRANSACTION START
        summary = SELECT * FROM ratings_summary WHERE itemID = itemID AND type = type
        if !summary:
            create_summary(itemID, type)
        detail = SELECT * FROM ratings_detail WHERE customer_ID = customer.id, rating_id = summary.id
        if !detail:
            create_detail(customer.id, summary.id)
        UPDATE ratings_detail SET rating = rating WHERE customer_ID = customer.id, rating_id = summary.id
        INSERT INTO ratings_summary VALUES (itemID, type, rating, date, customer.id)
        TRANSACTION COMMIT
    
    For simplicity, we treat the itemID as the unique identifier for the item. 
    """
    t = Transaction()
    t.append_read(f"summary({itemId})")
    t.append_read(f"detail({customer})")
    t.append_write(f"detail({customer})/rating({rating})")
    t.append_write(f"summary({itemId})/rating({rating})")
    return t

def rateItem_sim(num_transactions: int):
    """
    Example output:

    ['r-summary(80)', 'r-detail(57)', 'w-detail(57)/rating(3)', 'w-summary(80)/rating(3)']
    ['r-summary(80)', 'r-detail(46)', 'w-detail(46)/rating(9)', 'w-summary(80)/rating(9)']
    ['r-summary(72)', 'r-detail(10)', 'w-detail(10)/rating(5)', 'w-summary(72)/rating(5)']
    ['r-summary(76)', 'r-detail(1)', 'w-detail(1)/rating(5)', 'w-summary(76)/rating(5)']
    ['r-summary(34)', 'r-detail(43)', 'w-detail(43)/rating(5)', 'w-summary(34)/rating(5)']
    """
    num_items = 100
    num_customers = 100
    ratings = range(10)
    for _ in range(num_transactions):
        transaction = rateItem(np.random.choice(range(num_items)),
                               None,
                               np.random.choice(range(num_customers)),
                               np.random.choice(ratings))
        print(transaction)

### Transaction 3 ###
def createOrderPaymentFromCustomerPayment(order, customerPayment, amount):
    """
    Purpose: Save order payment details
    Github: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework/src/main/java/org/broadleafcommerce/core/payment/service/OrderPaymentServiceImpl.java#L106C5-L149C6
    
    Pseudocode:

    In: order_payments
    orderPayment = createOrderPayment(order, customerPayment)
    TRANSACTION START
    INSERT INTO order_payments VALUES (amount, UNCONFIRMED_TRANSACTION_TYPE, orderPayment, customerPayment)
    TRANSACTION COMMIT
    """
    UNCONFIRMED_TRANSACTION_TYPE = "unconfirmed type"
    orderPayment = (order, customerPayment)
    t = Transaction()
    t.append_write(f"amount({amount})")
    t.append_write(UNCONFIRMED_TRANSACTION_TYPE)
    t.append_write(f"orderPayment({orderPayment})")
    t.append_write(f"customerPayment({customerPayment})")
    return t

def order_payment_sim(num_transactions: int):
    """
    Example output:

    ['w-amount(263.53)', 'w-unconfirmed type', 'w-orderPayment((110, 561))', 'w-customerPayment(561)']
    ['w-amount(183.57)', 'w-unconfirmed type', 'w-orderPayment((379, 504))', 'w-customerPayment(504)']
    ['w-amount(238.83)', 'w-unconfirmed type', 'w-orderPayment((498, 520))', 'w-customerPayment(520)']
    ['w-amount(257.33)', 'w-unconfirmed type', 'w-orderPayment((681, 509))', 'w-customerPayment(509)']
    ['w-amount(221.4)', 'w-unconfirmed type', 'w-orderPayment((223, 859))', 'w-customerPayment(859)']
    """
    num_orders = 1000
    num_customerPayment = 1000
    for _ in range(num_transactions):
        transaction = createOrderPaymentFromCustomerPayment(np.random.choice(range(num_orders)),
                                                            np.random.choice(range(num_customerPayment)),
                                                            round(np.random.normal(200, 50), 2))
        print(transaction)

### Transaction 4 ###
def saveOfferCode(offerCode):
    """
    Purpose: Save offer code
    Github: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework/src/main/java/org/broadleafcommerce/core/offer/service/OfferServiceImpl.java#L140C1-L145C6
    
    Pseudocode:
    In: offers

    TRANSACTION START
    INSERT INTO offers VALUES offerCode, offer
    TRANSACTION COMMIT

    For simplicity, we represent the offer and offerCode with the same index.
    """
    t = Transaction()
    t.append_write(f"offerCode({offerCode})")
    t.append_write(f"offer({offerCode})")
    return t

def save_offer_sim(num_transactions: int):
    """
    Example output

    ['w-offerCode(422)']
    ['w-offerCode(723)']
    ['w-offerCode(332)']
    ['w-offerCode(304)']
    ['w-offerCode(325)']
    """
    num_offer_codes = 1000
    for _ in range(num_transactions):
        transaction = saveOfferCode(np.random.choice(range(num_offer_codes)))
        print(transaction)

### Transaction 5 ###
def lookupOfferByCode(code):
    """
    Purpose: Retrieve offer corresponding to given code
    Github: 

    Pseudocode: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework/src/main/java/org/broadleafcommerce/core/offer/service/OfferServiceImpl.java#L156C4-L163C6
    
    In: offers
    TRANSACTION START
    SELECT offer FROM offers WHERE offerCode == code
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"offer({code})")
    return t

def get_offer_sim(num_transactions: int):
    """
    Example output:

    ['r-offer(381)']
    ['r-offer(528)']
    ['r-offer(456)']
    ['r-offer(205)']
    ['r-offer(988)']
    """
    num_offer_codes = 1000
    for _ in range(num_transactions):
        transaction = lookupOfferByCode(np.random.choice(range(num_offer_codes)))
        print(transaction)

#######################
####   Simulation  ####
#######################

def main():
    """
    Generate Broadleaf transaction traces
    """
    num_transactions_1 = 5
    num_transactions_2 = 5
    num_transactions_3 = 5
    num_transactions_4 = 5
    num_transactions_5 = 5
    
    # Extra space for formatting
    print()

    # Transaction 1
    print(f"Generating Broadleaf update cart simulation")
    update_order_sim(num_transactions_1)
    print()

    # Transaction 2
    print(f"Generating Broadleaf rate item simulation")
    rateItem_sim(num_transactions_2)
    print()

    # Transaction 3
    print(f"Generating Broadleaf order payment simulation")
    order_payment_sim(num_transactions_3)
    print()

    # Transaction 4
    print(f"Generating Broadleaf save offer simulation")
    save_offer_sim(num_transactions_4)
    print()

    # Transaction 5
    print(f"Generating Broadleaf get offer simulation")
    get_offer_sim(num_transactions_5)
    print()

if __name__ == "__main__":
    main()