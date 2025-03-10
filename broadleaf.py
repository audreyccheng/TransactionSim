
import numpy as np
from transaction import Transaction

### Transaction 1 ###
def doFilterInternalUnlessIgnored(request, response, chain):
    """
    Purpose: Update cart with new order
    Source code: https://github.com/BroadleafCommerce/BroadleafCommerce/blob/develop-7.0.x/core/broadleaf-framework/src/main/java/org/broadleafcommerce/core/payment/service/OrderPaymentServiceImpl.java#L106C5-L149C6

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
    t.append_read(cart_id)
    t.append_write(order_id)
    return t

def broadleaf_update_order_sim(num_transactions: int):
    """
    Example output:

    ['r-5', 'w-7']
    ['r-76', 'w-55']
    ['r-3', 'w-49']
    ['r-95', 'w-73']
    ['r-80', 'w-37']
    ['r-40', 'w-99']
    ['r-17', 'w-55']
    ['r-82', 'w-78']
    ['r-36', 'w-95']
    ['r-7', 'w-40']
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
def transaction_2():
    # TODO
    pass

def main():
    broadleaf_update_order_sim(10) # Transaction 1
    
if __name__ == "__main__":
    main()