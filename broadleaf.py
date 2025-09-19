"""
Transaction simulations for BroadleafCommerce: https://github.com/BroadleafCommerce
Uses PostgreSQL, MySQL
Analyzed in Tang et al. Ad Hoc Transactions in Web Applications: The Good, 
the Bad, and the Ugly: https://ipads.se.sjtu.edu.cn/_media/publications/concerto-sigmod22.pdf

### EXAMPLE OUTPUT ###

Generating Broadleaf update cart simulation
['r-cart(6)', 'w-order(21)']
['r-cart(48)', 'w-order(67)']
['r-cart(97)', 'w-order(50)']
['r-cart(45)', 'w-order(54)']
['r-cart(98)', 'w-order(97)']

Generating Broadleaf rate item simulation
['r-summary(81)', 'r-detail(20)', 'w-detail(20)/rating(5)', 'w-summary(81)/rating(5)']
['r-summary(42)', 'r-detail(76)', 'w-detail(76)/rating(4)', 'w-summary(42)/rating(4)']
['r-summary(14)', 'r-detail(13)', 'w-detail(13)/rating(6)', 'w-summary(14)/rating(6)']
['r-summary(87)', 'r-detail(48)', 'w-detail(48)/rating(2)', 'w-summary(87)/rating(2)']
['r-summary(26)', 'r-detail(95)', 'w-detail(95)/rating(8)', 'w-summary(26)/rating(8)']

Generating Broadleaf order payment simulation
['r-cart(639)', 'r-customer(224)', 'r-customer_payment(889)', 'w-order_payment(639)']
['r-cart(514)', 'r-customer(763)', 'w-payment(889)', 'r-customer_payment(889)']
['r-cart(632)', 'r-customer(427)', 'w-payment(889)']
['r-cart(410)', 'r-customer(314)', 'w-payment(889)', 'r-customer_payment(889)', 'w-order_payment(410)']
['r-cart(923)', 'r-customer(104)', 'r-customer_payment(889)']

Generating Broadleaf save offer simulation
['w-offerCode(889)', 'w-offer(889)']
['w-offerCode(424)', 'w-offer(424)']
['w-offerCode(938)', 'w-offer(938)']
['w-offerCode(609)', 'w-offer(609)']
['w-offerCode(100)', 'w-offer(100)']

Generating Broadleaf get offer simulation
['r-offer(669)']
['r-offer(294)']
['r-offer(710)']
['r-offer(816)']
['r-offer(340)']

Generating Broadleaf get next id simulation
['r-id(4)', 'w-id(4)']
['r-id(3)', 'w-id(3)']
['r-id(14)', 'w-id(14)']
['r-id(86)', 'w-id(86)', 'w-id(86)']
['r-id(11)', 'w-id(11)', 'w-id(11)']

Generating Broadleaf decrement SKU simulation
['r-quantity(21)', 'w-quantity(21)', 'r-quantity(27)', 'w-quantity(27)', 'r-quantity(63)', 'w-quantity(63)', 'r-quantity(65)', 'w-quantity(65)']
['r-quantity(27)', 'w-quantity(27)', 'r-quantity(80)', 'w-quantity(80)', 'r-quantity(32)', 'w-quantity(32)', 'r-quantity(6)', 'w-quantity(6)']
['r-quantity(58)', 'w-quantity(58)', 'r-quantity(93)', 'w-quantity(93)', 'r-quantity(91)', 'w-quantity(91)', 'r-quantity(63)', 'w-quantity(63)']
['r-quantity(38)', 'w-quantity(38)', 'r-quantity(71)', 'w-quantity(71)', 'r-quantity(19)', 'w-quantity(19)', 'r-quantity(7)', 'w-quantity(7)']
['r-quantity(57)', 'w-quantity(57)', 'r-quantity(2)', 'w-quantity(2)', 'r-quantity(77)', 'w-quantity(77)', 'r-quantity(61)', 'w-quantity(61)']
"""

import numpy as np
from transaction import Transaction

#################################
####   Simulator functions   ####
#################################

### Transaction 1 ###
def do_filter_internal_unless_ignored(request: tuple[int, int], response, chain):
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
        transaction = do_filter_internal_unless_ignored((cart_id, order_id), None, None)
        print(transaction)

### Transaction 2 ###
def rate_item(item_id, type, customer, rating):
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
    t.append_read(f"summary({item_id})")
    t.append_read(f"detail({customer})")
    t.append_write(f"detail({customer})/rating({rating})")
    t.append_write(f"summary({item_id})/rating({rating})")
    return t

def rate_item_sim(num_transactions: int):
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
        transaction = rate_item(np.random.choice(range(num_items)),
                               None,
                               np.random.choice(range(num_customers)),
                               np.random.choice(ratings))
        print(transaction)

### Transaction 3 ###
def savePaymentInfo(request, response, model, payment_form, result):
    """
    Purpose: save payment information
    Github: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework-web/src/main/java/org/broadleafcommerce/core/web/controller/checkout/BroadleafPaymentInfoController.java#L73C1-L104C1
    
    Pseudocode:

    In: carts, customers, saved_payments, customer_payments, order_payments

    TRANSACTION START
    cart = SELECT * FROM carts WHERE id=cart_id
    customer = SELECT * FROM customers WHERE id=customer_id
    if payment_form.should_save_new_payment and !payment_form.should_use_customer_payment:
        if customer_payment_id:
            UPDATE saved_payments SET payment=payment_form where customer=customer
        else:
            INSERT INTO saved_payments (customer, payment_form)
            payment_form.should_use_customer_payment = True
    if payment_form.should_use_customer_payment:
        customer_payment = SELECT * FROM customer_payments WHERE id = payment_form.get_customer_id()
        if (SELECT * FROM cart_state WHERE token == customer_payment.token) == NULL:
            orderPayment = createOrderPayment(order, customerPayment)
            INSERT INTO order_payments VALUES (cart.amount, UNCONFIRMED_TRANSACTION_TYPE, orderPayment, customerPayment)
    TRANSACTION COMMIT
    """
    cart_id = np.random.choice(1000)
    customer_id = np.random.choice(1000)
    t = Transaction()
    t.append_read(f"cart({cart_id})")
    t.append_read(f"customer({customer_id})")
    should_use_customer_payment = bool(np.random.choice(2))
    if np.random.choice(2):
        if np.random.choice(2):
            t.append_write(f"payment({payment_form})")
        else:
            t.append_write(f"payment({payment_form})")
            should_use_customer_payment = True
    if should_use_customer_payment:
        t.append_read(f"customer_payment({payment_form})")
        if np.random.choice(2):
            t.append_write(f"order_payment({cart_id})")
    return t

def order_payment_sim(num_transactions: int):
    """
    Example output:

    ['r-cart(670)', 'r-customer(401)']
    ['r-cart(60)', 'r-customer(972)', 'w-payment(177)', 'r-customer_payment(177)']
    ['r-cart(272)', 'r-customer(639)', 'w-payment(177)', 'r-customer_payment(177)', 'w-order_payment(272)']
    ['r-cart(961)', 'r-customer(260)', 'w-payment(177)']
    ['r-cart(226)', 'r-customer(439)', 'w-payment(177)', 'r-customer_payment(177)', 'w-order_payment(226)']
    """
    payment_form = np.random.choice(1000)
    for _ in range(num_transactions):
        t = savePaymentInfo(None, None, None, payment_form, None)
        print(t)

### Transaction 4 ###
def save_offer_code(offer_code):
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
    t.append_write(f"offerCode({offer_code})")
    t.append_write(f"offer({offer_code})")
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
        transaction = save_offer_code(np.random.choice(range(num_offer_codes)))
        print(transaction)

### Transaction 5 ###
def lookup_offer_by_code(code):
    """
    Purpose: Retrieve offer corresponding to given code
    Github: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework/src/main/java/org/broadleafcommerce/core/offer/service/OfferServiceImpl.java#L156C4-L163C6

    Pseudocode: 

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
        transaction = lookup_offer_by_code(np.random.choice(range(num_offer_codes)))
        print(transaction)

### Transaction 6 ###
def find_next_id(id_type, batch_size):
    """
    Purpose: Generate the next id based on idType and batchSize
    Github: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/common/src/main/java/org/broadleafcommerce/common/id/service/IdGenerationServiceImpl.java#L49C5-L80C6

    Pseudocode:
    in: idMap

    TRANSACTION START
    id = SELECT id FROM idMap WHERE type=idType
    if (id == NULL):
        id = new ID(idType, batchSize)
        INSERT INTO idMap VALUES (id, idType)
    ret = id.nextID++
    id.batchsize--
    UPDATE idMap SET id=id WHERE type=idType
    TRANSACTION COMMIT
    """
    t = Transaction()
    t.append_read(f"id({id_type})")
    if (np.random.choice(2) == 1):
        t.append_write(f"id({id_type})")
    t.append_write(f"id({id_type})")
    return t

def get_next_id_sim(num_transactions: int):
    """
    Example output:

    ['r-id(36)', 'w-id(36)', 'w-id(36)']
    ['r-id(83)', 'w-id(83)']
    ['r-id(16)', 'w-id(16)']
    ['r-id(32)', 'w-id(32)']
    ['r-id(88)', 'w-id(88)', 'w-id(88)']
    """
    num_id_types = 100
    for _ in range(num_transactions):
        t = find_next_id(np.random.choice(num_id_types), None)
        print(t)

### Tranasaction 7 ###
def decrement_sku(sku_quantities, context):
    """
    Purpose: Decrement SKU counts for each entry
    Github: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework/src/main/java/org/broadleafcommerce/core/inventory/service/InventoryServiceImpl.java#L203C5-L237C1

    Pseudocode:
    in: sku

    TRANSACTION START
    for entry in skuQuantities.entries:
        SELECT quantity_available FROM sku WHERE sku_id = entry.sku_id
        UPDATE sku SET quantity_available = quantity_available - entry.quantity WHERE sku_id = entry.sku_id
    TRANSACTION COMMIT

    For the simulation, we treat skuQuantities as a list of sku_ids.
    """
    t = Transaction()
    for sku_id in sku_quantities:
        t.append_read(f"quantity({sku_id})")
        t.append_write(f"quantity({sku_id})")
    return t

def decrement_SKU_sim(num_transactions: int):
    """
    Example output:

    ['r-quantity(88)', 'w-quantity(88)', 'r-quantity(25)', 'w-quantity(25)', 'r-quantity(66)', 'w-quantity(66)', 'r-quantity(57)', 'w-quantity(57)']
    ['r-quantity(27)', 'w-quantity(27)', 'r-quantity(36)', 'w-quantity(36)', 'r-quantity(60)', 'w-quantity(60)', 'r-quantity(14)', 'w-quantity(14)']
    ['r-quantity(82)', 'w-quantity(82)', 'r-quantity(28)', 'w-quantity(28)', 'r-quantity(26)', 'w-quantity(26)', 'r-quantity(24)', 'w-quantity(24)']
    ['r-quantity(47)', 'w-quantity(47)', 'r-quantity(45)', 'w-quantity(45)', 'r-quantity(53)', 'w-quantity(53)', 'r-quantity(94)', 'w-quantity(94)']
    ['r-quantity(85)', 'w-quantity(85)', 'r-quantity(55)', 'w-quantity(55)', 'r-quantity(77)', 'w-quantity(77)', 'r-quantity(38)', 'w-quantity(38)']
    """
    for _ in range(num_transactions):
        sku_quantities = np.random.choice(100, 4)
        t = decrement_sku(sku_quantities, None)
        print(t)

#######################
####   Simulation  ####
#######################

def main():
    """
    Generate Broadleaf transaction traces
    """
    # Number of transactions per transaction type.
    num_transactions_1 = 5
    num_transactions_2 = 5
    num_transactions_3 = 5
    num_transactions_4 = 5
    num_transactions_5 = 5
    num_transactions_6 = 5
    num_transactions_7 = 5
    
    # Extra space for formatting
    print()

    # Transaction 1
    print(f"Generating Broadleaf update cart simulation")
    update_order_sim(num_transactions_1)
    print()

    # Transaction 2
    print(f"Generating Broadleaf rate item simulation")
    rate_item_sim(num_transactions_2)
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

    # Transaction 6
    print(f"Generating Broadleaf get next id simulation")
    get_next_id_sim(num_transactions_6)
    print()

    # Transaction 7
    print("Generating Broadleaf decrement SKU simulation")
    decrement_SKU_sim(num_transactions_7)
    print()

if __name__ == "__main__":
    main()